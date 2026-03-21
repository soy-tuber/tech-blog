---
title: Streamlit × Flutter双方向連携をWSL2で実現する
tags:
  - WebDev
  - infrastructure
  - cloudflare
  - FastAPI
private: false
updated_at: '2026-03-21T21:41:13+09:00'
id: fb1ea862b27d27c4b9f7
organization_url_name: null
slide: false
ignorePublish: false
---


## CORS問題の解決策


WSL2環境下でStreamlitを外部からアクセス可能にする際、CORSエラーが発生するケースがあります。WSL2上で動作するNginxをプロキシサーバーとして利用することで解決できます。


### Nginx設定


[bash]
# /etc/nginx/sites-available/streamlit
server {
    listen 80;
    server_name your-domain.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
[/bash]

[bash]
sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo systemctl restart nginx
[/bash]


## FlutterからPythonへの双方向通信


Streamlitはリクエストごとにスクリプトを再実行する特性があるため、リアルタイム通信にはWebSocketを使用します。Flask-SocketIOで双方向通信を実現しました。


### Flutter側（Dart）


[text]
class FlutterStreamlitBridge {
  final WebSocketChannel channel;

  Future<void> sendCommand(String command) async {
    channel.sink.add(json.encode({"type":"command","data":command}));
  }

  Stream<String> receiveResponse() {
    return channel.stream.map((message) {
      final data = json.decode(message);
      return data['result'] as String;
    });
  }
}
[/text]


### Python側（Flask-SocketIO）


[python]
from flask import Flask
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('command')
def handle_command(data):
    def process():
        command_data = data.get('data')
        result = f"処理結果: {command_data}"
        socketio.emit('response', {'result': result})
    thread = threading.Thread(target=process)
    thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
[/python]

StreamlitとWebSocketサーバーは異なるポートで動作させる必要があります。


## Cloudflare Tunnel経由の実運用


開発環境から本番環境への移行にはCloudflare Tunnelを活用しました。Cloudflare TunnelはFreeプランでも利用可能です。

[bash]
cloudflared tunnel create streamlit-tunnel
cloudflared tunnel run streamlit-tunnel --url http://localhost:8501
[/bash]

SSL/TLS暗号化された通信経路が構築され、CloudflareのDDoS保護機能も自動的に適用されます。


## セキュリティ設計


不正アクセス防止のため、メールアドレスのドメイン検証を実装しています。

[python]
import sqlite3

class EmailValidator:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def validate_domain(self, email):
        domain = email.split('@')[-1]
        self.cursor.execute(
            "SELECT 1 FROM allowed_emails WHERE domain = ?", (domain,)
        )
        return self.cursor.fetchone() is not None
[/python]

その他のセキュリティ対策として以下を実装しています。
- OTP試行回数制限（5回失敗でロック）
- Cookieベースのセッション管理
- 暗号化されたトークンストレージ


## まとめ


WSL2環境下でStreamlitとFlutterを連携させる実践手法を解説しました。CORS問題の解決、WebSocketによるリアルタイム通信、Cloudflare Tunnelによる安全な公開方法が主なポイントです。NginxプロキシとWebSocketサーバーを組み合わせることで、フロントエンドとバックエンドのシームレスな統合を実現できます。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/web-infra/streamlit-flutter-wsl2)*
