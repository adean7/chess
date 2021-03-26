import socket
import _thread
import pickle

import engine

server = "192.168.0.11"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print("Waiting for a connection, Server Started")


def threaded_client(conn, p, game_id):
    global id_count

    #conn.send(str.encode(str(p)))
    conn.send(pickle.dumps(p))

    while True:
        for ID in games:
            game = games[ID]

            if game.timed_game and game.game_started:
                game.update_timers()

        try:
            data = pickle.loads(conn.recv(2048))
            #data = conn.recv(4096).decode()
            #print('Received: ', data)
        except:
            print(20)
            break

        if game_id in games:
            print(games)
            game = games[game_id]

            if not data:
                print('Disconnected')
                print(30)
                break
            else:
                #if data == 'reset':
                #    game = engine.GameState(game_id)
                #elif data != 'get':
                if data != 'get':
                    game.make_move(game.valid_moves[int(data)])

            print('Sending : ', game)
            conn.sendall(pickle.dumps(game))

            # conn.sendall(str.encode(reply))

        else:
            print(10)
            break

    try:
        del games[game_id]
    except KeyError:
        pass

    id_count -= 1

    print('Lost connection')
    conn.close()


games = {}
id_count = 0

while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    id_count += 1
    p = 0
    game_id = (id_count - 1) // 2

    if id_count % 2 == 1:
        games[game_id] = engine.GameState(game_id)
    else:
        games[game_id].ready = True
        p = 1

    _thread.start_new_thread(threaded_client, (conn, p, game_id))
