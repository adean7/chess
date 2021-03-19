import ai
import engine
import pygame as p


class Programme:
    def __init__(self, colors=None,
                 width=512, height=512, dimension=8, max_fps=30,
                 human_player_one=False, human_player_two=False):
        self.width = width
        self.height = height
        self.dimension = dimension
        self.sq_size = self.height // self.dimension
        self.max_fps = max_fps
        self.clock = p.time.Clock()

        self.colors = colors if colors is not None else \
            {'board1': 'white',
             'board2': 'gray',
             'sq_selected': 'purple',
             'valid_moves': 'yellow',
             'post_move': 'red',
             'end_game_text': 'black'}

        self.end_game_text_font = 'Helvetica'

        self.screen = p.display.set_mode((self.width, self.height))
        self.screen.fill(p.Color('white'))

        self.pieces = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp', 'bk', 'bq', 'br',
                       'bb', 'bn', 'bp']
        self.get_pieces_images()

        self.running = True
        # self.sq_selected = () # (row, column)
        # self.player_clicks = [] # e.g. [(6,4), (4,4)] moving from (6,4) to (
        # 4,4)

        self.move_made = False
        self.mousedown = ()
        self.game_over = False

        self.human_player_one = human_player_one
        self.human_player_two = human_player_two
        self.human_turn = None

    def reset(self):
        self.move_made = False
        self.mousedown = ()
        self.game_over = False

    def get_pieces_images(self):
        self.pieces_images = {}
        for string in self.pieces:
            self.pieces_images[string] = p.transform.scale(p.image.load(
                "images/" + string + ".png"), (self.sq_size, self.sq_size))

    def draw_board(self):
        colors = [p.Color(self.colors['board1']),
                  p.Color(self.colors['board2'])]

        for row in range(self.dimension):
            for col in range(self.dimension):
                color = colors[(row + col) % 2]
                p.draw.rect(self.screen, color, p.Rect(col * self.sq_size,
                                                       row * self.sq_size,
                                                       self.sq_size,
                                                       self.sq_size))

    def draw_pieces(self, board):
        for row in range(self.dimension):
            for col in range(self.dimension):
                piece = board[row][col]
                if piece != "--":
                    self.screen.blit(self.pieces_images[piece],
                                     p.Rect(col * self.sq_size,
                                            row * self.sq_size,
                                            self.sq_size,
                                            self.sq_size))

    def highlight_squares_pre_move(self, game_state, square_selected):
        if square_selected != ():
            row, col = square_selected
            if game_state.board[row][col][0] == ('w' if game_state.white_move
            else 'b'):
                surface = p.Surface((self.sq_size, self.sq_size))
                surface.set_alpha(100) # transparency value, 0->255 increasing
                surface.fill(p.Color(self.colors['sq_selected']))
                self.screen.blit(surface, (col * self.sq_size,
                                           row * self.sq_size))
                surface.fill(p.Color(self.colors['valid_moves']))
                for move in game_state.valid_moves:
                    if move.start_row == row and move.start_col == col:
                        self.screen.blit(surface, (self.sq_size * move.end_col,
                                                self.sq_size * move.end_row))

    def highlight_squares_post_move(self, game_state):
        if len(game_state.move_log) != 0:
            move = game_state.move_log[-1]

            surface = p.Surface((self.sq_size, self.sq_size))
            surface.set_alpha(100) # transparency value, 0->255 increasing
            surface.fill(p.Color(self.colors['post_move']))
            self.screen.blit(surface, (move.start_col * self.sq_size,
                                       move.start_row * self.sq_size))
            self.screen.blit(surface, (move.end_col * self.sq_size,
                                       move.end_row * self.sq_size))



def draw_game_state(prog, game_state, square_selected):
    prog.draw_board()
    prog.highlight_squares_pre_move(game_state, square_selected)
    prog.highlight_squares_post_move(game_state)
    prog.draw_pieces(game_state.board)


def animate_move(game_state, prog, sq_selected, mouse_pos):
    row = sq_selected[0]
    col = sq_selected[1]

    piece_selected = game_state.board[row][col]

    if piece_selected != '--':
        if game_state.board[row][col][0] == ('w' if game_state.white_move
        else 'b'):
            color = p.Color(prog.colors['sq_selected'])

            start_square = p.Rect(col * prog.sq_size,
                                  row * prog.sq_size,
                                  prog.sq_size,
                                  prog.sq_size)

            p.draw.rect(prog.screen, color, start_square)

            prog.screen.blit(prog.pieces_images[piece_selected],
                             p.Rect(mouse_pos[0] - prog.sq_size//2,
                                    mouse_pos[1] - prog.sq_size//2,
                                    prog.sq_size,
                                    prog.sq_size))
    p.display.flip()

def draw_end_game_text(prog, text):
    font = p.font.SysFont(prog.end_game_text_font, 32, True, False)
    text_object = font.render(text, 0, p.Color(prog.colors['end_game_text']))
    text_location = p.Rect(0, 0, prog.width, prog.height).move(
        (prog.width  - text_object.get_width())  / 2,
        (prog.height - text_object.get_height()) / 2)
    prog.screen.blit(text_object, text_location)



def manage_event(e, prog, gs):
    if e.type == p.QUIT:
        prog.running = False
    elif e.type == p.KEYDOWN:
        if e.key == p.K_r:
            prog.reset()
            # game_state reset is done in the main function
        elif e.key == p.K_u:
            gs.undo_move()
            prog.move_made = True
            prog.game_over = False

    if not prog.game_over:
        if e.type == p.MOUSEBUTTONDOWN and prog.human_turn:

            location = p.mouse.get_pos()

            col = location[0] // prog.sq_size
            row = location[1] // prog.sq_size

            prog.mousedown = (row, col)

        elif e.type == p.MOUSEBUTTONUP and prog.human_turn:
            location = p.mouse.get_pos()

            col = location[0] // prog.sq_size
            row = location[1] // prog.sq_size

            prog.mouseup = (row, col)

            move = engine.Move(prog.mousedown, prog.mouseup, gs.board)

            for m in gs.valid_moves:
                if move == m:
                    gs.make_move(m)
                    prog.move_made = True
                    break

            prog.mousedown = ()


def main():
    p.init()

    prog = Programme(human_player_one=True,
                     human_player_two=False)

    gs = engine.GameState()

    comp = ai.AI()

    while prog.running:
        prog.human_turn = (gs.white_move and prog.human_player_one) or \
                          (not gs.white_move and prog.human_player_two)

        for e in p.event.get():
            manage_event(e, prog, gs)
            # check for game reset here because code is a bit ugly :/
            if e.type == p.KEYDOWN and e.key == p.K_r:
                gs = engine.GameState()

        if not prog.game_over and not prog.human_turn and not prog.move_made:
            ai.make_ai_move(prog, gs, comp)

        if not prog.game_over:
            draw_game_state(prog, gs, prog.mousedown)

            if prog.mousedown != ():
                animate_move(gs, prog, prog.mousedown, p.mouse.get_pos())

            if prog.move_made:
                gs.get_valid_moves()
                prog.move_made = False

        if gs.checkmate:
            prog.game_over = True
            draw_end_game_text(prog,
                               '{} wins by checkmate!'.format('Black' if
                                                              gs.white_move
                                                              else 'White'))
        elif gs.stalemate:
            prog.game_over = True
            draw_end_game_text(prog, 'Stalemate!')

        prog.clock.tick(prog.max_fps)

        p.display.flip()




if __name__ == '__main__':
    main()

