import os
import subprocess
from dotenv import load_dotenv
import time 
import argparse

# 引数の解析
parser = argparse.ArgumentParser(description='Restore backup for PostgreSQL in Docker.')
parser.add_argument('source', choices=['S3', 'local'], help='Backup source: S3 or local')
parser.add_argument('filename', help='Name of the backup file.')
args = parser.parse_args()

# .envから環境変数を読み込む
load_dotenv()

# 環境変数の取得
DATABASE_VOLUME = os.getenv("POSTGRES_VOLUME_NAME")
BACKUP_DIR = os.getenv("BACKUP_DIR")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
POSTGRES_IMAGE = "postgres:15-alpine"  # 使用するPostgreSQLのイメージのバージョンを適切に設定してください。
TEMP_CONTAINER_NAME = "temp_restore_container"
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def check_postgres_ready():
    cmd = [
        "docker", "exec", TEMP_CONTAINER_NAME,
        "psql", "-U", DB_USER, "-d", DB_NAME, "-c", "SELECT 1;"
    ]
    try:
        subprocess.check_output(cmd)
        return True
    except subprocess.CalledProcessError:
        return False

# データベースをクリーンな状態にする
def clean_db():
    drop_db_command = [
        "docker", "exec", TEMP_CONTAINER_NAME,
        "psql", "-U", DB_USER, "-d", "postgres", "-c",
        f"DROP DATABASE IF EXISTS {DB_NAME};"
    ]
    subprocess.run(drop_db_command)

    create_db_command = [
        "docker", "exec", TEMP_CONTAINER_NAME,
        "psql", "-U", DB_USER, "-d", "postgres", "-c",
        f"CREATE DATABASE {DB_NAME};"
    ]
    subprocess.run(create_db_command)

# awscliをインストール
def install_awscli():
    subprocess.run([
        "docker", "exec", TEMP_CONTAINER_NAME,
        "apk", "add", "--no-cache", "python3", "py3-pip"
    ])
    subprocess.run([
        "docker", "exec", TEMP_CONTAINER_NAME,
        "pip3", "install", "awscli"
    ])

# 一時的なコンテナを作成
container_id = subprocess.check_output([
        "docker", "run", "-d",
        "-e", f"POSTGRES_PASSWORD={DB_PASSWORD}",
        "--name", "temp_restore_container",
        "--env-file", ".env",
        "-v", f"{BACKUP_DIR}:/backup", 
        "-v", f"{DATABASE_VOLUME}:/var/lib/postgresql/data",
        POSTGRES_IMAGE
    ]).decode().strip()

# PostgreSQLが起動するまで待つ
while not check_postgres_ready():
    time.sleep(5)


if args.source == "local":
    clean_db()
    restore_command = [
        "docker", "exec", TEMP_CONTAINER_NAME,
        "pg_restore", "-U", DB_USER, "-d", DB_NAME, f"/backup/{args.filename}"
    ]
    subprocess.run(restore_command)

elif args.source == "S3":
    print( f"{BUCKET_NAME}/{args.filename}")
    install_awscli()
    subprocess.run([
        "docker", "exec", TEMP_CONTAINER_NAME,
        "aws", "s3", "cp", f"s3://{BUCKET_NAME}/{args.filename}", "/backup/s3_backup.dump",
        f"--region={AWS_DEFAULT_REGION}"
    ], env={
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY
    })
    # s3からの取得が成功したら、データベースをクリーンな状態にしてからリストア
    if os.path.exists(f"{BACKUP_DIR}/s3_backup.dump"):
        clean_db()
        restore_command = [
            "docker", "exec", TEMP_CONTAINER_NAME,
            "pg_restore", "-U", DB_USER, "-d", DB_NAME, "/backup/s3_backup.dump"
        ]
        subprocess.run(restore_command)


# 一時的なコンテナを停止・削除
subprocess.run(f"docker stop {TEMP_CONTAINER_NAME}", shell=True)
subprocess.run(f"docker rm {TEMP_CONTAINER_NAME}", shell=True)