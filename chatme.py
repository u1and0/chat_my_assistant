#!/usr/bin/env python3
"""chatgptに複数回の質問と回答 CLI"""
import argparse
import asyncio
from lib import ai_constructor, CV, Mode


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
    cv_list = "\n".join(str(t) for t in CV.items().items())
    parser = argparse.ArgumentParser(
        description=f"""ChatGPT client speakers: {cv_list}""")
    parser.add_argument(
        "--character",
        "-c",
        default="ChatGPT",
        help="AIキャラクタ指定(default=ChatGPT)",
    )
    parser.add_argument(
        "--listen",
        "-l",
        action="store_true",
        help="""
Listening mode ユーザーの入力をキーボードからではなくマイクから拾う",
""",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gpt-3.5-turbo",
        help="ChatGPTモデル(default=gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--speaker",
        "-s",
        default=None,
        help="VOICEVOX キャラクターボイス(str or int, default None)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        action="count",
        default=0,
        help="""
AI音声の生成先 (-v=SLOW, -vv=FAST, -vvv=LOCAL, default=None = 音声で話さない)""",
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
    ai = ai_constructor(listen=args.listen,
                        model=args.model,
                        name=args.character,
                        speaker=args.speaker,
                        voice=Mode(args.voice),
                        character_file=args.yaml)
    # Start chat
    print("空行で入力確定, qまたはexitで会話終了")
    asyncio.run(ai.ask())
