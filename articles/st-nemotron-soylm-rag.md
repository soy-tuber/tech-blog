---
title: "SoyLM：クラウド不要の軽量RAGツールの実現とドキュメント改善の物語"
emoji: "🔧"
type: "tech"
topics: ["ai", "machinelearning", "llm", "python"]
published: true
canonical_url: "https://media.patentllm.org/blog/ai/nemotron-soylm-rag"
---

## 導入
ある日、RAGツール開発中に「READMEの説明不足」と「不要な依存関係」という2つの課題に直面しました。GitHubで公開予定のプロジェクト「SoyLM」のREADME.mdは誤ってNotebookLMを参照しており、技術的な説明もGemini APIに依存する記述が残っていたのです。また、「LM」という略語が「Language Model」か「Lite Model」かで議論が分かれ、ユーザーを混乱させる要因となっていました。  
この状況を解決するため、シングルファイルで動作するローカルRAGツールとしての思想を明確にし、ドキュメント・コードの両方を根本から見直すことにしました。

## 本文
### 問題の本質
1. **READMEの誤記**  
   「NotebookLM互換」という誤った記述があり、ローカルファーストの思想が伝わりにくかった
2. **技術的不明確さ**  
   - LMの意味が「Language Model」か不明
   - Gemini APIへの依存がコード内に残存
   - シングルファイル設計のメリットが伝わらない

### 解決のプロセス
#### 1. ドキュメントの刷新
- README.mdの見出しを「Local-first RAG tool」に変更
- NotebookLMへの言及を削除し、GitHubリンクのみを記載
- SoyLM = "Soy"（シンプルさ） + "LM"（Language Model）という命名の意図を明示

#### 2. コードの抜本的改善
```python
# app.pyの変更ポイント
# Gemini関連の全削除（APIキー・モデル定義・エンドポイント）
# フロントエンドからのGemini選択肢の削除
# 代わりにNemotron-Nano-9Bをデフォルトにハードコード
```

#### 3. 設計思想の明確化
- **ストレージ**: SQLite FTS5 + BM25で検索（外部サービス不要）
- **処理フロー**: ソース分析を事前実行（クエリ時の遅延を回避）
- **UI**: FastAPI + vanilla JSのシングルファイル構成
- **拡張性**: YouTube動画処理にはPlaywrightのフォールバックを実装

### 技術的特徴
| 機能 | 実装手法 | 特徴 |
|------|----------|------|
| 事前ロード | `flash_load_source` | クエリ時の遅延を解消 |
| 検索エンジン | SQLite FTS5 + BM25 | 軽量かつ高速な検索 |
| ストリーミング | SSE | リアルタイム応答を実現 |
| モデル互換性 | OpenAI互換エンドポイント | Nemotron以外のモデルも利用可能 |

### Redditでの発信
技術的価値を伝えるため、r/LocalLlamaで以下の投稿を実施：
```markdown
**Title**: SoyLM – ローカルRAGの究極のシンプル設計
**Body**:
クラウドAPIゼロで動作するRAGツールを構築。ドキュメント/URL/YouTube動画をアップロードすると、ローカルLLMが分析し、ソースに基づいた会話が可能に。

**主な設計思想**:
- シングルファイル設計（FastAPI + JSの1ファイル実装）
- 事前分析済みソース（クエリ時の高速化）
- SQLite 1つで全管理（ソース・履歴・検索インデックス）
- YouTube対応（Playwrightフォールバック）

GitHub: https://github.com/soy-tuber/SoyLM
```

## まとめ
このプロジェクトを通じて学んだのは、「シンプルさ」と「ローカルファースト」の重要性です。クラウド依存を排除した設計により、開発・運用コストを大幅に削減でき、技術文書の明確化でユーザー理解が飛躍的に向上しました。特にRedditでの反響は良好で、ローカルLLMコミュニティからのフィードバックを基にさらなる改善を進めています。  
今後の目標は、この設計思想を基に複数ソースのクロスドキュメント検索機能を追加し、SoyLMをRAGツールの新基準として確立することです。クラウド不要のRAGに興味があるエンジニアは、ぜひGitHubリポジトリを訪れてみてください。
