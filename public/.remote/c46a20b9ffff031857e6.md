---
title: PatentLLMにStripe Checkout課金を実装した話
tags:
  - WebDev
  - infrastructure
  - cloudflare
  - FastAPI
private: false
updated_at: '2026-03-21T21:41:11+09:00'
id: c46a20b9ffff031857e6
organization_url_name: null
slide: false
ignorePublish: false
---


## はじめに


PatentLLMの商用化に向け、Stripe Checkoutで課金システムを実装しました。既存のFTS5検索・Web検索・分析プロンプトは完成済み。残る課題は「課金ゲートの構築」でした。


## 設計方針：カード情報を持たない


▼直接API呼び出しを見送った理由

StripeのAPIを直接呼び出して課金処理を行う案も検討しましたが、見送りました。

- カード情報をサーバーで管理するとセキュリティリスクが高まる
- 決済エラー時にアプリ全体が利用不能になるリスク

▼Stripe Checkoutの採用

アプリ内に「Subscribe」ボタンを配置し、Stripeの決済画面に遷移する方式を採用。

- カード情報はStripe側でのみ管理（自サーバーに一切保持しない）
- 決済成功時にサブスクリプション状態をローカルSQLiteにキャッシュ
- Stripe APIへのフォールバックでネットワーク障害にも対応


## 実装のポイント


▼Graceful Degradation

[bash]
import os
import stripe

stripe_key = os.getenv('STRIPE_SECRET_KEY', '')

def is_billing_enabled():
    """課金ゲートの有効/無効を判定"""
    if not stripe_key:
        return False  # キー未設定→課金無効（開発環境）
    if stripe_key.startswith('sk_test_'):
        return False  # テストキー→課金無効
    return True
[/bash]

`.env`に`STRIPE_SECRET_KEY`を設定しない場合やテストキーの場合、課金ゲートを自動で無効化します。開発環境での動作確認が容易になり、本番移行時の設定ミスによるサービス停止も防げます。

▼ローカルキャッシュによるAPIコール削減

[bash]
import sqlite3
from datetime import datetime, timedelta

def check_subscription(user_id):
    """サブスクリプション状態を確認（ローカルキャッシュ優先）"""
    conn = sqlite3.connect('subscriptions.db')

    # ローカルキャッシュを確認
    row = conn.execute(
        'SELECT status, expires_at FROM subscriptions WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if row and row[0] == 'active':
        expires = datetime.fromisoformat(row[1])
        if expires > datetime.now():
            return True  # キャッシュ有効

    # キャッシュが無いか期限切れ→Stripe APIで確認
    sub = stripe.Subscription.retrieve(user_id)
    # 結果をキャッシュに保存
    conn.execute(
        'INSERT OR REPLACE INTO subscriptions VALUES (?, ?, ?)',
        (user_id, sub.status,
         (datetime.now() + timedelta(hours=1)).isoformat())
    )
    conn.commit()
    return sub.status == 'active'
[/bash]

有効期限内はローカルSQLiteのキャッシュを参照し、期限切れの場合のみStripe APIで再確認。APIコール頻度を最小限に抑えます。

▼UI：サブスクリプション管理

未登録ユーザー向けに以下のUIを追加しました：

- サイドバーに「Subscription」セクション（残り日数表示 + Customer Portalリンク）
- メイン画面に「Subscribe」ボタンを配置
- Stripe Customer Portalで解約・プラン変更をユーザー自身が操作可能


## まとめ


- Stripe Checkoutでカード情報を自サーバーに持たない設計
- 環境変数で課金ゲートのON/OFFを制御（開発/本番の切り替えが容易）
- ローカルSQLiteキャッシュでStripe APIコールを最小化

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/web-infra/patentllm-stripe)*
