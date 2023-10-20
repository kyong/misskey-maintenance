import os
import subprocess
from datetime import datetime
import boto3
from dotenv import load_dotenv
import argparse

# 引数の解析
parser = argparse.ArgumentParser(description='Restore backup for PostgreSQL in Docker.')
parser.add_argument('source', choices=['s3', 'local'], help='Backup source: S3 or local')
args = parser.parse_args()


# .envファイルから環境変数をロード
load_dotenv()

# 環境変数の取得
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
BACKUP_DIR = os.environ.get("BACKUP_DIR")
POSTGRES_CONTAINER_NAME = os.environ.get("POSTGRES_CONTAINER_NAME")


# データベースのバックアップ
current_date = datetime.now().strftime('%Y-%m-%d')
backup_file = os.path.join(BACKUP_DIR, f"backup_{current_date}.dump")

dump_command = [
    "docker", "exec", "-i", POSTGRES_CONTAINER_NAME,
    "pg_dump",
    f"-U{DB_USER}",
    f"-hlocalhost",
    "-Fc",  # custom format
    DB_NAME,
    f">{backup_file}"
]
subprocess.run(" ".join(dump_command), shell=True)


# AWS S3へのアップロード
if args.source == "s3":
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION
    )

    with open(backup_file, "rb") as f:
        s3.upload_fileobj(f, BUCKET_NAME, f"backup_{current_date}.dump")

elif args.source == "local":
    print(f"Backup saved to {backup_file}")
else:
    print("Invalid choice. Backup not saved to S3 or local.")