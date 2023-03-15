"""ChatGPTに複数回の質問と回答"""
import os
import json
import requests


def ask(ai_response=""):
    # AI聞き取り
    user_input = input("あなた: ")

    # URLに指定する内容
    api_key = os.getenv("CHATGPT_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model":
        "gpt-3.5-turbo",
        "user":
        "abc",
        "max_tokens":
        1000,
        "messages": [{
            "role": "assistant",
            "content": ai_response
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
    ask(ai_response)


ask()
