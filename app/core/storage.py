import os
import uuid
import boto3
from botocore.config import Config
from app.core.config import get_settings

class StorageProvider:
    def __init__(self):
        settings = get_settings()
        self.backend = settings.STORAGE_BACKEND.lower()
        self.local_dir = settings.STORAGE_LOCAL_DIR
        self.bucket_name = settings.FILES_BUCKET

        if self.backend == "s3":
            s3_config = {}
            if settings.AWS_ENDPOINT_URL:
                s3_config["endpoint_url"] = settings.AWS_ENDPOINT_URL
            
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or "test",
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or "test",
                region_name=settings.AWS_REGION or "us-east-1",
                config=Config(signature_version="s3v4"),
                **s3_config
            )
        else:
            self.s3_client = None
            if not os.path.exists(self.local_dir):
                os.makedirs(self.local_dir)

    def upload_file(self, content: bytes, filename: str) -> tuple[str, str]:

        if self.backend == "s3":
            key = f"attachments/{filename}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content
            )
            return self.bucket_name, key
        else:
            filepath = os.path.join(self.local_dir, filename)
            with open(filepath, "wb") as f:
                f.write(content)
            return "local", filepath

    def delete_file(self, bucket: str, object_key: str) -> None:
        
        if self.backend == "s3":
            try:
                self.s3_client.delete_object(
                    Bucket=bucket,
                    Key=object_key
                )
            except Exception:
                pass
        else:
            if os.path.exists(object_key):
                try:
                    os.remove(object_key)
                except Exception:
                    pass

    def get_file_stream(self, bucket: str, object_key: str) -> bytes:
        
        if self.backend == "s3":
            response = self.s3_client.get_object(
                Bucket=bucket,
                Key=object_key
            )
            return response["Body"].read()
        else:
            with open(object_key, "rb") as f:
                return f.read()

    def initiate_multipart(self, bucket: str, object_key: str) -> str:
        
        if self.backend == "s3":
            response = self.s3_client.create_multipart_upload(
                Bucket=bucket,
                Key=object_key
            )
            return response["UploadId"]
        return str(uuid.uuid4())

    def upload_part(self, bucket: str, object_key: str, upload_id: str, part_number: int, content: bytes) -> str:
        
        if self.backend == "s3":
            response = self.s3_client.upload_part(
                Bucket=bucket,
                Key=object_key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=content
            )
            return response["ETag"]
        else:
            part_filename = f"{upload_id}_part_{part_number}"
            part_path = os.path.join(self.local_dir, part_filename)
            with open(part_path, "wb") as f:
                f.write(content)
            return part_path

    def complete_multipart(self, bucket: str, object_key: str, upload_id: str, parts: list[dict]) -> str | None:
        
        if self.backend == "s3":
            sorted_parts = sorted(parts, key=lambda x: x["part_number"])
            s3_parts = [{"PartNumber": p["part_number"], "ETag": p["etag"]} for p in sorted_parts]
            response = self.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": s3_parts}
            )
            return response.get("ETag")
        else:
            target_path = object_key
            sorted_parts = sorted(parts, key=lambda x: x["part_number"])
            with open(target_path, "wb") as outfile:
                for part in sorted_parts:
                    part_path = part["file_path"]
                    if os.path.exists(part_path):
                        with open(part_path, "rb") as infile:
                            outfile.write(infile.read())
                        try:
                            os.remove(part_path)
                        except Exception:
                            pass
            return None

    def abort_multipart(self, bucket: str, object_key: str, upload_id: str, parts: list[dict]) -> None:
        
        if self.backend == "s3":
            try:
                self.s3_client.abort_multipart_upload(
                    Bucket=bucket,
                    Key=object_key,
                    UploadId=upload_id
                )
            except Exception:
                pass
        else:
            for part in parts:
                part_path = part.get("file_path")
                if part_path and os.path.exists(part_path):
                    try:
                        os.remove(part_path)
                    except Exception:
                        pass

_storage_provider = None

def get_storage_provider() -> StorageProvider:
    global _storage_provider
    if _storage_provider is None:
        _storage_provider = StorageProvider()
    return _storage_provider
