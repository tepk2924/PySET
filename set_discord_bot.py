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
                break
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

is_game_going_dict:dict[int, bool] = {}
game_dict:dict[int, GameState] = {}
score_board_dict:dict[int, dict[str, int]] = {}

@bot.slash_command()
async def new_game(ctx:discord.commands.context.ApplicationContext):
    global is_game_going_dict
    global game_dict
    global score_board_dict
    guild_id = ctx.guild_id
    is_game_going_dict[guild_id] = True
    game = GameState()
    game_dict[guild_id] = game
    score_board_dict[guild_id] = {}
    sending_txts = []
    sending_txts.append("=================새 게임을 시작합니다!=================")
    sending_txts.append(f"현재 보드 : ")
    sending_txts += get_board(game.board)
    sending_txts.append(f"덱에 남은 장수 : {len(game.deck)}")
    await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def quit_game(ctx:discord.commands.context.ApplicationContext):
    global is_game_going_dict
    global game_dict
    global score_board_dict
    guild_id = ctx.guild_id
    is_game_going_dict[guild_id] = False
    game_dict[guild_id] = None
    score_board_dict[guild_id] = None
    await ctx.respond("게임을 그만합니다!")

def get_board(board:list[SetCard]) -> list[str]:
    n_rows = len(board)//3
    n_char_rows = 5*n_rows
    chars = [[" " for _ in range(13)] for _ in range(n_char_rows)]
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
        if idx%5 == 3:
            K = 3*(idx - 3)//5
            if K + 1 < 10:
                chars[idx] = f"         [{K + 1}]               [{K + 2}]                [{K + 3}]"
            else:
                chars[idx] = f"       [{K + 1}]              [{K + 2}]               [{K + 3}]"
        elif idx%5 == 4:
            chars[idx] = ""
        else:
            chars[idx][0] = "."
            chars[idx][4] = "//"
            chars[idx][8] = "//"
            chars[idx][12] = "."
    for idx in range(len(board)):
        R, C = divmod(idx, 3)
        baser, basec = 5*R, 4*C + 1
        color, shape, count, pos = board[idx]
        char = chardict[(color, shape)]
        for jdx in range(3):
            for kdx in range(3):
                chars[baser + jdx][basec + kdx] = "      "
        for jdx in range(count):
            chars[baser + jdx][basec + pos - 1] = char
    return ["".join(line) for line in chars]

@bot.slash_command()
async def try_set(ctx:discord.commands.context.ApplicationContext,
                  first:str,
                  second:str,
                  third:str):
    global is_game_going_dict
    global game_dict
    global score_board_dict
    guild_id = ctx.guild_id
    if guild_id not in is_game_going_dict:
        is_game_going_dict[guild_id] = False
        game_dict[guild_id] = None
        score_board_dict[guild_id] = None
    is_game_going = is_game_going_dict[guild_id]
    game = game_dict[guild_id]
    score_board = score_board_dict[guild_id]
    value_error_handle = False
    try:
        first = int(first)
        second = int(second)
        third = int(third)
    except:
        value_error_handle = True
    if not is_game_going:
        await ctx.respond("먼저 Set 게임을 시작하세요.")
    elif value_error_handle:
        await ctx.respond("숫자 값 3개를 입력하세요.")
    elif first == second or second == third or third == first:
        await ctx.respond("모두 다른 카드를 선택해주세요.")
    elif first > len(game.board) or second > len(game.board) or third > len(game.board):
        await ctx.respond(f"현재 나와있는 카드의 수인 {len(game.board)} 이하의 수를 입력하세요.")
    elif first <= 0 or second <= 0 or third <= 0:
        await ctx.respond(f"1 이상의 자연수 세 개를 입력하세요.")
    else:
        success = game.try_claim(first, second, third)
        sending_txts = []
        author = ctx.author.name
        if author not in score_board:
            score_board[author] = 0
        if success:
            score_board[author] += 1
            sending_txts.append(f"Set가 맞습니다! {author} 1점 득점!")
            sending_txts.append(f"현재 보드 : ")
            sending_txts += get_board(game.board)
            sending_txts.append(f"덱에 남은 장수 : {len(game.deck)}")
        else:
            score_board[author] -= 1
            sending_txts.append(f"Set가 아닙니다! {author} 1점 감점!")
        if game.game_over:
            sending_txts.append(f"=======================게임 끝!=======================")
            sending_txts.append(f"최종 스코어 : ")
            sending_txts.append(f"{score_board}")
            max_score = max(score_board.values())
            winners = [key for key in score_board if score_board[key] == max_score]
            sending_txts.append(f"{', '.join(winners)} {'공동 ' if len(winners) >= 2 else ''}승리!")
            is_game_going = False
            game = None
            score_board = {}
        await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def score(ctx:discord.commands.context.ApplicationContext):
    global is_game_going_dict
    global score_board_dict
    guild_id = ctx.guild_id
    if guild_id not in is_game_going_dict:
        is_game_going_dict[guild_id] = False
        game_dict[guild_id] = None
        score_board_dict[guild_id] = None
    is_game_going = is_game_going_dict[guild_id]
    score_board = score_board_dict[guild_id]
    if not is_game_going:
        await ctx.respond("먼저 SET 게임을 시작하세요.")
    else:
        sending_txts = []
        sending_txts.append("스코어 : ")
        sending_txts.append(f"{score_board}")
        await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def board(ctx:discord.commands.context.ApplicationContext):
    global is_game_going_dict
    global game_dict
    guild_id = ctx.guild_id
    if guild_id not in is_game_going_dict:
        is_game_going_dict[guild_id] = False
        game_dict[guild_id] = None
        score_board_dict[guild_id] = None
    is_game_going = is_game_going_dict[guild_id]
    game = game_dict[guild_id]
    if not is_game_going:
        await ctx.respond("먼저 SET 게임을 시작하세요.")
    else:
        sending_txts = []
        sending_txts.append("현재 보드 : ")
        sending_txts += get_board(game.board)
        sending_txts.append(f"덱에 남은 장수 : {len(game.deck)}")
        await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def what_is_set(ctx:discord.commands.context.ApplicationContext):
    sending_txts = [
        "SET 게임은 81장의 카드가 모두 소진될 때 까지 가장 많은 set를 이루는 카드를 가져가는 사람이 이기는 게임.",
        "카드는 4가지 속성이 존재함: 모양(네모, 동그라미, 하트), 개수(1개, 2개, 3개), 위치(좌, 중, 우), 그리고 색깔(보라, 초록, 빨강)",
        "3개의 카드를 고를 때, 4가지의 속성 각각 전부 다르거나, 전부 같으면 그 3개의 카드는 set를 이룬다고 함.",
        "예시를 보고 싶으면 /example"
    ]
    await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def example(ctx:discord.commands.context.ApplicationContext):
    sending_txts = [
        "아래 예시는 set임.",
        ".      :green_circle:      //:red_circle:            //            :purple_circle:.",
        ".      :green_circle:      //:red_circle:            //                  .",
        ".      :green_circle:      //                  //                  .",
        "모양은 전부 같고, 개수는 전부 다르고, 위치는 전부 다르고, 색깔은 전부 다르기 때문.",
        "",
        "아래 예시는 set임.",
        ".      :green_heart:      //      :red_circle:      //      :purple_square:      .",
        ".      :green_heart:      //                  //      :purple_square:      .",
        ".      :green_heart:      //                  //                  .",
        "모양은 전부 다르고, 개수는 전부 다르고, 위치는 전부 같고, 색깔은 전부 다르기 때문.",
        "",
        "아래 예시는 set가 아님.",
        ".:red_heart:            //:red_heart:             //      :red_heart:      .",
        ".:red_heart:            //                   //      :red_heart:      .",
        ".:red_heart:            //                   //                  .",
        "모양은 전부 같고, 개수는 전부 다르고, 색깔은 전부 같지만, 위치는 왼쪽에 있는 거 2개, 가운데에 있는 거 1개라서 set가 아님. ",
        "",
        "그러니까, 어느 한 속성이라도 1:2로 나뉘는 게 있으면 set가 아님."
    ]
    await ctx.respond("\n".join(sending_txts))

@bot.slash_command()
async def help(ctx:discord.commands.context.ApplicationContext):
    sending_txts = [
        "/new_game : 새 SET 게임을 시작",
        "/board : 현재 보드의 상태 확인",
        "/try_set A B C : A, B, C번째 카드를 선택. (A, B, C는 자연수) set이면 1점 득점, 아니면 1점 감점",
        "/score : 현재 획득한 점수 확인",
        "/quit_game : 현재 게임을 그만두기",
        "/what_is_set : SET가 뭔지 설명받기"
    ]
    await ctx.respond("\n".join(sending_txts))

bot.run(APIkey)