from enum import IntEnum
from dataclasses import dataclass
import itertools
import random
import discord

class ColorEnum(IntEnum):
    RED = 1
    GREEN = 2
    PURPLE = 3

class ShapeEnum(IntEnum):
    SQUARE = 1
    CIRCLE = 2
    HEART = 3

class PosEnum(IntEnum):
    LEFT = 1
    MID = 2
    RIGHT = 3

@dataclass(frozen=True)
class SetCard:
    color: ColorEnum
    shape: ShapeEnum
    count: int
    pos: PosEnum

    def __str__(self):
        return f"[{self.color}, {self.shape}, {self.count}, {self.pos}]"
    
    def __repr__(self):
        return f"SetCard({self.color}, {self.shape}, {self.count}, {self.pos})"
    
    def __iter__(self):
        yield self.color
        yield self.shape
        yield self.count
        yield self.pos

def is_set(c1: SetCard, c2: SetCard, c3: SetCard) -> bool:
    for attr in ("color", "shape", "count", "pos"):
        vals = {
            getattr(c1, attr),
            getattr(c2, attr),
            getattr(c3, attr)
        }
        if len(vals) == 2:
            return False
    return True

def make_deck() -> list[SetCard]:
    deck = [
        SetCard(c, s, n, p)
        for c in range(1, 4)
        for s in range(1, 4)
        for n in range(1, 4)
        for p in range(1, 4)
    ]
    random.shuffle(deck)
    return deck

class GameState:
    def __init__(self):
        self.deck = make_deck()
        self.board: list[SetCard] = []
        self.game_over = False

        self.deal(12)
        self.ensure_set()
    
    def is_set_exist(self):
        for c1, c2, c3 in itertools.combinations(self.board, 3):
            if is_set(c1, c2, c3):
                return True
        return False

    def ensure_set(self):
        while not self.is_set_exist():
            if len(self.deck) < 3:
                self.game_over = True
            self.deal(3)

    def deal(self, n: int):
        for _ in range(n):
            if not self.deck:
                return
            self.board.append(self.deck.pop())
    
    def try_claim(self, idx1, idx2, idx3) -> bool:
        if self.game_over:
            return False
        
        cards = [self.board[idx1 - 1], self.board[idx2 - 1], self.board[idx3 - 1]]

        if not is_set(*cards):
            return False

        for c in cards:
            self.board.remove(c)

        if len(self.board) < 12:
            self.deal(3)

        self.ensure_set()
        return True

with open("APIkey.txt", "r") as f:
    APIkey = f.readline().rstrip()

bot = discord.Bot()

is_game_going:bool = False
game:GameState = None
score_board:dict = None

@bot.slash_command()
async def new_game(ctx:discord.commands.context.ApplicationContext):
    global is_game_going
    global game
    global score_board
    score_board = {}
    is_game_going = True
    game = GameState()
    await ctx.respond("새 게임을 시작합니다!")

@bot.slash_command()
async def quit_game(ctx:discord.commands.context.ApplicationContext):
    global is_game_going
    global game
    global score_board
    score_board = None
    is_game_going = False
    game = None
    await ctx.respond("게임을 그만합니다!")

def get_board(board:list[SetCard]) -> list[str]:
    n_rows = len(board)//3
    n_char_rows = 4*n_rows - 1
    chars = [[" " for _ in range(13)] for _ in range(n_char_rows)]
    black_chardict = {ShapeEnum.CIRCLE: ":black_circle:",
                      ShapeEnum.HEART: ":black_heart:",
                      ShapeEnum.SQUARE: ":black_large_square:"}
    chardict = {
        (ColorEnum.RED   , ShapeEnum.SQUARE): ":red_square:",
        (ColorEnum.RED   , ShapeEnum.CIRCLE): ":red_circle:",
        (ColorEnum.RED   , ShapeEnum.HEART ): ":red_heart:",
        (ColorEnum.GREEN , ShapeEnum.SQUARE): ":green_square:",
        (ColorEnum.GREEN , ShapeEnum.CIRCLE): ":green_circle:",
        (ColorEnum.GREEN , ShapeEnum.HEART ): ":green_heart:",
        (ColorEnum.PURPLE, ShapeEnum.SQUARE): ":purple_square:",
        (ColorEnum.PURPLE, ShapeEnum.CIRCLE): ":purple_circle:",
        (ColorEnum.PURPLE, ShapeEnum.HEART ): ":purple_heart:",
                }
    for idx in range(n_char_rows):
        if idx % 4 != 3:
            chars[idx][0] = "."
            chars[idx][4] = "  "
            chars[idx][8] = "  "
            chars[idx][12] = "."
    for idx in range(len(board)):
        R, C = divmod(idx, 3)
        baser, basec = 4*R, 4*C + 1
        color, shape, count, pos = board[idx]
        black_char = black_chardict[shape]
        char = chardict[(color, shape)]
        for jdx in range(3):
            for kdx in range(3):
                chars[baser + jdx][basec + kdx] = black_char
        for jdx in range(count):
            chars[baser + jdx][basec + pos - 1] = char
    return ["".join(line) for line in chars]

@bot.slash_command()
async def try_set(ctx:discord.commands.context.ApplicationContext,
              first,
              second,
              third):
    global is_game_going
    global game
    global score_board
    value_error_handle = False
    try:
        first = int(first)
        second = int(second)
        third = int(third)
    except:
        value_error_handle = True
    if value_error_handle:
        await ctx.respond("서로 다른 숫자 값 3개를 입력하세요.")
    elif not is_game_going:
        await ctx.respond("먼저 Set 게임을 시작하세요.")
    elif first == second or second == third or third == first:
        await ctx.respond("모두 다른 카드를 선택해주세요.")
    elif first > len(game.board) or second > len(game.board) or third > len(game.board):
        await ctx.respond(f"현재 나와있는 카드의 수인 {len(game.board)} 이하의 수를 입력하세요.")
    else:
        success = game.try_claim(first, second, third)
        sending_txts = []
        author = str(ctx.author)
        if author not in score_board:
            score_board[author] = 0
        if success:
            score_board[author] += 1
            sending_txts.append(f"Set이 맞습니다! {author} 1점 득점!")
            sending_txts.append(f"현재 보드 : ")
            sending_txts += get_board(game.board)
        else:
            score_board[author] -= 1
            sending_txts.append(f"Set이 아닙니다! {author} 1점 감점!")
        if game.game_over:
            sending_txts.append(f"게임 끝!")
            sending_txts.append(f"스코어 : ")
            sending_txts.append(f"{score_board}")
            is_game_going = False
            game = None
            score_board = {}
        await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def score(ctx:discord.commands.context.ApplicationContext):
    global is_game_going
    global score_board
    if not is_game_going:
        await ctx.respond("먼저 Set 게임을 시작하세요.")
    else:
        sending_txts = []
        sending_txts.append("스코어 : ")
        sending_txts.append(f"{score_board}")
        await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def board(ctx:discord.commands.context.ApplicationContext):
    global is_game_going
    global game
    if not is_game_going:
        await ctx.respond("먼저 Set 게임을 시작하세요.")
    else:
        sending_txts = []
        sending_txts.append("현재 보드 : ")
        sending_txts += get_board(game.board)
        sending_txts.append(f"덱에 남은 장수 : {len(game.deck)}")
        await ctx.respond("\n".join(sending_txts))

bot.run(APIkey)