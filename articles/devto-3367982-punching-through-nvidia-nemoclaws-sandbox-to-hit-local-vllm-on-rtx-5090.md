---
title: "Punching Through NVIDIA NemoClaw's Sandbox to Hit Local vLLM on RTX 5090"
date: 2026-03-18
topics: ["nvidia", "ai", "docker", "linux"]
published: true
canonical_url: "https://dev.to/soytuber/punching-through-nvidia-nemoclaws-sandbox-to-hit-local-vllm-on-rtx-5090-epl"
devto_url: "https://dev.to/soytuber/punching-through-nvidia-nemoclaws-sandbox-to-hit-local-vllm-on-rtx-5090-epl"
devto_id: 3367982
---

> **Disclaimer:** This is an experimental build, not a production setup. NemoClaw is early-stage (v0.0.7), the network hacks are volatile, and I'm documenting this because I couldn't find anyone else trying it.

## What Is NemoClaw?

NVIDIA NemoClaw (OpenShell) is a sandboxed execution environment for AI agents. It runs a k3s cluster inside Docker, creates isolated sandbox namespaces, and lets agents execute code in a locked-down container.

The default workflow: your agent talks to NVIDIA's cloud inference API. The sandbox allows outbound HTTPS to `integrate.api.nvidia.com` and blocks most other traffic.

But what if you have an RTX 5090 sitting right there on the host, running vLLM with Nemotron 9B? I wanted to see if I could route the sandbox's inference to my local GPU instead. Spoiler: it works, but the network isolation requires three separate workarounds.

## The Network Topology

```plaintext
WSL2 Host
  vLLM on 0.0.0.0:8000
  Docker bridge: 172.18.0.1 (yours will differ)
      |
  openshell-cluster container (172.18.0.2)
    k3s cluster
      Pod main namespace (10.200.0.1)
          |
      Sandbox namespace (10.200.0.2)  <-- you are here
```

The sandbox sits inside a network namespace, inside a pod, inside k3s, inside Docker. Three of these boundaries need explicit holes to let traffic through to the host.

## Layer 1: Host iptables

Docker's `DOCKER-USER` chain blocks cross-bridge traffic by default. Replace `br-xxx` with your actual bridge interface name (`ip addr` to find it):

```bash
sudo iptables -I DOCKER-USER 1 \
  -i br-<your-bridge> -p tcp --dport 8000 -j ACCEPT

sudo iptables -I FORWARD 1 \
  -i br-<your-bridge> -o eth0 -p tcp --dport 8000 -j ACCEPT
```

## Layer 2: Network Policy + TCP Relay

The sandbox only allows connections to endpoints in its policy file. Add local addresses:

```yaml
nvidia_inference:
  endpoints:
    - { host: integrate.api.nvidia.com, port: 443 }
    - { host: 10.200.0.1, port: 8000 }
    - { host: 172.18.0.1, port: 8000 }
```

But the sandbox namespace (10.200.0.2) can't reach the Docker bridge (172.18.0.1) directly — different network namespaces. A Python TCP relay in the pod's main namespace bridges the gap:

```python
# relay.py — runs in pod main namespace
server.bind(("10.200.0.1", 8000))
backend.connect(("172.18.0.1", 8000))  # -> host vLLM
```

## Layer 3: Sandbox iptables Injection

The sandbox's own iptables OUTPUT chain has a blanket REJECT. Inject an ACCEPT via nsenter:

```bash
SANDBOX_PID=$(docker exec openshell-cluster-nemoclaw \
  kubectl exec master-impala -n openshell -- \
  cat /var/run/sandbox.pid)

docker exec openshell-cluster-nemoclaw \
  kubectl exec master-impala -n openshell -- \
  nsenter -t $SANDBOX_PID -n \
  iptables -I OUTPUT 1 -d 10.200.0.1 -p tcp --dport 8000 -j ACCEPT
```

## The Hard Part: Making Tool Calls Actually Work

Getting inference responses from the sandbox was only half the battle. The real challenge was making the AI agent (opencode) execute tools — file read/write, shell commands — through local inference.

### The Problem

Nemotron 9B outputs tool calls as raw text in its response:

```python
<TOOLCALL>[{"name":"read_file","arguments":{"path":"app.py"}}]</TOOLCALL>
```

But AI coding agents like opencode expect OpenAI-compatible structured `tool_calls` objects in the API response. There's a mismatch at two levels:

1. **With `tools` parameter**: When a client sends a `tools` parameter in the API request, vLLM can use a custom tool parser plugin to convert the text. I wrote a parser registered via `@ToolParserManager.register_module(name="nemotron_toolcall")` that extracts `<TOOLCALL>` blocks and returns structured tool call objects. This works for direct API calls (e.g. curl with `tools` in the request body).

2. **Without `tools` parameter**: opencode doesn't send `tools` as an API parameter — it embeds tool definitions in the system prompt instead. This means vLLM's parser never activates, and the `<TOOLCALL>` text comes back as plain `content`.

### The Solution: A Gateway That Rewrites SSE Streams

A gateway server sits between the agent and vLLM:

```plaintext
opencode -> Gateway (:8000) -> vLLM (:8100)
```

The gateway buffers the streaming SSE response, accumulates the `content` field across chunks, and checks for `<TOOLCALL>` patterns. When detected, it:

- Strips the `<TOOLCALL>` text from `content`
- Parses the JSON inside
- Injects structured `tool_calls` into the final SSE response

This means tool execution works regardless of whether the client sends `tools` in the request. The gateway also manages on-demand vLLM startup/shutdown to free VRAM when idle.

### The Result

With the network hacks and the gateway in place, the opencode agent inside the sandbox can:

- Read and write files via tool calls
- Execute shell commands
- Iterate on code with multi-turn tool use

All powered by local Nemotron 9B on the RTX 5090, with zero cloud API calls.

## Does It Work?

```bash
# Inside the sandbox
~/ask "Explain PagedAttention in 3 sentences"
# -> hits local RTX 5090

opencode
# -> AI coding agent with tool execution, powered by local GPU
```

Yes. Zero cloud API calls. Code execution stays sandboxed (filesystem isolation is intact), but inference routes to the local GPU through the network holes we opened.

## The Catch: Everything Is Volatile

| Component | Survives restart? |
|---|---|
| Host iptables | No |
| TCP relay | No |
| Sandbox iptables | No |
| Network policy | Yes |
| Sandbox files | No |

Every restart means re-running the setup. A startup script is non-optional.

## Takeaway

NemoClaw's provider system is pluggable — `openshell provider create --type openai` with a custom URL works fine at the API level. The challenge is purely network isolation: the sandbox blocks outbound traffic that isn't whitelisted, and bridging across namespace boundaries requires manual relay and iptables work.

As a proof of concept for running a sandboxed AI agent on local hardware, it works. As a daily workflow — you'll want a startup script.


