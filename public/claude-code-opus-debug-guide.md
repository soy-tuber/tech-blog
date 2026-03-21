---
title: Claude Code実践ガイド：Opus 4.6によるデバッグ・テスト自動化・CUDA環境構築
tags:
  - Python
  - CLI
  - DevTools
  - productivity
private: false
updated_at: '2026-03-21T21:41:10+09:00'
id: 38a124f67ec19c45c345
organization_url_name: null
slide: false
ignorePublish: false
---

■はじめに

Claude CodeはAnthropicが提供するCLI（コマンドラインインターフェース）ツールで、ターミナルから直接Claude Opus 4.6を呼び出してコーディング、デバッグ、環境構築を行えます。エディタに依存せず、既存のワークフローにそのまま組み込める点が特徴です。

本記事では、Claude Codeを用いた以下の実践的なユースケースを解説します。

- プロンプト設計とCLAUDE.mdによるコスト・品質の制御
- Flaskアプリのデバッグ事例
- pytestテストコードの自動生成
- RTX 5090 + CUDA 13.1環境構築の支援
- GitHub ActionsによるCI/CD自動化

■第1章：CLAUDE.mdによるプロジェクト制御

Claude Codeはプロジェクトルートの `CLAUDE.md` を自動的に読み込み、AIの振る舞いを制御します。毎回プロンプトで指示する必要がなく、チーム全体で一貫した出力を得られます。

CLAUDE.mdの記述例：

[bash]
# CLAUDE.md
- 日本語で回答すること
- コードにはPythonの型ヒントを必ず付けること
- 説明は簡潔に。コード以外の出力は最小限にすること
- テストにはpytestを使用すること
- 推測でオプション名を作らないこと。不明な場合は確認を求めること
[/bash]

これにより、冗長な説明や不要な装飾を抑え、トークン消費を削減しつつ実用的な出力を得られます。

■第2章：デバッグ事例 — FlaskアプリのValueError

▼状況

ユーザー管理APIの `update_user` エンドポイントで、特定のリクエスト時に500エラーが発生しました。ログには `ValueError: invalid literal for int() with base 10: 'one'` と記録されています。

バグを含むコード：

[bash]
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    for key, value in data.items():
        if key == 'id':
            _ = int(value)  # リクエストボディに "id": "one" が来るとクラッシュ
            continue
        # ...
[/bash]

▼Claude Codeでの解決

エラーログとコードをClaude Codeに渡す：

[bash]
claude "このFlaskコードでValueErrorが出る。ログ: ValueError: invalid literal for int() with base 10: 'one'. app.pyのupdate_user関数を修正して"
[/bash]

Claude Codeの指摘：リクエストボディの `id` フィールドに対して `int()` を実行しているが、更新処理でボディのidは不要。URLパラメータの `user_id` のみを使用すべき。

修正後：

[bash]
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400

    set_clauses = []
    values = []
    for key, value in data.items():
        if key in ('id',):
            continue  # ボディのidは無視
        if key not in ('username', 'email'):
            continue
        set_clauses.append(f"{key} = ?")
        values.append(value)
    # ... DB更新処理
[/bash]

■第3章：テストコード自動生成

▼基本的なテスト生成

対象コード（calculator.py）：

[bash]
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
[/bash]

Claude Codeへの指示：

[bash]
claude "calculator.pyのdivide関数のpytestテストを生成して。正常系とゼロ除算の異常系をカバーすること"
[/bash]

生成されるテスト：

[bash]
import pytest
from calculator import divide

def test_divide_success():
    assert divide(10, 2) == 5.0
    assert divide(5, 2) == 2.5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        divide(10, 0)

@pytest.mark.parametrize("a, b, expected", [
    (10, 2, 5.0), (-10, 2, -5.0), (0, 5, 0.0), (1, 3, 0.333333),
])
def test_divide_parametrized(a, b, expected):
    assert divide(a, b) == pytest.approx(expected)
[/bash]

▼外部依存のモック化

APIを呼ぶ関数のテストでは、unittest.mockを使ったモックコードも生成できます：

[bash]
claude "fetch_user_data関数のテストを作成。requestsはmockし、成功時と404時をカバーして"
[/bash]

■第4章：RTX 5090 + CUDA 13.1 環境構築

GPU環境構築で最もハマるのはドライバー・CUDA・PyTorchのバージョン整合性です。Claude Codeにエラーメッセージを渡して原因特定と修正を行います。

▼WSL2でのCUDA環境構築

WSL2ではLinux側にNVIDIAドライバーをインストールしません。Windows側のドライバーが自動マウントされます。CUDA Toolkitのみをインストールします。

[bash]
# 既存のNVIDIAパッケージを削除
sudo apt purge -y '^nvidia-.*'
sudo apt autoremove -y

# CUDA Toolkit 13.1のインストール
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-13-1
[/bash]

▼PyTorchインストールと動作確認

PyTorchは公式サイト（pytorch.org）のインストールガイドに従い、自分のCUDAバージョンに合った方法で導入してください。

確認スクリプト：

[bash]
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    cap = torch.cuda.get_device_capability(0)
    print(f"Compute Capability: sm_{cap[0]}{cap[1]}0")
[/bash]

RTX 5090なら約32GB、sm_120と表示されます。エラーが出たらそのままClaude Codeに渡せば原因を特定できます。

■第5章：CI/CD自動化

▼GitHub ActionsによるCIワークフロー

[bash]
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt
    - run: pytest --tb=short
[/bash]

▼EC2へのCDワークフロー

[bash]
# .github/workflows/cd.yml
name: CD
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy via SSH
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ${{ secrets.EC2_USER }}
        key: ${{ secrets.AWS_SSH_PRIVATE_KEY }}
        script: |
          cd /home/ec2-user/app
          git pull origin main
          pip install -r requirements.txt
          pm2 restart app || pm2 start app.py --name app --interpreter python3
[/bash]

■まとめ

Claude Code + Opus 4.6の活用ポイント：

- CLAUDE.mdでプロジェクトルールを定義し、出力品質とコストを制御します
- エラーログ＋コードをセットで渡してデバッグを高速化します
- テストコード生成を自動化し、パラメータ化テストやモックまでカバーします
- CUDA/PyTorchのバージョン不整合はエラーメッセージをそのまま渡して解決します
- CI/CDワークフローの雛形生成で手動作業を削減します

エディタに縛られないCLIツールであるため、SSH先のサーバーやCI環境など、あらゆる場面で同じワークフローが使えます。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/claude-code-guide)*
