---
title: "Cloudflare Tunnel + Caddyで複数のWebアプリを自宅サーバーから公開する"
emoji: "🔧"
type: "tech"
topics: ["webdev", "fastapi", "infrastructure", "cloudflare"]
published: true
canonical_url: "https://media.patentllm.org/blog/web-infra/cloudflare-caddy-selfhost"
---


## はじめに


自宅サーバーで複数のWebアプリを公開する際、固定IPアドレスの取得やSSL証明書の管理、セキュリティ設定の煩雑さがネックになります。本記事では、Cloudflare Tunnel、Caddy、WSL2の組み合わせで、これらの課題を解決し、複数の実用的なWebアプリを安全に公開する実践手法を解説します。


## 全体アーキテクチャ


構成は以下の3層です。

- Cloudflare Tunnel：自宅サーバーをインターネットに接続するトンネル（cloudflaredコマンドで設定）
- Caddy：リバースプロキシとして機能し、セキュリティヘッダー付与やアクセスログ収集を担当
- Appサービス：各ポートで動作するStreamlit等のWebアプリ

CaddyはCloudflare Tunnel経由でリクエストを受け取り、対応するアプリにリダイレクトします。URLはサービス名.ドメイン名の形式で統一できます。


## ポート設計


- Appサービス：8xxx番台（アプリ実行ポート）
- Caddy：9xxx番台（リバースプロキシポート）
- URL命名規則：{サービス名}.example.org


## Caddyfileの書き方


Caddy 2.xでは、サイトアドレスを先頭に記述し、その中にリバースプロキシやログの設定を記載します。

[bash]
# Caddyfile例（Caddy 2.x形式）
:9530 {
    log {
        output file /var/log/caddy/access.log {
            roll_size 10mb
            roll_keep 30
        }
        format json
    }

    reverse_proxy localhost:8530 {
        header_up X-Forwarded-Proto https
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options "nosniff"
    }
}
[/bash]

この設定により、以下を実現できます。

- リバースプロキシ経由でアプリに転送
- セキュリティヘッダーの強制付与（Strict-Transport-Security等）
- JSON形式のアクセスログ収集

なお、Content-Security-Policyについては、Streamlit等の外部リソースを使用するアプリでは default-src 'self' だけでは厳しすぎる場合があります。アプリごとに適切なポリシーを設定してください。


## セキュリティ多層防御


本システムは以下の層でセキュリティを強化しています。

- Cloudflare：WAF/DDoS防御/SSL自動化
- cloudflared：自宅IPの非公開化
- Caddy：セキュリティヘッダー付与、アクセスログ収集
- アプリ認証：OTP/PINによるアクセス制限
- データ保護：Fernet暗号化による機密データ暗号化

Cloudflare Accessと組み合わせれば、SSO（シングルサインオン）や多要素認証も導入できます。


## 日次セキュリティ監視


cronジョブでCaddyのアクセスログを毎日分析し、不審なアクセスをGmailで通知する仕組みを構築しています。

[bash]
# cron設定（毎日23:55に実行）
55 23 * * * /home/user/logger/daily_log_analyzer.py
[/bash]

分析プロセスは以下の流れです。

- Caddy JSONログから当日分を抽出
- ステータスコード、サービス、IP、User-Agentを集計
- Gemini 2.5 Flashに分析を依頼し、不審パターンを検出
- 結果をGmailで通知


## まとめ


Cloudflare Tunnel + Caddyの組み合わせにより、固定IPなしで自宅サーバーを安全に公開できます。Caddyのセキュリティヘッダー自動付与とCloudflareのWAF/DDoS防御で、個人開発でもエンタープライズ級のセキュリティを実現できます。
