---
title: "Training a Shogi Engine: ONNX Conversion, TensorRT, and Getting Crushed by Ryfamate"
date: 2026-03-21
topics: ["ai", "machinelearning", "python", "gamedev"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-shogi-onnx-tuning"
devto_url: "https://dev.to/soytuber/training-a-shogi-engine-onnx-conversion-tensorrt-and-getting-crushed-by-ryfamate-111d"
devto_id: 3380028
---


Shogi — Japanese chess — has a thriving computer engine scene that most Western developers have never encountered. While the chess world has Stockfish and Leela Chess Zero, the shogi world has its own ecosystem of neural network engines, and the engineering challenges are fascinating.

This is the story of converting a 20-billion-parameter shogi model from PyTorch to ONNX, optimizing it for TensorRT inference, and discovering that model size means nothing if your search parameters are wrong.

## Shogi AI: Context for Chess Developers

If you know Stockfish or Leela Chess Zero, shogi engines will feel familiar with important differences:

- **Shogi has a much larger game tree** than chess. Captured pieces can be dropped back onto the board, which means the branching factor is roughly 80 (vs. chess's ~35). This makes brute-force search much harder.
- **dlshogi** is the shogi equivalent of Leela Chess Zero — a neural network engine that uses Monte Carlo Tree Search (MCTS) to evaluate positions. It's been competitive with or superior to traditional alpha-beta engines.
- **The model architecture** is a ResNet (typically 10-20 blocks) that outputs both a policy (move probabilities) and a value (position evaluation). Sound familiar? It's essentially the same dual-headed architecture Leela uses.
- **Floodgate** is a continuous online tournament where shogi engines play each other 24/7. Think of it as the TCEC of shogi, but with faster time controls and more participants.

The model I was working with — `checkpoint_20b_e2_p33.pth` — is a 20-block, 256-channel ResNet with Swish activation, trained through 2 epochs on professional shogi game records. "20b" in the shogi community means 20 blocks, not 20 billion parameters (the actual parameter count is around 87 million).

## Step 1: PyTorch to ONNX (The Path Through .npz)

The USI (Universal Shogi Interface) protocol expects engines to load ONNX models. But the training checkpoint is a PyTorch `.pth` file. The conversion pipeline goes:

`.pth` -> `.npz` -> `.onnx`

The `.npz` intermediate step exists because dlshogi's ONNX exporter expects the NumPy serialization format:

```python
import torch
from dlshogi.network.policy_value_network import policy_value_network
from dlshogi import serializers

model = policy_value_network("resnet20x256_swish")
checkpoint = torch.load("checkpoint_20b_e2_p33.pth", map_location="cpu")
model.load_state_dict(checkpoint['model'])
serializers.save_npz("model_20b_e2_p33.npz", model)
```

The `map_location="cpu"` flag is critical — without it, the loader tries to map the checkpoint to whatever GPU was used during training, which fails if you're on a different machine.

## Step 2: ONNX Export with TensorRT Compatibility

The ONNX export has two critical flags:

```bash
python convert_model_to_onnx.py \
    --npz model_20b_e2_p33.npz \
    --onnx model_20b.onnx \
    --dynamic-batch \
    --gpu 0
```

**Dynamic batch** allows TensorRT to optimize for variable batch sizes during MCTS. Without it, you're locked to a fixed batch size, which either wastes GPU cycles (batch too large) or limits search parallelism (batch too small).

**The Swish problem.** The model uses Swish activation (`x * sigmoid(x)`), but TensorRT doesn't natively support Swish as a single operation. The fix: call `set_swish(False)` before export to decompose Swish into its constituent operations (multiply + sigmoid), which TensorRT handles fine.

The exported model is split into `model_20b.onnx` (316KB of graph structure) and `model_20b.onnx.data` (93MB of weights).

## Step 3: The First Win (and False Confidence)

Testing against Tanuki (a moderate-strength engine), the converted model won convincingly:

- **197 moves, dlshogi wins as first player (sente)**
- Evaluation climbed steadily from +110 in the opening to +30,000 in the endgame
- Clean tactical execution in the middle game

This felt great. The model works, the conversion was successful, TensorRT is fast. Time to test against something stronger.

## Step 4: Getting Destroyed by Ryfamate

Ryfamate is a top-tier shogi engine based on the same dlshogi architecture but with careful parameter tuning. The result: **0-2, and it wasn't close.**

- Game 1: Ryfamate dominated from move 30 onward
- Game 2: Even after copying Ryfamate's opening book, my engine lost control of the middle game

What went wrong? The model weights were fine. The difference was entirely in the **MCTS search parameters**.

## The MCTS Parameter Gap

Two parameters made all the difference:

| Parameter | My Engine | Ryfamate |
|-----------|----------|----------|
| C_init (exploration constant) | 100 | 127 |
| Softmax_Temperature | 100 | 156 |

**C_init** controls the exploration-exploitation tradeoff in MCTS. Higher values make the engine explore more diverse moves before committing. At 100, my engine was settling on moves too quickly — missing better alternatives that required looking at less obvious candidates.

**Softmax_Temperature** controls how "sharp" the policy network's move probabilities are. A temperature of 100 produces a peaked distribution (the engine strongly prefers its top choice). At 156, Ryfamate's distribution is flatter — it considers a wider range of moves, which is crucial in complex middle-game positions where the "obvious" move isn't always the best one.

I copied Ryfamate's parameters exactly and ran 10 games. Result: **Ryfamate 10, my engine 0.** Complete shutout.

## The Lesson: Parameters > Model Size

This was humbling. The same architecture, similar training data, identical inference hardware — and Ryfamate wins 100% of the time. The difference is years of parameter tuning, opening book refinement, and endgame optimization that go beyond what a single training run can capture.

In the chess engine world, this is well-known. Stockfish developers spend enormous effort tuning search parameters through automated SPRT testing (Sequential Probability Ratio Test) — playing thousands of games to determine whether a parameter change of 0.01 actually improves play. The shogi community does the same thing, and Ryfamate represents thousands of hours of this kind of systematic optimization.

**The takeaway for ML practitioners:** model architecture and training are necessary but not sufficient. The deployment-time parameters — inference configuration, search settings, post-processing — can dominate the final performance. A perfectly trained model with wrong inference settings will lose to a mediocre model with carefully tuned parameters.

## What's Next

The path forward is clear:

1. **Automated parameter search**: Instead of manually tweaking C_init and temperature, run a systematic search using Optuna or similar — playing hundreds of games per configuration
2. **Opening book integration**: Strong engines don't search from move 1. They use pre-computed opening books for the first 20-30 moves
3. **Endgame tablebases**: Pre-computed perfect play for simple endgame positions (like chess endgame tablebases, but for shogi's unique drop mechanics)

The 0-10 scoreline against Ryfamate isn't a failure — it's a benchmark. Now I know exactly what to optimize.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

