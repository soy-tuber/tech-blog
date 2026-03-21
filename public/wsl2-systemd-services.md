---
title: WSL2でsystemdサービスを使いvLLM・Flask・cronを自動起動する運用術
tags:
  - python
  - devtools
  - cli
  - productivity
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


## WSL2のsystemd対応


WSL2でsystemdを有効化するには、/etc/wsl.confを設定します。

[bash]
# /etc/wsl.confに追記
[boot]
systemd=true
[/bash]

変更を反映するにはWSL2を再起動します。

[bash]
wsl --shutdown
[/bash]

設定後、systemctl --all でサービス一覧を確認できます。ユーザーサービスをWSL2起動時に自動開始させるには、loginctl enable-linger コマンドの実行が必要です。


## vLLMのsystemdユニットファイル



### 起動スクリプト


[bash]
#!/bin/bash
set -e
export CUDA_VISIBLE_DEVICES=0

python3 -m vllm.entrypoints.openai.api_server \
  --host 0.0.0.0 \
  --port 8000 \
  --model nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.9 \
  --trust-remote-code \
  --tensor-parallel-size 1
[/bash]


### systemdユニットファイル（~/.config/systemd/user/vllm.service）


[bash]
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/vllm
ExecStart=%h/vllm_server.sh
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
[/bash]

設定のポイントは以下の通りです。
- CUDA_VISIBLE_DEVICES=0で使用するGPUを指定します
- --trust-remote-codeはHugging Faceモデルのカスタムコード実行を許可します。信頼できるモデルにのみ使用してください
- Restart=alwaysで自動リカバリーを実現します


### 有効化コマンド


[bash]
systemctl --user daemon-reload
systemctl --user enable vllm.service
systemctl --user start vllm.service
[/bash]


## Flask APIのサービス化


vLLMのAPIをラップしたFlaskアプリケーションをサービス化します。

[python]
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json['prompt']
    response = requests.post(
        'http://localhost:8000/v1/completions',
        json={'model': 'nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese',
              'prompt': prompt, 'max_tokens': 200}
    )
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8510)
[/python]


### systemdユニットファイル


[bash]
[Unit]
Description=Flask API for vLLM
After=vllm.service

[Service]
Type=simple
WorkingDirectory=%h/flask_api
ExecStart=%h/.venv/bin/python app.py
Restart=always
RestartSec=3s

[Install]
WantedBy=default.target
[/bash]

After=vllm.serviceを指定することで、vLLMが起動完了後にのみFlask APIが起動します。


## cronとの使い分け


定期実行タスクにはsystemdタイマーを使用します。


### タイマー設定（~/.config/systemd/user/daily-report.timer）


[bash]
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
[/bash]

[bash]
systemctl --user enable daily-report.timer
[/bash]

cronと比較したsystemdタイマーの利点は以下の通りです。
- journalctlでログを一元管理できます
- 依存関係を明示的に指定できます
- Persistent=trueで未実行分を自動補完します


## 起動順序と依存関係


- vLLM：基盤となる推論エンジンです
- Flask API：vLLMに依存します（After=vllm.service）
- 日報生成：両方のログを参照します

[bash]
systemctl --user list-dependencies vllm.service
[/bash]


## ログ確認（journalctl）


[bash]
# サービス単位のログ
journalctl --user -u vllm.service -f

# 直近100件のログ
journalctl --user -u vllm.service -n 100

# エラーログのみ抽出
journalctl --user -u vllm.service --since "24 hours ago" | grep -i "error\|fail"
[/bash]


## まとめ


WSL2でsystemdを活用し、vLLM・Flask・定期タスクをシームレスに連携させる運用構築を解説しました。
- CUDA 12.8とRTX 5090を最大限活用したvLLMサービス化を実現しました
- After=指定によるサービス依存管理が同時起動エラーを解消する鍵です
- journalctlによるリアルタイムモニタリングで運用の安定性を確保します

本設定はNemotronを基盤にした日本語推論モデルの実用化を支えるインフラとして活用可能です。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/wsl2-systemd-services)*
