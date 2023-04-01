#!/usr/bin/env python3
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
from io import BytesIO
import json
from typing import Union
from time import sleep
import argparse
import requests
from pydub import AudioSegment
from pydub.playback import play
from .voicevox_character import CV, Mode

apikey = os.getenv("VOICEVOX_API_KEY")
url = "https://api.tts.quest/v1"
fast_url = "https://api.su-shiki.com/v2"
local_url = "http://localhost:50021"


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
    if mode == 3:  # Mode LOCAL
        body = audio_query(text, speaker=speaker).json()
        response = synthesis(body, speaker=speaker)
        return response
    elif mode == 2:  # Mode FAST
        params = {"key": apikey, "speaker": int(speaker), "text": text}
        response = requests.get(f"{fast_url}/voicevox/audio", params)
        return response
    # Mode SLOW
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
    sleep(3)
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
    audio = build_audio(resp.content)
    play(audio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOICEVOX CV")
    parser.add_argument("-s",
                        "--speaker",
                        default=0,
                        help="VOICEVOX Character voice ID")
    parser.add_argument("-v",
                        "--voicemode",
                        action="count",
                        default=0,
                        help="VOICEVOX モード Local Fast Slow")
    parser.add_argument("text", help="VOICEVOXに話させる文字列")
    args = parser.parse_args()
    # リクエスト過多の429エラーが出たときには
    # fastバージョンを使う
    # try:
    #     resp = get_voice(text)
    # except requests.HTTPError:
    #     resp = get_voice(text, mode=Mode.FAST)
    print(Mode(args.voicemode))
    play_voice(args.text, speaker=args.speaker, mode=Mode(args.voicemode))
