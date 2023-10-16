# misskey-maintenance


## misskey　DBバックアップ
MisskeyをDockerで立ち上げている環境向けのバックアップ。
Crontabで定期実行を想定していて、
Misskeyのコンテナを停止した状態で実行する


## 使い方

### 環境変数を設定

```
cp .env.sample .env
```

```
// Misskeyで設定しているDBの情報
DB_USER
DB_PASSWORD
DB_NAME

// S3バックアップを使用する場合のみ、S3へのアクセス情報が必要
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
BUCKET_NAME

// 保管するバックアップのディレクトリパス(S3バックアップでも必要)
BACKUP_DIR

// Dockerのコンテナ名
POSTGRES_CONTAINER_NAME
POSTGRES_VOLUME_NAME
```

### 依存関係をインストール
```
pip install -r requirements.txt
```

### バックアップを実行

```
python backup_db.py
```

### リストア
```
python restore_backup.py local|s3 backup_2023-00-00.dump
```