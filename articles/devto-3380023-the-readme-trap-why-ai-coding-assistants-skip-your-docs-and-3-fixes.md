---
title: "The README Trap: Why AI Coding Assistants Skip Your Docs (and 3 Fixes)"
date: 2026-03-21
topics: ["ai", "documentation", "productivity", "devops"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-readme-trap"
devto_url: "https://dev.to/soytuber/the-readme-trap-why-ai-coding-assistants-skip-your-docs-and-3-fixes-4o7e"
devto_id: 3380023
---


Here's a pattern that will sound familiar: you carefully write a README with architecture decisions, API conventions, and setup instructions. Then you ask your AI coding assistant to implement a feature. It generates code that contradicts half the decisions in your README because it never read the file.

This isn't a Claude Code bug. It's a workflow design problem. And once you understand why it happens, the fixes are straightforward.

## Why the README Gets Skipped

AI coding assistants operate on context. They see your current conversation, the files you've explicitly opened or referenced, and whatever system instructions are configured. They don't proactively scan your entire repository on every prompt.

This is actually reasonable behavior — reading every file in a large repo before answering "fix this typo" would be wasteful. But it means architectural documents, style guides, and READMEs only get read when explicitly referenced.

The result: you end up with code that works but violates conventions documented three directories up in a README nobody asked the AI to read.

## Fix 1: CLAUDE.md Rules (The 60-Second Solution)

Claude Code reads `CLAUDE.md` at the start of every session. It's the single highest-leverage file in your project for shaping AI behavior:

```markdown
# Project Rules

- Read README.md before implementing any new feature or modifying existing code
- If README.md conflicts with existing code, flag the conflict before proceeding
- After completing changes, verify they are consistent with README.md
```

That's it. Three lines. Claude will now read your README before making significant changes. It won't do it unprompted for every minor question, but for implementation tasks, it consistently follows this instruction.

**Limitation**: This assumes your README is accurate and up-to-date. If it's stale, Claude might implement outdated patterns.

## Fix 2: Freshness-Checking Hook (The Robust Solution)

The stale-README problem is real. I've worked on projects where the README described an architecture that was refactored two years ago. Having an AI diligently follow those outdated instructions is worse than not reading the README at all.

Claude Code supports hooks — scripts that run before your prompt is processed. Here's a hook that checks README freshness:

```bash
#!/bin/bash
# .claude/hooks/check-readme.sh

if [ -f README.md ]; then
    mod_date=$(git log -1 --format="%ci" -- README.md 2>/dev/null)
    days_old=$(( ($(date +%s) - $(git log -1 --format="%ct" -- README.md 2>/dev/null)) / 86400 ))

    if [ "$days_old" -gt 180 ]; then
        echo "WARNING: README.md was last updated ${days_old} days ago (${mod_date%% *})."
        echo "Treat it as potentially outdated. Verify against actual code before following."
    elif [ "$days_old" -gt 30 ]; then
        echo "README.md last updated ${days_old} days ago. Read before implementing."
    else
        echo "README.md is current (updated ${days_old} days ago). Read before implementing."
    fi
fi
```

This gives Claude calibrated instructions:
- **Fresh README** (under 30 days): "Read and follow it"
- **Aging README** (30-180 days): "Read but verify"
- **Stale README** (180+ days): "Treat as potentially outdated"

In practice, this reduced "implemented the wrong pattern" incidents by about 30% on projects with older documentation.

## Fix 3: CLAUDE.md + README as a Living System

The most effective approach combines both: CLAUDE.md contains *rules* (always read X, never do Y), while README.md contains *context* (architecture, conventions, setup).

```markdown
# CLAUDE.md

## Before Starting Any Task
1. Read README.md for project architecture and conventions
2. Check CHANGELOG.md for recent breaking changes
3. If modifying an API endpoint, read the OpenAPI spec in docs/api.yaml

## Code Standards
- Python: Follow ruff configuration in pyproject.toml
- SQL: Use parameterized queries only, never string formatting
- Tests: Every new function needs at least one test
```

The README stays focused on what it does best — documenting the project for humans — while CLAUDE.md translates those conventions into actionable AI instructions.

## The Meta-Lesson: Documentation as Infrastructure

The README trap reveals something important about working with AI coding assistants: **documentation is no longer optional infrastructure — it's executable configuration.**

When a human joins your team, they might skim the README, ask colleagues questions, and gradually absorb conventions through code review. An AI assistant has none of those informal channels. It follows what it's explicitly told to read and ignores everything else.

This actually makes documentation *more* valuable, not less. A well-maintained README + CLAUDE.md combination means every AI-assisted change respects your project's conventions. A neglected README means the AI makes reasonable but inconsistent choices — exactly the kind of subtle inconsistency that's hard to catch in code review.

The teams I've seen get the most from AI coding assistants are the ones that treat their documentation like code: versioned, reviewed, and kept ruthlessly up to date. The README trap isn't about AI being dumb. It's about documentation finally having consequences.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

