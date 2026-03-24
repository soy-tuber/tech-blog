---
title: "Adding Stripe Checkout to a Solo SaaS: Lessons from PatentLLM's $1K/mo Plan"
date: 2026-03-21
topics: ["stripe", "saas", "python", "startup"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-patentllm-stripe"
devto_url: "https://dev.to/soytuber/adding-stripe-checkout-to-a-solo-saas-lessons-from-patentllms-1kmo-plan-1c4d"
devto_id: 3380012
---


PatentLLM started as a free patent search tool. Making it a paid product meant answering one question first: how do you handle payments when you're a solo developer who doesn't want to touch credit card numbers?

The answer, of course, is Stripe Checkout. But the implementation details — graceful degradation for development, local caching to avoid API hammering, and the sales infrastructure around it — were more interesting than I expected.

## Why Stripe Checkout Instead of Stripe Elements

Stripe offers two main integration paths:

**Stripe Elements** gives you embeddable UI components. You get full control over the look and feel, but you're responsible for handling card data, SCA (Strong Customer Authentication), and error states.

**Stripe Checkout** redirects users to a Stripe-hosted payment page. You lose design control but gain PCI compliance for free, automatic SCA handling, and support for dozens of payment methods without any additional code.

For a solo developer targeting US patent law firms at $1,000/month, the choice was obvious. These are not consumers who care about a pixel-perfect checkout experience. They care about security, invoices, and whether their IT department will approve the vendor. Stripe Checkout checks all those boxes.

## The Integration

The core flow is minimal:

```python
import stripe
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.post("/subscribe")
async def create_checkout_session(request: Request):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price": PRICE_ID,
            "quantity": 1,
        }],
        success_url=f"{BASE_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/pricing",
        customer_email=current_user.email,
    )
    return RedirectResponse(session.url, status_code=303)
```

The user clicks "Subscribe," gets redirected to Stripe's hosted checkout page, enters their card, and gets redirected back. At no point does my server see a credit card number.

## Graceful Degradation: The Key Design Decision

Here's the thing about developing a SaaS locally: you don't want to set up Stripe test keys just to work on the search algorithm. And you definitely don't want a missing environment variable to crash the entire app.

The solution is a graceful degradation pattern:

```python
def get_stripe_mode():
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        return "disabled"  # No paywall at all
    if key.startswith("sk_test_"):
        return "test"      # Stripe test mode
    return "live"          # Production

def check_subscription(user_id: str) -> bool:
    mode = get_stripe_mode()
    if mode == "disabled":
        return True  # All features unlocked in dev
    cached = check_local_cache(user_id)
    if cached is not None:
        return cached
    return check_stripe_api(user_id)
```

This three-tier approach means:
- **No key**: Everything unlocked, zero API calls. Perfect for development.
- **Test key**: Full payment flow with Stripe test cards. Perfect for staging.
- **Live key**: Real payments. Production.

The same codebase works in all three environments without any if-else branching in the feature code.

## Local Subscription Cache

Calling the Stripe API on every page load to check subscription status is wasteful and slow. Instead, I cache subscription state in a local SQLite database:

```python
def cache_subscription(user_id, active, expires_at):
    db.execute(
        "INSERT OR REPLACE INTO subscriptions "
        "(user_id, active, expires_at, checked_at) "
        "VALUES (?, ?, ?, ?)",
        (user_id, active, expires_at, datetime.utcnow())
    )

def check_local_cache(user_id):
    row = db.execute(
        "SELECT active, expires_at, checked_at "
        "FROM subscriptions WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    if not row:
        return None
    if (datetime.utcnow() - row[2]).seconds > 3600:
        return None  # Stale cache
    return row[0] and row[1] > datetime.utcnow()
```

The cache is the first thing checked. Only if it's missing or stale does the app hit the Stripe API. This reduces API calls by roughly 99% in normal operation.

## Webhook for Real-Time Updates

Stripe sends webhooks when subscription status changes (renewal, cancellation, payment failure). A webhook endpoint keeps the local cache fresh:

```python
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    if event.type == "customer.subscription.updated":
        sub = event.data.object
        cache_subscription(
            user_id=sub.metadata.get("user_id"),
            active=sub.status == "active",
            expires_at=datetime.fromtimestamp(sub.current_period_end)
        )
    return {"status": "ok"}
```

## The Sales Side: Building the Law Firm Pipeline

Technical integration is the easy part. Finding customers is harder. For context: US patent law firms range from 2-person practices to 500+ attorney firms. The target for a $1K/month tool is mid-size firms (10-50 attorneys) that do enough patent prosecution to benefit from AI-assisted prior art search but aren't big enough to build their own tools.

I generated a tiered prospect list:
- **Tier 1**: 16 large firms (Fish & Richardson, Finnegan, etc.) — long sales cycles, but high LTV
- **Tier 2**: 24 mid-size firms — the sweet spot
- **Tier 3+**: Smaller firms — potential for self-serve sign-up

The outreach template is short and specific: what the tool does, a link to try it (free tier), and one sentence about why AI-assisted prior art search matters for their workflow. No jargon. No "leverage synergies." Just "search 3.5M patents in 3ms."

## What I'd Do Differently

**Start with annual billing.** Monthly churn at $1K/mo is painful. A 20% discount for annual billing ($9,600/year instead of $12,000) is standard in legal SaaS and dramatically improves cash flow predictability.

**Add a usage-based component.** The search feature has near-zero marginal cost. The AI analysis feature (which calls Gemini) has real API costs. A hybrid model — flat monthly fee for search, pay-per-use for AI analysis — would better align pricing with value delivered.

**Customer Portal from day one.** Stripe's Customer Portal lets users manage their own subscriptions — update payment methods, download invoices, cancel. Enabling it takes 10 minutes in the Stripe Dashboard and eliminates an entire category of support requests.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

