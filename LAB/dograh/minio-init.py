#!/usr/bin/env python3

import json
import os
import sys

import boto3
from botocore.config import Config
from minio import Minio
from minio.credentials import StaticProvider
from minio.minioadmin import MinioAdmin


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
BUCKET = os.environ.get("MINIO_BUCKET", "voice-audio")
POLICY_NAME = "dograh-voice-audio"

ROOT_USER = os.environ["MINIO_ROOT_USER"]
ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]

APP_USER = os.environ["AWS_ACCESS_KEY_ID"]
APP_PASSWORD = os.environ["AWS_SECRET_ACCESS_KEY"]

POLICY_FILE = "/config/minio-policy.json"
CORS_FILE = "/config/minio-cors.json"


def log(message):
    print(f"[minio-init] {message}", flush=True)


def main():

    log("Starting MinIO provisioning.")

    # --------------------------------------------------
    # Root administration clients
    # --------------------------------------------------

    admin = MinioAdmin(
        ENDPOINT,
        StaticProvider(ROOT_USER, ROOT_PASSWORD),
        secure=False,
    )

    root_client = Minio(
        ENDPOINT,
        access_key=ROOT_USER,
        secret_key=ROOT_PASSWORD,
        secure=False,
    )

    # --------------------------------------------------
    # 1. Ensure application user exists
    # --------------------------------------------------

    users = admin.user_list()

    if APP_USER not in users:
        admin.user_add(APP_USER, APP_PASSWORD)
        log("Application user created.")
    else:
        log("Application user already exists.")

    # --------------------------------------------------
    # 2. Ensure private bucket exists
    # --------------------------------------------------

    if not root_client.bucket_exists(BUCKET):
        root_client.make_bucket(BUCKET)
        log(f"Bucket created: {BUCKET}")
    else:
        log(f"Bucket already exists: {BUCKET}")

    # --------------------------------------------------
    # 3. Remove anonymous bucket policy
    # --------------------------------------------------

    root_client.delete_bucket_policy(BUCKET)

    log("Bucket anonymous-access policy removed.")

    # --------------------------------------------------
    # 4. Ensure application policy exists
    # --------------------------------------------------

    policies = admin.policy_list()

    if POLICY_NAME not in policies:
        admin.policy_add(POLICY_NAME, POLICY_FILE)
        log(f"Policy created: {POLICY_NAME}")
    else:
        log(f"Policy already exists: {POLICY_NAME}")

    # --------------------------------------------------
    # 5. Attach policy to application user
    # --------------------------------------------------

    admin.attach_policy(
        [POLICY_NAME],
        user=APP_USER,
    )

    log("Application policy attached.")

    # --------------------------------------------------
    # 6. Apply bucket CORS configuration
    # --------------------------------------------------

    with open(CORS_FILE, "r", encoding="utf-8") as file:
        cors_configuration = json.load(file)

    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{ENDPOINT}",
        aws_access_key_id=ROOT_USER,
        aws_secret_access_key=ROOT_PASSWORD,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )

    s3.put_bucket_cors(
        Bucket=BUCKET,
        CORSConfiguration=cors_configuration,
    )

    log("Bucket CORS configuration applied.")

    # --------------------------------------------------
    # 7. Verify application-level permissions
    # --------------------------------------------------

    app_client = Minio(
        ENDPOINT,
        access_key=APP_USER,
        secret_key=APP_PASSWORD,
        secure=False,
    )

    if not app_client.bucket_exists(BUCKET):
        raise RuntimeError("Application cannot access the bucket.")

    log("Application credentials verified.")

    log("MinIO provisioning completed successfully.")


if __name__ == "__main__":

    try:
        main()

    except Exception as error:
        log(f"ERROR: {type(error).__name__}: {error}")
        sys.exit(1)