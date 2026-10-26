"""DynamoDB persistence for Konforme.

Everything lives in one table. Each model declares where its items go:

    __partition__ = ("Account", "account_id")  ->  PK = "Account#<account_id>"
    __sort__      = ("id",)                     ->  SK = "<ModelName>#<id>"

so "all scans of an account" is a single Query on PK with an SK prefix. Children of
a non-account parent (scan results, plan milestones, ...) use the parent as their
partition, e.g. ("Scan", "scan_id"). Reference data uses ("Ref", None).

Global secondary indexes:
    by-entity  (entity, eid)  every item: get by id without knowing the partition,
                              and list every item of a model (daily jobs)
    lk_email / lk_token / lk_verify / lk_reset
                              sparse lookups for values that must be found without
                              an account (login email, invite/reset/verify tokens, ...)

Session is a small unit of work that mirrors how the code used SQLAlchemy:
objects read through a session are tracked, changes are written on commit()
(atomically when they fit in one DynamoDB transaction), rollback() discards them.
Reads see the session's own pending adds/deletes.
"""

from __future__ import annotations

import dataclasses
import enum
import types
import typing
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import lru_cache

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from config import settings

ENTITY_INDEX = "by-entity"
LOOKUP_INDEXES = ("lk_email", "lk_token", "lk_verify", "lk_reset")
TRANSACTION_LIMIT = 100



class IntegrityError(Exception):
    """A write would break a uniqueness rule (duplicate key, email already taken...)."""


# --- table access ---------------------------------------------------------------


def _boto_kwargs() -> dict:
    kwargs = {"region_name": settings.dynamodb_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return kwargs


@lru_cache(maxsize=1)
def _resource():
    return boto3.resource("dynamodb", **_boto_kwargs())


def table():
    return _resource().Table(settings.dynamodb_table)


def _client():
    return _resource().meta.client


def reset_connections() -> None:
    """Forget cached boto3 handles (tests switch endpoints/mocks between runs)."""
    _resource.cache_clear()


def create_table() -> None:
    """Create the table and indexes (tests and local development; Terraform owns production)."""
    attrs = [("PK", "S"), ("SK", "S"), ("entity", "S"), ("eid", "S")] + [(name, "S") for name in LOOKUP_INDEXES]
    gsis = [
        {
            "IndexName": ENTITY_INDEX,
            "KeySchema": [{"AttributeName": "entity", "KeyType": "HASH"}, {"AttributeName": "eid", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "ALL"},
        }
    ] + [
        {
            "IndexName": name,
            "KeySchema": [{"AttributeName": name, "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "KEYS_ONLY"},
        }
        for name in LOOKUP_INDEXES
    ]
    _client().create_table(
        TableName=settings.dynamodb_table,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": n, "AttributeType": t} for n, t in attrs],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        GlobalSecondaryIndexes=gsis,
    )
    _client().get_waiter("table_exists").wait(TableName=settings.dynamodb_table)


def ping() -> None:
    """Cheap connectivity check for /health."""
    table().get_item(Key={"PK": "Health", "SK": "Health"})


def next_sequence(name: str) -> int:
    """Atomically increment and return a named counter (replaces SQL autoincrement)."""
    resp = table().update_item(
        Key={"PK": "Counter", "SK": name},
        UpdateExpression="ADD #v :one",
        ExpressionAttributeNames={"#v": "value"},
        ExpressionAttributeValues={":one": 1},
        ReturnValues="UPDATED_NEW",
    )
    return int(resp["Attributes"]["value"])


# --- model metadata -------------------------------------------------------------


def _meta(cls, name, default):
    return getattr(cls, name, default)


def _key_part(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return f"{value:012d}"  # zero-padded so SK order matches numeric order
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return "" if value is None else str(value)


def partition_key(cls, partition_value) -> str:
    prefix, field = cls.__partition__
    if field is None:
        return f"{prefix}#{cls.__name__}"
    return f"{prefix}#{_key_part(partition_value) or 'GLOBAL'}"


def _key_of(obj) -> tuple[str, str]:
    cls = type(obj)
    _, field = cls.__partition__
    pk = partition_key(cls, getattr(obj, field) if field else None)
    sort_fields = _meta(cls, "__sort__", ("id",))
    sk = "#".join([cls.__name__] + [_key_part(getattr(obj, f)) for f in sort_fields])
    return pk, sk


def _sk_prefix(cls) -> str:
    return f"{cls.__name__}#"


@lru_cache(maxsize=None)
def _field_types(cls) -> dict[str, type]:
    hints = typing.get_type_hints(cls)
    out = {}
    for f in dataclasses.fields(cls):
        tp = hints[f.name]
        if typing.get_origin(tp) in (typing.Union, types.UnionType):
            args = [a for a in typing.get_args(tp) if a is not type(None)]
            tp = args[0] if len(args) == 1 else str
        out[f.name] = tp
    return out


# --- (de)serialisation ----------------------------------------------------------


def _to_attr(value):
    if isinstance(value, enum.Enum):
        value = value.value
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _to_attr(v) for k, v in value.items() if v is not None}
    if isinstance(value, (list, tuple)):
        return [_to_attr(v) for v in value]
    return value


def _from_attr(tp, value):
    if value is None:
        return None
    if tp is datetime:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if tp is date:
        return date.fromisoformat(value[:10])
    if tp is bool:
        return bool(value)
    if tp is int:
        return int(value)
    if tp is float:
        return float(value)
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def to_item(obj) -> dict:
    """Model instance -> DynamoDB item (keys, index attributes and fields)."""
    cls = type(obj)
    pk, sk = _key_of(obj)
    item = {"PK": pk, "SK": sk, "entity": cls.__name__, "eid": _key_part(obj.id)}
    for f in dataclasses.fields(cls):
        value = getattr(obj, f.name)
        if value is not None:
            item[f.name] = _to_attr(value)
    for index, field in _meta(cls, "__lookups__", {}).items():
        value = getattr(obj, field)
        if value:
            item[index] = f"{cls.__name__}#{value}"
    return item


def _from_item(cls, item: dict):
    hints = _field_types(cls)
    kwargs = {name: _from_attr(tp, item.get(name)) for name, tp in hints.items() if name in item}
    obj = cls(**kwargs)
    # Fields absent from the item are stored NULLs, not "use the default"
    for name in hints:
        if name not in item:
            setattr(obj, name, None)
    return obj


def _guard_keys(obj, item: dict | None = None) -> dict[str, dict]:
    """Uniqueness guard items: one per declared unique field with a value."""
    cls = type(obj)
    item = item if item is not None else to_item(obj)
    out = {}
    for field in _meta(cls, "__unique__", ()):
        value = item.get(field)
        if value:
            key = {"PK": f"Unique#{cls.__name__}.{field}#{value}", "SK": "Unique"}
            out[key["PK"]] = key
    return out


def _children_of(cls) -> list[type]:
    from models import ALL_MODELS

    return [
        m for m in ALL_MODELS
        if m is not cls and m.__partition__[0] == cls.__name__ and m.__partition__[1] is not None
    ]


# --- session --------------------------------------------------------------------


class Session:
    def __init__(self):
        self._table = table()
        self._identity: dict[tuple[str, str], object] = {}
        self._snapshots: dict[tuple[str, str], dict] = {}
        self._new: list = []
        self._deleted: dict[tuple[str, str], object] = {}
        # Partition query results, reused until the next commit/rollback (avoids N+1 reads)
        self._partition_cache: dict[tuple[str, str], list[dict]] = {}

    # context-manager / SQLAlchemy-compatible no-ops
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        pass

    def flush(self):
        pass

    def refresh(self, obj):
        pass

    # --- tracking ---

    def _attach(self, obj):
        obj._session = self
        return obj

    def _materialize(self, cls, item):
        key = (item["PK"], item["SK"])
        if key in self._deleted:
            return None
        existing = self._identity.get(key)
        if existing is not None:
            return existing
        obj = self._attach(_from_item(cls, item))
        self._identity[key] = obj
        self._snapshots[key] = to_item(obj)
        return obj

    def _pending(self, cls, predicate=lambda o: True):
        return [o for o in self._new if type(o) is cls and predicate(o)]

    def _query_all(self, **kwargs) -> list[dict]:
        items, start = [], None
        while True:
            if start:
                kwargs["ExclusiveStartKey"] = start
            resp = self._table.query(**kwargs)
            items.extend(resp["Items"])
            start = resp.get("LastEvaluatedKey")
            if not start:
                return items

    def _get_item(self, key: dict) -> dict | None:
        return self._table.get_item(Key=key, ConsistentRead=True).get("Item")

    # --- reads ---

    def get(self, cls, id):
        """Fetch one object by id (any partition)."""
        if id is None:
            return None
        for obj in self._pending(cls, lambda o: o.id == id):
            return obj
        for key, obj in self._identity.items():
            if type(obj) is cls and obj.id == id and key not in self._deleted:
                return obj
        hits = self._table.query(
            IndexName=ENTITY_INDEX,
            KeyConditionExpression=Key("entity").eq(cls.__name__) & Key("eid").eq(_key_part(id)),
        )["Items"]
        if not hits:
            return None
        # The index is eventually consistent; re-read the item itself for current data
        item = self._get_item({"PK": hits[0]["PK"], "SK": hits[0]["SK"]})
        return self._materialize(cls, item) if item else None

    def get_by_key(self, cls, partition_value=None, **sort_values):
        """Fetch one object by its full key, e.g. get_by_key(AccountControl, account_id, control_id=...)."""
        probe = {f.name: None for f in dataclasses.fields(cls) if f.name in sort_values}
        probe.update(sort_values)
        pk = partition_key(cls, partition_value)
        sk = "#".join([cls.__name__] + [_key_part(probe[f]) for f in _meta(cls, "__sort__", ("id",))])
        key = (pk, sk)
        if key in self._deleted:
            return None
        if key in self._identity:
            return self._identity[key]
        for obj in self._pending(cls, lambda o: _key_of(o) == key):
            return obj
        item = self._get_item({"PK": pk, "SK": sk})
        return self._materialize(cls, item) if item else None

    def list(self, cls, partition_value=None) -> list:
        """All objects of a model in one partition (e.g. every Scan of an account)."""
        pk = partition_key(cls, partition_value)
        cache_key = (pk, cls.__name__)
        items = self._partition_cache.get(cache_key)
        if items is None:
            items = self._query_all(
                KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(_sk_prefix(cls)),
                ConsistentRead=True,
            )
            self._partition_cache[cache_key] = items
        found = [o for o in (self._materialize(cls, i) for i in items) if o is not None]
        seen = {id(o) for o in found}
        found += [o for o in self._pending(cls, lambda o: _key_of(o)[0] == pk) if id(o) not in seen]
        return found

    def last(self, cls, partition_value=None):
        """The object with the highest sort key in a partition (e.g. newest audit entry)."""
        pk = partition_key(cls, partition_value)
        items = self._table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(_sk_prefix(cls)),
            ScanIndexForward=False,
            Limit=5,  # a few spare in case the newest were deleted in this session
            ConsistentRead=True,
        )["Items"]
        candidates = [o for o in (self._materialize(cls, i) for i in items) if o is not None]
        candidates += self._pending(cls, lambda o: _key_of(o)[0] == pk)
        return max(candidates, key=lambda o: _key_of(o)[1], default=None)

    def all(self, cls) -> list:
        """Every object of a model across all partitions (daily jobs, reference data)."""
        if cls.__partition__[1] is None:
            return self.list(cls)
        items = self._query_all(IndexName=ENTITY_INDEX, KeyConditionExpression=Key("entity").eq(cls.__name__))
        found = [o for o in (self._materialize(cls, i) for i in items) if o is not None]
        seen = {id(o) for o in found}
        return found + [o for o in self._pending(cls) if id(o) not in seen]

    def lookup(self, cls, field: str, value):
        """Find the object whose unique lookup field equals value (email, token, ...)."""
        if not value:
            return None
        for obj in self._pending(cls, lambda o: getattr(o, field) == value):
            return obj
        index = next(i for i, f in cls.__lookups__.items() if f == field)
        hits = self._table.query(
            IndexName=index,
            KeyConditionExpression=Key(index).eq(f"{cls.__name__}#{value}"),
        )["Items"]
        for hit in hits:
            item = self._get_item({"PK": hit["PK"], "SK": hit["SK"]})
            if item and item.get(field) == value:
                obj = self._materialize(cls, item)
                if obj is not None and getattr(obj, field) == value:
                    return obj
        return None

    # --- writes ---

    def add(self, obj):
        if getattr(obj, "_session", None) is self:
            return
        self._attach(obj)
        self._new.append(obj)

    def add_all(self, objs):
        for obj in objs:
            self.add(obj)

    def delete(self, obj):
        if obj in self._new:
            self._new.remove(obj)
            return
        for key, tracked in self._identity.items():
            if tracked is obj:
                self._deleted[key] = obj
                return
        raise ValueError("delete() of an object this session did not load")

    def rollback(self):
        for key, obj in self._identity.items():
            snap = self._snapshots[key]
            fresh = _from_item(type(obj), snap)
            for f in dataclasses.fields(obj):
                setattr(obj, f.name, getattr(fresh, f.name))
        self._new.clear()
        self._deleted.clear()
        self._partition_cache.clear()

    def commit(self):
        ops: list[dict] = []
        touched_now = datetime.now(timezone.utc)

        # Deletes (with cascade into child partitions)
        for key, obj in self._deleted.items():
            self._delete_ops(obj, self._snapshots[key], ops)

        # Updates of tracked objects
        for key, obj in self._identity.items():
            if key in self._deleted:
                continue
            old = self._snapshots[key]
            new = to_item(obj)
            if new == old:
                continue
            for field in _meta(type(obj), "__onupdate__", ()):
                setattr(obj, field, touched_now)
            new = to_item(obj)
            if (new["PK"], new["SK"]) != key:
                ops.append({"Delete": {"Key": {"PK": key[0], "SK": key[1]}}})
                ops.append(self._put_op(new, must_be_new=True))
            else:
                ops.append(self._update_op(key, old, new))
            old_guards, new_guards = _guard_keys(obj, old), _guard_keys(obj, new)
            for pk in old_guards.keys() - new_guards.keys():
                ops.append({"Delete": {"Key": old_guards[pk]}})
            for pk in new_guards.keys() - old_guards.keys():
                ops.append(self._put_op(new_guards[pk], must_be_new=True))

        # Inserts
        for obj in self._new:
            item = to_item(obj)
            ops.append(self._put_op(item, must_be_new=True))
            for guard in _guard_keys(obj, item).values():
                ops.append(self._put_op(guard, must_be_new=True))

        self._execute(ops)

        # Reset tracking to the committed state
        for key in list(self._deleted):
            self._identity.pop(key, None)
            self._snapshots.pop(key, None)
        self._deleted.clear()
        rekeyed = {}
        for key, obj in list(self._identity.items()):
            new_key = _key_of(obj)
            if new_key != key:
                self._snapshots.pop(key)
                del self._identity[key]
            rekeyed[new_key] = obj
        for obj in self._new:
            rekeyed[_key_of(obj)] = obj
        self._identity = rekeyed
        self._snapshots = {k: to_item(o) for k, o in self._identity.items()}
        self._new.clear()
        self._partition_cache.clear()

    # --- write helpers ---

    def _delete_ops(self, obj, snapshot: dict, ops: list):
        ops.append({"Delete": {"Key": {"PK": snapshot["PK"], "SK": snapshot["SK"]}}})
        for guard in _guard_keys(obj, snapshot).values():
            ops.append({"Delete": {"Key": guard}})
        for child_cls in _children_of(type(obj)):
            items = self._query_all(
                KeyConditionExpression=Key("PK").eq(partition_key(child_cls, obj.id))
                & Key("SK").begins_with(_sk_prefix(child_cls)),
                ConsistentRead=True,
            )
            for item in items:
                child = _from_item(child_cls, item)
                self._delete_ops(child, to_item(child), ops)

    def _put_op(self, item: dict, must_be_new: bool) -> dict:
        op = {"Put": {"Item": item}}
        if must_be_new:
            op["Put"]["ConditionExpression"] = "attribute_not_exists(PK)"
        return op

    def _update_op(self, key, old: dict, new: dict) -> dict:
        sets, removes, names, values = [], [], {}, {}
        for i, name in enumerate(sorted((old.keys() | new.keys()) - {"PK", "SK"})):
            if old.get(name) == new.get(name):
                continue
            names[f"#a{i}"] = name
            if name in new:
                values[f":v{i}"] = new[name]
                sets.append(f"#a{i} = :v{i}")
            else:
                removes.append(f"#a{i}")
        expr = " ".join(p for p in (
            "SET " + ", ".join(sets) if sets else "",
            "REMOVE " + ", ".join(removes) if removes else "",
        ) if p)
        op = {"Update": {"Key": {"PK": key[0], "SK": key[1]}, "UpdateExpression": expr, "ExpressionAttributeNames": names}}
        if values:
            op["Update"]["ExpressionAttributeValues"] = values
        return op

    @staticmethod
    def _merge_ops(ops: list[dict]) -> list[dict]:
        """A delete followed by a put of the same key (delete-and-reinsert) becomes one overwrite.

        DynamoDB rejects two operations on the same item in one transaction.
        """
        def key_of(op):
            kind, body = next(iter(op.items()))
            src = body["Item"] if kind == "Put" else body["Key"]
            return src["PK"], src["SK"]

        put_keys = {key_of(op) for op in ops if "Put" in op}
        deleted_keys = {key_of(op) for op in ops if "Delete" in op}
        replaced = put_keys & deleted_keys
        merged = []
        for op in ops:
            key = key_of(op)
            if key in replaced:
                if "Delete" in op:
                    continue
                op = {"Put": {k: v for k, v in op["Put"].items() if k != "ConditionExpression"}}
            merged.append(op)
        return merged

    def _execute(self, ops: list[dict]):
        ops = self._merge_ops(ops)
        if not ops:
            return
        # Large cascades/seeds cannot be one transaction; apply them in chunks
        for start in range(0, len(ops), TRANSACTION_LIMIT):
            chunk = ops[start:start + TRANSACTION_LIMIT]
            try:
                _client().transact_write_items(TransactItems=[self._with_table(op) for op in chunk])
            except ClientError as e:
                if e.response["Error"]["Code"] == "TransactionCanceledException":
                    reasons = e.response.get("CancellationReasons", [])
                    if any(r.get("Code") == "ConditionalCheckFailed" for r in reasons):
                        raise IntegrityError("Duplicate key or unique value") from e
                raise

    def _with_table(self, op: dict) -> dict:
        # The resource's client serialises Python values itself; only add the table name
        kind, body = next(iter(op.items()))
        return {kind: dict(body, TableName=settings.dynamodb_table)}


# --- ordering helpers (match PostgreSQL: NULLs sort as the largest value) -------


def order_by(objs, *attrs: str, desc: bool = False) -> list:
    """Sort like ORDER BY a, b [DESC]: NULLs last ascending, first descending."""
    def key(o):
        return tuple((getattr(o, a) is None, getattr(o, a)) if getattr(o, a) is not None else (True, 0) for a in attrs)
    return sorted(objs, key=key, reverse=desc)


def newest(objs, attr: str):
    """First row of ORDER BY attr DESC, or None."""
    ordered = order_by(objs, attr, desc=True)
    return ordered[0] if ordered else None


def session_of(obj) -> Session:
    session = getattr(obj, "_session", None)
    if session is None:
        raise RuntimeError(f"{type(obj).__name__} is not attached to a session")
    return session


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Old import name, kept so `with SessionLocal() as db:` call sites keep working
SessionLocal = Session
