---
title: NITE CHRIPデータをFTS5で高速検索する法規制分析ダッシュボード
tags:
  - Python
  - CLI
  - DevTools
  - productivity
private: false
updated_at: '2026-03-21T21:41:11+09:00'
id: 301d7fac7c704ae6922a
organization_url_name: null
slide: false
ignorePublish: false
---


## NITE CHRIPデータの変換


化学物質リスク情報プラットフォーム（CHRIP）から提供される法規制データはXML形式で公開されています。本プロジェクトではCSV形式への変換を経てFTS5に取り込む設計としました。

[python]
import xml.etree.ElementTree as ET
import pandas as pd

def xml_to_csv(xml_path, output_csv):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    records = []
    for item in root.findall('item'):
        record = {
            'cas_number': item.find('cas_number').text if item.find('cas_number') is not None else '',
            'substance_name': item.find('substance_name').text if item.find('substance_name') is not None else '',
            'regulation_id': item.find('regulation_id').text if item.find('regulation_id') is not None else '',
            'regulation_text': item.find('regulation_text').text if item.find('regulation_text') is not None else ''
        }
        records.append(record)
    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False, encoding='utf-8')
[/python]

WSL2 Ubuntu環境では、内部処理はUTF-8で統一し、外部システムとの連携時のみ必要に応じてエンコーディング変換を行うのがベストプラクティスです。


## FTS5インデックス構築


SQLiteのFTS5拡張機能を活用し、化学物質名や法規制文書の高速検索を実現します。

[sql]
CREATE VIRTUAL TABLE chemicals_fts USING fts5(
  cas_number,
  substance_name,
  regulation_text,
  tokenize='simple'
);

-- CSVから一括インポート
.mode csv
.import /tmp/chrip.csv chemicals_fts
[/sql]

FTS5は仮想テーブルのため、通常のBTreeインデックスを直接作成することはできません。CAS番号での高速検索が必要な場合は、別途通常のテーブルにCAS番号とFTS5のrowidを紐付けてインデックスを張る方法が有効です。


## Streamlitによる可視化


CAS番号検索結果を表示するStreamlitアプリケーションを構築しました。

[python]
import streamlit as st
from google import genai

client = genai.Client()

if 'cas_cache' not in st.session_state:
    st.session_state.cas_cache = {}

def get_cas_analysis(cas_number, substance_text):
    if cas_number in st.session_state.cas_cache:
        return st.session_state.cas_cache[cas_number]
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"以下の化学物質の法規制情報を要約してください。\n{substance_text}"
    )
    st.session_state.cas_cache[cas_number] = response.text
    return response.text

cas_input = st.text_input('CAS番号を入力してください')
if cas_input:
    # SQLite FTS5で検索
    results = search_fts5(cas_input)
    st.write(f"検索結果: {len(results)}件")
[/python]


## CAS番号の自動抽出


SDS（安全データシート）からCAS番号を自動抽出するテンプレートを実装しました。

[python]
from google import genai

client = genai.Client()

def extract_cas_from_sds(sds_text):
    prompt = """以下のSDS文書からCAS番号を抽出してください。
複数存在する場合はカンマ区切りで返してください。
抽出対象は「CAS No.」または「CAS番号」表記のみとします。
文書: """ + sds_text

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()
[/python]


## 産業界向け実装事例


製品のSDSをアップロードしてCAS番号を自動抽出し、法規制データベースと照合して非準拠リスクを可視化するワークフローを構築できます。特許データベースと連携すれば、類似物質の特許状況分析も可能です。


## まとめ


本ダッシュボードは、NITE CHRIPの法規制データをFTS5で高速検索可能にし、Gemini APIによるAI分析を組み合わせることで、化学物質の規制対応業務を効率化します。大規模データを扱う場合は、SQLiteのページサイズ最適化（pragma page_size）や、チャンク単位でのデータ読み込みが有効です。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/nite-chrip-search)*
