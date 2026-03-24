---
title: "Building a 5-in-1 Local LLM App with Flutter Web and Flask"
date: 2026-03-21
topics: ["flutter", "python", "ai", "privacy"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-flutter-5in1-app"
devto_url: "https://dev.to/soytuber/building-a-5-in-1-local-llm-app-with-flutter-web-and-flask-57fm"
devto_id: 3380004
---


The idea started simple: build five small apps that demonstrate what a local LLM can do with private data — data you'd never send to a cloud API. A secret diary with sentiment analysis. A password strength checker. A confidential document summarizer.

Someone looked at the prototypes and said: "These ideas are boring."

They were right. Five HTML files hitting a vLLM endpoint with generic prompts isn't exactly groundbreaking. But the criticism led to something much more interesting: what if the "private data" wasn't synthetic — what if it was my own 874MB of Claude Code session history?

## The Pivot: Mining Your Own Development History

Claude Code stores conversation history as JSONL files. Over months of heavy use, mine had grown to 874MB — containing every question I'd asked, every code snippet Claude had generated, every debugging session, every architectural decision.

That's not just chat logs. That's a structured record of how I think, what problems I solve, and how my approach has evolved over time. The five apps became:

1. **Session-to-Blog** — Pick any Claude Code session and generate a polished blog post from the conversation
2. **Project Retrospective** — Analyze all sessions for a project and generate insights about development patterns
3. **Local File Q&A** — Ask questions about any file on your machine, answered by the local LLM with full context
4. **Code Quiz Generator** — Feed in source code, get comprehension quizzes to test your understanding
5. **Git Story Generator** — Transform commit history into a narrative development timeline

## Why Flutter Web Instead of Five HTML Files

The prototypes were each a single HTML file making `fetch()` calls to vLLM's OpenAI-compatible API. That works for demos, but managing five separate files with duplicated CSS, JavaScript, and API logic gets messy fast.

Flutter Web offered a real solution:

- **Single codebase** for all five features, with shared state management
- **Tab-based navigation** that feels like a native app
- **Responsive layout** that works on both desktop and mobile
- **Material Design** out of the box — no CSS wrestling

The architecture ended up clean: Flutter Web for the frontend, Flask for the backend API that reads the JSONL history and coordinates with the local LLM.

## The Sudo Problem (and Why It Matters)

Installing Flutter on Linux typically requires `sudo` for `/usr/local/flutter`. On my development machine, the user account had a numerically complex password, and `sudo` kept failing. This is a small thing, but it's the kind of problem that wastes an hour if you don't know the workaround.

The fix: install Flutter directly to your home directory.

```bash
# Download and extract to home directory
cd ~
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$HOME/flutter/bin:$PATH"

# Verify
flutter doctor
```

No `sudo` needed. Add the PATH export to your `.bashrc` and you're done. Flutter 3.41.2 installed and running in under five minutes.

## The Flask + Flutter Integration

The key architectural decision was serving the Flutter Web build from the Flask server itself. This means a single process serves both the API and the frontend:

```python
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='flutter_build/web')

@app.route('/')
def serve_flutter():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    # Read Claude Code JSONL files
    sessions = parse_jsonl_sessions(HISTORY_DIR)
    return jsonify(sessions)

@app.route('/api/generate', methods=['POST'])
def generate():
    # Forward to local vLLM endpoint
    prompt = build_prompt(request.json)
    response = call_local_llm(prompt)
    return jsonify({"result": response})
```

The build script compiles Flutter to static web assets and copies them into the Flask project:

```bash
cd flutter_app && flutter build web --release
cp -r build/web ../flask_server/flutter_build/web
```

One `python app.py` command and everything runs. No CORS configuration. No separate dev servers. No nginx reverse proxy for development.

## 874MB of History: What Local LLMs Can Do That Cloud Can't

The entire point of this project is that 874MB of personal development history should never leave your machine. Cloud APIs have terms of service, data retention policies, and potential training data usage. A local LLM running on your own hardware has none of these concerns.

With Nemotron 9B running on an RTX 5090, the session-to-blog feature processes a typical 50KB conversation and generates a 1,500-word blog post in about 12 seconds. The project retrospective — which analyzes multiple sessions and cross-references patterns — takes about 45 seconds but produces genuinely insightful output about recurring problems, commonly used patterns, and skill progression over time.

## Lessons Learned

**Start with real data.** The original five apps with synthetic data were forgettable. The moment real personal data entered the picture, the project became genuinely useful.

**Flutter Web is production-ready for internal tools.** The performance is fine for CRUD apps and dashboards. Don't expect 60fps animations, but for a tool that displays text and makes API calls, it's perfectly smooth.

**Serve everything from one process during development.** The Flask-serves-Flutter pattern eliminates an entire class of development headaches. Add nginx or Cloudflare in front for production, but keep development simple.

**Local LLMs need local UIs.** Running a model on your machine but accessing it through a cloud-hosted frontend defeats the purpose. The entire chain — UI, API, model — should run locally for genuine data privacy.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

