---
title: "Implementing Stripe Checkout Billing in PatentLLM"
date: 2026-03-08
topics: ["webdev", "devops", "infrastructure"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/web-infra/patentllm-stripe"
devto_url: "https://dev.to/soytuber/implementing-stripe-checkout-billing-in-patentllm-1kh6"
devto_id: 3326329
---

## Introduction

To commercialize PatentLLM, we implemented a billing system using Stripe Checkout. Existing FTS5 search, web search, and analysis prompts were already complete. The remaining challenge was to "build a billing gate."

## Design Policy: Do Not Hold Card Information

### Reasons for Not Directly Calling the API

We considered directly calling the Stripe API to handle billing, but decided against it.

- Managing card information on the server increases security risks.
- Risk of the entire application becoming unusable during payment errors.

### Adoption of Stripe Checkout

We adopted a method where a "Subscribe" button is placed within the application, transitioning the user to Stripe's payment screen.

- Card information is managed solely by Stripe (not held on our server at all).
- Subscription status is cached in local SQLite upon successful payment.
- Handles network failures with fallback to Stripe API.

## Implementation Highlights

### Graceful Degradation

```bash
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
```

If `STRIPE_SECRET_KEY` is not set in `.env` or if a test key is used, the billing gate is automatically disabled. This simplifies testing in development environments and prevents service outages due to misconfigurations during production deployment.

### Reducing API Calls with Local Cache

```bash
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
```

The local SQLite cache is referenced when valid, and the Stripe API is re-checked only when expired. This minimizes the frequency of API calls.

### UI: Subscription Management

We added the following UI for unregistered users:

- "Subscription" section in the sidebar (displaying remaining days + Customer Portal link).
- "Subscribe" button placed on the main screen.
- Users can manage cancellations and plan changes themselves via the Stripe Customer Portal.

## Summary

- Designed not to hold card information on our server using Stripe Checkout.
- Billing gate ON/OFF controlled by environment variables (easy switching between development/production).
- Minimized Stripe API calls with local SQLite cache.
