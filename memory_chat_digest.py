"""chatgptに複数回の質問と回答
会話を要約して短期的に記憶する
過去の会話を長期記憶としてのgistから取得し、
要約した会話履歴を長期記憶としてgistへ保存する
"""
import os
import sys
import json
import requests
from time import sleep
import asyncio
import random
from gist_memory import Gist

api_key = os.getenv("CHATGPT_API_KEY")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}


async def wait_for_input(timeout: float) -> str:
    """時間経過でタイムアウトエラーを発生させる"""
    try:
        input_task = asyncio.create_task(async_input())
        done, pending = await asyncio.wait({input_task}, timeout=timeout)
        if input_task in done:
            return input_task.result()
        else:
            raise asyncio.TimeoutError("Timeout")
    except asyncio.CancelledError:
        input_task.cancel()
        raise


async def async_input() -> str:
    return await asyncio.get_running_loop().run_in_executor(
        None, input, "あなた: ")


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

    async def ask(self):
        # AI聞き取り
        try:
            # 5分話さなければ下記の指示をしてAIが話し始める
            user_input = await wait_for_input(300)
        except asyncio.TimeoutError:
            if random.random() < 1 / 4:
                print("\n")
                user_input = "続けて"
            elif random.random() < 2 / 4:
                print("\n")
                user_input = "他の話題は？"
            elif random.random() < 3 / 4:
                print("\n")
                user_input = "これまでの話題から一つピックアップして"
            else:
                await self.ask()
        except KeyboardInterrupt:
            sys.exit(1)
        if user_input.strip() == "q" or user_input.strip() == "exit":
            sys.exit(0)
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
        for text in f"AI: {ai_response}\n":  # 一文字ずつ出力
            try:
                print(text, end="", flush=True)
                sleep(0.1)
            except KeyboardInterrupt:
                break
        # 会話を要約
        self.chat_summary = self.summarize(user_input, ai_response)
        # 最後に要約を長期記憶へ保存
        self.gist.patch(self.chat_summary)
        # 次の質問
        await self.ask()


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
    asyncio.run(ai.ask())
