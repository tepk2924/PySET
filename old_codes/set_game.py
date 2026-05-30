from enum import IntEnum
from dataclasses import dataclass
from old_codes.enums import *
import itertools
import random

@dataclass(frozen=True)
class SetCard:
    color: ColorEnum
    shape: ShapeEnum
    count: int
    fill: FillEnum

def is_set(c1: SetCard, c2: SetCard, c3: SetCard) -> bool:
    for attr in ("color", "shape", "count", "fill"):
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
        SetCard(c, s, n, f)
        for c in range(1, 4)
        for s in range(1, 4)
        for n in range(1, 4)
        for f in range(1, 4)
    ]
    random.shuffle(deck)
    return deck

class GameState:
    def __init__(self):
        self.deck = make_deck()
        self.board: list[SetCard] = []
        self.scores: dict[str, int] = {}
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
    
    def add_player(self, player_id: str):
        self.scores[player_id] = 0

    def remove_player(self, player_id: str):
        self.scores.pop(player_id, None)
    
    def try_claim(self, player_id: str, card_indices: list[int]) -> bool:
        if self.game_over:
            return False
        
        idx1, idx2, idx3 = card_indices
        cards = [self.board[idx1], self.board[idx2], self.board[idx3]]

        if not is_set(*cards):
            return False

        # 성공
        for c in cards:
            self.board.remove(c)

        self.scores[player_id] += 1

        # 보드 유지 (최소 12장)
        if len(self.board) < 12:
            self.deal(3)

        self.ensure_set()
        return True