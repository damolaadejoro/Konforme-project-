#!/usr/bin/env python3
"""One-time copy of the PostgreSQL database into the DynamoDB table.

Usage (needs psycopg2-binary in addition to requirements.txt):
    POSTGRES_URL=postgresql://konforme:...@db:5432/konforme \\
    DYNAMODB_TABLE=konforme AWS_DEFAULT_REGION=eu-west-1 \\
    python scripts/migrate_postgres_to_dynamodb.py [--dry-run] [--force]

Copies every row of every table with the same field values, then:
  - recreates the uniqueness guards (account/user emails, report document ids)
  - sets the audit-log id counter past the highest migrated id
  - compares row counts per table
  - re-verifies every account's audit hash chain on the migrated data

Refuses to run if the table already holds accounts, unless --force.
"""

import argparse
import dataclasses
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2  # noqa: E402
import psycopg2.extras  # noqa: E402
from boto3.dynamodb.conditions import Key  # noqa: E402

import audit_service  # noqa: E402
import models  # noqa: E402
import store  # noqa: E402

# PostgreSQL table -> model
TABLES = {
    "accounts": models.Account,
    "users": models.User,
    "cloud_credentials": models.CloudCredential,
    "aws_accounts": models.AwsAccount,
    "scans": models.Scan,
    "scan_results": models.ScanResult,
    "assessments": models.Assessment,
    "assessment_versions": models.AssessmentVersion,
    "assessment_responses": models.AssessmentResponse,
    "evidence": models.Evidence,
    "remediation_plans": models.RemediationPlan,
    "remediation_plan_milestones": models.RemediationPlanMilestone,
    "remediation_plan_links": models.RemediationPlanLink,
    "remediation_tasks": models.RemediationTask,
    "countries": models.Country,
    "entity_tiers": models.EntityTier,
    "country_controls": models.CountryControl,
    "country_deadlines": models.CountryDeadline,
    "country_assessment_questions": models.CountryAssessmentQuestion,
    "base_controls": models.BaseControl,
    "account_controls": models.AccountControl,
    "control_campaigns": models.ControlCampaign,
    "campaign_tasks": models.CampaignTask,
    "business_processes": models.BusinessProcess,
    "process_controls": models.ProcessControl,
    "oauth_states": models.OAuthState,
    "evidence_links": models.EvidenceLink,
    "assessment_question_controls": models.AssessmentQuestionControl,
    "audit_log": models.AuditLog,
    "pending_people_task_instantiations": models.PendingPeopleTaskInstantiation,
    "people_tasks": models.PeopleTask,
    "reports": models.Report,
    "people_task_completions": models.PeopleTaskCompletion,
}

# EvidenceLink lives in the account partition; take account_id from its evidence row
QUERIES = {
    "evidence_links": "SELECT el.*, e.account_id FROM evidence_links el JOIN evidence e ON e.id = el.evidence_id",
}


def existing_tables(cur) -> set[str]:
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return {r["tablename"] for r in cur.fetchall()}


def build(cls, row: dict):
    """Model instance from a row: NULLs stay NULL; columns this database lacks keep the model default."""
    fields = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in row.items() if k in fields})


class _SourceRows:
    """Duck-typed session so audit_service.verify_chain can check the PostgreSQL rows too."""

    def __init__(self, rows):
        self._rows = rows

    def list(self, cls, account_id):
        return [r for r in self._rows if r.account_id == account_id]


def entity_count(table, entity: str) -> int:
    total, start = 0, None
    while True:
        kwargs = {"IndexName": store.ENTITY_INDEX, "KeyConditionExpression": Key("entity").eq(entity), "Select": "COUNT"}
        if start:
            kwargs["ExclusiveStartKey"] = start
        resp = table.query(**kwargs)
        total += resp["Count"]
        start = resp.get("LastEvaluatedKey")
        if not start:
            return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="read and convert everything, write nothing")
    parser.add_argument("--force", action="store_true", help="write even if the table already has accounts")
    args = parser.parse_args()

    pg = psycopg2.connect(os.environ["POSTGRES_URL"])
    pg.set_session(readonly=True)
    cur = pg.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SET TIME ZONE 'UTC'")

    table = store.table()
    if not args.force and entity_count(table, "Account") > 0:
        sys.exit("DynamoDB table already has accounts; refusing to overwrite (use --force).")

    present = existing_tables(cur)
    source_counts: dict[str, int] = {}
    source_audit: list = []
    max_audit_id = 0

    with table.batch_writer(overwrite_by_pkeys=["PK", "SK"]) as batch:
        for pg_table, cls in TABLES.items():
            if pg_table not in present:
                print(f"  skip {pg_table:36} (not in this database)")
                continue
            cur.execute(QUERIES.get(pg_table, f"SELECT * FROM {pg_table}"))
            rows = cur.fetchall()
            source_counts[cls.__name__] = len(rows)
            for row in rows:
                obj = build(cls, dict(row))
                item = store.to_item(obj)
                guards = store._guard_keys(obj, item).values()
                if cls is models.AuditLog:
                    max_audit_id = max(max_audit_id, obj.id)
                    source_audit.append(obj)
                if not args.dry_run:
                    batch.put_item(Item=item)
                    for guard in guards:
                        batch.put_item(Item=guard)
            print(f"  {'read' if args.dry_run else 'copied'} {pg_table:34} {len(rows):6d} rows")

        if not args.dry_run:
            batch.put_item(Item={"PK": "Counter", "SK": "AuditLog", "value": max_audit_id})

    if args.dry_run:
        print("Dry run: nothing written.")
        return

    print("\nComparing counts (index catches up within seconds)...")
    time.sleep(5)
    mismatches = []
    for entity, expected in source_counts.items():
        for _ in range(6):
            actual = entity_count(table, entity)
            if actual == expected:
                break
            time.sleep(5)
        status = "ok" if actual == expected else "MISMATCH"
        if actual != expected:
            mismatches.append(entity)
        print(f"  {entity:34} postgres={expected:6d} dynamodb={actual:6d} {status}")

    print("\nVerifying audit hash chains on the migrated data...")
    broken, already_broken = [], []
    for account_id in sorted({a.account_id for a in source_audit}, key=str):
        before = audit_service.verify_chain(_SourceRows(source_audit), account_id)
        after = audit_service.verify_chain(store.Session(), account_id)
        if not before["valid"]:
            already_broken.append(account_id)  # broken in PostgreSQL too; not caused by the copy
        elif not after["valid"]:
            broken.append((account_id, after["first_broken_at"]))
    print(f"  {len(broken)} chains broken by the copy" + (f": {broken}" if broken else ""))
    if already_broken:
        print(f"  note: {len(already_broken)} chains were already broken in PostgreSQL: {already_broken}")

    if mismatches or broken:
        sys.exit("Migration finished with problems (see above). Do NOT cut over.")
    print("\nMigration complete and verified.")


if __name__ == "__main__":
    main()
