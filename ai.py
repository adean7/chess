import random


class AI:
    piece_scores = {'k': 0,
                    'q': 9,
                    'r': 5,
                    'b': 3,
                    'n': 3,
                    'p': 1,
                    '-': 0}

    checkmate = 1000 #float('inf')
    stalemate = 0

    max_depth = 4



def make_ai_move(prog, game_state, comp):
    ai_move = find_best_move_nega_max_a_b(game_state, comp)

    if ai_move is None:
        ai_move = find_random_move(game_state)

    game_state.make_move(ai_move)

    prog.move_made = True


def find_best_move_nega_max_a_b(game_state, comp):
    global next_move

    next_move = None

    find_move_nega_max_a_b(game_state, game_state.valid_moves, comp,
                          comp.max_depth, -1 * comp.checkmate, comp.checkmate,
                          1 if game_state.white_move else -1)

    return next_move


def find_move_nega_max_a_b(game_state, valid_moves, comp, current_depth,
                           alpha, beta, turn_multiplier):
    global next_move

    if current_depth == 0:
        return turn_multiplier * score_board(game_state, comp)

    # can add move ordering later to improve efficiency

    shuffled_moves = random.sample(valid_moves, len(valid_moves))

    max_score = -1 * comp.checkmate

    for move in shuffled_moves:
        game_state.make_move(move, quick=True)

        #next_moves = game_state.get_valid_moves(return_moves=True)

        score = -1 * find_move_nega_max_a_b(game_state,
                                            game_state.valid_moves, comp,
                                            current_depth - 1,
                                            -beta, -alpha,
                                            -1 * turn_multiplier)

        if score > max_score:
            max_score = score
            if current_depth == comp.max_depth:
                next_move = move

        game_state.undo_move()

        if max_score > alpha:
            alpha = max_score

        if alpha >= beta:
            break

    return max_score




def find_best_move_nega_max(game_state, comp):
    global next_move

    next_move = None

    find_move_nega_max(game_state, game_state.valid_moves, comp,
                       comp.max_depth,
                       1 if game_state.white_move else -1)

    return next_move


def find_move_nega_max(game_state, valid_moves, comp, current_depth,
                       turn_multiplier):
    global next_move

    if current_depth == 0:
        return turn_multiplier * score_board(game_state, comp)

    shuffled_moves = random.sample(valid_moves, len(valid_moves))

    max_score = -1 * comp.checkmate

    for move in shuffled_moves:
        game_state.make_move(move, quick=True)

        #next_moves = game_state.get_valid_moves(return_moves=True)

        score = -1 * find_move_nega_max(game_state, game_state.valid_moves,
                                        comp, current_depth - 1,
                                        -1 * turn_multiplier)

        if score > max_score:
            max_score = score
            if current_depth == comp.max_depth:
                next_move = move

        game_state.undo_move()

    return max_score




def find_best_move_min_max(game_state, comp):
    global next_move

    next_move = None

    find_move_min_max(game_state, game_state.valid_moves, comp,
                      comp.max_depth, game_state.white_move)

    return next_move


def find_move_min_max(game_state, valid_moves, comp, current_depth,
                      white_move):
    global next_move

    if current_depth == 0:
        return score_material(game_state.board, comp.piece_scores)

    shuffled_moves = random.sample(valid_moves, len(valid_moves))

    if white_move:
        max_score = -comp.checkmate

        for move in shuffled_moves:
            game_state.make_move(move)
            next_moves = game_state.get_valid_moves(return_moves=True)
            score = find_move_min_max(game_state, next_moves, comp,
                                      current_depth - 1, white_move=False)

            if score > max_score:
                max_score = score
                if current_depth == comp.max_depth:
                    next_move = move

            game_state.undo_move()

        return max_score

    else:
        min_score = comp.checkmate

        for move in shuffled_moves:
            game_state.make_move(move)
            next_moves = game_state.get_valid_moves(return_moves=True)
            score = find_move_min_max(game_state, next_moves, comp,
                                      current_depth - 1, white_move=True)

            if score < min_score:
                min_score = score
                if current_depth == comp.max_depth:
                    next_move = move

            game_state.undo_move()

        return min_score




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




def score_board(game_state, comp):
    if game_state.checkmate:
        if game_state.white_move:
            return -1 * comp.checkmate
        else:
            return +1 * comp.checkmate
    elif game_state.stalemate:
        return comp.stalemate

    score = score_material(game_state.board, comp.piece_scores)

    return score


def score_material(board, piece_scores):
    score = 0

    for row in board:
        for square in row:
            score += piece_scores[square[1]] * (+1 if square[0] == 'w' else -1)

    return score
