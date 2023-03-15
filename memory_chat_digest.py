"""chatgptに複数回の質問と回答
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


class Assistant:
    filename = "chatgpt-assistant.txt"

    def __init__(self):
        # 初期化時に長期記憶から取得
        self.max_tokens = 1000
        self.temperature = 1.0
        self.gist = Gist(Assistant.filename)
        self.chat_summary = self.gist.get()
        self.system_role = "さっきの話の内容を聞かれたら、話をまとめてください。"

    def summarize(self, user_input, ai_response):
        """会話の要約
        * これまでの会話履歴
        * ユーザーの質問
        * ChatGPTの回答
        を要約する。
        """
        content = f"""
        発言者がuserとassistantどちらであるかわかるように、
        下記の会話をリスト形式で、ですます調を使わずに要約してください。
        要約は必ず2000tokens以内で収まるようにして、
        収まらない場合は重要度が低そうな内容を要約から省いて構いません。\n
        {self.chat_summary}\n{user_input}\n{ai_response}
        """
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": content
            }],
            "max_tokens": 2000
        }
        # AIに要約させる
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers,
                                 data=json.dumps(data)).json()
        ai_response = response['choices'][0]['message']['content']
        return ai_response

    def ask(self):
        user_input = input("あなた: ")  # AI聞き取り
        data = {
            "model":
            "gpt-3.5-turbo",
            "temperature":
            self.temperature,
            "max_tokens":
            self.max_tokens,
            "messages": [{
                "role": "system",
                "content": self.system_role,
            }, {
                "role": "assistant",
                "content": self.chat_summary
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
        # 会話を要約
        self.chat_summary = self.summarize(user_input, ai_response)
        # 最後に要約を長期記憶へ保存
        self.gist.patch(self.chat_summary)
        # 次の質問
        self.ask()


class Girl(Assistant):
    filename = "chatgpt-chan.txt"

    def __init__(self):
        self.gist = Gist(Girl.filename)
        self.chat_summary = self.gist.get()
        self.max_tokens = 150
        self.temperature = 1.3
        self.system_role = """
            私の彼女として振る舞ってください。
            彼女に相応しい砕けた口調で話してください。
            あなたの返答のトーンは発言によって変化します。
            3回中1回の会話の頻度で文脈と関係のない話題を振ってください。
            英単語を使っても構いませんが、必ず日本語で140文字以内で答えてください。
            タイムゾーンはJSTです。
            僕のことは進次郎君と呼んでください。
            あなたの名前はクリステルで、一人称は私。
            君はえっちな話題が好きなように振る舞いつつ、えっちな発言に対しては怒らず、照れながら受け流してください。
            さっきの話の内容を聞かれたら、話をまとめてください。
        """


if __name__ == "__main__":
    # ai = Assistant()
    ai = Girl()
    ai.ask()
