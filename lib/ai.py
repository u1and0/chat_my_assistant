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
from typing import Optional
import random
from time import sleep
from itertools import cycle
import asyncio
import wave
import yaml
import aiohttp
from .voicevox_character import CV, Mode

# ChatGPT API Key
API_KEY = os.environ["CHATGPT_API_KEY"]
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
# OpenAI model
MODEL = "gpt-3.5-turbo"
# 会話履歴の形式
Message = namedtuple("Message", ["role", "content"])


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
    """一定時間内に入力があればその入力を返し、そうでなければランダムな返答を返す関数。
    Parameter: 入力を待つ最大時間（秒単位）
    Return: 入力があった場合はその入力、なかった場合はランダムに選ばれた返答
    """
    silent_input = [
        "",
        "続けて",
        "他の話題は？",
        "これまでの話題から一つピックアップして",
    ]
    try:
        input_task = asyncio.create_task(async_input())
        done, _ = await asyncio.wait({input_task}, timeout=timeout)
        if input_task in done:
            return input_task.result()
        raise asyncio.TimeoutError("Timeout")
    except asyncio.CancelledError:
        input_task.cancel()
        raise
    except asyncio.TimeoutError:
        # タイムアウトしたらランダムな質問を返す
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
    default_system_role = """
        さっきの話の内容を聞かれたときに\
        「憶えていない」や「記憶を持たない」と言った発言をしない代わりに、\
        あなたの発言と会話のやり取りを要約して話してください。\
        以下に与えるユーザーの好みを会話の流れで必要に応じて活用してください。\

        # ユーザーの好み\
        """

    def __init__(self,
                 name="ChatGPT",
                 max_tokens=1000,
                 temperature=1.0,
                 system_role="",
                 filename="chatgpt-assistant.txt",
                 gist=None,
                 chat_summary="",
                 messages_limit: int = 2,
                 voice: Mode = Mode.NONE,
                 speaker: CV = CV.四国めたんノーマル):
        # YAMLから設定するオプション
        self.name = name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_role = system_role + AI.default_system_role
        self.filename = filename
        self.gist = gist  # 長期記憶
        self.chat_summary = chat_summary  # 会話履歴
        self.messages_limit = int(messages_limit)  # 会話履歴のストック上限数
        self.voice = voice
        # AIの発話用テキスト読み上げキャラクターを設定
        self.speaker = self.set_speaker(speaker)

    async def post(self, chat_messages: list[Message]) -> str:
        """ユーザーの入力を受け取り、ChatGPT APIにPOSTし、AIの応答を返す"""
        if self.gist is not None:
            from .gist_memory import Gist
            profiling_gist = Gist(Profiler.filename)
        # else:
        # ローカルのユーザープロファイルを読み込む
        # ユーザーが質問するたびにユーザープロファイリングの結果が変わるので、
        # POSTするたびにユーザープロファイリングの取得処理が必要
        user_profile = profiling_gist.get()
        messages = [{
            "role": str(Role.SYSTEM),
            "content": self.system_role + user_profile
        }, {
            "role": str(Role.ASSISTANT),
            "content": self.chat_summary
        }]
        messages += [h._asdict() for h in chat_messages]  # 会話のやり取り
        data = {
            "model": MODEL,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(ENDPOINT,
                                    headers=HEADERS,
                                    data=json.dumps(data)) as response:
                ai_response = await response.json()
        content = get_content(ai_response)
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

    async def summarize(self, chat_messages: list[Message]):
        """要約用のChatGPT: Summarizerを呼び出して要約文を作成し、
        要約文をgistへアップロードする。
        """
        summarizer = Summarizer(self.name, self.filename, self.gist,
                                self.chat_summary)
        # 要約文を作成
        self.chat_summary = await summarizer.post(chat_messages)
        # 要約文をGistへ保存
        self.gist.patch(self.chat_summary)
        del summarizer

    async def profiling(self, user_input: str):
        """ユーザーのプロファイリング分析用の
        ChatGPT: Profilerを呼び出してユーザープロファイリングを実行し、
        ユーザープロファイリングをgistへアップロードする。
        """
        profiler = Profiler(self.gist)
        # ユーザープロファイリングを作成
        profiling_data = await profiler.post(user_input)
        if self.gist is not None:
            # ユーザープロファイリングをGistへ保存
            profiler.gist.patch(profiling_data)
        # else:
        # ローカルファイルへユーザープロファイルを保存する処理
        del profiler

    async def ask(self, chat_messages: list[Message] = []):
        """AIへの質問"""
        user_input = ""
        while user_input.strip() == "":  # 入力待受
            # 待っても入力がなければ、再度質問待ち
            # 入力があればループを抜け回答を考えてもらう
            try:
                user_input = await wait_for_input(TIMEOUT)
                user_input = user_input.replace("/n", " ")
                if user_input.strip() in ("q", "exit"):
                    raise SystemExit
            except KeyboardInterrupt:
                print()
        # ユーザーの入力を会話履歴に追加
        chat_messages.append(Message(str(Role.USER), user_input))
        # ユーザープロファイリングをバックグラウンドで進める非同期処理
        asyncio.create_task(self.profiling(user_input))
        # 回答を考えてもらう
        spinner_task = asyncio.create_task(spinner())  # スピナー表示
        # ai_responseが出てくるまで待つ
        ai_response: str = await self.post(chat_messages)
        spinner_task.cancel()
        # 会話履歴に追加
        chat_messages.append(Message(str(Role.ASSISTANT), ai_response))
        # N会話分のlimitを超えるとtoken節約のために会話の内容を忘れる
        # 2倍するのはUserの質問とAssistantと回答で1セットだから。
        while len(chat_messages) > self.messages_limit * 2:
            chat_messages.pop(0)
        # 会話の要約をバックグラウンドで進める非同期処理
        asyncio.create_task(self.summarize(chat_messages))
        # 音声出力オプションがあれば、音声の再生
        if self.voice > 0:
            from lib.voicevox_audio import play_voice
            try:
                play_voice(ai_response, self.speaker, self.voice)
            except (EOFError, wave.Error) as wav_e:
                print("Error: 音声再生中にエラーが発生しました。", f"{wav_e}無視してテキストを表示します。")
        print_one_by_one(f"{self.name}: {ai_response}\n")
        # 次の質問
        await self.ask(chat_messages)


class Summarizer(AI):
    """要約文を考えるためのChatGPTインスタンス"""
    # Summarizerでは下記プロパティは固定値として扱う
    max_tokens = 2000
    temperature = 0
    system_role = """
    発言者がuserとassistantどちらであるかわかるように、
    下記の会話をリスト形式で、ですます調を使わずにである調で要約してください。
    要約は必ず2000tokens以内で収まるようにして、
    収まらない場合は重要度が低そうな内容を要約から省いて構いません。
    """

    def __init__(self, name, filename, gist, chat_summary):
        """
        * 親クラスから引き継がれるプロパティ
            * `name`
            * `filename`
            * `gist`
            * `chat_summary`
        * 子クラスで定義された定数を使用
            * `max_tokens`
            * `temperature`
            * `system_role`
        """
        super().__init__(name=name,
                         max_tokens=Summarizer.max_tokens,
                         temperature=Summarizer.temperature,
                         system_role=Summarizer.system_role,
                         filename=filename,
                         gist=gist,
                         chat_summary=chat_summary)

    async def post(self, messages: list[Message]) -> str:
        """会話履歴と会話の内容を送信して会話の要約を作る"""
        content = "\n".join([self.chat_summary] + [
            f"- {self.name}: {m.content}" if m.role ==
            Role.ASSISTANT else f"- User: {m.content}" for m in messages
        ])
        data = {
            "model":
            MODEL,
            "max_tokens":
            Summarizer.max_tokens,
            "temperature":
            Summarizer.temperature,
            "messages": [{
                "role": str(Role.SYSTEM),
                "content": Summarizer.system_role
            }, {
                "role": str(Role.USER),
                "content": content
            }]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(ENDPOINT,
                                    headers=HEADERS,
                                    data=json.dumps(data)) as response:
                if response.status != 200:
                    raise ValueError(
                        f'Error: {response.status}, Message: {response.json()}'
                    )
                ai_response = await response.json()
        content = get_content(ai_response)
        return content


class Profiler(AI):
    """ユーザーの好みを分析するためのChatGPTインスタンス
    """
    # Summarizerでは下記プロパティは固定値として扱う
    max_tokens = 500
    temperature = 0
    filename = "user_personality.txt"
    system_role = """
    出力例のようにして、発言内容からUserの好みをリストアップしてください。

    ### 入力例 ###
    # これまでのユーザーの好み
    - 昼寝が好き
    - 山登り
    - プログラミング言語の中でも特にPythonが好き

    # ユーザーの発言
    来週は山登りに行くんだ。今朝の朝食は美味しかったな。いつもはコーヒーを飲むんだけどね今朝は紅茶が出てきただけど、ジャムトーストと合うんだな。そういや今日の仕事は大変そうなので、楽しみにしているドラマに間に合うか心配だな。

    ### 出力例 ###
    - 昼寝が好き
    - プログラミング言語の中でも特にPythonが好き
    - 山登り
    - コーヒーを飲む
    - ドラマ鑑賞
    """

    def __init__(self, gist):
        """
        * 親クラスから引き継がれるプロパティ
            * `name`
            * `filename`
            * `gist`
            * `chat_summary`
        * 子クラスで定義された定数を使用
            * `max_tokens`
            * `temperature`
            * `system_role`
        """
        if gist is not None:  # gistがNoneでない == ローカルモードで実行されていない
            from .gist_memory import Gist
            gist = Gist(Profiler.filename)
        super().__init__(max_tokens=Profiler.max_tokens,
                         temperature=Profiler.temperature,
                         system_role=Profiler.system_role,
                         filename=Profiler.filename,
                         gist=gist)

    async def post(self, user_input: str):
        """ユーザーの発言を送信してユーザーの好みを分析する"""
        user_profile = self.gist.get()  # これまでの好み
        content = f"""
            # これまでのユーザーの好み
            {user_profile}

            # ユーザーの発言
            {user_input}
            """
        data = {
            "model":
            MODEL,
            "max_tokens":
            Profiler.max_tokens,
            "temperature":
            Profiler.temperature,
            "messages": [{
                "role": str(Role.SYSTEM),
                "content": Profiler.system_role
            }, {
                "role": str(Role.USER),
                "content": content
            }]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(ENDPOINT,
                                    headers=HEADERS,
                                    data=json.dumps(data)) as response:
                if response.status != 200:
                    raise ValueError(
                        f'Error: {response.status}, Message: {response.json()}'
                    )
                ai_response = await response.json()
        content = get_content(ai_response)
        return content


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
    if isinstance(voice, int):
        voice = Mode(voice)
    ai.voice = voice
    return ai
