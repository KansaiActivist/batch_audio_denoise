# batch_audio_denoise
音声からノイズを除去
## 導入手順（Windows）

### 手順1：必要なソフトをインストール

Python 3.11 または 3.12 を推奨します。

PowerShell またはコマンドプロンプトで実行します。

```
python -m pip install numpy soundfile noisereduce tqdm
```

次に、音声形式の変換に必要な FFmpeg をインストールします。

```
winget install Gyan.FFmpeg
```

インストール後、ターミナルを再起動して確認します。

```
ffmpeg -version
```

バージョン情報が表示されれば準備完了です。

### 手順2：フォルダを準備

例えば、以下のように配置します。

```
AudioProject/
├── batch_audio_denoise.py
├── input/
│   ├── voice01.wav
│   ├── voice02.mp3
│   ├── voice03.flac
│   └── voice04.m4a
└── output/
```

### 手順3：一括処理を実行

スクリプトのあるフォルダで、次のコマンドを実行します。

```
python batch_audio_denoise.py input output
```

処理結果は `output` フォルダに WAV 形式で保存されます。

## 3. ノイズ除去の強さを調整

| コマンド | 用途 |
| --- | --- |
| `--strength 0.4` | 声の自然さを優先 |
| `--strength 0.6` | 軽めのノイズ除去 |
| `--strength 0.8` | 標準設定 |
| `--strength 1.0` | 強めのノイズ除去 |

例えば、会話やセリフの音声なら、まずは次の設定を試してください。

```
python batch_audio_denoise.py input output --strength 0.6
```

サブフォルダも含めて処理する場合：

```
python batch_audio_denoise.py input output --recursive --strength 0.6
```

## 4. 注意点

- この方式は、空調音や一定の背景ノイズなどの軽減に向いています。
- 大きな雑音、他人の声、音楽が混ざった音声では、完全には除去できません。
- 除去を強くしすぎると、声が金属的になったり、子音が欠けたりすることがあります。
- 出力は WAV 形式です。入力が MP3 でも、元と同じ拡張子にはなりません。
