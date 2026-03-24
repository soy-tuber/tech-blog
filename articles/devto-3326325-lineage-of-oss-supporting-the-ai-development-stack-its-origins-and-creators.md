---
title: "Lineage of OSS Supporting the AI Development Stack: Its Origins and Creators"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/giants-of-code"
devto_url: "https://dev.to/soytuber/lineage-of-oss-supporting-the-ai-development-stack-its-origins-and-creators-1aia"
devto_id: 3326325
---

Local AI development environments are built upon numerous open-source technologies. This article organizes the key technologies that constitute the author's development environment (RTX 5090 + Core Ultra 9 285K + WSL2 Ubuntu), detailing their origins and design decisions in chronological order.

## Programming Language: Python (1991) — Guido van Rossum

Guido van Rossum, from the Netherlands, began developing Python in 1989 as a Christmas holiday project while working at CWI (Centrum Wiskunde & Informatica - National Research Institute for Mathematics and Computer Science) in Amsterdam. The name is derived from Monty Python. Its design philosophy, "Readability is paramount," is symbolized by its enforced block structure through indentation.

The reasons for its adoption as the common language of AI include the numerical computation foundation provided by NumPy/SciPy, its compatibility with Jupyter Notebook, and the ease of experimentation offered by dynamic typing. Van Rossum guided the language as its "Benevolent Dictator For Life (BDFL)" and retired from the role in 2018. He subsequently joined Microsoft and is working on projects to accelerate CPython.

## GPU General-Purpose Computing: CUDA (1993) — Jensen Huang

Born in Taiwan, Jensen Huang (黄仁勲) moved to the U.S. at age 9. After studying electrical engineering at Oregon State University and gaining chip design experience at LSI Logic and AMD, he co-founded NVIDIA in 1993 with Chris Malachowsky and Curtis Priem at a Denny's restaurant. He was 30 years old at the time.

In 1999, NVIDIA defined the term "GPU" and released the GeForce 256. In 2006, they introduced CUDA, a programming model that enables GPUs for general-purpose parallel computing. Neural network training is inherently matrix computation, which pairs well with the parallel processing capabilities of thousands of GPU cores. AlexNet (trained on a GTX 580) demonstrated this in 2012, marking the beginning of the deep learning era. The current RTX 5090 features 21,760 CUDA Cores and 680 Tensor Cores, achieving approximately 170 TFLOPS in FP16.

## Embedded Database: SQLite (2000) — D. Richard Hipp

D. Richard Hipp was involved in developing damage control systems for U.S. Navy guided missile destroyers. The systems at the time used Informix, but faced issues with the cumbersome server startup process. He designed SQLite as a serverless database to address this, creating an RDBMS that requires no configuration and is self-contained in a single file.

Its estimated deployment count exceeds one billion. It is embedded in devices and applications such as iPhone, Android, Chrome, Firefox, and the flight control systems of the Boeing 787. The license is public domain (copyright waived). Hipp continues to maintain the codebase almost single-handedly, with the full-featured code size being approximately 600KB. It guarantees ACID transactions using WAL (Write-Ahead Logging).

## OS: Ubuntu (2004) — Mark Shuttleworth

Mark Shuttleworth, from South Africa, founded the SSL certificate authority Thawte in 1999 and sold it to VeriSign for approximately $575 million. In 2002, he traveled to the International Space Station aboard a Soyuz spacecraft, becoming the first private citizen from the African continent to go to space. After his return in 2004, he founded Canonical and released Ubuntu.

Based on Debian, its regular releases (LTS every two years) and APT package management resolved the problem of Linux installations "taking several days" at the time. The name means "I am because we are" in Zulu. Currently, the majority of AI research infrastructure, including HuggingFace servers, Google Colab backend VMs, and AWS Deep Learning AMIs, runs on Ubuntu.

## Foundation of Deep Networks: ResNet (2015) — Kaiming He

Kaiming He, from Guangdong Province, China, graduated from Tsinghua University and earned his Ph.D. from the Chinese University of Hong Kong. He published ResNet during his research at Microsoft Research Asia. To address the "degradation problem," where training accuracy itself worsens as networks become deeper, he proposed Skip Connections (residual connections).

With the structure y = F(x) + x, unnecessary layers can learn F(x)=0, effectively becoming an identity mapping. This design successfully enabled the training of a 152-layer network. Residual Connections are also incorporated into current Transformer architectures (e.g., GPT, BERT). It has over 400,000 citations on Google Scholar. He moved from FAIR (Meta AI) and became a professor at MIT in 2024.

## Deep Learning Framework: PyTorch (2016) — Soumith Chintala

Soumith Chintala, from Hyderabad, India, developed PyTorch after studying under Yann LeCun at New York University and joining Facebook AI Research (FAIR). Traditional frameworks like Theano and older TensorFlow versions used a "Define-and-Run" approach, where the computation graph was predefined, making debugging difficult.

PyTorch adopted "Define-by-Run" (dynamic computation graphs), where the graph is built during Python code execution. Automatic differentiation runs with a single line, `loss.backward()`, and standard Python debuggers can be used. This significantly lowered the barrier to implementing deep learning.

## Web App Framework: Streamlit (2019) — Adrien Treuille

Adrien Treuille was an Associate Professor of Computer Science at Carnegie Mellon University. Specializing in crowd simulation and computational design, he encountered challenges with the high barrier to building web applications when demonstrating research results. After working on AR/VR projects at Google, he co-founded Streamlit in 2018 with Thiago Teixeira and Amanda Kelly.

Python scripts can be directly transformed into interactive web applications. No knowledge of HTML/CSS/JavaScript is required. State management is possible with `st.session_state`, and chat UI can be built with `st.chat_message`. Snowflake acquired Streamlit for approximately $800 million in 2022.

## Secure Tunneling: Cloudflare Tunnel (2018) — Matthew Prince

Matthew Prince double-majored at Harvard Law School and Harvard Business School. His experience running "Project Honey Pot," a spam email tracking project during his studies, led him to co-found Cloudflare in 2009 with Michelle Zatlyn and Lee Holloway.

Cloudflare Tunnel (formerly Argo Tunnel, GA in 2018) establishes a tunnel via an outbound connection from your home server to the Cloudflare edge. It eliminates the need for port forwarding, static IPs, and SSL certificate management. DDoS protection and WAF are provided at the Cloudflare edge. By simply installing the `cloudflared` client and running `cloudflared tunnel --url http://localhost:8501`, your local application is exposed to the public.

## LLM Fine-tuning: Unsloth (2023) — Daniel Han & Michael Han

Developed by brothers Daniel Han and Michael Han, based in Australia. Both are University of Sydney alumni and pursued development independently, not affiliated with large corporations. Through kernel fusion (merging multiple operations into a single CUDA kernel) and re-materialization (recomputing intermediate tensors), they reduced VRAM usage by 60-80% and improved training speed by 2-5x.

The VRAM required for full FT of a 7B model decreased from 80GB to 8-16GB. This made local FT practical on GPUs like the RTX 4090 (24GB) and RTX 5090 (32GB).

## Open-Weight LLM: Nemotron (2024) — NVIDIA / Bryan Catanzaro

Developed by Bryan Catanzaro's team, who leads NVIDIA's Applied Deep Learning Research division. Catanzaro studied under Kurt Keutzer at Stanford University and has been involved in accelerating deep learning with GPUs since its early stages.

Nemotron is a family of models focused on synthetic data generation and high-quality alignment, fine-tuning base models like Llama with NVIDIA's proprietary HelpSteer2 dataset and RLHF. Llama-3.1-Nemotron-70B-Instruct achieved a score on the Arena Hard benchmark that surpassed GPT-4o at the time. This is part of NVIDIA's strategy to control all layers of the AI stack, from CUDA to models.

## Python Package Manager: uv (2024) — Charlie Marsh

Charlie Marsh studied Computer Science at Harvard University, worked at Khan Academy and Spring, and then developed the Python linter Ruff. Following Ruff's success, he founded Astral and developed uv. He rewrote Python's pip dependency resolver in Rust, achieving 10-100x speed improvements. Virtual environment creation takes approximately 0.5 seconds (compared to 20-40 seconds for pip).

Additionally, the `uv run` command eliminates the need for explicit virtual environment activation and supports PEP 723 inline metadata. It unifies the complex workflows of poetry/pyenv.

## Technology Stack Overview

OS / Development Environment: Ubuntu (Mark Shuttleworth / Canonical), Cursor (Anysphere)
Package Management: uv (Charlie Marsh / Astral)
Data: SQLite (D. Richard Hipp), JSONL
AI Frameworks: PyTorch (Soumith Chintala / Meta AI), ResNet (Kaiming He), Unsloth (Daniel & Michael Han), Nemotron (Bryan Catanzaro / NVIDIA)
Web / Deployment: Streamlit (Adrien Treuille / Snowflake), Cloudflare Tunnel (Matthew Prince / Cloudflare)
Hardware / Language: NVIDIA RTX 5090 / CUDA (Jensen Huang), Python (Guido van Rossum)
