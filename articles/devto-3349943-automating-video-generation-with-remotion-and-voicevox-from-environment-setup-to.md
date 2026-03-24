---
title: "Automating Video Generation with Remotion and VOICEVOX: From Environment Setup to Performance Optimization"
date: 2026-03-14
topics: ["webdev", "devops", "infrastructure"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/web-infra/mega-remotion"
devto_url: "https://dev.to/soytuber/automating-video-generation-with-remotion-and-voicevox-from-environment-setup-to-performance-4kbh"
devto_id: 3349943
---

## Introduction: An Approach to Automating Video Generation

When attempting to generate videos programmatically with Remotion, you may encounter issues such as ffmpeg or ffprobe downloads never finishing, or processes stalling.

The evolution of AI and LLMs is significantly changing the content creation process. Historically, video production required extensive time and specialized knowledge, from scriptwriting to editing, speech synthesis, and rendering. However, with the maturation of AI technology, the barriers to video production are lowering, making programmatic automated video generation a realistic option.

This article explains how to build a video generation system combining the React-based video generation framework "Remotion," the speech synthesis engine "VOICEVOX," and AI tools like "Cursor AI" and "Gemini 3.1 Pro." We will introduce rendering errors encountered during actual development and performance tuning techniques.

From environment setup to code implementation, and optimization aimed at high-end environments like the RTX 5090 (32GB VRAM), we've summarized practical insights.

## Chapter 1: Advantages of Video Generation with Remotion

Remotion is a library that allows you to generate videos programmatically using React components. Unlike traditional GUI-based video production tools, you can describe videos as code using JavaScript, TypeScript, HTML, and CSS.

The advantages of code-based video generation include automation and scalability. By fetching information from data sources and pouring it into React components acting as templates, you can efficiently generate personalized videos.

Additionally, version control and reusability are benefits. Because the video is described as code, you can track change history with Git and facilitate team collaboration. Created components can be reused in other projects, and you can leverage Web development skills like React and TypeScript directly.

## Chapter 2: Preparing the Development Environment and Hardware Requirements

Before jumping into full-scale implementation, let's prepare the necessary environment and tools. Since video generation consumes computational resources, hardware selection is also critical.

### Hardware Requirements and Recommended Specs
Video rendering performance is affected by GPU VRAM capacity and CPU core count.
For example, using a high-end GPU like the RTX 5090 (32GB VRAM) demonstrates high performance in parallel rendering with Remotion or workflows running AI models simultaneously. The more VRAM you have, the more frames you can expand into memory at once, allowing for a higher number of parallel rendering tasks. While development is possible on Macs with Apple Silicon, VRAM capacity and CUDA core count become crucial for large-scale server-side rendering.

### Installing Essential Tools
Please install the following tools in advance.

- Node.js & npm: The execution foundation for Remotion. LTS versions are recommended.
- Python 3: Used to control the VOICEVOX Engine API.
- FFmpeg: Essential for video encoding. Don't forget to set the path.
- VOICEVOX Engine: Download the core engine part, not the app version, so it can be started as a local server.
- Cursor AI: In this article, we will use Cursor, an AI-equipped editor, to improve development efficiency.

### Initializing the Remotion Project
First, create a basic project. Run the following command in your terminal.

```bash
npx create-video@latest
```

Name the project "my-tech-video" and select a template. Move to the created directory and install dependencies.

```bash
cd my-tech-video
npm install
```

Here, we also install additional packages for integrating with VOICEVOX and type definitions.

```bash
npm install zod
npm install -D ts-node @types/zod
```

The foundation is now set.

## Chapter 3: Three Traps Encountered and Their Solutions

We will share three actual problems encountered during development with Remotion and their solutions.

### Trap 1: The Infinite ffmpeg/ffprobe Download Hell
When executing a rendering command, Remotion automatically tries to download required binaries. However, depending on the network environment, this download might stall.

```bash
Downloading ffmpeg 0 Mb/74.9 Mb
...
```

If the log displays this and does not progress, manual installation and path configuration are effective. By explicitly specifying the binary paths in the Remotion configuration file (`remotion.config.ts`), you can bypass the automatic download. After consulting Gemini 3.1 Pro, I was advised that setting environment variables or specifying paths is an effective solution.

### Trap 2: Misreading "190,000 Frames"
Immediately after starting a render, you might see a log like this in the terminal:

```bash
(2/3) Rendering frames (2x) 1821/191504/public/audio/yu
```

Seeing these numbers might make you feel it will take an enormous amount of time, but this may not be the total frame count; it can sometimes include internal processing counters or parts of temporary file paths.
To check the correct frame count and duration, use the following command:

```bash
npx remotion preview
```

It's important to verify the accurate time on the preview screen.

### Trap 3: Comments Disabled After YouTube Upload
I encountered an issue where the comments section was disabled after uploading the generated video to YouTube.
The cause was the "Made for Kids (COPPA)" setting. If mistakenly marked as "Made for Kids" via API or upload settings, YouTube's platform policy forcibly disables the comment feature. Adjusting the settings resolves this issue.

## Chapter 4: Implementing Automated Speech Generation via VOICEVOX Integration

We will link Remotion with VOICEVOX to build a system that generates speech from text and creates a video to match.

### Python Script for Speech Generation
Create a Python script that calls the VOICEVOX Engine API to generate speech.

Create a `scripts` directory in the project root and place `voicevox_api.py` inside.

```python
import requests
import json
import os
import sys
import wave

# VOICEVOX Engine URL (Default port)
VOICEVOX_ENGINE_URL = "http://localhost:50021"

def get_audio_duration_from_file(file_path: str) -> float:
    """Get the duration of a WAV file in seconds"""
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
    Generate speech from text using VOICEVOX Engine and save it as a WAV file.
    Returns the duration of the generated audio in seconds.
    """
    try:
        # 1. Get audio_query
        query_params = {"text": text, "speaker": speaker_id}
        audio_query_response = requests.post(
            f"{VOICEVOX_ENGINE_URL}/audio_query",
            params=query_params,
            timeout=10
        )
        audio_query_response.raise_for_status()
        audio_query = audio_query_response.json()

        # 2. Execute synthesis
        synthesis_params = {"speaker": speaker_id}
        synthesis_response = requests.post(
            f"{VOICEVOX_ENGINE_URL}/synthesis",
            headers={"Content-Type": "application/json"},
            params=synthesis_params,
            data=json.dumps(audio_query),
            timeout=30
        )
        synthesis_response.raise_for_status()

        # 3. Save audio data
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(synthesis_response.content)

        # 4. Get and return the duration of generated audio
        return get_audio_duration_from_file(output_path)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        text = sys.argv[1]
        speaker_id = int(sys.argv[2])
        output_path = sys.argv[3]
        duration = generate_audio(text, speaker_id, output_path)
        print(duration)
        sys.exit(0)
    elif len(sys.argv) == 2:
        file_path = sys.argv[1]
        duration = get_audio_duration_from_file(file_path)
        print(duration)
        sys.exit(0)
    else:
        sys.exit(1)
```

### Calling from Node.js and Preparing Assets
Implement TypeScript code that calls this Python script from Remotion's build process to prepare necessary assets for the video.

Create `src/server/generate-voice.ts`.

```typescript
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

export const generateVoice = (text: string, speakerId: number, outputPath: string): Promise<number> => {
    return new Promise((resolve, reject) => {
        const pythonScriptPath = path.join(process.cwd(), 'scripts', 'voicevox_api.py');
        fs.mkdir(path.dirname(outputPath), { recursive: true }).catch(reject);

        const pythonProcess = spawn('python', [pythonScriptPath, text, speakerId.toString(), outputPath]);
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
```

Furthermore, implement a `prepareAssets` function that reads `src/content.json` defining the video content and batch-generates audio.

```typescript
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

    for (const [index, section] of contentData.entries()) {
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
```

### Integrating with Remotion Configuration File
Edit `remotion.config.ts` to configure asset generation during the bundle phase.

```typescript
import { Config } from '@remotion/cli/config';
import { prepareAssets } from './src/server/prepare-assets';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);

export const remotionConfig = Config.defineConfig({
    bundle: async (config) => {
        const fps = 30;
        const sections = await prepareAssets(fps);
        
        // Describe processes such as injecting generated section info as default Props for compositions
        return config;
    },
});
```

## Chapter 5: Rendering Settings and Performance Tuning

Since video rendering consumes CPU and memory, configuring proper settings is crucial.

### Identifying Bottlenecks and Measurement
Use Remotion's `renderMedia` function to programmatically execute rendering and measure the time.

```typescript
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
```

### Memoization of React Components
Because Remotion operates on React, preventing unnecessary re-renders leads to performance improvements. Utilize `React.memo` and `useMemo`.

```typescript
const MemoizedCircle: React.FC<CircleProps> = React.memo(({ cx, cy, r, fill }) => {
    return <circle cx={cx} cy={cy} r={r} fill={fill} />;
});

const staticItems = React.useMemo(() => {
    return Array.from({ length: 1000 }).map((_, i) => ({ id: i }));
}, []);
```

### Parallel Rendering and Utilizing VRAM
By setting the `concurrency` option, multi-threaded rendering is possible. With environments like the RTX 5090 (32GB VRAM), you can increase parallel count without easily running out of memory, enabling high-speed rendering. In low-VRAM environments, prioritize stability by lowering the parallel count.

### Optimizing FFmpeg Settings
Adjust the balance between image quality and encode time via `crf` and `preset` settings.
- crf: Default is 23. Increasing this value (e.g., 28) reduces file size and speeds up encoding.
- preset: Options include ultrafast, superfast, fast, medium, slow, etc. It is recommended to use ultrafast during testing, and medium or slow for production.

## Chapter 6: Improving Development Efficiency with Cursor AI

During development, utilizing AI models like Cursor AI or Claude Opus 4.6 can streamline investigating FFmpeg options and parsing error logs.

### Giving Specific Instructions to AI (Prompt Examples)
When dealing with AI, providing specific context and instructions yields highly accurate answers.

"In Node.js TypeScript, implement a function that uses the `child_process` module to call a Python script and receives a number (audio duration) from standard output. Include error handling and Promise-based asynchronous processing."

By requesting this way, you can rapidly build robust code. Also, during performance tuning, asking "Suggest improvements to prevent re-rendering of this React component" will get pointers on where to apply `React.memo`.

## Conclusion: Toward Automated Video Generation

In this article, we covered everything from building a video generation system combining Remotion and VOICEVOX to performance tuning.
Automating video generation opens new possibilities, such as generating personalized videos and data-driven video distribution.

By utilizing appropriate tools and AI, and setting up hardware environments like the RTX 5090, the development experience improves even further.

[Technology Stack Summary]
- Framework: Remotion, React
- Language: TypeScript, Python
- Speech Synthesis: VOICEVOX Engine
- Development Tools: Cursor AI, VS Code
- Infrastructure: Node.js, FFmpeg
- Recommended Hardware: RTX 4090/5090 (VRAM 24GB/32GB), Multi-core CPU

## Supplement: Troubleshooting Checklist

Common problems encountered during development and their solutions.

- Rendering stops midway
-> Possible memory shortage. Reduce `concurrency` (parallel count).
-> If it's a VRAM shortage, review GPU-utilizing processes or consider upgrading hardware.

- Audio and Video are out of sync
-> Ensure `fps` settings are consistent across the entire project.
-> Verify the audio file's sampling rate is appropriate (usually 44.1kHz or 48kHz).

- Generated video has poor quality
-> Try lowering the `crf` value in `renderMedia` (e.g., 28 -> 20).
-> Explicitly setting the bitrate is also effective.
