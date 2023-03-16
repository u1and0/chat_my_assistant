""" ChatGPTとの会話の要約を長期記憶としてgistへ保存する

# USAGE
gist = Gist("chatgpt-assistant.txt")

content = gist.get()
print(content)

content = gist.patch("明日も晴れ")
print(content)
"""
import os
import requests
import json


class Gist:
    """gist API handler"""
    _root = "https://api.github.com/gists/"
    _id = os.getenv("GIST_ID")
    url = _root + _id
    __token = os.getenv("GITHUB_TOKEN")

    def __init__(self, filename):
        """指定したgist ファイルに対するAPI操作"""
        self.filename = filename

    def get(self):
        """会話履歴を取得"""
        resp = requests.get(Gist.url).json()
        content = resp["files"][self.filename]["content"]
        return content

    def patch(self, body):
        """会話履歴を保存"""
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {Gist.__token}"
        }
        data = {"files": {self.filename: {"content": body}}}
        resp = requests.patch(Gist.url, headers=headers,
                              data=json.dumps(data)).json()
        return resp["files"][self.filename]["content"]
