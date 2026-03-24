---
title: "Cloudflare Tunnel Practical Guide: Securely Exposing a Home AI Server Without Port Forwarding"
date: 2026-03-14
topics: ["webdev", "devops", "infrastructure"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/web-infra/080_premium"
devto_url: "https://dev.to/soytuber/cloudflare-tunnel-practical-guide-securely-exposing-a-home-ai-server-without-port-forwarding-4mec"
devto_id: 3349944
---

## Introduction: Utilizing the Computational Resources of the RTX 5090

For AI developers, a local home environment is a crucial laboratory. Especially if you have acquired the latest RTX 5090 and have an environment where you can freely use its vast 32GB of VRAM, it's a shame to keep it confined within your home. Have you ever wanted to check a generative AI demo on your smartphone while out, or instantly run and show off a custom LLM app during a client meeting?

However, when trying to expose a home server to the internet, the wall of "port forwarding" traditionally stood in the way. Router NAT settings, firewall hole-punching, ISP port restrictions, and the maintenance costs of a static IP address. These are infrastructure management burdens unrelated to the essence of development and also introduce security risks.

Enter "Cloudflare Tunnel." This technology establishes a connection from the inside out (Outbound) from your home server to Cloudflare's edge network, creating a tunnel. There is no need to open ports for external access (Inbound). It works flawlessly even under CGNAT (Carrier-Grade NAT) environments or with dynamic IP addresses, and you can use Cloudflare's robust DDoS protection and WAF for free.

In this article, in addition to the connection procedures, we will explain "service persistence using systemd" and "introducing an authentication foundation using Cloudflare Access." Let's build a secure and practical infrastructure for a home server equipped with an RTX 5090 (such as a Windows 11 WSL2 environment).

## Chapter 1: Architecture and Preparation

The core of Cloudflare Tunnel is a lightweight daemon called "cloudflared" running within the server. This establishes an encrypted connection with Cloudflare's global network. When a user accesses your domain, the request is received at Cloudflare's edge and forwarded to your home server through this tunnel.

### Prerequisites

- Custom Domain: Must be DNS-managed by Cloudflare. Ensure the nameservers are pointed to Cloudflare.
- Home Server: Linux (Ubuntu/Debian recommended), macOS, or Windows 11 WSL2 (Ubuntu) environment.
- Cloudflare Account: The free plan is sufficient.

### Installing cloudflared

First, install the daemon. Here we use an Ubuntu environment as an example.

Run the following commands to add the repository and perform the installation.

```bash
# Install required dependencies
sudo apt-get update
sudo apt-get install -y curl lsb-release

# Add Cloudflare's GPG key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add repository
echo "deb https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Install
sudo apt-get update
sudo apt-get install cloudflared
```

Once the installation is complete, check the version to ensure it was installed correctly.

```bash
cloudflared --version
```

## Chapter 2: Authentication and Tunnel Creation

Handling authentication files is the first stumbling block. Especially when working in a headless environment or via SSH, browser authentication linking can fail.

### Authentication and Certificate Issuance

Running the following command will display an authentication URL.

```bash
cloudflared tunnel login
```

Open the displayed URL in your browser, log in to Cloudflare, select the target domain, and click "Authorize". Upon success, a certificate file "cert.pem" will be generated locally.

If you are working on a server connected via SSH and authenticate by opening the URL in your local PC's browser, the certificate might not be automatically transferred to the server side. In that case, obtain the file from the "cert.pem" download link displayed in the browser and manually place it in the server's `~/.cloudflared/cert.pem`.

### Creating the Tunnel

Next, create the tunnel itself. Give it an easily manageable name (e.g., home-gpu-server).

```bash
cloudflared tunnel create home-gpu-server
```

When this command succeeds, a Tunnel ID (UUID) is issued. Please save this UUID as it will be used in the configuration file later. Simultaneously, a JSON file containing authentication information is generated under `~/.cloudflared/`.

## Chapter 3: Implementing the Configuration File "config.yml"

While it's possible to specify arguments via the command line, managing them in a configuration file (`config.yml`) is recommended for operations. Routing settings for simultaneously exposing multiple services (e.g., Streamlit app, FastAPI, SSH) are also configured here.

Create `~/.cloudflared/config.yml` and write the following contents. Replace the UUID and username to match your environment.

```yaml
# Tunnel UUID (issued via the create command)
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Path to the credentials file
credentials-file: /home/your_user/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

# Ingress rules (matched from top to bottom)
ingress:
  # Main AI app (e.g., Streamlit)
  # Subdomain: app.example.com
  - hostname: app.example.com
    service: http://localhost:8501

  # API Endpoint (e.g., FastAPI)
  # Subdomain: api.example.com
  - hostname: api.example.com
    service: http://localhost:8000

  # SSH Access (Browser rendering)
  # Subdomain: ssh.example.com
  - hostname: ssh.example.com
    service: ssh://localhost:22

  # Default rule (Required)
  # Requests that don't match return 404
  - service: http_status:404
```

### Registering DNS Records

Register the hostnames (subdomains) specified in the configuration file to Cloudflare's DNS and link them with the tunnel. CNAME records will be created.

```bash
# Link domain for the app
cloudflared tunnel route dns home-gpu-server app.example.com

# Link domain for the API
cloudflared tunnel route dns home-gpu-server api.example.com
```

## Chapter 4: Service Persistence via systemd (Auto-start Configuration)

While you can start it manually during development, for continuous operation, it is convenient to configure the tunnel and app to automatically start up upon OS boot (with systemd enabled in WSL2 environments).

### Converting cloudflared to a Service

cloudflared has a built-in service installation feature.

```bash
sudo cloudflared service install
```

This copies the configuration file to `/etc/cloudflared/config.yml` and registers it as a systemd service. If the `config.yml` you created earlier is in your home directory, copy it to the designated location using the following commands.

```bash
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
sudo cp ~/.cloudflared/cert.pem /etc/cloudflared/
```

Start the service.

```bash
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared
```

### Converting the Application (Streamlit) to a Service

Starting just the tunnel is meaningless if the app inside isn't running. Let's manage Python apps like Streamlit using systemd as well. Below is an example of a service definition file for an app using a virtual environment (`.venv`) built with a package manager like `uv`.

Create a file named `/etc/systemd/system/ai-app.service`.

```ini
[Unit]
Description=AI Streamlit App
# Wait for network and tunnel to be ready
After=network.target cloudflared.service

[Service]
Type=simple
# Specify execution user
User=your_user
WorkingDirectory=/home/your_user/projects/my-ai-app
# Set PATH environment variable (include virtual environment bin)
Environment="PATH=/home/your_user/projects/my-ai-app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
# App launch command
ExecStart=/home/your_user/projects/my-ai-app/.venv/bin/streamlit run src/main.py --server.port 8501 --server.headless true
# Auto-restart settings on crash
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

After creation, have systemd recognize it and start it.

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-app
sudo systemctl start ai-app
```

Now, just by turning on the server, Cloudflare Tunnel and the AI app will automatically start and be accessible externally.

## Chapter 5: Secure Access Control via Cloudflare Access

Although port forwarding isn't required, exposing it to the web means anyone can access it. If you don't want others to see the app under development, you can insert an authentication screen using Cloudflare Access (Zero Trust). This is also available on the free tier.

1. Access the Cloudflare Zero Trust Dashboard (https://one.dash.cloudflare.com/).
2. Select "Access" -> "Applications" -> "Add an application".
3. Choose "Self-hosted" and enter the exposed subdomain (e.g., app.example.com).
4. In the policy settings, set conditions to allow access.
   - Rule action: Allow
   - Include: Emails - Your email address
5. Save and apply.

With this, accessing your app will display a login screen provided by Cloudflare. Unless you enter the code sent to the specified email address, packets will not reach the home server at the end of the tunnel. It is more robust than Basic authentication and saves the trouble of implementing authentication features within the app itself.

## Conclusion: Streamlining Infrastructure Management to Focus on Development

Through the above steps, we were able to expose a home server equipped with the RTX 5090's 32GB VRAM in a secure and stable state.

- Port forwarding: Not required
- Static IP: Not required
- SSL Certificates: Managed automatically by Cloudflare
- DDoS Protection: Included standard
- Authentication feature: Can be retrofitted with Cloudflare Access

This setup dramatically reduces operational overhead. Alleviate the burden of infrastructure management and focus on your true goal: developing AI/LLM applications.

If errors occur, you can check real-time logs with the following commands.

```bash
# Check tunnel logs
sudo journalctl -u cloudflared -f

# Check app logs
sudo journalctl -u ai-app -f
```

The possibilities for home servers are expanding. Build a secure infrastructure and accelerate your development.
