---
title: "Claude Code Practical Guide: Debugging, Test Automation, and CUDA Environment Setup with Opus 4.6"
date: 2026-03-14
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/claude-code-guide"
devto_url: "https://dev.to/soytuber/claude-code-practical-guide-debugging-test-automation-and-cuda-environment-setup-with-opus-46-na6"
devto_id: 3349946
---

## Introduction

Claude Code is a CLI (Command Line Interface) tool provided by Anthropic that allows you to directly invoke Claude Opus 4.6 from your terminal to perform coding, debugging, and environment setup. Its distinct feature is that it is editor-independent and can be directly integrated into your existing workflows.

In this article, we explain the following practical use cases using Claude Code:

- Project control via CLAUDE.md for cost and quality management
- A debugging case study of a Flask app
- Automatic generation of pytest test code
- Assistance in setting up an RTX 5090 + CUDA 13.1 environment
- CI/CD automation with GitHub Actions

## Chapter 1: Project Control with CLAUDE.md

Claude Code automatically reads `CLAUDE.md` in the project root to control the AI's behavior. This eliminates the need to provide instructions in every prompt, allowing you to obtain consistent outputs across the entire team.

Example of CLAUDE.md:

```bash
# CLAUDE.md
- Reply in Japanese
- Always include Python type hints in code
- Keep explanations brief. Minimize output other than code
- Use pytest for testing
- Do not invent option names by guessing. Ask for clarification if unsure
```

This suppresses redundant explanations and unnecessary decorations, allowing you to get practical outputs while reducing token consumption.

## Chapter 2: Debugging Case Study — Flask App ValueError

### Situation

A 500 error occurred during a specific request at the `update_user` endpoint of the user management API. The log records: `ValueError: invalid literal for int() with base 10: 'one'`.

Code containing the bug:

```bash
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    for key, value in data.items():
        if key == 'id':
            _ = int(value)  # Crashes if "id": "one" arrives in the request body
            continue
        # ...
```

### Resolution with Claude Code

Pass the error log and code to Claude Code:

```bash
claude "This Flask code throws a ValueError. Log: ValueError: invalid literal for int() with base 10: 'one'. Fix the update_user function in app.py"
```

Claude Code's observation: It runs `int()` against the `id` field in the request body, but the body's id is not needed for the update process. Only the URL parameter `user_id` should be used.

After the fix:

```bash
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400

    set_clauses = []
    values = []
    for key, value in data.items():
        if key in ('id',):
            continue  # Ignore id in the body
        if key not in ('username', 'email'):
            continue
        set_clauses.append(f"{key} = ?")
        values.append(value)
    # ... DB update processing
```

## Chapter 3: Automatic Test Code Generation

### Basic Test Generation

Target code (calculator.py):

```bash
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
```

Instruction to Claude Code:

```bash
claude "Generate a pytest test for the divide function in calculator.py. Ensure you cover the normal case and the abnormal zero-division case"
```

Generated test:

```bash
import pytest
from calculator import divide

def test_divide_success():
    assert divide(10, 2) == 5.0
    assert divide(5, 2) == 2.5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        divide(10, 0)

@pytest.mark.parametrize("a, b, expected", [
    (10, 2, 5.0), (-10, 2, -5.0), (0, 5, 0.0), (1, 3, 0.333333),
])
def test_divide_parametrized(a, b, expected):
    assert divide(a, b) == pytest.approx(expected)
```

### Mocking External Dependencies

For testing functions that call APIs, you can also generate mock code using unittest.mock:

```bash
claude "Create a test for the fetch_user_data function. Mock requests and cover the success and 404 cases"
```

## Chapter 4: RTX 5090 + CUDA 13.1 Environment Setup

The most common pitfall when setting up a GPU environment is version consistency among the driver, CUDA, and PyTorch. Pass error messages to Claude Code to identify causes and apply fixes.

### CUDA Environment Setup on WSL2

In WSL2, you do not install NVIDIA drivers on the Linux side. Windows-side drivers are automatically mounted. Only the CUDA Toolkit is installed.

```bash
# Remove existing NVIDIA packages
sudo apt purge -y '^nvidia-.*'
sudo apt autoremove -y

# Install CUDA Toolkit 13.1
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-13-1
```

### PyTorch Installation and Operation Check

Follow the installation guide on the official PyTorch website (pytorch.org) to install it using the method that matches your CUDA version.

Verification script:

```bash
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    cap = torch.cuda.get_device_capability(0)
    print(f"Compute Capability: sm_{cap[0]}{cap[1]}0")
```

For an RTX 5090, it will display approximately 32GB and sm_120. If an error occurs, you can pass it straight to Claude Code to identify the cause.

## Chapter 5: CI/CD Automation

### CI Workflow via GitHub Actions

```bash
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt
    - run: pytest --tb=short
```

### CD Workflow to EC2

```bash
# .github/workflows/cd.yml
name: CD
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy via SSH
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ${{ secrets.EC2_USER }}
        key: ${{ secrets.AWS_SSH_PRIVATE_KEY }}
        script: |
          cd /home/ec2-user/app
          git pull origin main
          pip install -r requirements.txt
          pm2 restart app || pm2 start app.py --name app --interpreter python3
```

## Conclusion

Key points for utilizing Claude Code + Opus 4.6:

- Define project rules with CLAUDE.md to control output quality and cost
- Accelerate debugging by passing error logs + code together
- Automate test code generation, covering parametrized tests and mocks
- Resolve CUDA/PyTorch version mismatches by passing error messages as they are
- Reduce manual labor by generating boilerplates for CI/CD workflows

Because it is an editor-independent CLI tool, you can use the same workflow in any scenario, such as on SSH-connected servers or CI environments.
