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

<iframe width="560" height="315" src="https://www.youtube.com/embed/KWh5uhvWWgQ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>


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
Clone the repository to your local machine.
Install the necessary dependencies using pip install -r requirements.txt.

# Requirements

* pydub>=0.25.1
* PyYAML>=6.0
* requests>=2.28.1
* openai API key

# Optional

* Git(Gist) API key
* VOICEVOX
* VOICEVOX API key


see more [ChatGPTに人格と記憶と声を持たせて話し相手になってもらう](https://qiita.com/drafts/1446f763aaf2a8b0c804)


# LICENCE
This project is licensed under the MIT License. See the LICENSE file for more details.
