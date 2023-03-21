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
import subprocess
from time import sleep
import requests
from pydub import AudioSegment
from pydub.playback import play

apikey = os.getenv("VOICEVOX_API_KEY")
url = "https://api.tts.quest/v1"
fast_url = "https://api.su-shiki.com/v2"


def check_point():
    """ API残数確認
    注意: APIポイント確認だけでも1500ポイント消費する
    """
    return requests.get(f"{fast_url}/api", params={"key": apikey}).text


def get_voice(text, character_id=0, fast=False) -> requests.Response:
    """VOICEVOX web apiへアクセスしてaudioレスポンスを得る"""
    if fast:
        params = {"key": apikey, "speaker": character_id, "text": text}
        resp = requests.get(f"{fast_url}/voicevox/audio", params)
        return resp
    wav_api = requests.get(
        f"{url}/voicevox",  # 末尾のスラッシュがないとエラー
        # f"{url}/voicevox/?text={text}&speaker=0",
        params={
            "speaker": character_id,
            "text": text
        })
    if wav_api.status_code != 200:
        print("Warnig: Use fast mode")
        raise requests.HTTPError(wav_api.status_code)
    wav_url = wav_api.json()["wavDownloadUrl"]
    resp = requests.get(wav_url)
    return resp


def build_audio(binary, wav_file=""):
    """audioバイナリを作成
    ファイルパス wav_fileが渡されたらそのファイルにwavを保存する。
    """
    if wav_file:
        with open(wav_file, "wb") as f:
            f.write(binary)
    else:
        wav_file = BytesIO(binary)
    return AudioSegment.from_wav(wav_file)


text = "今日の朝ご飯はなに？"
# リクエスト過多の429エラーが出たときには
# fastバージョンを使う
try:
    resp = get_voice(text)
except requests.HTTPError:
    resp = get_voice(text, fast=True)
print("GET from: ", resp.url)
audio = build_audio(resp.content)
play(audio)
