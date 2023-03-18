#!/usr/bin/env python3
"""chatgptに複数回の質問と回答
会話を要約して短期的に記憶する
過去の会話を長期記憶としてのgistから取得し、
要約した会話履歴を長期記憶としてgistへ保存する
"""
import os
import sys
import json
import random
from time import sleep
from itertools import cycle
import asyncio
import aiohttp
from gist_memory import Gist

api_key = os.getenv("CHATGPT_API_KEY")
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
# アシスタントが書き込む間隔(秒)
INTERVAL = 0.02


async def spinner():
    """非同期処理待ちスピナー"""
    dots = cycle([".", "..", "..."])
    while True:
        print(f"{next(dots):<3}", end="\r")
        await asyncio.sleep(0.1)


def get_content(resp_json: dict) -> str:
    """JSONからAIの回答を取得"""
    return resp_json['choices'][0]['message']['content']


def multi_input() -> str:
    lines = []
    line = input("あなた: ")
    lines.append(line)
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            return "\n".join(lines)


def print_one_by_one(text):
    """一文字ずつ出力"""
    for char in f"{text}\n":
        try:
            print(char, end="", flush=True)
            sleep(INTERVAL)
        except KeyboardInterrupt:
            return


async def wait_for_input(text: str, timeout: float) -> str:
    """時間経過でタイムアウトエラーを発生させる"""
    silent_input = [
        "",
        "続けて",
        "他の話題は？",
        "これまでの話題から一つピックアップして",
    ]
    try:
        # 5分入力しなければ下記のいずれかの指示をしてAIが話し始める
        # text = await wait_for_input(300)
        input_task = asyncio.create_task(async_input())
        done, _ = await asyncio.wait({input_task}, timeout=timeout)
        if input_task in done:
            return input_task.result()
        raise asyncio.TimeoutError("Timeout")
    except asyncio.CancelledError:
        input_task.cancel()
        raise
    except asyncio.TimeoutError:
        # 5分黙っていたらランダムに一つ質問
        text = random.choice(silent_input)
    except KeyboardInterrupt:
        sys.exit(1)
    return text


async def async_input() -> str:
    """ユーザーinputを非同期に待つ"""
    return await asyncio.get_running_loop().run_in_executor(None, multi_input)


class Assistant:
    filename = "chatgpt-assistant.txt"
    name = "AI"

    def __init__(self):
        # 初期化時に長期記憶から取得
        self.max_tokens = 1000
        self.temperature = 1.0
        self.gist = Gist(Assistant.filename)
        self.chat_summary = self.gist.get()
        self.system_role = "さっきの話の内容を聞かれたら、話をまとめてください。"

    async def post(self, data: dict) -> str:
        """POST question to ChatGPT API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url,
                                    headers=headers,
                                    data=json.dumps(data)) as response:
                ai_response = await response.json()
        content = get_content(ai_response)
        return content

    async def summarize(self, user_input: str, ai_response: str):
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
        収まらない場合は重要度が低そうな内容を要約から省いて構いません。
        \n---\n
        {self.chat_summary}\n{user_input}\n{ai_response}
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{
                    "role": "user",
                    "content": content
                }],
                "max_tokens": 2000
            }
            async with session.post(url,
                                    headers=headers,
                                    data=json.dumps(data)) as response:
                ai_response = await response.json()
        content = get_content(ai_response)
        self.chat_summary = content
        # 最後に要約を長期記憶へ保存
        self.gist.patch(content)
        return content

    async def ask(self, user_input: str = ""):
        """AIへの質問"""
        if not user_input:
            user_input = await wait_for_input(user_input, timeout=300)
        # 入力がなければ、再度質問待ち
        if not user_input:
            await self.ask()
        user_input = user_input.strip().replace("/n", "")
        if user_input in ("q", "exit"):
            sys.exit(0)
        # ChatGPTへのPOSTリクエスト
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
        # 回答を考えてもらう
        # ai_responseが出てくるまで待つ
        spinner_task = asyncio.create_task(spinner())
        try:
            ai_response = await self.post(data)
        except KeyboardInterrupt:
            print()
            await ai.ask()
        finally:
            spinner_task.cancel()
        # 会話を要約
        # create_taskして完了を待たずにai_responseをprintする
        asyncio.create_task(self.summarize(user_input, ai_response))
        # 非同期で飛ばしてゆっくり出力している間に要約の処理を行う
        print_one_by_one(f"{self.name}: {ai_response}\n")
        # 次の質問
        await ai.ask()


class Girl(Assistant):
    filename = "chatgpt-chan.txt"
    name = "クリステル"

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
    print("空行で入力確定, qまたはexitで会話終了")
    ai = Girl()
    asyncio.run(ai.ask())
