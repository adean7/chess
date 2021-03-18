import random


class AI:
    piece_scores = {'k': 0,
                    'q': 9,
                    'r': 6,
                    'b': 3,
                    'n': 3,
                    'p': 1,
                    '-': 0}

    checkmate = 1000 #float('inf')
    stalemate = 0

    depth = 2


def make_ai_move(prog, game_state, comp):
    ai_move = find_best_move_minmax(game_state, comp)
    if ai_move is None:
        ai_move = find_random_move(game_state)
    game_state.make_move(ai_move)
    prog.move_made = True
    #prog.clock.tick(60)


def score_material(board, piece_scores):
    score = 0

    for row in board:
        for square in row:
            score += piece_scores[square[1]] * (+1 if square[0] == 'w' else -1)

    return score


def find_best_move_minmax(game_state, comp):
    global next_move

    next_move = None

    find_move_minmax(game_state, comp)

    return next_move


def find_move_minmax(game_state, comp):
    global next_move

    if comp.depth == 0:
        return score_material(game_state.board, comp.piece_scores)


def find_best_move_basic(game_state, comp):
    turn_multiplier = +1 if game_state.white_move else -1

    opponent_minmax_score = +1 * comp.checkmate

    best_player_move = None

    shuffled_moves = random.sample(game_state.valid_moves,
                                   len(game_state.valid_moves))

    for player_move in shuffled_moves:
        game_state.make_move(player_move)

        #opponent_moves = game_state.get_valid_moves(return_moves=True)
        game_state.get_valid_moves()
        opponent_moves_shuffled = random.sample(game_state.valid_moves,
                                                len(game_state.valid_moves))

        if game_state.stalemate:
            opponent_max_score = comp.stalemate
        elif game_state.checkmate:
            opponent_max_score = -1 * comp.checkmate
        else:
            opponent_max_score = -1 * comp.checkmate

            for opponent_move in opponent_moves_shuffled:
                game_state.make_move(opponent_move)
                game_state.get_valid_moves()

                if game_state.checkmate:
                    score = comp.checkmate
                elif game_state.stalemate:
                    score = comp.stalemate
                else:
                    score = -turn_multiplier * \
                            score_material(game_state.board, comp.piece_scores)

                if score > opponent_max_score:
                    opponent_max_score = score

                game_state.undo_move()

        if opponent_max_score < opponent_minmax_score:
            opponent_minmax_score = opponent_max_score
            best_player_move = player_move

        game_state.undo_move()

    return best_player_move


def find_random_move(game_state):
    return game_state.valid_moves[random.randint(0,
                                                 len(game_state.valid_moves)\
                                                 -1)]