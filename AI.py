import random

piece_scores = {'k': 0,
                'q': 9,
                'r': 6,
                'b': 3,
                'n': 3,
                'p': 1}

checkmate = 1000 #float('inf')
stalemate = 0

def make_ai_move(prog, game_state):
    ai_move = find_random_move(game_state.valid_moves)
    game_state.make_move(ai_move)
    prog.move_made = True
    #prog.clock.tick(60)

def find_random_move(moves):
    return moves[random.randint(0, len(moves)-1)]


def find_best_move(moves):
    return
