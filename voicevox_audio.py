"""
[WEB版VOICEVOX API（高速）](https://voicevox.su-shiki.com/su-shikiapis/)
[WEB版VOICEVOX API（低速）](https://voicevox.su-shiki.com/su-shikiapis/ttsquest/)
fast=Trueオプションで高速URLを使用します。
ただし、API消費に限りがありますのでご注意ください。

消費ポイントの計算式　1500+100*(UTF-8文字数)
初期のポイント: 1,000,000ポイント

確認の仕方はcheck_point()
"""
import os
import sys
from io import BytesIO
import json
from typing import Union
from enum import IntEnum, auto
import argparse
import requests
from pydub import AudioSegment
from pydub.playback import play

apikey = os.getenv("VOICEVOX_API_KEY")
url = "https://api.tts.quest/v1"
fast_url = "https://api.su-shiki.com/v2"
local_url = "http://localhost:50021"


class CV(IntEnum):
    """VOICEVOX Characters Voice IDs

    $ curl -fsSL 'https://api.su-shiki.com/v2/voicevox/speakers?key={API_KEY}' | jq
    [
      {
        "supported_features": {
          "permitted_synthesis_morphing": "SELF_ONLY"
        },
        "name": "四国めたん",
        "speaker_uuid": "7ffcb7ce-00ec-4bdc-82cd-45a8889e43ff",
        "styles": [
          {
            "name": "ノーマル",
            "id": 2
          },
          {
            "name": "あまあま",
            "id": 0
          },
          ...

    Python用に整形
    $ curl -fsSL 'https://api.su-shiki.com/v2/voicevox/speakers?key={API_KEY}' |
        jq '.[] | "\(.name)\(.styles[].name) = \(.styles[].id)"'
    """

    四国めたんあまあま = 0
    四国めたんノーマル = 2
    四国めたんセクシー = 4
    四国めたんツンツン = 6
    四国めたんささやき = 36
    四国めたんヒソヒソ = 37

    ずんだもんノーマル = 3
    ずんだもんあまあま = 1
    ずんだもんツンツン = 7
    ずんだもんセクシー = 5
    ずんだもんささやき = 22
    ずんだもんヒソヒソ = 38

    春日部つむぎノーマル = 8
    雨晴はうノーマル = 10
    波音リツノーマル = 9

    玄野武宏ノーマル = 11
    玄野武宏喜び = 39
    玄野武宏ツンギレ = 40
    玄野武宏悲しみ = 41

    白上虎太郎ふつう = 12
    白上虎太郎わーい = 32
    白上虎太郎びくびく = 33
    白上虎太郎おこ = 34
    白上虎太郎びえーん = 35

    青山龍星ノーマル = 13
    冥鳴ひまりノーマル = 14
    九州そらノーマル = 16
    九州そらあまあま = 15
    九州そらツンツン = 18
    九州そらセクシー = 17
    九州そらささやき = 19

    もち子さんノーマル = 20
    剣崎雌雄ノーマル = 21

    WhiteCULノーマル = 23
    WhiteCULたのしい = 24
    WhiteCULかなしい = 25
    WhiteCULびえーん = 26

    後鬼人間ver = 27
    後鬼ぬいぐるみver = 28

    No7ノーマル = 29
    No7アナウンス = 30
    No7読み聞かせ = 31

    ちび式じいノーマル = 42

    櫻歌ミコノーマル = 43
    櫻歌ミコ第二形態 = 44
    櫻歌ミコロリ = 45

    小夜SAYOノーマル = 46

    ナースロボ＿タイプＴノーマル = 47
    ナースロボ＿タイプＴ楽々 = 48
    ナースロボ＿タイプＴ恐怖 = 49
    ナースロボ＿タイプＴ内緒話 = 50

    聖騎士紅桜ノーマル = 51
    雀松朱司ノーマル = 52
    麒ヶ島宗麟ノーマル = 53

    def __str__(self):
        """
        >>> CV.四国めたんノーマル
        四国めたんノーマル
        """
        return self.name

    def __repr__(self):
        return self.__str__()

    @classmethod
    def table(cls):
        """CV一覧
        ID: キャラクター名
        WARNING: IDに抜けがあるとValueErrorで一覧表示できない
        """
        dic = {}
        i = 0
        while True:
            try:
                dic[i] = CV(i)
                i += 1
            except ValueError:
                break
        return dic

    @classmethod
    def from_string(cls, value):
        """
        >>> CV(2)
        四国めたんノーマル
        """
        return cls[value].name


class Mode(IntEnum):
    """VOICEVOX mode"""
    SLOW = auto()
    FAST = auto()
    LOCAL = auto()


def check_point() -> dict:
    """ API残数確認
    注意: APIポイント確認だけでも1500ポイント消費する
    """
    return requests.get(f"{fast_url}/api", params={"key": apikey}).text


def audio_query(text: str, speaker: Union[int, CV] = 0) -> requests.Response:
    """音声の合成用クエリの作成"""
    headers = {"accept": "application/json"}
    params = {"text": text, "speaker": int(speaker)}
    return requests.post(f"{local_url}/audio_query",
                         headers=headers,
                         params=params)


def synthesis(data, speaker: Union[int, CV] = CV(0)) -> requests.Response:
    """音声合成するAPI"""
    headers = {"accept": "audio/wav", "Content-Type": "application/json"}
    params = {"speaker": int(speaker)}
    return requests.post(f"{local_url}/synthesis",
                         headers=headers,
                         data=json.dumps(data),
                         params=params)


def get_voice(text,
              speaker: Union[int, CV] = CV(0),
              mode: Union[int, Mode] = Mode.SLOW) -> requests.Response:
    """VOICEVOX web apiへアクセスしてaudioレスポンスを得る"""
    if mode == 3:
        body = audio_query(text, speaker=speaker).json()
        response = synthesis(body, speaker=speaker)
        return response
    elif mode == 2:
        params = {"key": apikey, "speaker": int(speaker), "text": text}
        response = requests.get(f"{fast_url}/voicevox/audio", params)
        return response
    # else mode == 1:
    wav_api = requests.get(
        f"{url}/voicevox",  # 末尾のスラッシュがないとエラー
        params={
            "speaker": int(speaker),
            "text": text
        })
    if wav_api.status_code != 200:
        print("Warnig: Use fast mode")
        raise requests.HTTPError(wav_api.status_code)
    wav_url = wav_api.json()["wavDownloadUrl"]
    response = requests.get(wav_url)
    return response


def build_audio(binary, wav_file=None):
    """audioバイナリを作成
    ファイルパス wav_fileが渡されたらそのファイルにwavを保存する。
    """
    if wav_file:
        with open(wav_file, "wb") as f:
            f.write(binary)
    else:
        wav_file = BytesIO(binary)
    return AudioSegment.from_wav(wav_file)


def play_voice(text,
               speaker: Union[int, CV] = CV.四国めたんあまあま,
               mode: Union[int, Mode] = Mode.SLOW):
    """テキストの再生"""
    resp = get_voice(text, speaker, mode)
    audio = build_audio(resp.content, wav_file="sample.wav")
    play(audio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOICEVOX CV")
    parser.add_argument("-s", "--speaker", default=0,
                        help="VOICEVOX Character voice ID")
    parser.add_argument("text",  help="VOICEVOXに話させる文字列")
    args = parser.parse_args()
    # リクエスト過多の429エラーが出たときには
    # fastバージョンを使う
    # try:
    #     resp = get_voice(text)
    # except requests.HTTPError:
    #     resp = get_voice(text, mode=Mode.FAST)
    play_voice(args.text, speaker=args.speaker, mode=Mode.LOCAL)
