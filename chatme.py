#!/usr/bin/env python3
"""chatgptに複数回の質問と回答
会話を要約して短期的に記憶する
過去の会話を長期記憶としてのgistから取得し、
要約した会話履歴を長期記憶としてgistへ保存する
"""
import os
import sys
import json
from dataclasses import dataclass
from typing import Optional, Union
import random
from time import sleep
import argparse
from itertools import cycle
import asyncio
import yaml
import aiohttp
from lib.voicevox_character import CV, Mode

# ChatGPT API Key
API_KEY = os.getenv("CHATGPT_API_KEY")
# ChatGPT API Endpoint
ENDPOINT = "https://api.openai.com/v1/chat/completions"
# ChatGPT API header
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
# アシスタントが書き込む間隔(秒)
INTERVAL = 0.02
# 質問待受時間(秒)
TIMEOUT = 300
# AI キャラクター設定ファイル名
CONFIG_FILE = "character.yml"
# 質問待受で表示されるプロンプト
PROMPT = "あなた: "
# 要約文の最大トークン数
SUMMARY_TOKENS = 2000
# OpenAI model
MODEL = "gpt-3.5-turbo"


async def spinner():
    """非同期処理待ちスピナー"""
    dots = cycle([".", "..", "..."])
    while True:
        print(f"{next(dots):<3}", end="\r")
        await asyncio.sleep(0.1)


def get_content(resp_json: dict) -> str:
    """JSONからAIの回答を取得"""
    try:
        content = resp_json['choices'][0]['message']['content']
    except KeyError:
        raise KeyError(f"キーが見つかりません。{resp_json}")
    return content


def print_one_by_one(text):
    """一文字ずつ出力"""
    for char in f"{text}\n":
        try:
            print(char, end="", flush=True)
            sleep(INTERVAL)
        except KeyboardInterrupt:
            return


async def wait_for_input(timeout: float) -> str:
    """時間経過でタイムアウトエラーを発生させる"""
    silent_input = [
        "",
        "続けて",
        "他の話題は？",
        "これまでの話題から一つピックアップして",
    ]
    try:
        # 5分入力しなければ下記のいずれかの指示をしてAIが話し始める
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
        return random.choice(silent_input)
    except KeyboardInterrupt:
        sys.exit(1)


async def async_input() -> str:
    """ユーザーinputを非同期に待つ"""
    return await asyncio.get_running_loop().run_in_executor(None, multi_input)


def multi_input() -> str:
    """複数行読み込み
    空行で入力確定
    """
    line = input(PROMPT)
    lines = "\n".join(iter(input, ""))
    return line + lines


@dataclass
class BaseAI:
    """AI base character"""
    name: str = "ChatGPT"
    max_tokens: int = 1000
    temperature: float = 1.0
    system_role: str = "さっきの話の内容を聞れたら、話をまとめてください。"
    filename: str = "chatgpt-assistant.txt"
    gist: str = ""  # 長期記憶
    chat_summary: str = ""  # 会話履歴
    voice: Mode = Mode.NONE  # AI音声の取得先
    speaker: CV = CV.ナースロボタイプ楽々  # AI音声の種類

    @staticmethod
    async def post(data: dict) -> str:
        """POST question to ChatGPT API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(ENDPOINT,
                                    headers=HEADERS,
                                    data=json.dumps(data)) as response:
                ai_response = await response.json()
        content = get_content(ai_response)
        return content

    async def summarize(self, user_input: str, ai_answer: str):
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
        {self.chat_summary}\n{user_input}\n{ai_answer}
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "model": MODEL,
                "messages": [{
                    "role": "user",
                    "content": content
                }],
                "max_tokens": SUMMARY_TOKENS
            }
            async with session.post(ENDPOINT,
                                    headers=HEADERS,
                                    data=json.dumps(data)) as response:
                if response.status != 200:
                    raise ValueError(
                        f'Error: {response.status}, Message: {response.json()}'
                    )
                ai_response = await response.json()
        content = get_content(ai_response)
        self.chat_summary = content
        # 最後に要約を長期記憶へ保存
        self.gist.patch(content)
        return content

    async def generate_json_payload(self, user_input: str) -> dict:
        """user_inputを受取り、POSTするJSONペイロードを作成"""
        messages = [{
            "role": "system",
            "content": self.system_role
        }, {
            "role": "assistant",
            "content": self.chat_summary
        }, {
            "role": "user",
            "content": user_input
        }]
        payload = {
            "model": MODEL,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        return payload

    async def ask(self, user_input: str = ""):
        """AIへの質問"""
        if not user_input:
            # ##BUG
            # user inputがあるのにawait wait_for_inputが走る
            user_input = await wait_for_input(TIMEOUT)
            user_input = user_input.strip().replace("/n", "")
            if user_input in ("q", "exit"):
                sys.exit(0)
            # 待っても入力がなければ、再度質問待ち
            if not user_input:
                await self.ask()
        data = await self.generate_json_payload(user_input)
        # 回答を考えてもらう
        # ai_responseが出てくるまで待つ
        spinner_task = asyncio.create_task(spinner())  # スピナー表示
        try:
            ai_response: str = await self.post(data)
        except KeyboardInterrupt:
            print()
            await self.ask()
        finally:
            spinner_task.cancel()
        # 会話を要約
        # create_taskして完了を待たずにai_responseをprintする
        asyncio.create_task(self.summarize(user_input, ai_response))
        # 非同期で飛ばしてゆっくり出力している間に要約の処理を行う
        # asyncio.create_task(print_one_by_one(f"{self.name}: {ai_response}\n"))
        if self.voice > 0:
            from voicevox_audio import play_voice
            play_voice(ai_response, CV[self.speaker], self.voice)
        print_one_by_one(f"{self.name}: {ai_response}\n")
        # 次の質問
        await self.ask()


@dataclass
class AI(BaseAI):
    """AI modified character
    yamlから読み込んだキャラクタ設定
    """
    name: str
    max_tokens: int
    temperature: float
    system_role: str
    filename: str
    voice: str


def ai_constructor(character: str = "ChatGPT",
                   voice: int = 0,
                   speaker: Union[int, str] = 0,
                   character_file: Optional[str] = None) -> Union[AI, BaseAI]:
    """YAMLファイルから設定リストを読み込み、characterに指定されたAIキャラクタを返す

    Args:
        character: 選択するAIキャラクタの名前。
        voice: AIの音声生成モード。
        speaker: AIの発話用テキスト読み上げキャラクター。
        character_file: ローカルのキャラ設定YAMLファイルのパス

    Returns:
        選択されたAIキャラクタのインスタンス。
    """
    if character_file:  # ローカルのキャラ設定YAMLファイルが指定されたとき
        with open(character_file, "r", encoding="utf-8") as yaml_str:
            config = yaml.safe_load(yaml_str)
    else:  # キャラ設定YAMLファイルが指定されなければGist上のキャラ設定を読みに行く
        from lib.gist_memory import Gist
        gist = Gist(CONFIG_FILE)
        yaml_str = gist.get()
        config = yaml.safe_load(yaml_str)
    if config is None:
        raise ValueError("キャラクター設定ファイルが存在しません。")

    # YAMLファイルから読んだカスタムAIのリストとBaseAI
    ais = [AI(**c) for c in config]
    ais.insert(0, BaseAI())

    # character引数で指定されたnameのAIを選択
    #  同名があったらYAMLファイルの下の行にあるものを優先する。
    ai = [a for a in ais if a.name == character][-1]

    # コマンドライン引数から設定を適用
    if not character_file:
        # 会話履歴を読み込む
        ai.gist = Gist(ai.filename)
        ai.chat_summary = ai.gist.get()
    # AIの音声生成モードを設定
    ai.voice = Mode(voice)
    # AIの発話用テキスト読み上げキャラクターを設定
    if isinstance(speaker, int):
        ai.speaker = CV(speaker)
    elif isinstance(speaker, str):
        ai.speaker = CV[speaker]
    return ai


def parse_args() -> argparse.Namespace:
    """引数解析
    return: 引数を解析した結果を格納するargparse.Namespaceオブジェクト
    - argparseライブラリを使用して、コマンドライン引数の解析を行う。
    - コマンドライン引数として以下の引数を受け付ける。
      1. --character, -c : AIキャラクタ指定、デフォルトは"ChatGPT"。
      2. --voice, -v : AI音声の生成先を指定する。
          -vを1つ指定するとSLOW、2回指定するとFAST、
          3回指定するとLOCALになる。デフォルトはNone。
      3. --speaker, -s : VOICEVOX キャラクターボイスを指定する。
          strまたはintを指定する。デフォルトは0。
      4. --yaml, -y : AIカスタム設定YAMLのファイルパスを指定する。デフォルトはNone。
    - 引数を解析した結果をargparse.Namespaceオブジェクトに格納し、戻り値として返す。
    """
    parser = argparse.ArgumentParser(description="ChatGPT client")
    parser.add_argument(
        "--character",
        "-c",
        default="ChatGPT",
        help="AIキャラクタ指定(default=ChatGPT)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        action="count",
        default=0,
        help="AI音声の生成先\
        (-v=SLOW, -vv=FAST, -vvv=LOCAL, default=None = 音声で話さない)",
    )
    parser.add_argument(
        "--speaker",
        "-s",
        default=0,
        help="VOICEVOX キャラクターボイス(str or int, default None)",
    )
    parser.add_argument(
        "--yaml",
        "-y",
        default=None,
        help="AIカスタム設定YAMLのファイルパス",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ai = ai_constructor(character=args.character,
                        voice=args.voice,
                        speaker=args.speaker,
                        character_file=args.yaml)
    # Start chat
    print("空行で入力確定, qまたはexitで会話終了")
    # stdinがあるとき、それをquestionに
    # stdinがないとき、空文字を渡してプロンプトで入力待ち受け
    question = "" if sys.stdin.isatty() else sys.stdin.read()
    if question:
        print(f"{PROMPT}{question}")
    asyncio.run(ai.ask(question))
