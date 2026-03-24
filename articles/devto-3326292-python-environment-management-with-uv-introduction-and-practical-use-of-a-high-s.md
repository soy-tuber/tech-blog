---
title: "Python Environment Management with uv: Introduction and Practical Use of a High-Speed Package Manager Replacing pip/venv"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/uv-python-guide"
devto_url: "https://dev.to/soytuber/python-environment-management-with-uv-introduction-and-practical-use-of-a-high-speed-package-il"
devto_id: 3326292
---

## What is uv?

uv is a Rust-based Python package manager developed by Astral (Charlie Marsh). It integrates the functionalities previously handled by pip, venv, poetry, and pyenv into a single tool, accelerating dependency resolution by 10 to 100 times. Released in 2024, its adoption is rapidly growing.

## Why uv? The Problem with pip

pip's dependency resolution is implemented in Python and can take several minutes for complex projects. Creating a virtual environment also takes 20 to 40 seconds. This waiting time disrupts development flow and concentration.

uv re-implements dependency resolution in Rust, combining parallel downloads and a caching mechanism to achieve the following speeds:

- Package installation: 10 to 100 times faster than pip
- Virtual environment creation: Approximately 0.5 seconds (pip takes 20-40 seconds)
- Lock file generation: Completed in seconds

## Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your shell or update your PATH.

## Basic Usage

### Project Initialization

```bash
uv init my-project
cd my-project
```

A pyproject.toml file will be generated. Dependencies are declared here.

### Adding Packages

```bash
uv add requests
uv add torch --index-url https://download.pytorch.org/whl/cu131
```

A uv.lock file is automatically generated, ensuring a reproducible environment.

### Running Scripts

```bash
uv run python main.py
```

There's no need to activate the virtual environment. `uv run` automatically creates and uses a .venv.

## PEP 723: Inline Script Metadata

You can declare dependencies directly within a single script without a pyproject.toml file.

```bash
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "beautifulsoup4"]
# ///

import requests
from bs4 import BeautifulSoup

resp = requests.get("https://example.com")
soup = BeautifulSoup(resp.text, "html.parser")
print(soup.title.string)
```

To execute:

```bash
uv run scrape.py
```

Dependencies are automatically installed and the script is executed. No venv creation or activation is required. This is ideal for disposable scripts.

## Python Version Management (pyenv Alternative)

```bash
# Install Python 3.12
uv python install 3.12

# Run with a specific version
uv run --python 3.12 python main.py

# Pin the project's Python version
uv python pin 3.12
```

Instead of switching Python versions system-wide like pyenv, uv manages versions on a per-project basis.

## pip Compatibility Mode

uv can also be used with projects that have existing requirements.txt files.

```bash
uv pip install -r requirements.txt
uv pip install torch
uv pip freeze
```

It uses the same command structure as pip, but with improved speed. The migration cost is virtually zero.

## Practical Example: AI Development in an RTX 5090 Environment

Here's an example of setting up PyTorch with CUDA 13.1 support using uv:

```bash
uv init ai-project
cd ai-project
uv add torch --index-url https://download.pytorch.org/whl/cu131
uv add unsloth transformers datasets
uv run python -c "import torch; print(torch.cuda.get_device_name(0))"
```

Tasks that used to take several minutes with traditional pip + venv can now be completed in tens of seconds.

## Summary

What uv replaces:

- pip → `uv add` / `uv pip install` (10-100x faster)
- venv → `uv run` (automatic management, no activation needed)
- poetry → `uv init` + uv.lock (reproducibility with lock files)
- pyenv → `uv python install` / `pin` (Python version management)

A single tool now completes the management of your Python development environment. Especially in AI development, where heavy packages related to PyTorch and CUDA are frequently installed, the speed benefits are significant.
