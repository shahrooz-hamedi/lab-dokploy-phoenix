
#!/opt/venv/bin/python

import json
import os
import sys
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from minio import Minio
from minio.minioadmin import MinioAdmin
from minio.credentials import StaticProvider
from minio.error import MinioAdminException


ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
BUCKET = os.environ.get("MINIO_BUCKET", "voice-audio")
POLICY_NAME = "dograh-voice-audio"

ROOT_USER = os.environ["MINIO_ROOT_USER"]
ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]

APP_USER = os.environ["AWS_ACCESS_KEY_ID"]
APP_PASSWORD = os.environ["AWS_SECRET_ACCESS_KEY"]

POLICY_FILE = "/config/minio-policy.json"

S3_ENDPOINT = f"http://{ENDPOINT}"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr, flush=True)
    sys.exit(1)


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        fail(f"Cannot read {path}: {exc}")


def make_s3_client(access_key, secret_key):
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 5, "mode": "standard"},
        ),
    )


def make_minio_client():
    return Minio(
        ENDPOINT,
        access_key=ROOT_USER,
        secret_key=ROOT_PASSWORD,
        secure=False,
    )


def make_admin_client():
    return MinioAdmin(
        endpoint=ENDPOINT,
        credentials=StaticProvider(ROOT_USER, ROOT_PASSWORD),
        secure=False,
    )


def wait_for_minio():
    client = make_minio_client()

    for attempt in range(30):
        try:
            client.list_buckets()
            print("MinIO is responding.", flush=True)
            return client
        except Exception as exc:
            print(
                f"Waiting for MinIO ({attempt + 1}/30): {exc}",
                flush=True,
            )
            time.sleep(2)

    fail("MinIO did not become available.")


def ensure_bucket(root_client):
    if root_client.bucket_exists(BUCKET):
        print(f"Bucket exists: {BUCKET}", flush=True)
        return

    root_client.make_bucket(BUCKET)
    print(f"Created bucket: {BUCKET}", flush=True)


def refuse_existing_bucket_policy(s3_root):
    try:
        response = s3_root.get_bucket_policy(Bucket=BUCKET)

        if response.get("Policy"):
            fail(
                "An existing bucket policy was found. "
                "Initialization stopped without changing it."
            )

    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")

        if code in ("NoSuchBucketPolicy", "NoSuchPolicy"):
            print("No existing bucket policy.", flush=True)
            return

        fail(f"Could not inspect bucket policy: {exc}")


def ensure_app_user(admin):
    try:
        admin.user_info(APP_USER)
        print(
            "Application user already exists; password was not changed.",
            flush=True,
        )
        return

    except MinioAdminException as exc:
        if str(exc._code) != "404":
            fail(f"Could not inspect application user: {exc}")

    try:
        admin.user_add(APP_USER, APP_PASSWORD)
        print("Created Dograh application user.", flush=True)
    except Exception as exc:
        fail(f"Could not create application user: {exc}")


def ensure_app_policy(admin):
    """
    Use the policy list to check policy existence.

    In this MinIO deployment, policy_list() returns the policy
    name but its associated document is an empty string.
    Do not attempt to parse or compare that empty value.

    The existing Dograh policy was previously created from
    the repository policy file. Preserve it unchanged.
    """

    try:
        policies_response = admin.policy_list()

        if not policies_response or not policies_response.strip():
            fail(
                "MinIO returned an empty policy list. "
                "Cannot safely determine whether the application policy exists."
            )

        policies = json.loads(policies_response)

        if not isinstance(policies, dict):
            fail(
                "MinIO returned an unexpected policy-list format. "
                "Expected a JSON object."
            )

    except SystemExit:
        raise
    except Exception as exc:
        fail(f"Could not retrieve or parse MinIO policy list: {exc}")

    if POLICY_NAME in policies:
        print(
            "Dograh application policy already exists; leaving it unchanged.",
            flush=True,
        )
        return

    try:
        admin.policy_add(
            POLICY_NAME,
            policy_file=POLICY_FILE,
        )
        print("Created Dograh application policy.", flush=True)

    except Exception as exc:
        fail(f"Could not create application policy: {exc}")


def attach_app_policy(admin):
    try:
        admin.policy_set(
            POLICY_NAME,
            user=APP_USER,
        )
        print("Attached application policy.", flush=True)
    except Exception as exc:
        fail(f"Could not attach application policy: {exc}")


def verify_app_access():
    app_client = make_s3_client(APP_USER, APP_PASSWORD)

    try:
        app_client.head_bucket(Bucket=BUCKET)
        print("Application credentials verified.", flush=True)
    except Exception as exc:
        fail(f"Application credential verification failed: {exc}")


def main():
    print("Starting Dograh MinIO initialization.", flush=True)

    if not APP_USER or not APP_PASSWORD:
        fail("Application S3 credentials must not be empty.")

    # Validate the repository policy file before initialization.
    load_json(POLICY_FILE)

    root_client = wait_for_minio()
    admin = make_admin_client()
    s3_root = make_s3_client(ROOT_USER, ROOT_PASSWORD)

    ensure_bucket(root_client)

    # Never remove or replace an existing bucket policy.
    refuse_existing_bucket_policy(s3_root)

    ensure_app_user(admin)
    ensure_app_policy(admin)
    attach_app_policy(admin)

    # Community MinIO uses server-level CORS configuration.
    # Per-bucket PutBucketCors is not supported by this image.
    print(
        "Skipping per-bucket CORS; use MINIO_API_CORS_ALLOW_ORIGIN "
        "on the MinIO service.",
        flush=True,
    )

    verify_app_access()

    print("Dograh MinIO initialization completed successfully.", flush=True)


if __name__ == "__main__":
    main()
