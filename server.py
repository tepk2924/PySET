## SERVER ##

import socket
import threading
import json
from set_game import *

client_sockets = []

## Server IP and Port ##

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9999

game = GameState()
clients = {}
lock = threading.Lock()
board_update_pending = {}

########## processing in thread ##
## new client, new thread ##

def card_to_list(c: SetCard):
    return [c.color, c.shape, c.count, c.fill]

def list_to_card(lst):
    return SetCard(*lst)

def handle_client(conn, addr):
    global board_update_pending
    player_id = f"{addr[0]}:{addr[1]}"
    print(f"{player_id} connected")

    with lock:
        clients[player_id] = conn
        game.add_player(player_id)
        board_update_pending[player_id] = False

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            msg = json.loads(data.decode())

            if msg["type"] == "claim_set":
                with lock:
                    if game.game_over:
                        success = False
                    else:
                        cards_indices = msg["cards_idx"]
                        success = game.try_claim(player_id, cards_indices)                
                if success:
                    for key in board_update_pending:
                        board_update_pending[key] = True

            elif msg["type"] == "current_board":
                if board_update_pending[player_id] == True:
                    do_update = True
                    board_update_pending[player_id] = False
                else:
                    do_update = False
                msg = {
                    "type": "state",
                    "board": [card_to_list(c) for c in game.board],
                    "scores": game.scores,
                    "game_over": game.game_over,
                    "do_update": do_update
                }
                data = json.dumps(msg).encode()
                conn.sendall(data)
    except ConnectionResetError:
        with lock:
            print(f"{player_id} disconnected")
            clients.pop(player_id, None)
            game.remove_player(player_id)

        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"SET server started with host ip : {HOST}")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

if __name__ == "__main__":
    main()