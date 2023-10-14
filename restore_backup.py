import os
import subprocess
from dotenv import load_dotenv

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
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# 一時的なコンテナを作成
# subprocess.run(
#     f"docker run  --name {TEMP_CONTAINER_NAME} -v {DATABASE_VOLUME}:/var/lib/postgresql/data -v {BACKUP_DIR}:/backup -d {POSTGRES_IMAGE}",
#     shell=True)
# print(BACKUP_DIR)

container_id = subprocess.check_output([
        "docker", "run", "-d",
        "-e", f"POSTGRES_PASSWORD={DB_PASSWORD}",
        "--name", "temp_restore_container",
        "--env-file", ".env",
        "-v", f"{BACKUP_DIR}:/backup", 
        "-v", f"{DATABASE_VOLUME}:/var/lib/postgresql/data",
        POSTGRES_IMAGE
    ]).decode().strip()

# リストア操作
backup_source = input("Choose backup source (S3/local): ")

if backup_source == "local":
    local_backup_file = input("Enter the backup file name you want to restore (e.g., backup_2023-09-24.dump): ")
    restore_command = [
        "docker", "exec", TEMP_CONTAINER_NAME,
        "pg_restore", "-U", DB_USER, "-d", DB_NAME, f"/backup/{local_backup_file}"
    ]
    subprocess.run(restore_command)

elif backup_source == "S3":
    s3_backup_file = input("Enter the backup file name from S3 you want to restore (e.g., s3://your_bucket/backup_2023-09-24.dump): ")
    subprocess.run([
        "docker", "exec", TEMP_CONTAINER_NAME,
        "aws", "s3", "cp", s3_backup_file, "/backup/s3_backup.dump",
        "--region", "your_region",  # 必要に応じてAWSのリージョンを設定してください。
        "--access-key", AWS_ACCESS_KEY_ID,
        "--secret-access-key", AWS_SECRET_ACCESS_KEY
    ])
    subprocess.run([
        "docker", "exec", TEMP_CONTAINER_NAME,
        "pg_restore", "-U", DB_USER, "-d", DB_NAME, "/backup/s3_backup.dump"
    ])

# 一時的なコンテナを停止・削除
# subprocess.run(f"docker stop {TEMP_CONTAINER_NAME}", shell=True)
# subprocess.run(f"docker rm {TEMP_CONTAINER_NAME}", shell=True)