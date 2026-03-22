---
title: RcloneでGoogle Drive自動バックアップ — ヘッドレスOAuth認証とsystemd設定
tags:
  - WebDev
  - infrastructure
  - cloudflare
  - FastAPI
private: false
updated_at: '2026-03-21T21:41:10+09:00'
id: c74d7b63712740fc22ec
organization_url_name: null
slide: false
ignorePublish: false
---

■はじめに：AI開発におけるデータ管理とRcloneの壁

AIやLLM（大規模言語モデル）の開発現場において、データの保全は重要です。学習データセット、数日に及ぶトレーニングを経て生成されたモデルのチェックポイント、そして推論結果のログなど、これらはエンジニアの知恵と計算リソースの結晶です。

特に昨今のハードウェア進化は目覚ましく、筆者の環境で使用しているNVIDIA RTX 5090は32GBもの広大なVRAMを搭載しています。このメモリ容量により、巨大なモデルのファインチューニングや、バッチサイズを増やした効率的な学習が可能になりました。しかし、VRAMが増えれば扱うモデルサイズもデータ量も肥大化します。ローカルサーバーのSSDは枯渇しやすく、ディスク容量不足による学習停止のリスクが常につきまといます。

そこで有用となるのが、Google DriveやS3互換オブジェクトストレージへのデータ退避です。Rcloneはクラウドストレージ連携に非常に強力なツールですが、GUIを持たないヘッドレスサーバーでの認証フローには躓きやすいポイントがあります。

本記事では、Rcloneのヘッドレス認証におけるフローを整理し、SSH接続のみのサーバー環境でも確実にGoogle Driveをマウントし、堅牢な自動バックアップシステムを構築する手順を解説します。中級エンジニア向けに、エラーハンドリングを含めた実用的なシェルスクリプトとSystemdによる自動化までを網羅します。

■Rclone認証の落とし穴：なぜブラウザが開かないのか

Rcloneの標準的な認証フローはOAuth 2.0を利用しています。通常、ローカルPCで `rclone config` を実行すると、ブラウザが自動的に起動し、Googleの認証画面で「許可」ボタンを押すことでアクセストークンが取得されます。Rcloneはローカルホストで一時的なWebサーバーを立ち上げ、認証サーバーからのコールバックを受け取ることでこれを実現しています。

しかし、SSHで接続しているリモートサーバーやWSL2 (Ubuntu) のCUI環境、Dockerコンテナ内などにはブラウザが存在しない場合があります。Rcloneがブラウザを起動しようとしても失敗し、認証プロセスがタイムアウトしてしまいます。

多くのエンジニアがここで陥る失敗パターンは以下の通りです。

- Auto configで「Yes」を選んでしまい、サーバー側でブラウザ起動エラーが発生する。
- X11転送などを試みるが、ファイアウォールや依存関係の問題で時間を浪費する。
- 手動でトークンをコピーしようとするが、JSONの形式ミスや改行コードの混入で認証に失敗する。

これらの問題は、Rcloneが提供するヘッドレス向けの認証手順（Authorizeコマンド）を正しく理解することでスムーズに解決可能です。

■ヘッドレス認証の5ステップ

ここからは、実際にサーバー（ヘッドレス）と手元のPC（ブラウザあり）を使って認証を通す手順を解説します。

▼Step 1: Rcloneのインストールとバージョン統一

まず、サーバーと手元のPCの両方にRcloneをインストールします。重要なのは、両者のバージョンを可能な限り合わせることです。バージョンが大きく異なると、生成されるトークンの形式に互換性がなくなり、認証エラーの原因となります（2026年2月現在の最新安定版はv1.73系です）。

以下のコマンドでインストールを行います（Linux/macOS/WSL共通）。


sudo -v ; curl https://rclone.org/install.sh | sudo bash


インストール後、以下のコマンドでバージョンを確認してください。


rclone version


▼Step 2: サーバー側での設定開始

サーバー（ヘッドレス環境）にSSH接続し、設定を開始します。


rclone config


対話形式のプロンプトが表示されます。以下の手順で進めてください。

1. `n` (New remote) を入力。
2. `name` に任意のリモート名を入力（例: `gdrive_backup`）。
3. `Storage` で「Google Drive」を選択（通常は `drive` と入力するか、リスト番号を選択）。
4. `client_id` と `client_secret` は空欄でEnter（必要に応じてGoogle Cloud Consoleで作成したものを使用）。
5. `scope` は「1」を選択（Full access）。バックアップ用途ならフルアクセスが推奨されます。
6. `root_folder_id` と `service_account_file` は空欄でEnter。

ここからが重要です。

7. `Use auto config?` という質問に対して、必ず「n」と答えてください。


Use auto config?
 * Say Y if not sure
 * Say N if you are working on a remote or headless machine
y) Yes (default)
n) No
y/n> n


ここで「n」を選ぶと、Rcloneは待機状態に入り、以下のようなメッセージとコマンドを表示します。


rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"


このターミナルは閉じずに、そのままにしておきます。

▼Step 3: ローカルPCでのトークン生成

手元のPC（ブラウザが使える環境）のターミナルを開きます。サーバー側で表示された `rclone authorize` コマンドをコピーし、実行します。


rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"


コマンドを実行すると、手元のPCでブラウザが起動し、Googleのログイン画面が表示されます。バックアップに使用したいアカウントでログインし、Rcloneへのアクセスを許可してください。

ブラウザに「Success!」と表示されたら認証成功です。ターミナルに戻ると、以下のようなJSON形式のアクセストークンが表示されています。


Paste the following into your remote machine >
{"access_token":"ya29.a0...","token_type":"Bearer","refresh_token":"1//04...","expiry":"2024-01-01T12:00:00.000000+09:00"}
< End paste


この `{` から `}` までのJSON文字列全体をコピーしてください。
注意点として、ターミナルの改行などでスペースが入らないよう、クリップボードに正確にコピーすることが重要です。

▼Step 4: トークンの移植と設定完了

サーバー側のターミナルに戻ります。 `config_token>` というプロンプトが表示されているはずですので、先ほどコピーしたJSONトークンを貼り付けてEnterを押します。

その後、以下の質問に答えて設定を完了します。

1. `Configure this as a team drive?` は環境に合わせて選択（個人の場合は `n`）。
2. `Keep this "gdrive_backup" remote?` で `y` を入力。
3. `q` を入力して設定を終了。

これで認証は完了です。以下のコマンドで接続確認を行います。


rclone lsd gdrive_backup:


Google Drive内のディレクトリ一覧が表示されれば成功です。

■実践：堅牢な自動バックアップシステムの構築

認証が通っただけでは不十分です。AI開発の現場では、プロセスが落ちることなく、エラー時には即座に通知が飛び、ログが適切に残るバックアップシステムが必要です。ここでは、排他制御とエラー通知機能を備えたシェルスクリプトを作成します。

▼堅牢なバックアップスクリプトの作成

以下のスクリプトを `/usr/local/bin/backup_to_cloud.sh` として作成します。このスクリプトは、Slackへの通知機能（Webhook URLが必要）と二重起動防止機能を備えています。


#!/bin/bash

# 設定
REMOTE_NAME="gdrive_backup"
REMOTE_DIR="server_backups/$(hostname)/$(date +%Y%m%d)"
SOURCE_DIR="/home/user/ai_projects/checkpoints"
LOG_FILE="/var/log/rclone_backup.log"
LOCK_FILE="/var/run/rclone_backup.lock"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" # 任意

# ロギング関数
log_message() {
    echo " $1" | tee -a "$LOG_FILE"
}

# 通知関数
send_notification() {
    if; then
        curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"$1\"}" "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
}

# 二重起動チェック
if; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null; then
        log_message "Error: Backup process is already running (PID: $PID)."
        exit 1
    else
        log_message "Warning: Stale lock file found. Removing."
        rm "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"

# バックアップ開始
log_message "Starting backup: $SOURCE_DIR -> $REMOTE_NAME:$REMOTE_DIR"

# rclone sync実行
# --transfers 8: 並列転送数（帯域に合わせて調整）
# --bwlimit 50M: 帯域制限（50MB/s）でネットワーク占有を防止
# --drive-chunk-size 64M: Google Drive向けの最適化
# --exclude "venv/**": 不要なディレクトリを除外

/usr/bin/rclone sync "$SOURCE_DIR" "$REMOTE_NAME:$REMOTE_DIR" \
    --transfers 8 \
    --checkers 16 \
    --bwlimit 50M \
    --drive-chunk-size 64M \
    --exclude "venv/**" \
    --exclude "__pycache__/**" \
    --exclude ".git/**" \
    --log-file "$LOG_FILE" \
    --log-level INFO

EXIT_CODE=$?

if; then
    log_message "Backup completed successfully."
    # 成功時は通知しない、または日次レポートなどで通知
else
    log_message "Backup failed with exit code $EXIT_CODE."
    send_notification "🚨 Backup Failed! Check logs at $LOG_FILE"
fi

# ロックファイル削除
rm "$LOCK_FILE"
exit $EXIT_CODE


スクリプトを作成したら、実行権限を付与します。


sudo chmod +x /usr/local/bin/backup_to_cloud.sh


▼Systemdによる定期実行と管理

Cronでも定期実行は可能ですが、ログ管理や依存関係の制御が容易なSystemd Timerを使用することをお勧めします。

1. Serviceファイルの作成
`/etc/systemd/system/rclone-backup.service`



Description=Rclone Backup Service
After=network-online.target
Wants=network-online.target


Type=oneshot
User=root
ExecStart=/usr/local/bin/backup_to_cloud.sh
StandardOutput=append:/var/log/rclone_backup_systemd.log
StandardError=append:/var/log/rclone_backup_systemd.log


WantedBy=multi-user.target


2. Timerファイルの作成
`/etc/systemd/system/rclone-backup.timer`



Description=Run Rclone Backup daily at 3 AM


OnCalendar=*-*-* 03:00:00
Persistent=true


WantedBy=timers.target


3. 有効化と起動


sudo systemctl daemon-reload
sudo systemctl enable --now rclone-backup.timer


これで、毎日午前3時に自動的にバックアップが実行されます。サーバーが再起動しても、ネットワークが確立された後に確実に実行されるようになります。

■トラブルシューティングと最適化

運用中に発生しやすい問題とその対策をまとめます。

- 「Failed to copy: googleapi: Error 403: User rate limit exceeded」
Google Drive APIのレート制限に引っかかっています。 `--tpslimit 10` などのオプションを追加して、1秒あたりのトランザクション数を制限してください。また、独自のClient ID/Secretを使用することで、共有の制限枠を回避できる場合があります。

- 巨大なファイルの転送速度が出ない
RTX 5090環境などで生成される数十GBクラスのモデルファイル（.pth, .safetensors）を転送する場合、`--drive-chunk-size` を `256M` や `512M` に増やすことで、スループットの向上が期待できます。ただし、メモリ使用量も増えるため、サーバーのRAM容量（筆者環境では64GB）と相談して設定してください。

- コールドデータの退避先としてのマウント利用
Rcloneには `rclone mount` 機能があります。これを活用すれば、Google Driveをローカルディレクトリのようにマウントできます。学習データの読み込み速度は遅くなりますが、頻繁にアクセスしないコールドデータの退避先として、あるいは推論時のモデル読み込み先として直接マウントすることで、ローカルディスクを圧迫せずに32GBのVRAMを持つRTX 5090を活用できます。

マウントコマンド例（バックグラウンド実行）:


rclone mount gdrive_backup: /mnt/gdrive \
    --daemon \
    --vfs-cache-mode full \
    --vfs-cache-max-size 50G \
    --allow-other


`--vfs-cache-mode full` を指定することで、書き込み時のキャッシュが有効になり、アプリケーション側からのファイル操作が安定します。

■まとめ

Rcloneのヘッドレス認証は、仕組みを理解すればスムーズに設定可能です。重要なのは「サーバーで設定を開始し、ローカルでトークンを作り、サーバーに戻す」という3ステップのフローです。

今回構築した環境により、AI開発サーバーにおいて以下の運用が可能になります。

- ブラウザレス環境での確実なGoogle Drive連携
- RTX 5090 (32GB) の性能をフル活用するためのデータ退避経路の確保
- Systemdによる堅牢な自動バックアップとSlack通知

ディスク容量の枯渇リスクを低減し、モデルの学習や実験に集中できる環境を整えることは、開発効率の向上に直結します。本記事の手順を参考に、堅牢なデータ管理システムを構築してください。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/web-infra/086_premium)*
