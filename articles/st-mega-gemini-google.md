---
title: "Gemini APIで会話データを資産化 — 履歴エクスポート・RAG・Streamlit"
emoji: "🔧"
type: "tech"
topics: ["ai", "machinelearning", "llm", "python"]
published: false
canonical_url: "https://media.patentllm.org/blog/ai/mega-gemini-google"
---

■はじめに：AIの「脳」を自分の手に取り戻す

現代のエンジニアにとって、GeminiやChatGPTといったLLM（大規模言語モデル）は、単なるツールを超えた「第二の脳」です。日々のコーディング、デバッグ、アーキテクチャの検討、あるいはキャリアの相談に至るまで、私たちは膨大な思考プロセスをAIに預けています。しかし、ここで一つの重大な問題に直面します。「この貴重な対話データは、本当に自分のものであるか？」という問いです。

ブラウザの履歴に埋もれ、検索もままならない状態では、過去の知見を活かすことはできません。また、Google Takeoutのような標準機能が期待通りに動作しない場合、私たちの知的資産は消失の危機に晒されます。さらに、最新のRTX 5090（VRAM 32GB）のような強力なハードウェアを手に入れても、適切なデータとワークフローがなければ、その性能を最大限に引き出すことは不可能です。

この記事は、Geminiを使い倒すエンジニアのために、散逸しがちな会話履歴のエクスポート手法から、Google Workspaceを用いた知識ベースの構築、さらにはローカルLLMとRAG（検索拡張生成）を組み合わせたアプリケーション開発までを網羅した実践的なガイドです。

泥臭いハックから自動化スクリプトまで、すべてのコードは動作するように設計されています。あなたのAI活用を「消費」から「資産化」へとシフトさせるための参考として活用してください。

■第1章：Gemini会話履歴のエクスポート手法

Geminiとの対話は、あなたの思考の写し鏡です。まずはこのデータを手元に確保することから始めましょう。しかし、ここには注意すべき点があります。

▼課題：Google Takeoutのエクスポート不具合

Googleには「Google Takeout」というデータエクスポート機能がありますが、Geminiの履歴に関しては動作が不安定な場合があります。数百件のチャット履歴をエクスポートしようとした際、ダウンロードされたZipファイルが「1MB未満」で、中身が空っぽだったという困惑した経験があります。

特にGoogle Workspace（企業アカウント）を利用している場合や、API経由での利用が混在している場合、Web UI上のチャット履歴が正しくアーカイブされないことがあります。また、エクスポートされたとしても複雑なJSON構造になっており、そのままでは人間が読める形式ではありません。

▼解決策A：PythonスクリプトによるJSON整形（Takeoutが成功した場合）

もしGoogle Takeoutで無事に `GeminiChat.json` が入手できた場合、それを可読性の高いMarkdownやCSVに変換する必要があります。以下のPythonスクリプトは、ネストされたJSON構造を解析し、日付やタイトルを整形して出力します。

```python
import json
import os
import csv
from datetime import datetime

def format_timestamp(ts_str):
    """ISO 8601形式の日時を整形"""
    try:
        if ts_str.endswith('Z'):
            ts_str = ts_str
        dt_object = datetime.fromisoformat(ts_str)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts_str

def process_gemini_json(json_file_path, output_dir="exported_gemini_chats"):
    """GeminiChat.jsonを読み込みMarkdownとCSVを出力"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    all_chat_data = []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"エラー: {e}")
        return

    # データ構造の正規化（リストであることを保証）
    if isinstance(data, dict):
        data =
    
    print(f"{len(data)}件のチャットデータを処理します...")

    for i, chat_entry in enumerate(data):
        title = chat_entry.get('title', f"無題のチャット_{i+1}")
        # ファイル名に使えない文字を除去
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title: safe_title = f"chat_{i+1}"
        
        created_at = format_timestamp(chat_entry.get('create_time', '不明'))
        
        # Markdown生成
        md_filename = os.path.join(output_dir, f"{safe_title}.md")
        full_text = ""
        
        with open(md_filename, 'w', encoding='utf-8') as md_f:
            md_f.write(f"# {title}\n\n")
            md_f.write(f"日付: {created_at}\n\n")
            
            conversations = chat_entry.get('conversations', [])
            if not conversations and 'content' in chat_entry:
                # 構造が異なる場合のフォールバック
                conversations =)}]

            for convo in conversations:
                speaker = convo.get('speaker', 'Unknown')
                text = convo.get('text', '')
                md_f.write(f"■ {speaker}\n{text}\n\n")
                full_text += f"{speaker}: {text}\n"
        
        all_chat_data.append({
            'title': title,
            'created_at': created_at,
            'summary': full_text.replace('\n', ' ') + '...',
            'file': md_filename
        })

    # CSV出力
    csv_file = os.path.join(output_dir, "summary.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=)
        writer.writeheader()
        writer.writerows(all_chat_data)
    
    print(f"完了: {output_dir} に保存されました。")

if __name__ == "__main__":
    # ここにJSONファイルのパスを指定
    # json_path = "takeout/Gemini/GeminiChat.json" 
    # process_gemini_json(json_path)
    print("JSONパスを指定して実行してください")
```

▼解決策B：Chrome拡張機能によるエクスポート（Takeoutが失敗した場合）

Google Takeoutが機能しない、あるいは「Geminiアプリ」の項目自体が表示されない場合、ブラウザに表示されている情報を直接保存するアプローチが有効です。「ChatExporter for Gemini」などのChrome拡張機能を利用することで、DOMから直接テキストを抽出し、Markdown形式で保存できます。

この方法はサーバーサイドの不具合に依存せず、現在見えているものを確実に保存できるため、バックアップとして非常に有効です。大量の履歴がある場合でも、ブラウザのスクロールに合わせて順次データを取得してくれるツールを選定することが重要です。

■第2章：Googleエコシステムでの知識ベース構築（GAS × AppSheet）

エクスポートしたデータは、そのままにしておくのはもったいないでしょう。次は、これを検索可能な「知識ベース」としてGoogle Workspace内に再構築します。Google Apps Script (GAS) と AppSheet を組み合わせることで、サーバー管理不要のセキュアなAIアシスタントを作成できます。

▼疎結合アーキテクチャのメリット

このシステムは「Google Sheets（データベース）」「GAS（ロジック）」「AppSheet（UI）」を疎結合に保つことで、高いメンテナンス性を実現します。

- Google Sheets: 会話ログを構造化データとして保存。RAGの検索対象となる。
- GAS: Gemini APIを呼び出し、シートへの読み書きを行う。
- AppSheet: スマホやPCからアクセスできる直感的なUIを提供。

▼実装：Gemini履歴を自動保存するGASコード

以下のコードは、AppSheetからのリクエストを受け取り、最新の推論モデルである Gemini 3.1 Pro のAPIを叩いて回答を生成し、その結果をスプレッドシートに追記するGASの関数です。

```javascript
const GEMINI_API_KEY = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
const SHEET_ID = 'あなたのスプレッドシートID';

function callGemini(prompt, historyContext) {
  // Gemini 3.1 Pro Previewを使用
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key=${GEMINI_API_KEY}`;
  
  // 過去の文脈があればプロンプトに追加（簡易RAG）
  const finalPrompt = historyContext 
    ? `以下の過去の文脈を踏まえて回答してください。\n文脈: ${historyContext}\n\n質問: ${prompt}`
    : prompt;

  const payload = {
    "contents":
    }]
  };

  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const json = JSON.parse(response.getContentText());
    if (json.candidates && json.candidates.content) {
      return json.candidates.content.parts.text;
    } else {
      return "エラー: 回答を生成できませんでした。";
    }
  } catch (e) {
    return `通信エラー: ${e.toString()}`;
  }
}

// AppSheetからのWebhookやトリガーで実行される関数
function onUserQuery(e) {
  // ※実際にはAppSheet Automation等から引数を受け取る想定
  const userPrompt = e ? e.prompt : "テスト質問"; 
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Log');
  
  // 過去ログから関連情報を検索するロジック（簡易版）
  const lastRow = sheet.getLastRow();
  let context = "";
  if (lastRow > 1) {
    context = sheet.getRange(lastRow, 3).getValue(); // 前回の回答を文脈とする
  }

  const aiResponse = callGemini(userPrompt, context);
  
  // タイムスタンプ、プロンプト、回答を保存
  sheet.appendRow();
  
  return aiResponse;
}
```

このスクリプトをGoogle Sheetsの拡張機能からGASプロジェクトとして作成し、スクリプトプロパティにAPIキーを設定することで動作します。これにより、あなたの会話はすべてスプレッドシートに蓄積され、検索可能なデータベースとなります。

■第3章：RTX 5090とRAGによるスライド自動生成

知識ベースが整ったら、次はアウトプットの自動化です。ここでは、最新のハイエンドGPU「RTX 5090」のパワーを活用し、法務や技術などの専門分野に特化したコンテンツ生成と、Google Slidesへの自動出力を実現します。

▼RTX 5090 (VRAM 32GB) を活用したローカルLLM

RTX 5090の最大の特徴は、32GBという広大なVRAM容量とBlackwellアーキテクチャによる高い推論性能です。これにより、Gemma 3 (27B) やQwen2.5-32Bといった中規模以上のLLMを、軽微な量子化でフルにロードすることが可能になります。

複雑な論理パズルを含む専門的なタスクでは、一般的なAPI経由のモデルではハルシネーションが起きがちです。そこで、Unslothというライブラリを使用し、RTX 5090上でローカルLLMをファインチューニングするアプローチが有効です。

```python
from unsloth import FastLanguageModel
import torch

def train_local_model():
    # RTX 5090の32GB VRAMを活かしてモデルをロード
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/gemma-3-27b-it", # Gemma 3 27Bモデルを使用
        max_seq_length = 4096,
        dtype = None, # 自動設定
        load_in_4bit = True, # 27Bモデルを余裕を持って動かすため4bit量子化
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules =,
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
    )
    
    # ここにデータセットのロードとTrainerの設定が入ります
    print("学習開始: RTX 5090 VRAM 32GB Environment")
```

▼コンテンツからスライドへの自動変換

ローカルLLMやGemini APIによって生成された精度の高い回答や解説は、JSON形式で構造化して出力します。これをGoogle Apps Scriptで読み込み、スライドを自動生成します。

```javascript
function generateSlidesFromData() {
  // 生成するスライドのデータ（Python側からJSONで受け取る想定）
  const slidesData =
    },
    {
      title: "実験結果",
      body: "専門的な解釈において、Gemini 3.1 Proと同等の精度を達成。",
      points:
    }
  ];

  const presentation = SlidesApp.create("AI生成レポート_RTX5090検証");
  const slides = presentation.getSlides();
  if (slides.length > 0) slides.remove();

  slidesData.forEach(data => {
    const slide = presentation.appendSlide(SlidesApp.PredefinedLayout.TITLE_AND_BODY);
    
    const titleShape = slide.getShapes().find(s => s.getPlaceholderType() === SlidesApp.PlaceholderType.TITLE);
    if (titleShape) titleShape.getText().setText(data.title);
    
    const bodyShape = slide.getShapes().find(s => s.getPlaceholderType() === SlidesApp.PlaceholderType.BODY);
    if (bodyShape) {
      let textContent = data.body + "\n\n";
      data.points.forEach(p => textContent += `・${p}\n`);
      bodyShape.getText().setText(textContent);
    }
  });

  Logger.log("スライド生成完了: " + presentation.getUrl());
}
```

この自動化により、資料作成の時間は大幅に短縮されます。人間は構成と内容の精査に集中し、レイアウト調整という単純作業から解放されます。

■第4章：リアルタイム・ダッシュボード構築（Streamlit + Gemini）

最後に、日々のデータ分析やモニタリングに使える、リアルタイムダッシュボードの構築です。Pythonのフレームワーク「Streamlit」を使えば、HTMLやCSSの知識がなくても数行のコードでWebアプリを作成できます。ここにGemini APIを統合することで、データの意味をAIがリアルタイムで解釈するダッシュボードが完成します。

▼Streamlitアプリケーションの実装

以下のコードは、ユーザーの入力を受け取り、高速なレスポンスが特徴の Gemini 2.0 Flash で感情分析を行い、その結果をリアルタイムでグラフ化するダッシュボードの例です。

```python
import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import altair as alt
import json

# APIキーの設定（環境変数から読み込み推奨）
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
# リアルタイム処理に適した高速モデルを使用
model = genai.GenerativeModel('gemini-2.0-flash')

def main():
    st.set_page_config(layout="wide", page_title="Gemini AI Dashboard")
    st.title("Gemini リアルタイム分析ダッシュボード")

    # セッション状態の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # サイドバー：履歴表示
    with st.sidebar:
        st.header("分析履歴")
        for msg in reversed(st.session_state.messages):
            st.text(f"{msg}: {msg}...")

    # メインエリア：入力と表示
    user_input = st.text_input("分析したいテキストを入力してください:")

    if st.button("分析開始") and user_input:
        st.session_state.messages.append({"role": "User", "content": user_input})
        
        with st.spinner("Geminiが思考中..."):
            try:
                # JSON形式での出力を強制するプロンプト
                prompt = f"""
                以下のテキストの感情分析を行い、ポジティブ、ネガティブ、ニュートラルの割合をJSON形式で出力してください。
                キーは 'sentiment' とし、リスト形式で {{"category": "...", "percentage": ...}} を返してください。
                テキスト: {user_input}
                """
                response = model.generate_content(prompt)
                response_text = response.text
                
                # JSON部分の抽出（簡易的な処理）
                json_str = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(json_str)
                
                # グラフ描画
                if "sentiment" in data:
                    df = pd.DataFrame(data)
                    chart = alt.Chart(df).mark_arc().encode(
                        theta=alt.Theta(field="percentage", type="quantitative"),
                        color=alt.Color(field="category", type="nominal"),
                        tooltip=
                    ).properties(title="感情分析結果")
                    
                    st.altair_chart(chart, use_container_width=True)
                    st.success("分析完了")
                    
                    st.session_state.messages.append({"role": "AI", "content": str(data)})
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
```

このダッシュボードは、顧客からのフィードバック分析や、社内チャットの雰囲気検知など、様々な用途に応用可能です。Geminiの高速なレスポンスとStreamlitの手軽さが、プロトタイピングの速度を向上させます。

■まとめ：AIとの共創関係を築く

本記事では、Gemini APIを活用するための4つのフェーズを紹介しました。

- **保存:** Chrome拡張やスクリプトで、対話データを確実にエクスポートする。
- **管理:** GASとGoogle Sheetsで、自分だけの知識ベースを構築する。
- **生成:** RTX 5090 (32GB) のパワーを活かし、ローカルLLMでコンテンツを生み出し、GASで資料化する。
- **可視化:** Streamlitでリアルタイムにデータを分析し、意思決定をサポートする。

これらの技術は、単独で使うよりも組み合わせることで真価を発揮します。RTX 5090のような強力なハードウェア環境は、AIをローカルで自在に操るための基盤となります。

まずは手元の履歴をエクスポートすることから始めてみてください。そこには、あなた自身の思考の軌跡という、有用な知見が眠っているはずです。
