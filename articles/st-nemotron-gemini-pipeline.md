---
title: "ローカル×クラウドLLM 2段階パイプライン — Nemotron + Gemini Flash"
emoji: "🔧"
type: "tech"
topics: ["ai", "machinelearning", "llm", "python"]
published: false
canonical_url: "https://media.patentllm.org/blog/ai/nemotron-gemini-pipeline"
---


## なぜ2段階が必要なのか


Nemotron Nano 9B-v2-Japaneseをローカルで動かして記事生成を試みると、思考プロセスが未完了のまま出力される「thinking漏れ」問題が発生することがあります。技術解説記事では、推論過程が途切れると専門的な誤解を招くリスクが高まります。ローカルLLM単体では出力打ち切り問題が避けにくい一方、Nemotronは推論品質が高く無料で利用可能です。出力の整形やファクトチェックにはクラウドLLMの強みが必要であるため、2段階パイプラインを設計しました。


## Stage1: Nemotron（品質重視・無料）


[python]
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tokenizer = AutoTokenizer.from_pretrained(
    "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    trust_remote_code=True
)
model = AutoModelForCausalLM.from_pretrained(
    "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

prompt = """以下の技術トピックについて、専門的な解説を作成してください。
- 一貫性を保ち、技術的正確性を最優先
- 結論は明確に記述

トピック: {user_input}"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=2048)
raw_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
[/python]

このステージでは、RTX 5090の32GB VRAMを活用し、32Kコンテキストで処理します。


## Stage2: Gemini 2.5 Flash（整形＋ファクトチェック）



### 前処理：thinking除去

Nemotron出力の思考過程を削除するため、正規表現を適用します。

[python]
import re

def strip_thinking(text):
    # <think>...</think> ブロックを削除
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # 余分な改行を統合
    return re.sub(r'\n{3,}', '\n\n', cleaned).strip()
[/python]


### Geminiによる整形


[python]
from google import genai

client = genai.Client()

cleaned_text = strip_thinking(raw_text)
gemini_prompt = f"""ローカルLLM生成テキストを以下のルールで高品質化してください。
1. 技術用語は公式定義と一致させる
2. 数値データは出典を明記
3. 事実関係を検証し、誤りがあれば修正する

入力テキスト:
{cleaned_text}"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=gemini_prompt
)
final_text = response.text
[/python]


## バッチ実行


[bash]
#!/bin/bash
# batch_pipeline.sh
python stage1_generator.py --input "$1" --output /tmp/gen1.txt
python stage2_processor.py --input /tmp/gen1.txt --output /tmp/gen2.txt

if diff /tmp/gen1.txt /tmp/gen2.txt > /dev/null; then
    echo "変化なし: スキップ"
else
    echo "整形完了" >> /var/log/pipeline.log
    cp /tmp/gen2.txt "${1}_cleaned.md"
fi
[/bash]


## 出力品質の比較



### 生成前（Nemotron raw）

量子コンピュータは、スーパーポジションを利用して計算を高速化します。この技術は、情報理論の限界を超える可能性があります。


### 整形後（Gemini cleaned）

量子コンピュータは、量子ビット（qubit）のスーパーポジションを活用し、特定の計算問題を従来のコンピュータよりも高速に処理する技術です。Googleは2019年にSycamoreプロセッサで量子超越性を実証しました（Nature, 2019）。ただし、実用的なスケールアップには量子エラー訂正の実装が必須であり、現時点では限定的な応用にとどまっています。


## まとめ


ローカルLLM（Nemotron）の品質とクラウドLLM（Gemini 2.5 Flash）の整形能力を組み合わせることで、以下のメリットを実現しました。
- コスト削減：Nemotronは無料（電気代のみ）、Geminiは低コストで利用可能です
- プライバシー保護：社内データをクラウドに送らずにローカルで処理できます
- 品質向上：ファクトチェックにより技術的正確性が向上します

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。
