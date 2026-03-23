---
title: "uv入門：pip/venvを置き換えるPython高速パッケージマネージャ"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: false
canonical_url: "https://media.patentllm.org/blog/dev-tool/uv-python-guide"
---


## uvとは


uvはAstral社（Charlie Marsh）が開発したRust製のPythonパッケージマネージャです。pip、venv、poetry、pyenvが担っていた機能を一つのツールに統合し、依存関係解決を10〜100倍高速化しました。2024年にリリースされ、急速に普及が進んでいます。


## なぜuvか：pipの問題


pipの依存関係解決はPythonで実装されており、複雑なプロジェクトでは数分かかることがあります。仮想環境の作成にも20〜40秒を要します。この待ち時間は開発の集中状態を中断させます。

uvはRustで依存関係解決を再実装し、並列ダウンロードとキャッシュ機構を組み合わせることで、以下の速度を実現します。

- パッケージインストール：pipの10〜100倍
- 仮想環境作成：約0.5秒（pipは20〜40秒）
- ロックファイル生成：秒単位で完了


## インストール


[bash]
curl -LsSf https://astral.sh/uv/install.sh | sh
[/bash]

インストール後、シェルを再起動するかPATHを通します。


## 基本的な使い方



### プロジェクトの初期化


[bash]
uv init my-project
cd my-project
[/bash]

pyproject.tomlが生成されます。依存関係はここに記述されます。


### パッケージの追加


[bash]
uv add requests
[/bash]

uv.lockが自動生成され、再現性のある環境が保証されます。


### スクリプトの実行


[bash]
uv run python main.py
[/bash]

仮想環境のactivateが不要です。uv runが自動的に.venvを作成・使用します。


## PEP 723：インラインスクリプトメタデータ


単体スクリプトにpyproject.tomlなしで依存関係を記述できます。

[bash]
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "beautifulsoup4"]
# ///

import requests
from bs4 import BeautifulSoup

resp = requests.get("https://example.com")
soup = BeautifulSoup(resp.text, "html.parser")
print(soup.title.string)
[/bash]

実行：

[bash]
uv run scrape.py
[/bash]

依存関係のインストールから実行まで自動で行われます。venv作成もactivateも不要です。使い捨てスクリプトに最適です。


## Pythonバージョン管理（pyenv代替）


[bash]
# Python 3.12をインストール
uv python install 3.12

# 特定バージョンで実行
uv run --python 3.12 python main.py

# プロジェクトのPythonバージョンを固定
uv python pin 3.12
[/bash]

pyenvのようにシステム全体のPython切り替えではなく、プロジェクト単位でバージョンを管理します。


## pip互換モード


既存のrequirements.txtがあるプロジェクトでも使えます。

[bash]
uv pip install -r requirements.txt
uv pip install torch
uv pip freeze
[/bash]

pipと同じコマンド体系で、速度だけが向上します。移行コストがほぼゼロです。


## まとめ


uvが置き換えるもの：

- pip → uv add / uv pip install（10〜100倍高速）
- venv → uv run（自動管理、activateが不要）
- poetry → uv init + uv.lock（ロックファイルによる再現性）
- pyenv → uv python install / pin（Pythonバージョン管理）

一つのツールでPython開発環境の管理が完結します。特にAI開発ではPyTorchやCUDA関連の重いパッケージを頻繁にインストールするため、速度の恩恵が大きいです。
