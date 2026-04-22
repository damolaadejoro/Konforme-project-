"""Abstraction over filesystem and S3 storage for evidence files."""

import os
import uuid
from abc import ABC, abstractmethod

import boto3
from botocore.exceptions import ClientError

from config import settings


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store data, return the storage key."""
        ...

    @abstractmethod
    def get_download_url(self, key: str, filename: str, expiry: int = 3600) -> str:
        """Get a URL to download the file (signed URL for S3, file path for filesystem)."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the stored object."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if the object exists."""
        ...

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Retrieve the raw bytes."""
        ...


class FilesystemStorage(StorageBackend):
    """Store files on the local filesystem (existing behavior)."""

    def __init__(self):
        self.base_dir = settings.upload_dir

    def _full_path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def put(self, key: str, data: bytes, content_type: str) -> str:
        path = self._full_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return key

    def get_download_url(self, key: str, filename: str, expiry: int = 3600) -> str:
        # For filesystem, return the path — caller must serve via FileResponse
        return self._full_path(key)

    def delete(self, key: str) -> None:
        path = self._full_path(key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    def get(self, key: str) -> bytes:
        with open(self._full_path(key), "rb") as f:
            return f.read()


class S3Storage(StorageBackend):
    """Store files in AWS S3."""

    def __init__(self):
        kwargs = {"region_name": settings.s3_evidence_region}
        if settings.s3_evidence_access_key_id:
            kwargs["aws_access_key_id"] = settings.s3_evidence_access_key_id
            kwargs["aws_secret_access_key"] = settings.s3_evidence_secret_access_key
        self.client = boto3.client("s3", **kwargs)
        self.bucket = settings.s3_evidence_bucket
        self.prefix = settings.s3_evidence_prefix

    def _s3_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def put(self, key: str, data: bytes, content_type: str) -> str:
        s3_key = self._s3_key(key)
        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def get_download_url(self, key: str, filename: str, expiry: int = 3600) -> str:
        s3_key = self._s3_key(key)
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expiry,
        )

    def delete(self, key: str) -> None:
        s3_key = self._s3_key(key)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
        except ClientError:
            pass

    def exists(self, key: str) -> bool:
        s3_key = self._s3_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False

    def get(self, key: str) -> bytes:
        s3_key = self._s3_key(key)
        resp = self.client.get_object(Bucket=self.bucket, Key=s3_key)
        return resp["Body"].read()


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Factory: returns S3Storage if bucket is configured, else FilesystemStorage."""
    global _storage_instance
    if _storage_instance is None:
        if settings.s3_evidence_bucket:
            _storage_instance = S3Storage()
        else:
            _storage_instance = FilesystemStorage()
    return _storage_instance
