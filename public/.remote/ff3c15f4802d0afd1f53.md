---
title: Cloudflare Tunnel実践入門：自宅AIサーバーをポート開放なしでセキュアに公開する
tags:
  - WebDev
  - infrastructure
  - cloudflare
  - FastAPI
private: false
updated_at: '2026-03-21T21:41:11+09:00'
id: ff3c15f4802d0afd1f53
organization_url_name: null
slide: false
ignorePublish: false
---

■はじめに：RTX 5090の計算資源を活用する

AI開発者にとって、自宅のローカル環境は重要な実験場です。特に最新のRTX 5090を入手し、広大な32GB VRAMを自由に使える環境があるならば、それを自宅内だけに閉じ込めておくのは惜しいことです。外出先からスマホで生成AIのデモを確認したり、クライアントとのミーティングで自作のLLMアプリを即座に動かして見せたりしたいと思ったことはありませんか。

しかし、自宅サーバーをインターネットに公開しようとすると、従来は「ポート開放」という壁が立ちはだかりました。ルーターのNAT設定、ファイアウォールの穴あけ、ISPによるポート制限、そして固定IPアドレスの維持費。これらは開発の本質とは無関係なインフラ管理の負担であり、セキュリティリスクを抱え込むことにもなります。

そこで登場するのが「Cloudflare Tunnel」です。この技術は、自宅サーバーからCloudflareのエッジネットワークへ向けて、内側から外側へ（Outbound）接続を確立することでトンネルを作ります。外部からのアクセス（Inbound）用のポートを開ける必要はありません。CGNAT（キャリアグレードNAT）環境下でも、動的IPアドレスでも問題なく動作し、Cloudflareの強力なDDoS保護やWAFを無料で利用できます。

本記事では、接続手順に加えて「systemdを用いたサービスの永続化」や「Cloudflare Accessによる認証基盤の導入」について解説します。RTX 5090を搭載した自宅サーバー（Windows 11のWSL2環境など）を、セキュアで実用的なインフラとして構築しましょう。

■第1章：アーキテクチャと事前準備

Cloudflare Tunnelの中核は、サーバー内で動作する軽量なデーモン「cloudflared」です。これがCloudflareのグローバルネットワークと暗号化された接続を確立します。ユーザーがあなたのドメインにアクセスすると、リクエストはCloudflareのエッジで受け取られ、このトンネルを通って自宅サーバーへ転送されます。

▼必要なもの

- 独自ドメイン：CloudflareでDNS管理されている必要があります。ネームサーバーをCloudflareに向けた状態にしてください。
- 自宅サーバー：Linux（Ubuntu/Debian推奨）、macOS、またはWindows 11のWSL2 (Ubuntu) 環境。
- Cloudflareアカウント：無料プランで十分です。

▼cloudflaredのインストール

まずはデーモンをインストールします。ここではUbuntu環境を例に説明します。

以下のコマンドを実行してリポジトリを追加し、インストールを行います。


# 必要な依存関係のインストール
sudo apt-get update
sudo apt-get install -y curl lsb-release

# CloudflareのGPGキーを追加
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# リポジトリの追加
echo "deb https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# インストール
sudo apt-get update
sudo apt-get install cloudflared


インストールが完了したら、バージョンを確認して正常に入ったかチェックします。


cloudflared --version


■第2章：認証とトンネルの作成

認証ファイルの扱いは最初の躓きポイントです。特にヘッドレス環境やSSH経由で作業している場合、ブラウザ認証の連携で失敗することがあります。

▼認証と証明書の発行

以下のコマンドを実行すると、認証用URLが表示されます。


cloudflared tunnel login


表示されたURLをブラウザで開き、Cloudflareにログインして対象のドメインを選択し「Authorize」をクリックします。成功すると、ローカルに証明書ファイル「cert.pem」が生成されます。

もしSSH接続先のサーバーで作業している場合、URLをローカルPCのブラウザで開いて認証しても、サーバー側に証明書が自動転送されないことがあります。その場合、ブラウザに表示される「cert.pem」のダウンロードリンクからファイルを入手し、サーバーの「~/.cloudflared/cert.pem」へ手動で配置してください。

▼トンネルの作成

次に、トンネル自体を作成します。名前は管理しやすいものを付けてください（例: home-gpu-server）。


cloudflared tunnel create home-gpu-server


このコマンドが成功すると、トンネルID（UUID）が発行されます。このUUIDは後ほど設定ファイルで使用するため、控えておいてください。同時に、認証情報を含むJSONファイルが「~/.cloudflared/」配下に生成されます。

■第3章：設定ファイル「config.yml」の実装

コマンドライン引数で指定することも可能ですが、運用を考えると設定ファイル（config.yml）での管理が推奨されます。複数のサービス（例: Streamlitアプリ、FastAPI、SSH）を同時に公開する場合のルーティング設定もここで行います。

「~/.cloudflared/config.yml」を作成し、以下の内容を記述してください。UUIDやユーザー名はご自身の環境に合わせて書き換えてください。


# トンネルのUUID（createコマンドで発行されたもの）
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# 認証情報のパス
credentials-file: /home/your_user/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

# イングレスルール（上から順にマッチします）
ingress:
  # メインのAIアプリ（Streamlitなど）
  # サブドメイン: app.example.com
  - hostname: app.example.com
    service: http://localhost:8501

  # APIエンドポイント（FastAPIなど）
  # サブドメイン: api.example.com
  - hostname: api.example.com
    service: http://localhost:8000

  # SSHアクセス（ブラウザレンダリング）
  # サブドメイン: ssh.example.com
  - hostname: ssh.example.com
    service: ssh://localhost:22

  # デフォルトのルール（必須）
  # マッチしないリクエストは404を返す
  - service: http_status:404


▼DNSレコードの登録

設定ファイルで指定したホスト名（サブドメイン）を、CloudflareのDNSに登録してトンネルと紐付けます。CNAMEレコードが作成されます。


# アプリ用ドメインの紐付け
cloudflared tunnel route dns home-gpu-server app.example.com

# API用ドメインの紐付け
cloudflared tunnel route dns home-gpu-server api.example.com


■第4章：systemdによるサービスの永続化（自動起動設定）

開発中は手動で起動してもよいですが、継続的に運用するなら、OS起動時（WSL2環境の場合はsystemdを有効化した状態）に自動的にトンネルとアプリが立ち上がるように構成すると便利です。

▼cloudflaredのサービス化

cloudflaredにはサービスインストール機能が備わっています。


sudo cloudflared service install


これにより、設定ファイルが「/etc/cloudflared/config.yml」にコピーされ、systemdのサービスとして登録されます。もし先ほど作成したconfig.ymlがホームディレクトリにある場合は、以下のコマンドで所定の位置にコピーしてください。


sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
sudo cp ~/.cloudflared/cert.pem /etc/cloudflared/


サービスを起動します。


sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared


▼アプリケーション（Streamlit）のサービス化

トンネルだけ起動しても、中身のアプリが動いていなければ意味がありません。StreamlitなどのPythonアプリもsystemdで管理しましょう。以下は、パッケージマネージャ「uv」などで構築した仮想環境（.venv）を使用したアプリのサービス定義ファイルの例です。

「/etc/systemd/system/ai-app.service」というファイルを作成します。



Description=AI Streamlit App
# ネットワークとトンネルの準備完了を待つ
After=network.target cloudflared.service


Type=simple
# 実行ユーザーを指定
User=your_user
WorkingDirectory=/home/your_user/projects/my-ai-app
# パス環境変数の設定（仮想環境のbinを含める）
Environment="PATH=/home/your_user/projects/my-ai-app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
# アプリ起動コマンド
ExecStart=/home/your_user/projects/my-ai-app/.venv/bin/streamlit run src/main.py --server.port 8501 --server.headless true
# クラッシュ時の自動再起動設定
Restart=always
RestartSec=3


WantedBy=multi-user.target


作成後、systemdに認識させて起動します。


sudo systemctl daemon-reload
sudo systemctl enable ai-app
sudo systemctl start ai-app


これで、サーバーの電源を入れるだけで、Cloudflare TunnelとAIアプリが自動的に立ち上がり、外部からアクセスできる状態になります。

■第5章：Cloudflare Accessによるセキュアなアクセス制御

ポート開放不要とはいえ、Web上に公開すれば誰でもアクセスできてしまいます。開発中のアプリを他人に見られたくない場合、Cloudflare Access（Zero Trust）を使って認証画面を挟むことができます。これも無料枠で利用可能です。

1. Cloudflare Zero Trustダッシュボード（https://one.dash.cloudflare.com/）にアクセスします。
2. 「Access」→「Applications」→「Add an application」を選択します。
3. 「Self-hosted」を選び、公開したサブドメイン（例: app.example.com）を入力します。
4. ポリシー設定で、アクセスを許可する条件を設定します。
   ・Rule action: Allow
   ・Include: Emails - あなたのメールアドレス
5. 保存して適用します。

これで、あなたのアプリにアクセスすると、Cloudflareが提供するログイン画面が表示されるようになります。指定したメールアドレスに届くコードを入力しない限り、トンネルの先にある自宅サーバーにはパケットが届きません。Basic認証などよりも強固で、アプリ側に認証機能を実装する手間も省けます。

■まとめ：インフラ管理を効率化し開発に集中する

以上の手順で、RTX 5090の32GB VRAMを搭載した自宅サーバーを、セキュアかつ安定した状態で公開することができました。

- ポート開放：不要
- 固定IP：不要
- SSL証明書：Cloudflareが自動管理
- DDoS対策：標準装備
- 認証機能：Cloudflare Accessで後付け可能

この構成により、運用の手間を大幅に減らすことができます。インフラ管理の負担を軽減し、本来の目的であるAI/LLMアプリケーションの開発に注力してください。

エラーが発生した際は、以下のコマンドでリアルタイムログを確認することができます。


# トンネルのログ確認
sudo journalctl -u cloudflared -f

# アプリのログ確認
sudo journalctl -u ai-app -f


自宅サーバーの可能性は広がります。安全なインフラを構築し、開発を加速させましょう。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/web-infra/080_premium)*
