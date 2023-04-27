""" ChatGPTとの会話の要約を長期記憶としてgistへ保存する

# USAGE
gist = Gist("chatgpt-assistant.txt")

content = gist.get()
print(content)

content = gist.patch("明日も晴れ")
print(content)
"""
import os
import json
import requests


class Gist:
    """gist API handler"""
    __id = os.environ["GIST_ID"]
    __url = "https://api.github.com/gists/" + __id
    __token = os.environ["GITHUB_TOKEN"]
    __client_id = os.getenv("GIST_CLIENT_ID")
    __client_secret = os.getenv("GIST_CLIENT_SECRET")

    def __init__(self, filename):
        """指定したgist ファイルに対するAPI操作"""
        self.filename = filename

    @classmethod
    def set_params(cls):
        """GistのAPI limit制限緩和のために
        client_idとclient_secretをパラメータにセットする
        環境変数にどちらかが設定されていない場合はNoneを返す。

        API limitを制限を解除するためには
        paramsにclient_idとclient_secretを含める必要がある。

        https://docs.github.com/ja/rest?apiVersion=2022-11-28#rate-limiting

        curl 'https://api.github.com/gists/<GIST_ID>?client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>
        """
        exist_id: bool = Gist.__client_id is not None
        exist_secret: bool = Gist.__client_secret is not None
        if (exist_id and exist_secret):
            return {
                "client_id": Gist.__client_id,
                "client_secret": Gist.__client_secret
            }
        return None

    def get(self):
        """Gist上の指定ファイルの内容を取得"""
        resp = requests.get(Gist.__url, params=Gist.set_params())
        resp.raise_for_status()
        content = resp.json()["files"][self.filename]["content"]
        return content

    def patch(self, body):
        """bodyの内容をGistへ保存"""
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {Gist.__token}"
        }
        data = {"files": {self.filename: {"content": body}}}
        resp = requests.patch(Gist.__url,
                              headers=headers,
                              params=Gist.set_params(),
                              data=json.dumps(data))
        resp.raise_for_status()
        return resp.json()["files"][self.filename]["content"]
