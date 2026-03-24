---
title: "Building a 5-in-1 App with Local LLM and Flutter"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/flutter-local-llm"
devto_url: "https://dev.to/soytuber/building-a-5-in-1-app-with-local-llm-and-flutter-3jkn"
devto_id: 3326328
---

## Introduction

"I want to leverage AI without sending data to the cloud." The biggest strength of local LLMs is their ability to process local data without exposing it externally.

I ran Nemotron using vLLM on a Desktop PC (RTX 5090) and integrated five functions into a single app with Flutter Web.

## Shift in Development Policy

### Initial Idea: General-Purpose AI Tools

Initially, I planned to create five general-purpose tools, such as a secret diary AI and a password strength checker. However, the "unique value of local LLMs" felt diluted.

### Shift: Leveraging My Own Development Data

I focused on my local Claude Code session history data. I switched to a concept where an LLM analyzes my development history.

## Five Functions

1.  Claude Code → Blog Post: Automatically generate technical articles from session history.
2.  Project Retrospective AI: Cross-analyze all sessions for a retrospective.
3.  Local File Q&A: Safely ask questions about confidential files.
4.  Code → Quiz Generation: Generate comprehension tests from source code.
5.  Git → Development Story: Convert commit history into a narrative format.

## Technical Configuration

### Architecture

*   Desktop PC (RTX 5090): Runs Nemotron with vLLM, providing an OpenAI-compatible API.
*   Flask API Server: Handles data preprocessing and LLM calls.
*   Flutter Web Frontend: Integrates the five functions with tab switching.

The Chromebook serves as an always-on server for various services, while the Desktop PC is dedicated to GPU inference. Internal connections are established via Tailscale VPN.

### Flask + Flutter Integration

```bash
# Flaskサーバー（app.py）
from flask import Flask, jsonify, request
import requests

app = Flask(__name__, static_folder='flutter_build/web')

VLLM_URL = 'http://xxx.xxx.xx.xx:8000/v1/chat/completions'

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    # vLLMのOpenAI互換APIにリクエスト（Tailscale経由）
    response = requests.post(VLLM_URL, json={
        'model': 'nvidia/Nemotron-Mini-4B-Instruct',
        'messages': [{'role': 'user', 'content': data['prompt']}]
    })
    return jsonify(response.json())
```

### Flutter Web Build and Deployment

```bash
# Flutter Webビルド
cd flutter_app
flutter build web

# ビルド成果物をFlaskの静的ファイルディレクトリにコピー
cp -r build/web ../flutter_build/web
```

Since Flask serves the built Flutter Web files, everything runs on a single server.

## Key Points: Practicality of Local LLMs

*   Unlike cloud APIs, no data leaves your environment.
*   vLLM's OpenAI-compatible API allows model switching without code changes.
*   Flutter's responsive UI enables usage on both PCs and smartphones.

## Conclusion

The combination of local LLMs and Flutter is a practical option for building AI applications under the constraint of "keeping data local." The integration of Flask + Flutter Web allows for a complete backend and frontend solution on a single server.
