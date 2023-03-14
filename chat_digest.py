"""ChatGPTに複数回の質問と回答"""
import os
import json
import requests

api_key = os.getenv("CHATGPT_API_KEY")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}


def summarize(chat_summary, user_input, ai_response):
    """会話の要約
    * これまでの会話履歴
    * ユーザーの質問
    * ChatGPTの回答
    を要約する。
    """
    data = {
        "model":
        "gpt-3.5-turbo",
        "messages": [
            {
                "role":
                "user",
                "content":
                f"下記の会話を要約してください。\n\n{chat_summary}{user_input}{ai_response}"
            },
        ],
        "max_tokens":
        1000
    }
    # POSTリクエスト
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             headers=headers,
                             data=json.dumps(data)).json()
    ai_response = response['choices'][0]['message']['content']
    return ai_response


def ask(chat_summary=""):
    # AI聞き取り
    user_input = input("あなた: ")
    data = {
        "model":
        "gpt-3.5-turbo",
        "user":
        "abc",
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
    # Siri読み上げ
    print(f"AI: {ai_response}")
    chat_summary = summarize(chat_summary, user_input, ai_response)
    ask(chat_summary)


ask()
