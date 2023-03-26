ChatGPT client



# Usage

```
memory_chat_digest.py [-h] [--character CHARACTER] [--voice] [--speaker SPEAKER] [--yaml YAML]

ChatGPT client

optional arguments:
  -h, --help            show this help message and exit
  --character CHARACTER, -c CHARACTER
                        AIキャラクタ指定(default=ChatGPT)
  --voice, -v           AI音声の生成先 (-v=SLOW, -vv=FAST, -vvv=LOCAL, default=None = 音声で話さない)
  --speaker SPEAKER, -s SPEAKER
                        VOICEVOX キャラクターボイス(str or int, default None)
  --yaml YAML, -y YAML  AIカスタム設定YAMLのファイルパス
```




# Installation

# Requirements

* pydub>=0.25.1
* PyYAML>=6.0
* requests>=2.28.1
