---
title: "LoRA and FT Are Unnecessary: How to Approach Distilled Models"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/why-unsloth-unnecessary"
devto_url: "https://dev.to/soytuber/lora-and-ft-are-unnecessary-how-to-approach-distilled-models-92j"
devto_id: 3326326
---

## Introduction

Fine-tuning (FT) a distilled model is either ineffective or leads to overfitting. What LoRA aims to achieve can be accomplished with prompts.

## Fine-tuning a Distilled Model is Pointless

Distillation is the process of condensing the knowledge of a large teacher model into a smaller model. To use a soy sauce brewing analogy, it's the finished product created through ingredient selection, koji mold cultivation, and fermentation management.

Attempting to add flavor to this finished product afterward will not work well.

### Pattern 1: No Change
If the learning rate is set conservatively, the model's output will barely change. The weights, already optimized through distillation, are dominant, and the impact of additional training is absorbed.

### Pattern 2: Overfitting
If the learning rate is increased or the number of epochs is extended, the model will respond perfectly to the training data, but its generalization performance for unknown inputs will significantly decrease. It will merely memorize the training data.

### Pattern 3: Performance Degradation
The general capabilities acquired through distillation are overwritten, leading to an overall performance drop compared to the original model. In LLMs, the naturalness of Japanese might be lost.

In any of these patterns, the conclusion is that the model before FT is the most practical. If you want to change the flavor, you have no choice but to restart from the ingredients and methods used before distillation.

## LoRA Can Be Replaced by Prompts

The reason LoRA is unnecessary is separate from distillation. Simply put, current LLMs are sophisticated enough to be sufficiently controlled by prompts.

Taking Nemotron-Nano-9B-v2-Japanese as an example, all the following tasks can be accomplished solely by prompt specification:

*   Summarizing judicial documents and extracting key issues
*   Structuring patent specifications
*   Batch generation of blog posts
*   Generating code documentation
*   Data classification and labeling

You define the role and constraints with a System Prompt, demonstrate the output format with Few-shot examples, and control the reasoning process with Chain-of-Thought. You can control the model's behavior solely through the inference-time context, without modifying any of its weights.

Most of what LoRA attempts to do can be written in a prompt. Current LLMs are intelligent enough for that.

## Don't Modify the Model, Design Its Surroundings

What should be done with a distilled model is not to modify the model itself, but to design its surroundings.

There's no need to drink soy sauce as is; you can make dashi-shoyu (seasoned soy sauce).

*   Inject external knowledge with RAG
*   Build pre-processing and post-processing into a pipeline
*   Integrate with external tools using an MCP server
*   Stream data as a batch processing engine

These are all architectural tasks and do not involve touching the model's weights at all. While leveraging the capabilities perfected through distillation, you create "dashi-shoyu" tailored to your specific use case.

## Summary

Fine-tuning a distilled model is either meaningless or harmful. LoRA can be replaced by prompts. Architecture is what brings a model to life.

## Addendum: Insights from Shogi AI Distillation Experiments

The ideas in this article are based on experiences gained with Shogi AI. We confirmed that fine-tuning a distilled model is either ineffective or leads to overfitting.
