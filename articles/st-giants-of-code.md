---
title: "AI開発スタックを支えるOSSの系譜：その起源と作り手たち"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: false
canonical_url: "https://media.patentllm.org/blog/dev-tool/giants-of-code"
---

ローカルAI開発環境は多数のオープンソース技術の上に成り立っています。本記事では、筆者の開発環境（RTX 5090 + Core Ultra 9 285K + WSL2 Ubuntu）を構成する主要技術について、その起源と設計上の判断を年代順に整理します。


## プログラミング言語：Python（1991年〜）— Guido van Rossum


オランダ出身のGuido van Rossumが、アムステルダムのCWI（数学・情報科学研究所）に勤務していた1989年、クリスマス休暇の暇つぶしとして開発を開始しました。名前はMonty Pythonに由来します。設計哲学は「読みやすさが最高の価値」で、インデントによるブロック構造の強制がその象徴です。

AIの共通言語となった背景には、NumPy/SciPyの数値計算基盤、Jupyter Notebookとの親和性、動的型付けによる実験の容易さがあります。van Rossumは「慈悲深き終身独裁者（BDFL）」として言語を導き、2018年にBDFLを引退しました。その後Microsoftに入社し、CPythonの高速化プロジェクトに取り組んでいます。


## GPU汎用計算：CUDA（1993年〜）— Jensen Huang


台湾生まれ、9歳で渡米したJensen Huang（黄仁勲）は、オレゴン州立大学で電気工学を学び、LSI LogicとAMDでチップ設計を経験した後、1993年にデニーズのレストランでChris MalachowskyとCurtis Priemの2人とNVIDIAを共同創業しました。30歳のときです。

1999年に「GPU」という用語を定義しGeForce 256を発表しました。2006年、GPUを汎用並列計算に使うプログラミングモデルCUDAを発表しました。ニューラルネットワークの学習は本質的に行列演算であり、GPUの数千コアによる並列処理と相性が良いです。2012年のAlexNet（GTX 580で訓練）がこれを実証し、深層学習時代が始まりました。現行のRTX 5090は21,760 CUDA Cores、680 Tensor Coresを搭載し、FP16で約170TFLOPSを実現します。


## 組み込みデータベース：SQLite（2000年〜）— D. Richard Hipp


D. Richard Hippは米海軍の誘導ミサイル駆逐艦のダメージコントロールシステム開発に携わっていました。当時のシステムはInformixを使用していましたが、サーバーの起動に手間がかかる問題があり、サーバー不要のデータベースとしてSQLiteを設計しました。設定不要、単一ファイルで完結するRDBMSです。

推定デプロイ数は10億超です。iPhone、Android、Chrome、Firefox、Boeing 787の飛行制御システム等に組み込まれています。ライセンスはパブリックドメイン（著作権放棄）です。Hippは現在もほぼ一人でコードベースを保守しており、コードサイズはフル機能で約600KBです。ACIDトランザクションをWALで保証します。


## OS：Ubuntu（2004年〜）— Mark Shuttleworth


南アフリカ出身のMark Shuttleworthは、1999年にSSL認証局Thawteを設立しVeriSignに約5.75億ドルで売却しました。2002年にはソユーズで国際宇宙ステーションに滞在し、アフリカ大陸初の民間宇宙旅行者となりました。帰還後の2004年、Canonicalを設立しUbuntuを公開しました。

Debianベースで、定期リリース（LTSは2年周期）とAPTパッケージ管理により、当時のLinuxの「インストールに数日かかる」問題を解消しました。名前はズールー語で「私があるのは、あなたがあるから」の意です。現在、HuggingFaceのサーバー、Google ColabのバックエンドVM、AWSのDeep Learning AMIなど、AI研究インフラの大半がUbuntu上で稼働しています。


## 深層ネットワークの基盤：ResNet（2015年）— Kaiming He


Kaiming Heは中国・広東省出身で、清華大学を卒業後、香港中文大学で博士号を取得しました。Microsoft Research Asiaでの研究中にResNetを発表しました。ネットワークを深くすると訓練精度自体が悪化する「劣化問題」に対し、Skip Connection（残差接続）を提案しました。

y = F(x) + x という構造により、不要な層はF(x)=0を学習すれば恒等写像になります。この設計で152層のネットワークの訓練に成功しました。現在のTransformerアーキテクチャ（GPT、BERT等）にもResidual Connectionが組み込まれています。Google Scholar引用数は40万件超です。HeはFAIR（Meta AI）を経て、2024年にMITの教授に着任しました。


## 深層学習フレームワーク：PyTorch（2016年〜）— Soumith Chintala


インド・ハイデラバード出身のSoumith Chintalaは、ニューヨーク大学でYann LeCunに師事した後、Facebook AI Research（FAIR）に加わりPyTorchを開発しました。従来のTheano/旧TensorFlowは計算グラフを事前定義する「Define-and-Run」方式で、デバッグが困難でした。

PyTorchは「Define-by-Run」（動的計算グラフ）を採用し、Pythonコード実行時にグラフが構築されます。loss.backward()一行で自動微分が走り、通常のPythonデバッガが使えます。これにより深層学習の実装ハードルが大幅に下がりました。


## Webアプリフレームワーク：Streamlit（2019年〜）— Adrien Treuille


Adrien Treuilleはカーネギーメロン大学のコンピュータサイエンス准教授でした。群衆シミュレーションや計算デザインを専門としていましたが、研究成果をデモとして見せる際にWebアプリ構築のハードルが高いことに課題を感じ、GoogleでのAR/VRプロジェクトを経て、2018年にThiago Teixeira、Amanda Kellyと共にStreamlitを創業しました。

PythonスクリプトがそのままインタラクティブなWebアプリになります。HTML/CSS/JavaScriptの知識が不要です。st.session_stateで状態管理、st.chat_messageでチャットUI構築が可能です。2022年にSnowflakeが約8億ドルで買収しました。


## セキュアトンネリング：Cloudflare Tunnel（2018年〜）— Matthew Prince


Matthew Princeはハーバード・ロースクールとハーバード・ビジネススクールをダブルで修了しました。在学中にスパムメールの追跡プロジェクト「Project Honey Pot」を運営した経験から、2009年にMichelle Zatlyn、Lee Hollowayと共にCloudflareを創業しました。

Cloudflare Tunnel（旧Argo Tunnel、2018年GA）は、自宅サーバーからCloudflareエッジへのアウトバウンド接続でトンネルを確立します。ポート開放、固定IP、SSL証明書管理が不要です。DDoS防御とWAFがCloudflareエッジで提供されます。cloudflaredクライアントをインストールし、cloudflared tunnel --url http://localhost:8501 を実行するだけで、ローカルアプリが外部公開されます。


## LLMファインチューニング：Unsloth（2023年〜）— Daniel Han & Michael Han


オーストラリア在住のDaniel HanとMichael Hanの兄弟が開発しました。2人ともシドニー大学出身で、大企業に属さず独立して開発を進めました。カーネルフュージョン（複数演算の単一CUDAカーネル融合）と再マテリアライゼーション（中間テンソルの再計算）により、VRAM使用量を60〜80%削減、訓練速度を2〜5倍向上させました。

7BモデルのフルFTに必要なVRAMが80GB→8〜16GBになりました。RTX 4090（24GB）やRTX 5090（32GB）でのローカルFTを実用化しました。


## オープンウェイトLLM：Nemotron（2024年〜）— NVIDIA / Bryan Catanzaro


NVIDIAのApplied Deep Learning Research部門を率いるBryan Catanzaroのチームが開発しました。Catanzaroはスタンフォード大学でKurt Keutzerに師事し、GPUによる深層学習の高速化研究の初期から携わってきた人物です。

Nemotronは合成データ生成と高品質なアラインメントに注力したモデルファミリーで、Llama等のベースモデルをNVIDIA独自のHelpSteer2データセットとRLHFで調整しています。Llama-3.1-Nemotron-70B-InstructはArena Hardベンチマークで当時のGPT-4oを上回るスコアを記録しました。CUDAからモデルまで、NVIDIAがAIスタックの全層を自社で押さえる戦略の一環です。


## Pythonパッケージマネージャ：uv（2024年〜）— Charlie Marsh


Charlie Marshはハーバード大学でコンピュータサイエンスを学び、Khan Academy、Springでの勤務を経て、PythonリンターRuffを開発しました。RuffのヒットをきっかけにAstralを創業し、uvを開発しました。Pythonのpipの依存関係解決をRustで書き直し、10〜100倍の高速化を実現しました。仮想環境作成は約0.5秒（pipは20〜40秒）です。

また、uv runコマンドにより仮想環境の明示的なactivateが不要になり、PEP 723のインラインメタデータに対応しました。poetry/pyenvの複雑なワークフローを一元化しました。


## 技術スタック一覧


OS・開発環境: Ubuntu（Mark Shuttleworth / Canonical）、Cursor（Anysphere）
パッケージ管理: uv（Charlie Marsh / Astral）
データ: SQLite（D. Richard Hipp）、JSONL
AIフレームワーク: PyTorch（Soumith Chintala / Meta AI）、ResNet（Kaiming He）、Unsloth（Daniel & Michael Han）、Nemotron（Bryan Catanzaro / NVIDIA）
Web・公開: Streamlit（Adrien Treuille / Snowflake）、Cloudflare Tunnel（Matthew Prince / Cloudflare）
ハードウェア・言語: NVIDIA RTX 5090 / CUDA（Jensen Huang）、Python（Guido van Rossum）
