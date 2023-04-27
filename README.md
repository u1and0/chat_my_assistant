![gif](https://camo.qiitausercontent.com/22fc840e1ae8928fa4f6fee920cab44d82465fc4/68747470733a2f2f71696974612d696d6167652d73746f72652e73332e61702d6e6f727468656173742d312e616d617a6f6e6177732e636f6d2f302f3131333439342f30386332616432372d303439632d643135332d616231652d3032666164643034393233632e676966)

This is a command-line interface (CLI) client for ChatGPT, which allows you to have a conversation with ChatGPT through your console. The client is compatible with the GPT-3.5-turbo model and can summarize and store the conversation. Additionally, it provides an option to assume the role of a specific character during the conversation and even has an optional feature to respond to ChatGPT's replies with voice.


# Features
* コンソールでChatGPTと対話するAPIクライアント
* model gpt-3.5-turbo対応
* 会話を要約して記憶する
* 自身が指定したキャラクターになりきって話せる(optional)
* ChatGPTからの返答を音声で発する(optinal)

* Allows you to converse with ChatGPT through the command line interface
* Compatible with the GPT-3.5-turbo model
* Summarizes and stores conversations
* Optional character role-play mode
* Optional voice response feature to ChatGPT's replies

[![chat_my_assistant hello world](https://user-images.githubusercontent.com/16408916/229843758-86d7a411-0528-4ff6-85e8-aebb3097526f.png)](https://www.youtube.com/embed/KWh5uhvWWgQ)


# Usage

Run the application using python chatgpt.py.

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

```
$ git clone https://github.com/u1and0/chat_my_assistant
$ cd chat_my_assistant
$ pip install -r requirements.txt
$ sudo ln -s /home/your_name/path/to/chat_my_assistant/chatme.py /usr/bin/chatme
```

# Setting
* ChatGPT API用

```~/.secret
#!/bin/sh
export CHATGPT_API_KEY='sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' \
        GITHUB_TOKEN='ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' \
        GIST_ID='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' \
        VOICEVOX_API_KEY='XXXXXXXXXXXXXXX' \
        GIST_CLIENT_ID='XXXXXXXXXXXXXXXXXXXX' \
        GIST_CLIENT_SECRET='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
```

# Requirements

* requests>=2.28.1
* openai API key
* aiohttp>=3.8.1
* tiktoken>=0.3.3

# Optional

## 音声を出したいとき
* pydub>=0.25.1
* Install VOICEVOX
* VOICEVOX API key

## 音声を聞かせたいとき
* speechrecognition>=3.10.0

## 記憶させたいとき
* PyYAML>=6.0
* Git(Gist) API key


see more [ChatGPTに人格と記憶と声を持たせて話し相手になってもらう](https://qiita.com/1446f763aaf2a8b0c804)


# LICENCE
This project is licensed under the MIT License. See the [LICENSE](https://raw.githubusercontent.com/u1and0/chat_my_assistant/main/LICENSE) file for more details.
