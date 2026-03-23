---
title: "RemotionとVOICEVOXを用いた動画生成の自動化：環境構築からパフォーマンス最適化まで"
emoji: "🔧"
type: "tech"
topics: ["webdev", "fastapi", "infrastructure", "cloudflare"]
published: false
canonical_url: "https://media.patentllm.org/blog/web-infra/mega-remotion"
---

■はじめに：動画生成の自動化へのアプローチ

Remotionで動画をプログラム的に生成しようとした際、ffmpegやffprobeのダウンロードが終わらない、あるいはプロセスが停止するといった問題に直面することがあります。

AIやLLMの進化は、コンテンツ制作のプロセスを大きく変えつつあります。これまで動画制作は、スクリプト作成から編集、音声合成、レンダリングに至るまで多くの時間と専門知識を必要としました。しかし、AI技術の成熟により、動画制作の障壁は下がりつつあり、プログラムによる動画の自動生成が現実的な選択肢となっています。

本記事では、Reactベースの動画生成フレームワーク「Remotion」と、音声合成エンジン「VOICEVOX」、そして「Cursor AI」や「Gemini 3.1 Pro」などのAIツールを組み合わせた動画生成システムの構築方法を解説します。実際の開発で直面したレンダリングのエラーや、パフォーマンスチューニングの手法について紹介します。

環境構築からコードの実装、そしてRTX 5090（VRAM 32GB）のようなハイエンド環境を見据えた最適化まで、実用的な知見をまとめました。

■第1章：Remotionによる動画生成の利点

Remotionは、Reactコンポーネントを用いて動画をプログラム的に生成できるライブラリです。従来のGUIベースの動画制作ツールとは異なり、JavaScriptやTypeScript、HTML、CSSを使って動画をコードとして記述できます。

コードベースの動画生成の利点として、自動化とスケーラビリティが挙げられます。データソースから情報を取得し、テンプレートとなるReactコンポーネントに流し込むことで、パーソナライズされた動画を効率的に生成できます。

また、バージョン管理と再利用性も利点です。コードとして動画を記述するため、Gitなどで変更履歴を追跡し、チームでの共同作業が容易になります。作成したコンポーネントは他のプロジェクトでも再利用でき、ReactやTypeScriptなどのWeb開発スキルをそのまま活かすことができます。

■第2章：開発環境の準備とハードウェア要件

本格的な実装に入る前に、必要な環境とツールを整えましょう。動画生成は計算リソースを消費するため、ハードウェアの選定も重要です。

▼ハードウェア要件と推奨スペック
動画のレンダリングは、GPUのVRAM容量とCPUのコア数がパフォーマンスに影響します。
例えば、RTX 5090（VRAM 32GB）のようなハイエンドGPUを使用すると、Remotionでの並列レンダリングや、同時にAIモデルを動かすワークフローにおいて高いパフォーマンスを発揮します。VRAMが多いほど、より多くのフレームを一度にメモリに展開でき、レンダリングの並列数を上げることが可能です。Apple Silicon搭載のMacでも開発は可能ですが、サーバーサイドでの大規模なレンダリングにおいては、VRAM容量とCUDAコア数が重要になります。

▼必須ツールのインストール
以下のツールを事前にインストールしてください。

- Node.js & npm: Remotionの動作基盤です。LTSバージョンの利用を推奨します。
- Python 3: VOICEVOX EngineのAPIを制御するために使用します。
- FFmpeg: 動画のエンコードに必須です。パスを通しておくことを忘れずに。
- VOICEVOX Engine: アプリ版ではなく、エンジンのコア部分をダウンロードし、ローカルサーバーとして起動できるようにします。
- Cursor AI: 本記事では開発効率を上げるために、AI搭載エディタであるCursorを使用します。

▼Remotionプロジェクトの初期化
まずは基本的なプロジェクトを作成します。ターミナルで以下のコマンドを実行してください。


npx create-video@latest


プロジェクト名は「my-tech-video」とし、テンプレートを選択します。作成されたディレクトリに移動し、依存関係をインストールします。


cd my-tech-video
npm install


ここで、VOICEVOXとの連携や型定義のために追加のパッケージもインストールしておきます。


npm install zod
npm install -D ts-node @types/zod


これで土台は整いました。

■第3章：直面した3つの罠と解決策

Remotionでの開発において、実際に遭遇した3つの問題と解決策を共有します。

▼罠1：ffmpeg/ffprobeの無限ダウンロード地獄
レンダリングコマンドを実行すると、Remotionは必要なバイナリを自動でダウンロードしようとします。しかし、ネットワーク環境によっては、このダウンロードが進まない現象が発生することがあります。


Downloading ffmpeg 0 Mb/74.9 Mb
...


ログがこのように表示され進まない場合、手動でのインストールとパス設定が有効です。Remotionの設定ファイル（remotion.config.ts）でバイナリのパスを明示的に指定することで、自動ダウンロードを回避できます。Gemini 3.1 Proに相談したところ、環境変数の設定やパス指定が有効であるとの助言を得ました。

▼罠2：「19万フレーム」の誤読
レンダリングを開始した直後、ターミナルに以下のようなログが表示されることがあります。


(2/3) Rendering frames (2x) 1821/191504/public/audio/yu


この数字を見ると膨大な時間がかかるように感じますが、これは総フレーム数ではなく、内部的な処理カウンターや一時ファイルのパスの一部を含んだ表示である場合があります。
正しいフレーム数やデュレーションを確認するには、以下のコマンドを使用します。


npx remotion preview


プレビュー画面で正確な時間を確認することが重要です。

▼罠3：YouTubeアップロード後のコメント不可設定
生成した動画をYouTubeにアップロードした際、コメント欄が有効にならない現象に遭遇しました。
原因は「子ども向けコンテンツ（COPPA）」の設定でした。API経由やアップロード時の設定で、誤って「子ども向け」としてマークされると、YouTubeの仕様によりコメント機能が強制的に無効化されます。プラットフォームのポリシーによる挙動ですが、設定を見直すことで解決します。

■第4章：VOICEVOX連携による音声自動生成の実装

RemotionとVOICEVOXを連携させ、テキストから音声を生成し、それに合わせて動画を作るシステムを構築します。

▼Pythonによる音声生成スクリプト
VOICEVOX EngineのAPIを呼び出して音声を生成するPythonスクリプトを作成します。

プロジェクトルートに scripts ディレクトリを作成し、voicevox_api.py を配置します。


import requests
import json
import os
import sys
import wave

# VOICEVOX EngineのURL（デフォルトポート）
VOICEVOX_ENGINE_URL = "http://localhost:50021"

def get_audio_duration_from_file(file_path: str) -> float:
    """WAVファイルの長さを秒単位で取得する"""
    try:
        with wave.open(file_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        print(f"Error getting audio duration for {file_path}: {e}", file=sys.stderr)
        return 0.0

def generate_audio(text: str, speaker_id: int, output_path: str) -> float:
    """
    VOICEVOX Engineを使ってテキストから音声を生成し、WAVファイルとして保存する。
    生成された音声の長さを秒単位で返す。
    """
    try:
        # 1. audio_query を取得
        query_params = {"text": text, "speaker": speaker_id}
        audio_query_response = requests.post(
            f"{VOICEVOX_ENGINE_URL}/audio_query",
            params=query_params,
            timeout=10
        )
        audio_query_response.raise_for_status()
        audio_query = audio_query_response.json()

        # 2. synthesis を実行
        synthesis_params = {"speaker": speaker_id}
        synthesis_response = requests.post(
            f"{VOICEVOX_ENGINE_URL}/synthesis",
            headers={"Content-Type": "application/json"},
            params=synthesis_params,
            data=json.dumps(audio_query),
            timeout=30
        )
        synthesis_response.raise_for_status()

        # 3. 音声データを保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(synthesis_response.content)

        # 4. 生成された音声の長さを取得して返す
        return get_audio_duration_from_file(output_path)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        text = sys.argv
        speaker_id = int(sys.argv)
        output_path = sys.argv
        duration = generate_audio(text, speaker_id, output_path)
        print(duration)
        sys.exit(0)
    elif len(sys.argv) == 2:
        file_path = sys.argv
        duration = get_audio_duration_from_file(file_path)
        print(duration)
        sys.exit(0)
    else:
        sys.exit(1)


▼Node.jsからの呼び出しとアセット準備
RemotionのビルドプロセスからこのPythonスクリプトを呼び出し、動画に必要なアセットを準備するTypeScriptコードを実装します。

src/server/generate-voice.ts を作成します。


import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

export const generateVoice = (text: string, speakerId: number, outputPath: string): Promise<number> => {
    return new Promise((resolve, reject) => {
        const pythonScriptPath = path.join(process.cwd(), 'scripts', 'voicevox_api.py');
        fs.mkdir(path.dirname(outputPath), { recursive: true }).catch(reject);

        const pythonProcess = spawn('python',);
        let stdoutData = '';
        let stderrData = '';

        pythonProcess.stdout.on('data', (data) => { stdoutData += data.toString(); });
        pythonProcess.stderr.on('data', (data) => { stderrData += data.toString(); });

        pythonProcess.on('close', (code) => {
            if (code === 0) {
                const duration = parseFloat(stdoutData.trim());
                if (!isNaN(duration)) {
                    resolve(duration);
                } else {
                    reject(new Error(`Failed to parse duration: ${stdoutData}`));
                }
            } else {
                reject(new Error(`Python script exited with code ${code}: ${stderrData}`));
            }
        });
    });
};


さらに、動画の内容を定義する src/content.json を読み込み、一括で音声を生成する prepareAssets 関数を実装します。


import { generateVoice } from './generate-voice';
import path from 'path';
import fs from 'fs/promises';
import { z } from 'zod';

const contentSectionSchema = z.object({
    id: z.string(),
    text: z.string(),
    speakerId: z.number(),
    durationSeconds: z.number(),
});

export const preparedSectionSchema = contentSectionSchema.extend({
    audioPath: z.string(),
    durationInFrames: z.number(),
});

export type PreparedSection = z.infer<typeof preparedSectionSchema>;
const contentData = require('../../content.json');
const OUTPUT_AUDIO_DIR = path.join(process.cwd(), 'public', 'audio');

export const prepareAssets = async (fps: number = 30): Promise<PreparedSection[]> => {
    console.log('--- Preparing assets ---');
    const preparedSections: PreparedSection[] = [];

    for (const of contentData.entries()) {
        const audioFileName = `section${index}-${section.id}.wav`;
        const outputPath = path.join(OUTPUT_AUDIO_DIR, audioFileName);
        const relativeAudioPath = `audio/${audioFileName}`;

        try {
            let durationSeconds: number;
            const exists = await fs.stat(outputPath).then(() => true).catch(() => false);
            
            if (exists) {
                durationSeconds = await generateVoice(section.text, section.speakerId, outputPath); 
            } else {
                durationSeconds = await generateVoice(section.text, section.speakerId, outputPath);
            }

            const durationInFrames = Math.ceil(durationSeconds * fps);
            preparedSections.push({
                ...section,
                audioPath: relativeAudioPath,
                durationInFrames,
            });
        } catch (error) {
            console.warn(`Failed to generate audio for ${section.id}, using fallback.`);
            preparedSections.push({
                ...section,
                audioPath: relativeAudioPath,
                durationInFrames: section.durationSeconds * fps,
            });
        }
    }
    return preparedSections;
};


▼Remotion設定ファイルへの統合
remotion.config.ts を編集し、バンドル時にアセット生成を実行するように設定します。


import { Config } from '@remotion/cli/config';
import { prepareAssets } from './src/server/prepare-assets';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);

export const remotionConfig = Config.defineConfig({
    bundle: async (config) => {
        const fps = 30;
        const sections = await prepareAssets(fps);
        
        // 生成されたセクション情報をコンポジションのデフォルトPropsとして注入する処理などを記述
        return config;
    },
});


■第5章：レンダリング設定とパフォーマンスチューニング

動画レンダリングはCPUとメモリを消費するため、適切な設定を行うことが重要です。

▼ボトルネックの特定と計測
Remotionの renderMedia 関数を使ってプログラム的にレンダリングを実行し、時間を計測します。


import { renderMedia, getCompositions } from '@remotion/renderer';
import path from 'path';
import os from 'os';

const start = async () => {
    const startTime = process.hrtime.bigint();
    
    const bundle = await getCompositions({
        entry: path.join(__dirname, './Root.tsx'),
    });
    const composition = bundle.find((c) => c.id === 'MyVideo');
    if (!composition) throw new Error('Composition not found');

    const concurrency = Math.max(1, os.cpus().length - 1);
    
    await renderMedia({
        composition,
        outputLocation: path.join(__dirname, '../out/video.mp4'),
        codec: 'h264',
        crf: 28,
        preset: 'fast',
        concurrency,
        logLevel: 'info',
    });

    const endTime = process.hrtime.bigint();
    const duration = Number(endTime - startTime) / 1_000_000_000;
    console.log(`Render finished in ${duration.toFixed(2)}s`);
};
start();


▼Reactコンポーネントのメモ化
RemotionはReact上で動作するため、不要な再レンダリングを防ぐことがパフォーマンス向上に繋がります。React.memo や useMemo を活用します。


const MemoizedCircle: React.FC<CircleProps> = React.memo(({ cx, cy, r, fill }) => {
    return <circle cx={cx} cy={cy} r={r} fill={fill} />;
});

const staticItems = React.useMemo(() => {
    return Array.from({ length: 1000 }).map((_, i) => ({ id: i }));
}, []);


▼並列レンダリングとVRAMの活用
concurrency オプションを設定することで、マルチスレッドレンダリングが可能です。RTX 5090（VRAM 32GB）のような環境であれば、並列数を増やしてもメモリ不足に陥りにくく、高速なレンダリングが可能です。VRAMが少ない環境では、並列数を下げて安定性を優先します。

▼FFmpeg設定の最適化
crf と preset の設定で、画質とエンコード時間のバランスを調整します。
- crf: デフォルトは23。数値を上げると（例：28）ファイルサイズが小さくなり、エンコードが速くなります。
- preset: ultrafast, superfast, fast, medium, slow などがあります。テスト段階では ultrafast、本番では medium や slow の使い分けが推奨されます。

■第6章：Cursor AIを活用した開発効率化

開発において、Cursor AIやClaude Opus 4.6などのAIモデルを活用することで、FFmpegオプションの調査やエラーログの解析を効率化できます。

▼AIへの具体的な指示出し（プロンプト例）
AIに対しては、以下のように具体的なコンテキストを与えて指示を出すことで、精度の高い回答が得られます。

「Node.jsのTypeScriptで、Pythonスクリプトをchild_processモジュールを使って呼び出し、標準出力から数値（音声の長さ）を受け取る関数を実装してください。エラーハンドリングとPromiseベースの非同期処理を含めてください。」

このように依頼することで、堅牢なコードを迅速に作成できます。また、パフォーマンスチューニングの際にも、「このReactコンポーネントの再レンダリングを抑制するための改善案を提示して」と尋ねることで、React.memo の適用箇所を指摘してもらえます。

■まとめ：動画生成の自動化に向けて

本記事では、RemotionとVOICEVOXを組み合わせた動画生成システムの構築から、パフォーマンスチューニングまでを解説しました。
動画生成の自動化は、パーソナライズされた動画の生成や、データに基づいた動画配信など、新たな可能性を広げます。

適切なツールとAIを活用し、RTX 5090のようなハードウェア環境を整えることで、開発体験はさらに向上します。

【技術スタックまとめ】
- フレームワーク: Remotion, React
- 言語: TypeScript, Python
- 音声合成: VOICEVOX Engine
- 開発ツール: Cursor AI, VS Code
- インフラ: Node.js, FFmpeg
- 推奨ハードウェア: RTX 4090/5090 (VRAM 24GB/32GB), マルチコアCPU

■補足：トラブルシューティング・チェックリスト

開発中に遭遇しやすい問題とその解決策です。

- レンダリングが途中で止まる
→ メモリ不足の可能性があります。concurrency（並列数）を減らしてください。
→ VRAM不足の場合、GPUを使用する処理を見直すか、ハードウェアのアップグレードを検討してください。

- 音声と映像がズレる
→ fps の設定がプロジェクト全体で統一されているか確認してください。
→ 音声ファイルのサンプリングレートが適切か確認してください（通常は44.1kHzまたは48kHz）。

- 生成された動画の画質が悪い
→ renderMedia の crf 値を下げてみてください（例：28 -> 20）。
→ ビットレート設定を明示的に行うことも有効です。
