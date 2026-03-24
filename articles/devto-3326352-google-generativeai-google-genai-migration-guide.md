---
title: "google-generativeai google-genai Migration Guide"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/google-genai-sdk-migration"
devto_url: "https://dev.to/soytuber/google-generativeai-google-genai-migration-guide-29gl"
devto_id: 3326352
---

## What Happened

The `google.generativeai` package has been deprecated. Migration to the new `google-genai` SDK is recommended. Developers should migrate as soon as possible.

## Features of the New `google-genai` SDK

- Integrated interface with Gemini 2.5 Pro/Flash models
- Support for context caching
- Automatic loading of authentication via the `GOOGLE_GENAI_API_KEY` environment variable

## Specific Migration Steps

### Environment Setup

```bash
pip install --upgrade google-genai
```

### Changing Imports

```python
# Old Code (Deprecated)
import google.generativeai as genai
genai.configure(api_key="your-key")

# New Code
from google import genai
client = genai.Client()  # Automatically loads GOOGLE_GENAI_API_KEY
```

### Rewriting `generate_content`

```python
# Old Code
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Hello")

# New Code
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Hello",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=2048
    )
)
```

## Migration Example for an Existing Project

```python
# Old Code (hanrei-db.py)
import google.generativeai as genai
model = genai.GenerativeModel(model_name="gemini-2.5-pro")
response = model.generate_content("この判例を要約してください")

# New Code (After Migration)
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="この判例を要約してください",
    config=types.GenerateContentConfig(temperature=0.1)
)
```

## `GenerateContentConfig` Parameters

- `temperature`: Controls the randomness of generation (low temperature is recommended for fact-checking)
- `max_output_tokens`: Specifies the maximum number of output tokens
- `top_k` / `top_p`: Used for sampling control

Note: The class name differs from the old SDK's `GenerationConfig`. `frequency_penalty` and `presence_penalty` are not directly supported in the `google-genai` SDK.

## What Happens if `FutureWarning` is Ignored

1. Initial Stage: `FutureWarning` will occur frequently, but operation will continue.
2. Intermediate Stage: Execution of deprecated modules may become unstable.
3. Final Stage: There is a risk of becoming inoperable after support ends.

Early migration is recommended.

## Summary

- Change `import` to `from google import genai` and initialize with `Client()`.
- Pass `GenerateContentConfig` via the `config` argument in `generate_content`.
- Authentication can be simplified by setting the `GOOGLE_GENAI_API_KEY` environment variable.
- After confirming operation in a test environment, proceed with migration to the production environment.
