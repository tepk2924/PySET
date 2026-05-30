# client.py
import pygame
import socket
import threading
import json
from old_codes.enums import *

def handle_click(pos, cards):
    global selected_cards_indices

    for card in cards:
        if card.rect.collidepoint(pos):
            if card.selected:
                card.selected = False
                selected_cards_indices.remove(card)
            else:
                if len(selected_cards_indices) < 3:
                    card.selected = True
                    selected_cards_indices.append(card)
            break

selected_cards_indices = set()
current_board = []
do_update = False
lock = threading.Lock()
scores = {}

def pygame_thread():
    global current_board
    global do_update
    global selected_cards_indices

    pygame.init()
    screen = pygame.display.set_mode((640, 640))
    start_x = 50
    start_y = 50
    w, h = 80, 120
    gap = 10

    WHITE = (255, 255, 255)
    YELLOW = (255, 255, 0)
    GRAY = (200, 200, 200)
    BLACK = (0, 0, 0)
    running = True
    while running:
        screen.fill(BLACK)
        with lock:
            for i, card_data in enumerate(current_board):
                border = YELLOW if i in selected_cards_indices else GRAY
                row = i % 3
                col = i // 3

                new_x = start_x + col*(w + gap)
                new_y = start_y + row*(h + gap)
                rect = pygame.Rect(
                    new_x,
                    new_y,
                    w,
                    h
                )
                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, border, rect, width=10)

                card_color, card_shape, card_count, card_fill = card_data
                shape_color = {ColorEnum.GREEN: (0, 255, 0),
                               ColorEnum.PURPLE: (255, 0, 255),
                               ColorEnum.RED: (255, 0, 0)}[card_color]

                for idx in range(card_count):
                    min_x, min_y = new_x + 0.2*w, new_y + 0.4*h - 0.15*h*(card_count - 1) + 0.3*h*idx
                    X = lambda v: min_x + 0.1*v*w
                    Y = lambda v: min_y + 0.2*v*h/6
                    max_x, max_y = X(6), Y(6)
                    mid_x, mid_y = X(3), Y(3)
                    half_filler_width = 3
                    border_width = 5
                    if card_shape == ShapeEnum.OVAL:
                        if card_fill == FillEnum.EMPTY:
                            pygame.draw.ellipse(screen, shape_color, pygame.Rect(min_x, min_y, 0.6*w, 0.2*h), width=border_width)
                        elif card_fill == FillEnum.FULL:
                            pygame.draw.ellipse(screen, shape_color, pygame.Rect(min_x, min_y, 0.6*w, 0.2*h), width=0)
                        else:
                            pygame.draw.ellipse(screen, shape_color, pygame.Rect(min_x, min_y, 0.6*w, 0.2*h), width=border_width)
                            for jdx in range(1, 6):
                                pygame.draw.line(screen, shape_color, (X(jdx), Y(3 - (9 - (jdx - 3)**2)**.5)), (X(jdx), Y(3 + (9 - (jdx - 3)**2)**.5)), width=half_filler_width)
                    elif card_shape == ShapeEnum.DIAMOND:
                        if card_fill == FillEnum.EMPTY:
                            pygame.draw.polygon(screen, shape_color, [(min_x, mid_y), (mid_x, max_y), (max_x, mid_y), (mid_x, min_y)], width=border_width)
                        elif card_fill == FillEnum.FULL:
                            pygame.draw.polygon(screen, shape_color, [(min_x, mid_y), (mid_x, max_y), (max_x, mid_y), (mid_x, min_y)], width=0)
                        else:
                            pygame.draw.polygon(screen, shape_color, [(min_x, mid_y), (mid_x, max_y), (max_x, mid_y), (mid_x, min_y)], width=border_width)
                            pygame.draw.line(screen, shape_color, (X(1), Y(2)), (X(1), Y(4)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(2), Y(1)), (X(2), Y(5)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(3), min_y), (X(3), max_y), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(4), Y(1)), (X(4), Y(5)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(5), Y(2)), (X(5), Y(4)), width=half_filler_width)
                    else:
                        if card_fill == FillEnum.EMPTY:
                            pygame.draw.polygon(screen, shape_color, [(X(2), min_y), (X(4), Y(1)), (max_x, min_y), (X(4), max_y), (X(2), Y(5)), (min_x, max_y)], width=border_width)
                        elif card_fill == FillEnum.FULL:
                            pygame.draw.polygon(screen, shape_color, [(X(2), min_y), (X(4), Y(1)), (max_x, min_y), (X(4), max_y), (X(2), Y(5)), (min_x, max_y)], width=0)
                        else:
                            pygame.draw.polygon(screen, shape_color, [(X(2), min_y), (X(4), Y(1)), (max_x, min_y), (X(4), max_y), (X(2), Y(5)), (min_x, max_y)], width=border_width)
                            pygame.draw.line(screen, shape_color, (X(1), Y(3)), (X(1), Y(5.5)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(2), Y(0)), (X(2), Y(5)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(3), Y(0.5)), (X(3), Y(5.5)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(4), Y(1)), (X(4), Y(6)), width=half_filler_width)
                            pygame.draw.line(screen, shape_color, (X(5), Y(0.5)), (X(5), Y(3)), width=half_filler_width)
            
            font = pygame.font.SysFont(None, 24)
            text = font.render(str(scores), True, WHITE)
            screen.blit(text, (start_x, start_y + 3*h + 3*gap))
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    Qx, Rx = divmod(x - start_x, w + gap)
                    Qy, Ry = divmod(y - start_y, h + gap)
                    if Rx < w and Ry < h and Qy < 3:
                        idx = Qx*3 + Qy
                        if idx < len(current_board):
                            if idx in selected_cards_indices:
                                selected_cards_indices.remove(idx)
                            else:
                                selected_cards_indices.add(idx)
                            print(selected_cards_indices)
        pygame.display.flip()

def network():
    global current_board
    global do_update
    global selected_cards_indices
    global scores

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOST = input("host ip : ")
    sock.connect((HOST, 9999))
    while True:
        msg = {
            "type": "current_board"
        }
        sock.sendall(json.dumps(msg).encode())
        data = sock.recv(4096)
        msg = json.loads(data.decode())
        with lock:
            current_board = msg["board"]
            do_update = msg["do_update"]
            scores = msg["scores"]
            if do_update:
                selected_cards_indices = set()
            if len(selected_cards_indices) == 3:
                msg = {
                    "type": "claim_set",
                    "cards_idx": [*selected_cards_indices]
                }
                sock.sendall(json.dumps(msg).encode())
                selected_cards_indices = set()

thread1 = threading.Thread(target=pygame_thread)
thread2 = threading.Thread(target=network)

thread1.start()
thread2.start()