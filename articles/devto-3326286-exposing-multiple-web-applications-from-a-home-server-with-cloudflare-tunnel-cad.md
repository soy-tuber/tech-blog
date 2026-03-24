---
title: "Exposing Multiple Web Applications from a Home Server with Cloudflare Tunnel + Caddy"
date: 2026-03-08
topics: ["webdev", "devops", "infrastructure"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/web-infra/cloudflare-caddy-selfhost"
devto_url: "https://dev.to/soytuber/exposing-multiple-web-applications-from-a-home-server-with-cloudflare-tunnel-caddy-32nb"
devto_id: 3326286
---

## Introduction

When publishing multiple web applications on a home server, obtaining a static IP address, managing SSL certificates, and the complexity of security settings can be bottlenecks. This article explains a practical method to solve these challenges and securely publish multiple practical web applications using a combination of Cloudflare Tunnel, Caddy, and WSL2.

## Overall Architecture

The architecture consists of the following three layers:

- Cloudflare Tunnel: A tunnel connecting your home server to the internet (configured with the `cloudflared` command)
- Caddy: Functions as a reverse proxy, responsible for adding security headers and collecting access logs
- App Services: Web applications like Streamlit running on various ports

Caddy receives requests via Cloudflare Tunnel and redirects them to the corresponding applications. URLs can be standardized in the format `service_name.domain_name`.

## Port Design

- App Services: 8xxx range (application execution ports)
- Caddy: 9xxx range (reverse proxy ports)
- URL Naming Convention: `{service_name}.example.org`

## How to Write a Caddyfile

In Caddy 2.x, the site address is written at the beginning, followed by reverse proxy and logging configurations.

```bash
# Caddyfile example (Caddy 2.x format)
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
```

This configuration enables the following:

- Forwarding to applications via reverse proxy
- Enforcing security headers (e.g., Strict-Transport-Security)
- Collecting access logs in JSON format

Regarding Content-Security-Policy, `default-src 'self'` might be too strict for applications like Streamlit that use external resources. Please set an appropriate policy for each application.

## Multi-layered Security

This system enhances security through the following layers:

- Cloudflare: WAF/DDoS protection/SSL automation
- `cloudflared`: Hiding your home IP address
- Caddy: Adding security headers, collecting access logs
- Application Authentication: Access restriction via OTP/PIN
- Data Protection: Sensitive data encryption using Fernet encryption

When combined with Cloudflare Access, you can also implement SSO (Single Sign-On) and multi-factor authentication.

## Daily Security Monitoring

We have built a system that daily analyzes Caddy's access logs via a cron job and notifies suspicious access via Gmail.

```bash
# cron setting (runs daily at 23:55)
55 23 * * * /home/user/logger/daily_log_analyzer.py
```

The analysis process is as follows:

- Extract today's data from Caddy JSON logs
- Aggregate status codes, services, IPs, and User-Agents
- Request analysis from Gemini 2.5 Flash to detect suspicious patterns
- Notify results via Gmail

## Conclusion

The combination of Cloudflare Tunnel + Caddy allows you to securely publish your home server without a static IP address. With Caddy's automatic security header addition and Cloudflare's WAF/DDoS protection, even personal development can achieve enterprise-grade security.
