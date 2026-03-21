---
title: 特許検索AIをReddit r/LocalLLaMAに投稿したら65 upvoteと20件超の質問が来た話
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


## 特許検索エンジンをReddit r/LocalLLaMAに投稿したら、2時間で65アップボートと20件超の技術的質問が飛んできた話



## はじめに


2026年3月8日の夜、自作の無料特許検索エンジン patentllm.org https://patentllm.org を Reddit の r/LocalLLaMA（ローカルLLMコミュニティ、メンバー99.5万人）に投稿した。

タイトルは「I classified 3.5M US patents with Nemotron 9B on a single RTX 5090 — then built a free search engine on top」。
reddit.com/r/LocalLLaMA/comments/1ro52cu/comment/o9bfwnh https://www.reddit.com/r/LocalLLaMA/comments/1ro52cu/comment/o9bfwnh

投稿から2時間で65アップボート、20件超のコメント。しかもそのコメントの質が異常に高かったので、以下、実際のやり取りをベースに、海外エンジニアコミュニティから受けた質問と、そこから引き出された自分の設計思想を記録します。




## 投稿した内容


- USPTO PatentsViewから354万件の米国特許データを取得
- 74GBのSQLiteファイルにFTS5でインデックス構築
- Nemotron-Nano-9B（量子化なし）でRTX 5090上で全件を100カテゴリにタグ分類
- BM25ランキング（タイトル10.0、出願人5.0、要約3.0、クレーム1.0）
- FastAPI + Jinja2でサーバーサイドレンダリング
- Cloudflare Tunnel経由で配信




## Q&A：海外エンジニアからの質問と回答



### Q1:「なぜベクトル検索じゃなくてFTS5なの？」


最も多かった質問。r/LocalLLaMAではベクトル検索が主流なので、逆張りが目立った。

回答の要点： 特許検索では正確なフレーズマッチが重要。「solid-state battery electrolyte」と「energy storage medium」はベクトル空間では近いが、特許法上は完全に別物。FTS5なら完全一致検索、Boolean演算、BM25ランキングがSQLiteだけで完結する。3.5M件でもサブ秒で返る。

さらに、概念的なクエリ（「自動運転の障害物検出」のような自然言語）に対しては、ベクトル検索ではなくLLMによるクエリ拡張で対応している。ローカルLLMがFTS5用のクエリに変換するが、その際コーパスから事前抽出したキーワードインデックスからのみ検索語を選択させることで、LLMが存在しない用語を「ハルシネーション」することを防いでいる。


### Q2:「ハイブリッド（ベクトル＋FTS5）にしないの？」


回答の要点： 将来的には検討している。ただし実際にLanceDBを試した際、3.5M件のインデックス構築が不安定で中断した経験がある。SQLiteの方が安定しており予測可能だった。LLMベースのクエリ拡張で今のところ十分カバーできているので、パフォーマンスの壁にぶつかるまでは現行方式を維持する。


### Q3:「100個のテックタグはどうやって決めた？」


2人から同じ質問が来た。技術的に興味深いポイントだったようだ。

回答の要点： 2段階アプローチ。まずGeminiに数万件の特許を自由形式でタグ付けさせ、その結果を集計して意味のある上位100カテゴリに整理した。次にその固定リストをNemotron-Nano-9B（量子化なし、フル精度）に与えて、全件を分類させた。現在はCPCセクションG（物理学）とH（電気）を対象に処理済みで、RTX 5090で約30時間かかった。


### Q4:「74GBのSQLiteファイル、パーティションした方がいいのでは？」


年ごとに分割してマルチスレッドで読み込むべきという提案。

回答の要点： 現状74GBの単一ファイルでFTS5クエリはサブ秒で返っており、問題は起きていない。設計としては10年で1DBを想定している。現在のDBは2016-2025年をカバーしており、2005-2015年分を別ファイルとして構築中。ユーザーにどの年代を検索対象にするか選択させることで、検索頻度の違いに対応し、DB間を疎結合に保つ方式を考えている。バックアップは `cp` で終わる。


### Q5:「特許ファミリーの重複排除はどうしてる？」


継続出願（continuation）や分割出願（divisional）が検索結果に似たような特許を大量に出す問題。

回答の要点： 正直にまだやっていない。BM25 + 新しさの重み付け（30%）で最新のファミリーメンバーが上位に来る傾向はあるが、本質的な解決策ではない。PatentsViewのデータには出願参照情報が含まれているので、ファミリーのグループ化に使える。ロードマップには入っている。


### Q6:「クライアントの機密情報がLLMに流れる懸念は？」


弁理士としての守秘義務に関わる鋭い質問。

回答の要点： 無料検索（patentllm.org）はゼロログ設計。サーバーにもクライアント側にも検索履歴は保存されない。DB接続は読み取り専用。検索対象はすべてUSPTOの公開データなので機密情報の問題は発生しない。AI分析レイヤーではローカルLLM（Nemotron on RTX 5090）を使い、データが第三者サーバーに出ない設計にしている。これがクラウドAPIではなくセルフホストを選んだ主な理由。


### Q7:「AI要約機能を各特許に付けられない？」


回答の要点： 軽量モデル（Gemini Flash Lite等）でラップしてオンデマンド生成することも少し考えたが（よく使う手法）、コンテキストウィンドウが足りるかはまだ未検証。


### Q8・9:「先行特許調査機能はあるの？」「有料版はあるの？」


回答の要点： AI分析層（先行技術調査、FTO分析、競合ランドスケープ等7テンプレート）は構築済みだが、公開は早くても半年以上先。ソロ開発者として、品質・安定性の確保に加え、コスト面、リーガル面（免責・情報管理）の課題が多く、慎重に検討を進めている。無料検索は無料のまま継続。




## 印象的だったコメント


「patent lawyer who learned to code in December and processed 3.5M documents with a local model by March — this is the AI transition story in one post」

「74GB SQLite file on a Chromebook via tunnel is unhinged in the best way"（良い意味でぶっ飛んでる）」

「What a time to be alive. When people talk about AI democratizing software engineering, and the era of personalized software, this is exactly the kind of stuff I think about.」

「The 'vector search solves everything' crowd has never had to litigate over an exact phrase.」



ネットコミュニティを見ていても、〇〇に成功した系が多く、その先の技術選定の判断を議論する文化がまだ薄いと感じていたが、Redditのr/LocalLLaMAは「実際にローカルでLLMを動かしている人」が集まる場所で、「なぜそれを選んだのか」「自分はこうしている」という実践者同士の対話が自然に起きる場所がある、ということに感心しました。

patentllm.org https://patentllm.org — 検索は無料。ログインなし。ログなし。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/reddit-qa-patent-search)*
