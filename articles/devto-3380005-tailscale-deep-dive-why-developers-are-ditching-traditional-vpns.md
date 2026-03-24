---
title: "Tailscale Deep Dive: Why Developers Are Ditching Traditional VPNs"
date: 2026-03-21
topics: ["networking", "devops", "security", "linux"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-tailscale-deep-dive"
devto_url: "https://dev.to/soytuber/tailscale-deep-dive-why-developers-are-ditching-traditional-vpns-413h"
devto_id: 3380005
---


Every developer I know who tries Tailscale has the same reaction: "Wait, that's it? It just... works?"

That reaction is the entire product thesis. VPN setup has been painful for decades — configuring OpenVPN, managing certificates, debugging NAT traversal, opening firewall ports. Tailscale makes it feel like connecting to WiFi. But the engineering underneath is anything but simple.

Here's what's actually happening when you install Tailscale and everything "just works."

## The Foundation: WireGuard

Tailscale is built on WireGuard, and understanding WireGuard is essential to understanding why Tailscale performs so well.

WireGuard is a VPN protocol created by Jason Donenfeld. Compared to its predecessors:

| | OpenVPN | IPsec | WireGuard |
|---|---------|-------|-----------|
| Lines of code | ~100,000 | ~400,000 | ~4,000 |
| Encryption | Configurable (TLS) | Configurable (IKE) | Fixed (ChaCha20, Curve25519) |
| Handshake | Multi-round | Complex (IKE phases) | 1-RTT |
| Kernel integration | Userspace | Kernel module | Kernel module |
| Connection setup | Seconds | Seconds | Milliseconds |

The "fixed cryptography" decision is the most important design choice. OpenVPN and IPsec let you configure cipher suites, which means every deployment is a snowflake, and misconfigurations create vulnerabilities. WireGuard uses exactly one cryptographic construction — no negotiation, no downgrade attacks, no configuration.

The result: WireGuard achieves **3-4x the throughput** of OpenVPN on the same hardware, with sub-100ms connection establishment. It's so fast that you can have it running permanently without noticing any overhead.

## What Tailscale Adds on Top of WireGuard

WireGuard alone is a point-to-point VPN protocol. You need to manually configure each peer's public key, IP address, and endpoint. For two machines, this is fine. For 20 machines, it's a spreadsheet. For 200 machines, it's a full-time job.

Tailscale adds three critical layers:

### 1. Coordination Server (The Control Plane)

Tailscale runs a coordination server that manages the mesh network. When you install Tailscale on a device:

1. The device generates a WireGuard keypair
2. It registers the public key with the coordination server
3. The coordination server distributes peer information to all other devices in your network
4. Each device establishes direct WireGuard tunnels to every other device

**Key point:** The coordination server never sees your traffic. It only distributes public keys and endpoint information — the same role a DNS server plays, but for WireGuard peers. All actual data flows through direct, encrypted WireGuard tunnels.

This is the fundamental difference from traditional VPNs: there's no central server that all traffic routes through. It's a mesh network where every device connects directly to every other device.

### 2. NAT Traversal (The Hard Part)

Most devices are behind NAT — your laptop at a coffee shop, your home server behind a consumer router, your phone on a carrier network. NAT was designed to prevent direct incoming connections, which is exactly what a mesh VPN needs.

Tailscale's NAT traversal uses a technique called **STUN (Session Traversal Utilities for NAT)**:

1. Both devices send packets to a STUN server to discover their public IP and port mapping
2. The coordination server shares these discovered endpoints
3. Both devices simultaneously send packets to each other's discovered endpoints
4. NAT routers on both sides see the outgoing packets and create firewall holes
5. Direct connection established

This "UDP hole punching" works for about 94% of NAT configurations. For the remaining 6% (symmetric NAT, carrier-grade NAT, particularly aggressive firewalls), Tailscale has a fallback.

### 3. DERP Relay Servers (The Fallback)

When direct connection fails, traffic routes through Tailscale's DERP (Designated Encrypted Relay for Packets) servers. These are relay servers deployed globally — currently in 20+ cities worldwide.

**Critically, DERP relays see only encrypted WireGuard traffic.** They relay packets but cannot decrypt them. It's like a postal service that carries sealed envelopes — they know the source and destination, but not the contents.

DERP is designed as a fallback, not the primary path. Tailscale aggressively tries to establish direct connections, and the client continuously re-attempts direct paths even while using DERP. In practice:

- ~94% of connections are direct (peer-to-peer)
- ~5% start on DERP and upgrade to direct within seconds
- ~1% stay on DERP for the duration (truly hostile NAT environments)

## Zero Trust: Not Just a Buzzword

Traditional VPNs create a "trusted zone" — once you're connected, you can access everything on the network. This is the castle-and-moat model, and it's why VPN credentials are such a high-value target for attackers.

Tailscale's ACL (Access Control List) system operates differently. You define rules about which devices can access which services:

```json
{
  "acls": [
    {"action": "accept", "src": ["group:dev"], "dst": ["tag:production:443"]},
    {"action": "accept", "src": ["group:ops"], "dst": ["tag:production:*"]}
  ]
}
```

A developer can reach port 443 (HTTPS) on production servers but nothing else. An ops engineer gets full access. Compromising a developer's laptop doesn't give an attacker access to SSH on production — the network-level access simply doesn't exist.

## Why Developers Love Tailscale (Speaking from Experience)

I use Tailscale to connect a Chromebook (ARM64, always-on development machine) to a desktop with an RTX 5090 (GPU inference server). Here's what the experience is actually like:

**Setup took 3 minutes.** Install on both machines, log in with the same account, done. No port forwarding on the router. No dynamic DNS. No SSH tunnel management.

**SSH just works.** `ssh soy@100.109.56.59` connects to my desktop whether I'm at home, at a coffee shop, or on mobile data. The Tailscale IP never changes regardless of the physical network.

**It's invisible.** Tailscale runs as a background service and uses essentially zero CPU. I forget it's there until I need to access a machine remotely, at which point it's just... available.

**MagicDNS.** Instead of remembering `100.109.56.59`, I can use `desktop.tail-net.ts.net`. Tailscale runs a local DNS resolver that maps machine names to Tailscale IPs.

## Tailscale vs. Traditional VPNs: The Architecture Difference

```plaintext
Traditional VPN (Hub-and-Spoke):
  Device A --> VPN Server --> Device B
  Device C --> VPN Server --> Device D
  (All traffic routes through one server = bottleneck + single point of failure)

Tailscale (Mesh):
  Device A <--> Device B (direct)
  Device A <--> Device C (direct)
  Device B <--> Device D (direct)
  (Traffic goes directly between devices = no bottleneck, no SPOF)
```

The mesh approach means: no bandwidth bottleneck at a central server, latency is minimized (one hop instead of two), and there's no single point of failure. If the coordination server goes down, existing connections continue working — they just can't add new peers until it comes back.

## The Open Source Angle

Tailscale's client is open source (BSD 3-Clause license) and available on GitHub. The coordination server is proprietary, but there's an open-source alternative called **Headscale** that you can self-host. If you want the Tailscale architecture without depending on Tailscale the company, Headscale gives you that option.

This is a smart business model: the client being open source means security researchers can audit it, and the self-hostable alternative means large organizations aren't locked in. Tailscale's actual value proposition is the managed coordination server, DERP infrastructure, and the admin dashboard — operational overhead that most teams would rather pay for than maintain.

## When NOT to Use Tailscale

Tailscale isn't always the answer:

- **High-throughput data transfer**: WireGuard adds encryption overhead. For terabytes of data transfer between machines on the same LAN, a direct connection is faster.
- **Network-level isolation requirements**: Some compliance frameworks require physically separate networks. Tailscale's logical separation might not satisfy auditors.
- **Extremely latency-sensitive applications**: The NAT traversal and occasional DERP relay add milliseconds. For sub-millisecond requirements (HFT, real-time audio), dedicated infrastructure is better.

For everything else — developer access to servers, IoT device management, remote work infrastructure, connecting cloud and on-prem resources — Tailscale is the obvious choice. It's one of those tools where the main regret is not adopting it sooner.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

