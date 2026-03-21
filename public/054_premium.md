---
title: ローカルLLMのためのハードウェア選定：VRAMの壁を越えるGPU・CPU・メモリ構成の実践
tags:
  - gpu
  - nvidia
  - deeplearning
  - vllm
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

■はじめに：Gemini Flash相当をローカルで？遅すぎる開発環境がもたらした絶望

もしあなたが、私と同じようにGoogle Gemini 2.5 Flashの爆速レスポンスに感動し、「これを自分の手元で、プライバシーを気にせず、思う存分動かせたら」と夢見ているなら、この記事はあなたのためのものです。私は弁護士・監査役として、日々膨大なXBRLデータやPDF資料を解析し、それを基に自己進化型AIを構築するというヘビーなプロジェクトを進めています。ゴールは明確です。Gemini 2.5 Flashを凌駕する、いや、少なくとも同等以上の推論能力と速度を持つローカルLLMシステムを構築し、司法試験の択一式で8割、論文で事案処理が完璧にできるレベルにまでAIを引き上げることです。

しかし、現実は厳しいものでした。私の手元にあるPCは、購入当初は「高性能」と信じていたASUSのゲーミングPC。RTX 5070 Tiを搭載し、VRAMは8GBでした。これなら32Bクラスのモデルも動かせるだろうと意気揚々とローカルLLMのセットアップを始めたのですが、結果は惨敗でした。「遅すぎる」。これが正直な感想です。小さな7Bモデルならまだしも、Gemini Flash相当の「賢さ」を求めて32Bクラスのモデルを動かそうとすると、推論速度はまるで亀のようでした。

メインメモリにVRAMが溢れ、トークン生成に数分を要することもしばしばありました。まるでWebサイトの読み込みで砂時計が延々と回り続けるような、あの絶望的な待ち時間が、私の開発意欲を削り取りました。「こんなことでは、司法試験システム構築なんて夢のまた夢だ」「このままでは、AIに仕事を任せるどころか、AIに足を引っ張られることになる」。まるで「賢さ」の壁にぶち当たったかのような停滞感に襲われ、正直、もう諦めかけていました。

しかし、ある日、Geminiとの対話を通じて、私はその絶望的な状況から抜け出すための光明を見つけます。それは、「VRAMの多さは正義」という、ローカルLLMの世界における絶対的な真理でした。この記事では、私が体験した3つの具体的な「罠」から、いかにして「RTX 5090 + 32GB VRAM」という最終結論に至ったのか、そしてその最強の構成でGemini Flash相当のローカルLLM環境を「5分で再現する」具体的な手順まで、中級エンジニア向けに技術的な深掘りを交えて包み隠さずお伝えします。

▼本記事で得られること
- ローカルLLM環境構築における「VRAMの壁」とメモリ帯域幅の重要性
- プロ用GPUとコンシューマー用GPU、どちらがローカルLLMに適しているかの技術的真実
- 最強のローカルLLM環境を構築するためのPCパーツ選定の鉄則
- RTX 5090環境でGemini Flash相当のモデルを動かすための具体的なPythonコードとセットアップ手順
- 開発効率を劇的に向上させるためのライブラリ選定（vLLM, bitsandbytes）

もう、遅すぎる推論速度に悩む必要はありません。あなたのローカルLLM環境も、今日から爆速の「知のラボ」に生まれ変わります。

■私がハマった遅延と後悔

私のプロジェクト目標は、Gemini 2.5 Flashのような「賢さ」を持つモデルをローカルで動かすことでした。そのためには、最低でも32B（320億パラメータ）クラスのモデルが必要だと考えていました。しかし、当時私が使っていたRTX 5070 Ti（VRAM 16GB）では、この目標は物理的に不可能でした。

RTX 5070 Ti (VRAM 16GB) での悲劇
7Bモデルであれば何とか動くものの、少し複雑な質問や長文生成では体感で数秒から数十秒の待ち時間が発生しました。目標とする32Bクラスのモデル（例えばDeepSeek-R1-Distill-Qwen-32B）を動かそうとすると、VRAMに収まりきらず、モデルの一部がメインメモリ（システムRAM）にオフロードされてしまいます。

その結果、「推論速度が体感で10倍以上遅くなる」という事態に直面しました。これはGPUとCPU間のデータ転送速度（PCIeバス帯域）が、GPU内部のメモリ帯域に比べて圧倒的に遅いために起こる現象です。GPU内部のメモリ帯域が数百GB/sから1TB/sオーダーであるのに対し、PCIe Gen4 x16でも最大64GB/s程度に過ぎません。レイヤーごとにデータを往復させるオーバーヘッドは致命的で、質問を投げかけてから数分経ってようやく回答が返ってくるような状況では、思考のサイクルが完全に途切れてしまいます。

■決定的だった解決策：VRAM 32GB、RTX 5090こそが「知の解放」への鍵

これまでの失敗と試行錯誤を経て、私は一つの明確な結論にたどり着きました。それは、「VRAMの多さは正義」、そして「Gemini 2.5 Flash相当の性能をローカルで求めるなら、RTX 5090 (32GB VRAM) 以外に選択肢はない」というものです。

▼「VRAMの壁」の突破：32BモデルをGPUに丸ごとロードする快感

私が経験した最大のボトルネックは、32BモデルがVRAMに収まらず、メインメモリに溢れてしまうことでした。この問題を根本から解決するためには、32BモデルがVRAMに丸ごと収まるだけの容量が絶対条件でした。RTX 5090の32GB VRAMは、まさにこの「VRAMの壁」を突破するための決定的な解決策でした。

32BパラメータのモデルをFP16（16bit浮動小数点）でロードする場合、単純計算で約64GBのVRAMが必要です。これではRTX 5090でも足りません。しかし、現在のローカルLLM界隈では「4bit量子化（AWQ, GPTQ, GGUF）」が標準的です。4bit量子化を行えば、モデルサイズは約1/4になり、32Bモデルでも約18GB〜20GB程度に収まります。ここにコンテキスト長（KVキャッシュ）分のメモリ消費が加わります。

RTX 4090の24GB VRAMでは、32Bモデル（約20GB）をロードすると、残りのVRAMは4GB程度しかありません。これでは長いコンテキスト（長文の入力や履歴）を扱うとすぐにOOM（Out of Memory）になります。しかし、RTX 5090の32GB VRAMであれば、モデルロード後も10GB以上の余裕があります。これにより、数万トークンに及ぶ長文脈を扱っても速度低下が起きず、RAG（検索拡張生成）のようなメモリを食うタスクも快適にこなせます。

▼最高のPC構成：パソコン工房 LEVEL-R789-LC285K-XK1Xの衝撃

最終的に私が選んだのは、パソコン工房のLEVEL-R789-LC285K-XK1Xというモデルです。購入を決めた決定的な構成要素は以下の通りです。

- グラフィックス：NVIDIA GeForce RTX 5090 (VRAM 32GB)
これこそが、全ての遅延を解消し、Gemini 2.5 Flash相当のローカルAI推論を実現する「心臓」です。32GBというVRAM容量に加え、GDDR7によるメモリ帯域幅の向上により、トークン生成速度も飛躍的に向上しています。

- CPU：インテル Core Ultra 9 プロセッサー 285K
旧来のCore i9のような爆熱モデルではなく、電力効率とNPU（AI Boost）を強化した最新チップです。XBRLや大量のPDFを読み込むRAGのプリプロセス（前処理）において、CPU側の負荷を賢く分散し、GPUとの協調動作で全体のパフォーマンスを向上させます。

- ストレージ：2TB M.2 SSD
高速なSSDは、数100GBに及ぶデータセットのロードや、LLMのチェックポイント保存/読み込み速度を劇的に向上させます。

- 価格：約100万円（基本構成で約99万9,700円）
この価格は決して安くありません。しかし、「車を諦めてでも手に入れる」という私の決断に見合う、弁護士・監査役としての「知的能力を24時間フル稼働で拡張する専用ラボ」を手に入れるための、最高の投資だと確信しました。

■完全な実装手順（コピペ可）：RTX 5090でGemini Flash相当を5分で動かす

ここからは、あなたがRTX 5090を搭載した最強マシンを手に入れたと仮定し、Gemini 2.5 Flash相当のローカルLLM環境を最短5分で構築するための具体的な手順を解説します。OSはWindows 11 Home上のWSL2 (Ubuntu 24.04) を使用します。ネイティブLinuxも選択肢ですが、WSL2の進化によりWindows環境でもVRAMのオーバーヘッドを最小限に抑えつつ、快適な開発環境を構築可能です。

▼ステップ0：WSL2 (Ubuntu) のインストールと初期設定

WindowsのPowerShellを管理者権限で開き、以下のコマンドでWSL2とUbuntuをインストールします。


wsl --install -d Ubuntu-24.04


インストール後、WSL2のターミナルを開き、システムを最新の状態に保ちます。


sudo apt update && sudo apt upgrade -y
sudo apt install build-essential git curl wget -y


▼ステップ1：CUDA Toolkit 13.1のインストール

WSL2環境では、Windows側にNVIDIAドライバをインストールするだけで、WSL2側からもGPUが認識されます。WSL2側でドライバをインストールする必要はありません。CUDA Toolkitのみをインストールします。今回は最新のCUDA 13.1を使用します。


wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-13-1


インストール後、GPUが正しく認識されているか確認します。


nvidia-smi


ここで「NVIDIA GeForce RTX 5090」と「32768MiB」（約32GB）のVRAM容量が表示されれば成功です。

▼ステップ2：Python環境の構築 (uv)

Python仮想環境を構築し、依存関係をクリーンに保ちます。ここでは高速なパッケージマネージャである `uv` を使用します。


curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv venv llm-env --python 3.11
source llm-env/bin/activate


▼ステップ3：推論ライブラリのインストール

LLMを動かすためのコアライブラリをインストールします。PyTorchは公式サイトのインストールガイドに従い、自分のCUDAバージョンに合った方法で導入してください。その後、以下のライブラリを追加します。


uv pip install transformers accelerate bitsandbytes sentencepiece protobuf scipy
uv pip install vllm  # 高速推論エンジン


▼ステップ4：LLMモデルの実行コード（Transformers版）

まずはHugging Faceの `transformers` ライブラリを使って、標準的な方法でモデルをロードして動かしてみましょう。以下のコードを `run_llm.py` として保存してください。このコードは、VRAM 32GBを活かして32Bモデルを4bit量子化でロードし、高速に動作させます。

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# モデルID（例: DeepSeek-R1の32B蒸留モデル）
model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

# 4bit量子化の設定
# RTX 5090のパワーを活かしつつVRAMを節約し、長いコンテキストを扱えるようにする
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16 # RTX 50系はbfloat16にネイティブ対応
)

print(f"Loading model: {model_id}...")

# トークナイザーのロード
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

# モデルのロード
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto", # 自動的にGPUに割り当て
    trust_remote_code=True
)

print("Model loaded successfully!")
print(f"Current VRAM usage: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

# 推論実行関数
def generate_text(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
    
    return tokenizer.decode(outputs, skip_special_tokens=True)

# チャットループ
print("\n--- Start Chat (type 'exit' to quit) ---")
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    
    prompt = f"User: {user_input}\nAssistant:"
    
    response = generate_text(prompt)
    print(f"AI: {response.split('Assistant:').strip()}")
```

実行は以下のコマンドで行います。


python run_llm.py


▼ステップ5：vLLMによる爆速推論サーバーの構築（応用編）

`transformers` は手軽ですが、プロダクションレベルの速度を求めるなら `vLLM` が最強です。RTX 5090の大容量VRAMと `PagedAttention` アルゴリズムを組み合わせることで、スループットを数倍に高められます。

以下のコマンドで、OpenAI互換のAPIサーバーを立ち上げることができます。これにより、既存のOpenAI用クライアントツールからローカルLLMを利用可能になります。


# 32Bモデルを4bit量子化(AWQ)でロードしてサーバー起動
# ※モデルがAWQ形式で提供されている必要があります。
python -m vllm.entrypoints.openai.api_server \
    --model casperhansen/deepseek-r1-distill-qwen-32b-awq \
    --quantization awq \
    --dtype half \
    --gpu-memory-utilization 0.9 \
    --port 8000


起動したら、別のターミナルから以下のようにリクエストを送れます。


curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "casperhansen/deepseek-r1-distill-qwen-32b-awq",
        "messages":,
        "temperature": 0.7
    }'


このレスポンス速度を見れば、RTX 5090の真価を体感できるはずです。トークンが滝のように流れる様子は圧巻です。

■ハマりポイントと回避方法：スムーズなAI開発のためのチェックリスト

せっかく最強のハードウェアを手に入れたのに、ソフトウェアのトラブルで開発が停滞しては元も子もありません。私が経験した、あるいは見聞きしたハマりポイントとその回避策をまとめました。

▼1. NVIDIAドライバとCUDA Toolkitのバージョンミスマッチ

ハマりポイント：
新しいGPUが出ると、古いドライバやCUDAバージョンではうまく動作しないことがあります。特にPyTorchなどのライブラリは、特定のCUDAバージョンと密接に連携しています。Blackwell世代のRTX 5090は、古いCUDA（例えば11.x系）では動作しない可能性が高いです。

回避方法：
常に最新かつ安定版のNVIDIAドライバとCUDA Toolkitをインストールすることを推奨します。PyTorchの公式サイトで、使用しているPyTorchのバージョンと互換性のあるCUDAバージョンを確認し、それに合わせてCUDA Toolkitをインストールしましょう。本記事のようにCUDA 13.1を使用し、`nvidia-smi`でドライババージョン、`nvcc -V`でCUDAバージョンを確認する癖をつけてください。

▼2. VRAM不足時の無茶なモデルロード（OOM）

ハマりポイント：
「あと少しならVRAMに収まるはず」と、無理に大きなモデルをロードしようとすると、CUDA Out Of Memoryエラーが発生してプロセスが落ちます。あるいは、共有GPUメモリ（メインメモリ）へのオフロードが発生し、極端に遅くなります。

回避方法：
RTX 5090 (32GB VRAM) を選んだあなたは、32Bモデルであれば余裕がありますが、70Bクラスになると工夫が必要です。
- 量子化を活用する: 4bit (AWQ, GPTQ) や最近流行りのEXL2形式を使用する。
- コンテキスト長を制限する: 無限に会話を続けるとKVキャッシュが肥大化します。`max_model_len`などで制限をかけましょう。

▼3. 電源容量と冷却の不足

ハマりポイント：
RTX 5090は非常に高性能な反面、最大消費電力は450W〜500Wを超える可能性があります。電源容量が不足していると、高負荷時にPCが突然シャットダウンします。

回避方法：
最低1000W、推奨1200W以上の80PLUS PLATINUM認証電源を搭載したPCを選びましょう。また、12VHPWRケーブルの接続は確実に行い、コネクタが奥まで刺さっているか定期的に確認してください。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/gpu-inference/054_premium)*
