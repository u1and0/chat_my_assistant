"""chatgptに複数回の質問と回答
会話を要約して短期的に記憶する
過去の会話を長期記憶としてのgistから取得し、
要約した会話履歴を長期記憶としてgistへ保存する
"""
import os
import sys
import json
from enum import Enum, auto
from collections import namedtuple
from typing import Optional, Union
import random
from time import sleep
from itertools import cycle
import asyncio
import yaml
import aiohttp
from .voicevox_character import CV, Mode

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
# 会話履歴
Message = namedtuple("Message", ["role", "content"])
# デフォルトの役割プロンプト
SYSTEM_ROLE = """
        さっきの話の内容を聞かれたときに\
        「憶えていない」や「記憶を持たない」と言った発言をしない代わりに、\
        あなたの発言と会話のやり取りを要約して話してください。\
    """


class Role(Enum):
    """messagesオブジェクトのroleキー
    Usage: str(Role.ASSISTANT) == "assistant"
    """
    SYSTEM = auto()
    ASSISTANT = auto()
    USER = auto()

    def __str__(self):
        return self.name.lower()


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


class AI:
    """AI modified character
    yamlから読み込んだキャラクタ設定
    """
    def __init__(self,
                 name="ChatGPT",
                 max_tokens=1000,
                 temperature=1.0,
                 system_role=SYSTEM_ROLE,
                 filename="chatgpt-assistant.txt",
                 gist=None,
                 chat_summary="",
                 messages_limit=2,
                 voice: Union[Mode, str] = Mode.NONE,
                 speaker: CV = CV.四国めたんノーマル):
        # YAMLから設定するオプション
        self.name = name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_role = SYSTEM_ROLE
        self.filename = filename
        self.gist = gist  # 長期記憶
        self.chat_summary = chat_summary  # 会話履歴
        self.messages_limit = messages_limit  # 会話履歴のストック上限数
        # AIの発話用テキスト読み上げキャラクターを設定
        self.speaker = self.set_speaker(speaker)

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

    async def summarize(self, *messages: str):
        """会話の要約
        * これまでの会話履歴
        * ユーザーの質問
        * ChatGPTの回答
        を要約する。
        """
        concat = "\n".join(messages)
        content = f"""
        発言者がuserとassistantどちらであるかわかるように、
        下記の会話をリスト形式で、ですます調を使わずに要約してください。
        要約は必ず2000tokens以内で収まるようにして、
        収まらない場合は重要度が低そうな内容を要約から省いて構いません。
        \n---\n
        {self.chat_summary}\n{concat}
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "model": MODEL,
                "messages": [{
                    "role": str(Role.USER),
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

    def set_speaker(self, sp):
        """ AI.speakerの判定
        コマンドラインからspeakerオプションがintかstrで与えられていたら
        そのspeakerに変える
        コマンドラインからオプションを与えられていなかったらNoneが来るので
        プリセットキャラクターのAI.speakerを付与
        """
        try:
            speaker_id = int(sp)
            return CV(speaker_id)
        except ValueError:  # type(sp) == str
            return CV[sp]
        except TypeError:  # sp == None
            return self.speaker

    async def generate_json_payload(
            self, chat_history: Optional[list[Message]] = None) -> dict:
        """user_inputを受取り、POSTするJSONペイロードを作成"""
        role_summary_input = [
            Message(str(Role.SYSTEM), self.system_role),
            Message(str(Role.ASSISTANT), self.chat_summary),
        ] + chat_history
        messages = [h._asdict() for h in role_summary_input]
        # messages = [{
        #     "role": "system",
        #     "content": self.system_role
        # }, {
        #     "role": "assistant",
        #     "content": self.chat_summary
        # }, {
        #     "role": "user",
        #     "content": user_input
        # }]
        payload = {
            "model": MODEL,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages
        }
        return payload

    async def ask(self, chat_messages: list[Message]):
        """AIへの質問"""
        try:
            user_input = await wait_for_input(TIMEOUT)
            user_input = user_input.strip().replace("/n", "")
            if user_input in ("q", "exit"):
                print("\n終了処理: 会話を要約中です。")
                spinner_task = asyncio.create_task(spinner())  # スピナー表示
                await self.summarize(*[m.content for m in chat_messages])
                spinner_task.cancel()
                sys.exit(0)
            # 待っても入力がなければ、再度質問待ち
            if not user_input:
                await self.ask(chat_messages)
            chat_messages.append(Message(str(Role.USER), user_input))
            data = await self.generate_json_payload(chat_messages)
            # 回答を考えてもらう
            # ai_responseが出てくるまで待つ
            spinner_task = asyncio.create_task(spinner())  # スピナー表示
            ai_response: str = await self.post(data)
        except KeyboardInterrupt:
            print()
            await self.ask(chat_messages)
        finally:
            spinner_task.cancel()
            # 会話履歴に追加
            chat_messages.append(Message(str(Role.ASSISTANT), ai_response))
            # N会話分のlimitを超えるとtoken節約のために会話の内容を忘れる
            while len(chat_messages) > self.messages_limit * 2:
                chat_messages.pop(0)
            # 会話の要約をバックグラウンドで進める非同期処理
            asyncio.create_task(
                self.summarize(*[m.content for m in chat_messages]))
        # 音声出力オプションがあれば、音声の再生
        if self.voice > 0:
            from lib.voicevox_audio import play_voice
            play_voice(ai_response, self.speaker, self.voice)
        print_one_by_one(f"{self.name}: {ai_response}\n")
        # 次の質問
        await self.ask(chat_messages)


def ai_constructor(name: str = "ChatGPT",
                   voice: Mode = Mode.NONE,
                   speaker=None,
                   character_file: Optional[str] = None) -> AI:
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

    # YAMLファイルから読んだカスタムAIのリストとデフォルトのAI
    ais = [AI()] + [AI(**c) for c in config]

    # name引数で指定されたnameのAIを選択
    #  同名があったらYAMLファイルの下の行にあるものを優先する。
    ai = [a for a in ais if a.name == name][-1]

    # コマンドライン引数から設定を適用
    if not character_file:
        # 会話履歴を読み込む
        ai.gist = Gist(ai.filename)
        ai.chat_summary = ai.gist.get()
    # AIの音声生成モードを設定
    ai.voice = voice
    return ai
