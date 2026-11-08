#!/opt/venv/bin/python

import difflib
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


def normalize_policy(document):
    """
    Normalize policy JSON for comparison.

    Object key ordering and whitespace are irrelevant.
    Policy statement and permission-list ordering are also
    irrelevant, so lists are sorted by canonical JSON.
    """
    if isinstance(document, str):
        try:
            document = json.loads(document)
        except json.JSONDecodeError as exc:
            fail(f"Could not parse existing policy JSON: {exc}")

    if (
        isinstance(document, dict)
        and "policy" in document
        and len(document) == 1
    ):
        return normalize_policy(document["policy"])

    if isinstance(document, dict):
        return {
            key: normalize_policy(value)
            for key, value in sorted(document.items())
        }

    if isinstance(document, list):
        normalized = [normalize_policy(item) for item in document]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    return document


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


def ensure_app_policy(admin, policy_document):
    """
    Inspect the complete policy list instead of policy_info().

    policy_info() returned an empty response in the current
    deployment. An empty policy list is treated as an error,
    never as proof that the policy is absent.
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

    # Create the policy only when the policy list confirms
    # that it does not exist.
    if POLICY_NAME not in policies:
        try:
            admin.policy_add(
                POLICY_NAME,
                policy_file=POLICY_FILE,
            )
            print("Created Dograh application policy.", flush=True)
            return
        except Exception as exc:
            fail(f"Could not create application policy: {exc}")

    # The policy exists. Compare its actual document with
    # the repository policy before doing anything else.
    try:
        existing_document = policies[POLICY_NAME]

        normalized_existing = normalize_policy(existing_document)
        normalized_desired = normalize_policy(policy_document)

    except SystemExit:
        raise
    except Exception as exc:
        fail(f"Could not compare application policies: {exc}")

    if normalized_existing == normalized_desired:
        print(
            "Existing application policy matches repository policy.",
            flush=True,
        )
        return

    print(
        "POLICY DIAGNOSTIC: Existing MinIO policy differs "
        "from repository policy.",
        flush=True,
    )

    existing_text = json.dumps(
        existing_document,
        indent=2,
        sort_keys=True,
    ).splitlines()

    desired_text = json.dumps(
        policy_document,
        indent=2,
        sort_keys=True,
    ).splitlines()

    print("========== POLICY DIFFERENCE ==========", flush=True)

    for line in difflib.unified_diff(
        existing_text,
        desired_text,
        fromfile="existing-minio-policy",
        tofile="repository-policy",
        lineterm="",
    ):
        print(line, flush=True)

    fail(
        "Existing application policy differs from repository policy. "
        "The existing policy was NOT modified."
    )


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

    policy_document = load_json(POLICY_FILE)

    root_client = wait_for_minio()
    admin = make_admin_client()
    s3_root = make_s3_client(ROOT_USER, ROOT_PASSWORD)

    ensure_bucket(root_client)

    # Never remove or replace an existing bucket policy.
    refuse_existing_bucket_policy(s3_root)

    ensure_app_user(admin)
    ensure_app_policy(admin, policy_document)
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
