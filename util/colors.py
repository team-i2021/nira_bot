import enum

class Color(enum.IntEnum):
    # 基本的な色たち
    GREEN = 0x00ff00
    YELLOW = 0xffff00
    RED = 0xff0000
    BLUE = 0x0000ff
    BLACK = 0x000000
    WHITE = 0xffffff

    # エイリアス的な扱い
    NORMAL = 0x00ff00
    ATTENTION = 0xffff00
    ERROR = 0xff0000
