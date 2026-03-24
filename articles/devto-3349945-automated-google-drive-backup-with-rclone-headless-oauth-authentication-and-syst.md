---
title: "Automated Google Drive Backup with Rclone: Headless OAuth Authentication and systemd Configuration"
date: 2026-03-14
topics: ["webdev", "devops", "infrastructure"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/web-infra/086_premium"
devto_url: "https://dev.to/soytuber/automated-google-drive-backup-with-rclone-headless-oauth-authentication-and-systemd-configuration-1lp8"
devto_id: 3349945
---

## Introduction: Data Management in AI Development and the Rclone Barrier

In AI and LLM (Large Language Model) development environments, data preservation is critical. Training datasets, model checkpoints generated over days of training, and inference logs—these represent the crystallization of engineer wisdom and computational resources.

In particular, recent hardware evolution has been remarkable. The NVIDIA RTX 5090 I use in my environment is equipped with a vast 32GB of VRAM. This memory capacity enables fine-tuning of massive models and efficient training with increased batch sizes. However, as VRAM increases, both the model sizes and data volumes handled bloat. Local server SSDs deplete easily, constantly posing the risk of training halts due to insufficient disk space.

This is where backing up data to Google Drive or S3-compatible object storage becomes useful. Rclone is a highly powerful tool for cloud storage integration, but the authentication flow on a headless server lacking a GUI holds stumbling blocks.

This article organizes the flow of Rclone headless authentication and explains the steps to reliably mount Google Drive and build a robust automated backup system even in SSH-only server environments. Aimed at intermediate engineers, it covers everything from a practical shell script including error handling to automation using Systemd.

## The Pitfall of Rclone Authentication: Why the Browser Doesn't Open

Rclone's standard authentication flow utilizes OAuth 2.0. Normally, running `rclone config` on a local PC automatically opens a browser, and pressing the "Allow" button on Google's authentication screen retrieves an access token. Rclone achieves this by spinning up a temporary web server on localhost and receiving callbacks from the authentication server.

However, remote servers connected via SSH, WSL2 (Ubuntu) CLI environments, or inside Docker containers may lack a browser. When Rclone attempts to launch one, it fails, leading the authentication process to time out.

The common failure patterns engineers fall into here are as follows:

- Selecting "Yes" for Auto config, causing a browser launch error on the server side.
- Attempting X11 forwarding, but wasting time on firewall or dependency issues.
- Attempting to manually copy tokens, but failing authentication due to JSON formatting mistakes or mixed newline characters.

These problems can be smoothly resolved by correctly understanding the headless-oriented authentication procedure (the Authorize command) provided by Rclone.

## 5 Steps for Headless Authentication

From here, we will explain the steps to pass authentication using the server (headless) and your local PC (with a browser).

### Step 1: Installing Rclone and Unifying Versions

First, install Rclone on both the server and your local PC. Crucially, match their versions as closely as possible. Significantly different versions can cause token format incompatibilities, leading to authentication errors (as of February 2026, the latest stable release is the v1.73 series).

Run the following command to install (common across Linux/macOS/WSL).

```bash
sudo -v ; curl https://rclone.org/install.sh | sudo bash
```

After installation, verify the version with the following command.

```bash
rclone version
```

### Step 2: Starting Configuration on the Server Side

Connect to the server (headless environment) via SSH and start configuration.

```bash
rclone config
```

An interactive prompt will appear. Proceed with the following steps.

1. Enter `n` (New remote).
2. Enter any desired remote name for `name` (e.g., `gdrive_backup`).
3. Select "Google Drive" for `Storage` (usually enter `drive` or select the list number).
4. Leave `client_id` and `client_secret` blank and press Enter (use ones created in Google Cloud Console if necessary).
5. Select "1" for `scope` (Full access). Full access is recommended for backup purposes.
6. Leave `root_folder_id` and `service_account_file` blank and press Enter.

The following is the crucial part.

7. When asked `Use auto config?`, you must strictly answer "n".

```bash
Use auto config?
 * Say Y if not sure
 * Say N if you are working on a remote or headless machine
y) Yes (default)
n) No
y/n> n
```

When you choose "n" here, Rclone enters a standby state and displays a message and command like the following.

```bash
rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"
```

Leave this terminal open without closing it.

### Step 3: Generating the Token on the Local PC

Open a terminal on your local PC (an environment where a browser can be used). Copy and execute the `rclone authorize` command displayed on the server side.

```bash
rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"
```

Upon execution, the browser opens on your local PC, showing the Google login screen. Log in with the account you intend to use for backups and authorize access to Rclone.

When the browser shows "Success!", authentication is successful. Returning to the terminal, an access token in JSON format like the following is displayed.

```bash
Paste the following into your remote machine >
{"access_token":"ya29.a0...","token_type":"Bearer","refresh_token":"1//04...","expiry":"2024-01-01T12:00:00.000000+09:00"}
< End paste
```

Copy this entire JSON string from `{` to `}`.
Note that it is vital to copy it accurately to your clipboard without introducing spaces due to terminal line breaks.

### Step 4: Porting the Token and Completing Setup

Return to the server-side terminal. You should see a `config_token>` prompt. Paste the JSON token you just copied and press Enter.

Then, answer the subsequent questions to complete the configuration.

1. Select based on your environment for `Configure this as a team drive?` (enter `n` for personal).
2. Enter `y` for `Keep this "gdrive_backup" remote?`.
3. Enter `q` to quit the setup.

Authentication is now complete. Run the following command to test the connection.

```bash
rclone lsd gdrive_backup:
```

If a list of directories inside Google Drive is displayed, it was successful.

## Practice: Building a Robust Automated Backup System

Just passing authentication is insufficient. AI development environments require a backup system where processes don't drop, notifications are immediately sent upon errors, and logs are kept properly. Here, we create a shell script equipped with exclusive control and error notification features.

### Creating the Robust Backup Script

Create the following script as `/usr/local/bin/backup_to_cloud.sh`. This script is equipped with a Slack notification feature (requires a Webhook URL) and a double-execution prevention feature.

```bash
#!/bin/bash

# Configuration
REMOTE_NAME="gdrive_backup"
REMOTE_DIR="server_backups/$(hostname)/$(date +%Y%m%d)"
SOURCE_DIR="/home/user/ai_projects/checkpoints"
LOG_FILE="/var/log/rclone_backup.log"
LOCK_FILE="/var/run/rclone_backup.lock"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" # Optional

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# Notification function
send_notification() {
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"$1\"}" "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
}

# Double execution check
if [ -e "$LOCK_FILE" ]; then
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

# Start backup
log_message "Starting backup: $SOURCE_DIR -> $REMOTE_NAME:$REMOTE_DIR"

# Execute rclone sync
# --transfers 8: Number of parallel transfers (adjust according to bandwidth)
# --bwlimit 50M: Bandwidth limit (50MB/s) to prevent network monopolization
# --drive-chunk-size 64M: Optimization for Google Drive
# --exclude "venv/**": Exclude unnecessary directories

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

if [ $EXIT_CODE -eq 0 ]; then
    log_message "Backup completed successfully."
    # Do not notify on success, or notify via a daily report
else
    log_message "Backup failed with exit code $EXIT_CODE."
    send_notification "🚨 Backup Failed! Check logs at $LOG_FILE"
fi

# Remove lock file
rm "$LOCK_FILE"
exit $EXIT_CODE
```

After creating the script, grant execution permissions.

```bash
sudo chmod +x /usr/local/bin/backup_to_cloud.sh
```

### Regular Execution and Management via Systemd

While regular execution is possible with Cron, we recommend using Systemd Timer as it makes log management and dependency control easier.

1. Create Service file
`/etc/systemd/system/rclone-backup.service`

```ini
[Unit]
Description=Rclone Backup Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/local/bin/backup_to_cloud.sh
StandardOutput=append:/var/log/rclone_backup_systemd.log
StandardError=append:/var/log/rclone_backup_systemd.log

[Install]
WantedBy=multi-user.target
```

2. Create Timer file
`/etc/systemd/system/rclone-backup.timer`

```ini
[Unit]
Description=Run Rclone Backup daily at 3 AM

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rclone-backup.timer
```

With this, the backup will automatically execute every day at 3 AM. Even if the server restarts, it ensures execution after the network is established.

## Troubleshooting and Optimization

Here is a summary of common issues during operation and their countermeasures.

- "Failed to copy: googleapi: Error 403: User rate limit exceeded"
You hit the Google Drive API rate limit. Add an option like `--tpslimit 10` to limit transactions per second. Also, utilizing your own Client ID/Secret might circumvent the shared limits.

- Large files won't transfer quickly
When transferring dozens-of-GB class model files (.pth, .safetensors) generated in environments like the RTX 5090, expanding `--drive-chunk-size` to `256M` or `512M` can improve throughput. However, since it increases memory usage, set this by consulting your server's RAM capacity (64GB in my environment).

- Using mount as a haven for cold data
Rclone has an `rclone mount` feature. Utilizing this, you can mount Google Drive as a local directory. While training data load speeds become slower, you can leverage the RTX 5090's 32GB VRAM without pressuring local disks by directly mounting it as a destination to offload infrequently accessed cold data or as a source to load models during inference.

Mount command example (Background execution):

```bash
rclone mount gdrive_backup: /mnt/gdrive \
    --daemon \
    --vfs-cache-mode full \
    --vfs-cache-max-size 50G \
    --allow-other
```

Specifying `--vfs-cache-mode full` enables write caching, stabilizing file operations from applications.

## Conclusion

Rclone headless authentication is smoothly configurable once you understand the mechanics. The crucial point is the 3-step flow: "Start setup on server, create token on local, return to server".

With the environment constructed this time, the following operations become possible on an AI development server:

- Reliable Google Drive integration in browserless environments
- Securing a data retreat path to fully utilize the RTX 5090 (32GB) performance
- Robust automated backups via Systemd and Slack notifications

Reducing the risk of disk space depletion and setting up an environment to focus purely on model training and experiments directly improves development efficiency. Refer to the steps in this article to build a robust data management system.
