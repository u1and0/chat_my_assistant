"""VOICEVOX setting
Mode: VOICEVOXの音声生成先の列挙型
CV: キャラクター音声の列挙型"""
from enum import IntEnum, auto


class Mode(IntEnum):
    """VOICEVOX mode"""
    NONE = 0
    SLOW = auto()
    FAST = auto()
    LOCAL = auto()


class CV(IntEnum):
    """VOICEVOX Characters Voice IDs

    $ curl -fsSL 'https://api.su-shiki.com/v2/voicevox/speakers?key={API_KEY}'
        | jq
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
    $ curl -fsSL 'https://api.su-shiki.com/v2/voicevox/speakers?key={API_KEY}'
        | jq '.[] | "\(.name)\(.styles[].name) = \(.styles[].id)"'


    Usage:
        >>> CV["ずんだもんあまあま"] == 1
        True
        >>> int(CV["ずんだもんあまあま"] )
        1
        >>> CV(2)
        四国めたんノーマル
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

    # ナースロボ＿タイプＴノーマル だとIntEnumが正しく読み込まない
    ナースロボタイプノーマル = 47
    ナースロボタイプ楽々 = 48
    ナースロボタイプ恐怖 = 49
    ナースロボタイプ内緒話 = 50

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
    def items(cls):
        """CV一覧
        ID: キャラクター名 の辞書を返す。
        WARNING: IDに抜けがあるとValueErrorで一覧表示できない
        """
        return {int(p): p for p in cls}

    @classmethod
    def from_string(cls, value):
        """
        >>> CV(2)
        四国めたんノーマル
        """
        return cls[value].name
