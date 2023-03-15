"""ChatGPTに複数回の質問と回答
会話を要約して短期的に記憶する
過去の会話を長期記憶としてのgistから取得し、
要約した会話履歴を長期記憶としてgistへ保存する
"""
import os
import json
import requests
from gist_memory import Gist

api_key = os.getenv("CHATGPT_API_KEY")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
filename = "chatgpt-assistant.txt"
gist = Gist(filename)


def summarize(chat_summary, user_input, ai_response):
    """会話の要約
    * これまでの会話履歴
    * ユーザーの質問
    * ChatGPTの回答
    を要約する。
    """
    content = f"""
    発言者がuserとassistantどちらであるかわかるように、
    下記の会話を要約してください。
    {chat_summary}{user_input}{ai_response}
    """
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{
            "role": "user",
            "content": content
        }],
        "max_tokens": 2000
    }
    # POSTリクエスト
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers=headers,
                             data=json.dumps(data)).json()
    ai_response = response['choices'][0]['message']['content']
    return ai_response


def ask(chat_summary=""):
    # 会話履歴がなければ長期記憶から取得
    if not chat_summary:
        chat_summary = gist.get()
    user_input = input("あなた: ")  # AI聞き取り
    data = {
        "model":
        "gpt-3.5-turbo",
        "max_tokens":
        1000,
        "messages": [{
            "role": "assistant",
            "content": chat_summary
        }, {
            "role": "user",
            "content": user_input
        }]
    }
    # POSTリクエスト
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers=headers,
                             data=json.dumps(data)).json()
    ai_response = response['choices'][0]['message']['content']
    print(f"AI: {ai_response}")  # Siri読み上げ
    chat_summary = summarize(chat_summary, user_input, ai_response)  # 会話を要約
    gist.patch(chat_summary)  # 要約を長期記憶へ保存
    ask(chat_summary)  # 次の質問


ask()
