---
title: RTX 5090で将棋AI — TensorRT FP8量子化とFloodgate実戦の記録
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


## dlshogiとは


dlshogiは、ディープラーニングを組み込んだ将棋エンジンで、C++実装版とPythonラッパーから構成されます。Windows版ではONNX RuntimeとDirectML、Linux版ではTensorRTとCUDAで動作します。本プロジェクトでは、RTX 5090を搭載したWSL2 Ubuntu 24.04環境でTensorRTを活用した実装を行いました。

主な特徴は以下の通りです。
- ニューラルネットワークによる評価値生成
- 伝統的なαβ探索とのハイブリッド方式
- ラッパースクリプトによる複数エンジンの協調制御


## Fuka40Bモデルの構造


Fuka40Bは107.2Mパラメータを持つResNet40x384アーキテクチャを採用したモデルです。ReLU活性化関数を使用し、将棋盤の局面を高精度に評価するために設計されています。

- トレーニングデータ：蒸留済みデータセット
- 最適化アルゴリズム：AdamW（学習率0.00005、重み減衰0.01）
- バッチサイズ：4096


## FP8量子化の効果


TensorRTのFP8量子化は、VRAM負荷を削減しつつ推論速度を向上させる技術です。FP8はINT4と比較して量子化誤差が小さく、精度と性能のバランスに優れています。

実測結果（RTX 5090 + 32GB VRAM）：
- FP16：VRAM 12.4GB、35k NPS（Nodes Per Second）、一致率82%
- FP8：VRAM 7.8GB、90k NPS、一致率81%
- INT4：VRAM 6.2GB、75k NPS、一致率73%

FP8はINT4と比較して精度が高く、NPS（1秒あたりのノード評価数）でも優れた性能を示します。VRAM使用量が削減されるため、他のプロセスとの共存も容易です。


## TensorRT最適化の注意点


TensorRTの--bestオプションは、特定のモデルと量子化設定の組み合わせで推論品質を低下させる場合があります。40Bモデルでは--bestを使用するとNPSと一致率が両方低下しました。

正しい設定はFP8を明示的に指定する方法です。

[bash]
trtexec \
  --onnx=models/eval/model_fp8.onnx \
  --fp8 \
  --minShapes=input1:1x62x9x9,input2:1x57x9x9 \
  --optShapes=input1:256x62x9x9,input2:256x57x9x9 \
  --maxShapes=input1:256x62x9x9,input2:256x57x9x9 \
  --saveEngine=model_fp8_trt
[/bash]


## RTX 5090での性能


最適化設定で90k NPSを達成しました。

[python]
# floodgate_client.pyより抜粋
UCT_THREADS = 4
DNN_BATCH_SIZE = 256
GPU_MEMORY_FRACTION = 0.8  # 80% VRAM使用
[/python]

- バッチサイズ256時：90,200 NPS
- バッチサイズ512時：87,500 NPS（メモリ圧力で低下）
- VRAM使用量：7.8GB（FP8量子化時）


## Floodgate実戦結果


Floodgateでの実戦では、Time_Margin（秒読み時間）の設定が勝敗を大きく左右しました。

- Time_Margin 0ms設定：3-2で勝利（精密な終盤評価で勝利）
- Time_Margin 1000ms設定：0-5で敗北（思考時間確保の設定ミスで全敗）

短い秒読み時にはTime_Marginを必ず0に設定することが重要です。


## 3フェーズハイブリッドシステム


Fuka40BとSuisho11を協調させる3フェーズシステムを構築しました。

- フェーズ1（開局）：Fuka40Bが広範な局面を評価します
- フェーズ2（中盤）：Suisho11が戦術的局面に特化します
- フェーズ3（終盤）：Fuka40Bが深層探索を再開します

終盤でのFuka40B再開時に前局の検索木を継承するため、再開時間が短縮されます。


## まとめ


RTX 5090とTensorRT FP8量子化を活用した将棋AIの実戦記録を報告しました。FP8量子化はVRAM負荷を削減しつつ精度を維持し、90k NPSの高速推論を実現しました。Floodgate実戦ではTime_Marginの設定が勝敗を分けるポイントであり、3フェーズハイブリッドシステムで安定した勝率を確保しています。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/gpu-inference/shogi-ai-rtx5090)*
