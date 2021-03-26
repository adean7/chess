import network
import client


def single_game(game_type, color='white'):
    plyr = 0 if color == 'white' else 1

    prog = client.Programme(player=plyr,
                            network=None,
                            game_mode='singleplayer',
                            game_type=game_type)

    while prog.prog_running:
        prog.update_human_turn()

        prog.manage_events()

        prog.try_to_make_move()

        prog.get_ai_move()

        if not prog.game_state.game_over:
            prog.draw_game_state()

            if prog.piece_held is not None:
                prog.animate_move()

            prog.move_made = False

        prog.check_endgame()

        prog.tick_clock()

        client.update_display()


def double_game(game_type):
    pass


def online_game(ntwrk, game_type):
    plyr = ntwrk.get_player()

    prog = client.Programme(player=plyr,
                            network=ntwrk,
                            game_mode='online',
                            game_type=game_type)

    while prog.prog_running:
        try:
            prog.get_game_state()
        except:
            prog.prog_running = False
            break

        prog.manage_events()

        prog.try_to_send_move()

        if not prog.game_state.game_over:
            prog.draw_game_state()

            if prog.piece_held is not None:
                prog.animate_move()

            prog.move_made = False

        prog.check_endgame()

        prog.clock.tick(prog.max_fps)

        client.update_display()


def main(game_mode='singleplayer', game_type='blitz'):
    if game_mode == 'singleplayer':
        single_game(game_type)
    elif game_mode == 'doubleplayer':
        double_game(game_type)
    elif game_mode == 'online':
        ntwrk = network.Network()
        if ntwrk.connected:
            online_game(ntwrk, game_type)
        else:
            print('Failed to connect to server.')
            exit(44)


if __name__ == '__main__':
    main('singleplayer')
