import os
import requests
import json


class Gist:
    _root = "https://api.github.com/gists/"
    _id = "b45b4566b12a63527cd623c5b0e8d06b"
    url = _root + _id
    __token = os.getenv("GITHUB_TOKEN")

    def __init__(self, filename):
        self.filename = filename

    def get(self):
        resp = requests.get(Gist.url).json()
        content = resp["files"][self.filename]["content"]
        return content

    def patch(self, body):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {Gist.__token}"
        }
        data = {"files": {self.filename: {"content": body}}}
        resp = requests.patch(Gist.url, headers=headers,
                              data=json.dumps(data)).json()
        return resp["files"][self.filename]["content"]


if __name__ == "__main__":
    gist = Gist("chatgpt-assistant.txt")
    content = gist.get()
    print(content)
    # content = gist.patch("明日も晴れ")
    # print(content)
