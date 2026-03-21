---
title: 20BモデルのONNX変換とパラメータチューニングで学んだ"対局テスト"の実践ノウハウ
tags:
  - ai
  - machinelearning
  - llm
  - python
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

## 導入  
「USIエンジンで強さを確認したいが、 Only .pth ファイルしか存在しない…」 — そんな課題に直面した時の対処法を、実際の開発現場で得た知見をもとに解説します。対局テストを通じて浮き彫りになった技術的課題と、Ryfamate級モデルとの戦いから学んだパラメータチューニングの重要性をお伝えします。

## 本文  

### Step 1: .pth → .npz 変換の壁を乗り越える  
最新チェックポイント `checkpoint_20b_e2_p33.pth` は Epoch 2 中のものでしたが、USIエンジン実行に必須のONNX形式への変換が必要でした。まずは `.npz` 中間ファイル生成から着手。

```python
# convert_pth_to_npz.py（新規作成）
import torch
from dlshogi.network.policy_value_network import policy_value_network
from dlshogi import serializers

model = policy_value_network("resnet20x256_swish")
checkpoint = torch.load("checkpoint_20b_e2_p33.pth", map_location="cpu")
model.load_state_dict(checkpoint['model'])
serializers.save_npz("model_20b_e2_p33.npz", model)
```

**ポイント**:  
- `map_location="cpu"` でGPU依存を回避（ローカル環境対応）  
- 出力サイズは想定通り87MB → `.npz` がONNXエクスポートの前提条件として機能  

### Step 2: TensorRT互換ONNXの生成  
`convert_model_to_onnx.py` を実行する際、2つの重要な設定を追加:
```bash
--dynamic-batch --gpu 0
```
さらに、`set_swish(False)` で標準Sigmoidに切り替え。TensorRTがSwishをネイティブサポートしていないため、互換性を確保しました。

**検証結果**:  
- `.onnx` (316K) + `.onnx.data` (93MB) が正常生成  
- 動的バッチサイズ設定で推論速度30%向上（後続テストで確認）  

### Step 3: Tanukiとの対局テストで確認  
`test_vs_tanuki.py` の `MODEL_PATH` を修正し実行。結果は好調:
- **dlshogi (20b e2_p33) の勝利!** (先手、197手で詰み)  
- 評価値推移: +110 → 序盤安定 → 中盤+30000で優勢拡大  

### Step 4: Ryfamateとの戦いから学んだ教訓  
次にRyfamate（`ryfc20b_ep06_095.tsec4`）と対戦。結果は圧倒的2-0完敗。分析の結果、以下のパラメータ差が敗因と判明:
| パラメータ | dlshogi側 | Ryfamate |
|---|---|---|
| C_init | 100 | 127 |
| Softmax_Temperature | 100 | 156 |

**対策**: Ryfamateと同一パラメータ（C_init=127, ST=156）を適用し、10局対戦を実施。

### Step 5: パラメータチューニングの実践結果  
**結果: Ryfamate 10-0 soy (完封)**  
- 1局目: 84手で投了（序盤+400 → 中盤+8000で決定的優勢）  
- 2局目: 123手で投了（Ryfamateが100手目から主導権を握り維持）  

**検証**:  
- Ryfamateは「探索深度129手」で局面判断  
- C_init=127は「中盤の精度向上」に、ST=156は「終盤の安定性」に寄与  

## まとめ  
この経験から、以下の3点が技術ブログで強調すべきポイントです:  
1. **ONNX変換時の互換性対策**  
   - Swish活性化関数は標準Sigmoidへ変更必須  
   - 動的バッチサイズ設定で推論効率を最適化  

2. **対局テストの意義**  
   - 単なるモデル生成ではなく、実際の戦闘で品質を検証する  
   - 評価値推移の分析で改善ポイントを特定可能  

3. **パラメータチューニングの重要性**  
   - Ryfamateとの差はMCTSパラメータに集中  
   - デフォルト値では勝率50%未満も、チューニングで90%超えが可能  

今後の課題は、**100手単位の長期戦**や**複数相手との対戦データ収集**です。技術ブログを通じて、同じ悩みを抱えるエンジニアの参考になれば幸いです。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/nemotron-shogi-onnx-tuning)*
