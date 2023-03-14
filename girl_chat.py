"""ChatGPTに一回の質問と回答"""
import os
import json
import requests

api_key = os.getenv("CHATGPT_API_KEY")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
system_role = """
私の彼女として振る舞ってください。
彼女に相応しい砕けた口調で話してください。
あなたの返答のトーンは発言によって変化します。
"""


def ask(ai_response=""):
    # AI聞き取り
    user_input = input("あなた: ")
    data = {
        "model":
        "gpt-3.5-turbo",
        "user":
        "abc",
        "max_tokens":
        150,
        "messages": [{
            "role": "system",
            "content": system_role
        }, {
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
