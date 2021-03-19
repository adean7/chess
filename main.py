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
            {'fill'         : p.Color('white'),
             'board1'       : p.Color('white'),
             'board2'       : p.Color('gray'),
             'sq_selected'  : p.Color('purple'),
             'valid_moves'  : p.Color('yellow'),
             'post_move'    : p.Color('red'),
             'end_game_text': p.Color('black')}

        self.fonts = {'move_log': p.font.SysFont('Verdana', size=18,
                                                 bold=False, italic=False),

                      'end_game': p.font.SysFont('Verdana', size=32,
                                                 bold=True,  italic=False)}

        self.screen = p.display.set_mode((self.width, self.height))
        self.screen.fill(self.colors['fill'])

        self.pieces = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp',
                       'bk', 'bq', 'br', 'bb', 'bn', 'bp']
        self.get_pieces_images()

        self.move_made = False
        self.mousedown = ()
        self.game_over = False

        self.human_player_one = human_player_one
        self.human_player_two = human_player_two
        self.human_turn = None

        self.running = True

    def reset(self):
        self.move_made = False
        self.mousedown = ()
        self.game_over = False

    def get_pieces_images(self):
        self.pieces_images = {}
        for string in self.pieces:
            self.pieces_images[string] = p.transform.scale(p.image.load(
                "images/" + string + ".png"), (self.sq_size, self.sq_size))

    def draw_game_state(self, game_state):
        self.draw_board()
        self.highlight_squares_pre_move(game_state)
        self.highlight_squares_post_move(game_state.move_log)
        self.draw_pieces(game_state.board)
        self.draw_move_log(game_state)

    def draw_board(self):
        colors = [self.colors['board1'],
                  self.colors['board2']]

        for row in range(self.dimension):
            for col in range(self.dimension):
                color = colors[(row + col) % 2]
                p.draw.rect(self.screen, color, p.Rect(col * self.sq_size,
                                                       row * self.sq_size,
                                                       self.sq_size,
                                                       self.sq_size))

    def highlight_squares_pre_move(self, game_state):
        if self.mousedown != ():
            row = self.mousedown[0]
            col = self.mousedown[1]
            if game_state.board[row][col][0] == ('w' if game_state.white_move
            else 'b'):
                surface = p.Surface((self.sq_size, self.sq_size))
                surface.set_alpha(100) # transparency value, 0->255 increasing
                surface.fill(self.colors['sq_selected'])
                self.screen.blit(surface, (col * self.sq_size,
                                           row * self.sq_size))
                surface.fill(self.colors['valid_moves'])
                for move in game_state.valid_moves:
                    if move.start_row == row and move.start_col == col:
                        self.screen.blit(surface, (self.sq_size * move.end_col,
                                                self.sq_size * move.end_row))

    def highlight_squares_post_move(self, move_log):
        if len(move_log) != 0:
            move = move_log[-1]

            surface = p.Surface((self.sq_size, self.sq_size))
            surface.set_alpha(100) # transparency value, 0->255 increasing
            surface.fill(self.colors['post_move'])
            self.screen.blit(surface, (move.start_col * self.sq_size,
                                       move.start_row * self.sq_size))
            self.screen.blit(surface, (move.end_col * self.sq_size,
                                       move.end_row * self.sq_size))

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

    def draw_move_log(self, game_state):
        pass

    def draw_end_game_text(self, text):
        text_object = self.fonts['end_game'].render(text, 0, self.colors[
            'end_game_text'])
        text_location = p.Rect(0, 0, self.width, self.height).move(
            (self.width - text_object.get_width()) / 2,
            (self.height - text_object.get_height()) / 2)
        self.screen.blit(text_object, text_location)

    def animate_move(self, game_state):
        row = self.mousedown[0]
        col = self.mousedown[1]

        mouse_col, mouse_row = p.mouse.get_pos()

        piece_selected = game_state.board[row][col]

        if piece_selected != '--':
            if game_state.board[row][col][0] == ('w' if game_state.white_move
            else 'b'):

                start_square = p.Rect(col * self.sq_size,
                                      row * self.sq_size,
                                      self.sq_size,
                                      self.sq_size)

                p.draw.rect(self.screen, self.colors['sq_selected'],
                            start_square)

                self.screen.blit(self.pieces_images[piece_selected],
                                 p.Rect(mouse_col - self.sq_size//2,
                                        mouse_row - self.sq_size//2,
                                        self.sq_size,
                                        self.sq_size))
        p.display.flip()



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
                     human_player_two=True)

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
            prog.draw_game_state(gs)

            if prog.mousedown != ():
                prog.animate_move(gs)

            if prog.move_made:
                gs.get_valid_moves()
                prog.move_made = False

        if gs.checkmate:
            prog.game_over = True
            prog.draw_end_game_text(
                '{} wins by checkmate!'.format('Black' if gs.white_move
                                               else 'White'))
        elif gs.stalemate:
            prog.game_over = True
            prog.draw_end_game_text('Stalemate!')

        prog.clock.tick(prog.max_fps)

        p.display.flip()




if __name__ == '__main__':
    main()

