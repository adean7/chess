import ai
import engine
import pygame as p

#from multiprocessing import Process


class Programme:
    def __init__(self, colors=None,
                 width_board=512, height_board=512, dimension=8, max_fps=60,
                 human_player_one=False, human_player_two=False,
                 undo_moves=False):
        self.width_board = width_board
        self.height_board = height_board
        self.dimension = dimension
        self.sq_size = self.height_board // self.dimension
        self.max_fps = max_fps
        self.clock = p.time.Clock()

        self.undo_moves = undo_moves

        self.colors = colors if colors is not None else \
            {'fill'         : p.Color('white'),
             'board1'       : p.Color(255, 204, 255),
             'board2'       : p.Color(255, 255, 255),
             'sq_selected'  : p.Color('purple'),
             'valid_moves'  : p.Color('yellow'),
             'post_move'    : p.Color('red'),
             'move_log_bar' : p.Color(50, 50, 50),
             'move_log_text': p.Color('white'),
             'end_game_text': p.Color('black'),
             'result'       : p.Color('white')}

        self.fonts = {'move_log_text': p.font.SysFont('sfnsmono', size=16,
                                                 bold=False, italic=False),

                      'end_game'     : p.font.SysFont('Verdana', size=32,
                                                 bold=True,  italic=False),

                      'result'       : p.font.SysFont('Verdana', size=32,
                                                      bold=True, italic=False)}

        self.width_move_log = width_board // 2
        self.height_move_log = self.height_board
        self.move_log_padding = 5
        self.move_log_line_spacing = 2
        self.move_love_text_object_height = self.fonts['move_log_text'].render(
                'O-O-O', 0, self.colors['move_log_text']).get_height()
        self.num_recent_moves = 8

        self.screen = p.display.set_mode((self.width_board +
                                          self.width_move_log,
                                          self.height_board))
        self.screen.fill(self.colors['fill'])

        self.pieces = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp',
                       'bk', 'bq', 'br', 'bb', 'bn', 'bp']
        self.get_pieces_images()

        self.move_made = False
        self.mouseup = None
        self.mousedown = None
        self.piece_selected = None
        self.piece_selected_square = ()
        self.piece_held = None
        self.piece_held_origin = ()
        self.game_over = False

        self.human_player_one = human_player_one
        self.human_player_two = human_player_two
        self.human_turn = None

        self.running = True

    def reset(self):
        self.move_made = False
        self.mouseup = None
        self.mousedown = None
        self.piece_selected = None
        self.piece_selected_square = ()
        self.piece_held = None
        self.piece_held_origin = ()
        self.game_over = False

    def get_pieces_images(self):
        self.pieces_images = {}
        for string in self.pieces:
            self.pieces_images[string] = p.transform.scale(p.image.load(
                "images/" + string + ".png").convert_alpha(), (self.sq_size,
                                                               self.sq_size))

    def draw_game_state(self, game_state):
        self.draw_board()
        self.highlight_squares_pre_move(game_state)
        self.highlight_squares_post_move(game_state.move_log)
        self.draw_pieces(game_state.board)
        self.draw_move_log(game_state.move_log)

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
        if self.piece_held_origin != ():
            row = self.piece_held_origin[0]
            col = self.piece_held_origin[1]
            highlight = True
        elif self.piece_selected_square != ():
            row = self.piece_selected_square[0]
            col = self.piece_selected_square[1]
            highlight = True
        else:
            highlight = False

        if highlight:
            if game_state.board[row][col][0] == ('w' if
            game_state.white_move else 'b'):
                surface = p.Surface((self.sq_size, self.sq_size))
                surface.set_alpha(100) # transparency value
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

    def draw_move_log(self, move_log):
        rect = p.Rect(self.width_board,    0,
                      self.width_move_log, self.height_board)

        p.draw.rect(self.screen, self.colors['move_log_bar'], rect)

        text_y = self.move_log_padding

        recent_moves = move_log[-(2*self.num_recent_moves)+len(move_log)%2:]
        starting_num = max(0, len(move_log) - len(recent_moves))

        for move_num in range(0, len(recent_moves), 2):
            string = '{:>3d}. {:>7s} {:>7s}'.format(
                1 + ((move_num + starting_num) // 2),
                str(recent_moves[move_num]),
                str(recent_moves[move_num+1]) \
                    if move_num+1 < len(recent_moves) else '')
            text_object = self.fonts['move_log_text'].render(
                string, 0, self.colors['move_log_text'])

            text_location = rect.move(self.move_log_padding, text_y)
            self.screen.blit(text_object, text_location)

            text_y += text_object.get_height() + self.move_log_line_spacing

    def draw_end_game_text(self, text):
        text_object = self.fonts['end_game'].render(text, 0, self.colors[
            'end_game_text'])

        text_location = p.Rect(0, 0, self.width_board, self.height_board).move(
            (self.width_board - text_object.get_width()) / 2,
            (self.height_board - text_object.get_height()) / 2)

        self.screen.blit(text_object, text_location)

    def draw_result(self, text):
        text_object = self.fonts['result'].render(text, 0,
                                                  self.colors['result'])

        text_location = p.Rect(self.width_board, 0,
                               self.width_move_log, self.height_move_log).move(
            (self.width_move_log - text_object.get_width()) / 2,
            (self.move_love_text_object_height + self.move_log_line_spacing) *
            self.num_recent_moves + 10)

        self.screen.blit(text_object, text_location)


    def animate_move(self, white_move):
        if self.piece_held[0] == ('w' if white_move else 'b'):
            mouse_col, mouse_row = p.mouse.get_pos()

            start_square = p.Rect(self.piece_held_origin[1] * self.sq_size,
                                  self.piece_held_origin[0] * self.sq_size,
                                  self.sq_size,
                                  self.sq_size)

            p.draw.rect(self.screen, self.colors['sq_selected'],
                        start_square)

            rect = p.Rect(mouse_col - self.sq_size//2,
                          mouse_row - self.sq_size//2,
                          self.sq_size,
                          self.sq_size)

            self.screen.blit(self.pieces_images[self.piece_held],
                             rect)

        #p.display.update(rect)
        p.display.flip()

    def try_to_hold_piece(self, game_state):
        piece = game_state.board[self.mousedown.row][self.mousedown.col]

        if piece[0] == ('w' if game_state.white_move else 'b'):
            self.piece_held = piece
            self.piece_held_origin = (self.mousedown.row,
                                      self.mousedown.col)

    def get_mouse_click(self, pos):
        x, y = pos

        col = x // self.sq_size
        row = y // self.sq_size

        return Click(x, y, row, col)

    def attempt_move(self, move, game_state):
        for m in game_state.valid_moves:
            if move == m:
                game_state.make_move(m)
                self.move_made = True
                break



class Click:
    def __init__(self, x, y, row, col):
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.on_the_board = True if (0 <= self.row <= 7 and
                                     0 <= self.col <= 7) else False

    def __eq__(self, other):
        return True if (self.row == other.row and self.col == other.col) \
            else False



def manage_event(e, prog, gs):
    # we click the mouse
    if e.type == p.MOUSEBUTTONDOWN:
        prog.mousedown = prog.get_mouse_click(p.mouse.get_pos())

        if prog.mousedown.on_the_board:
            prog.try_to_hold_piece(gs)

    elif e.type == p.MOUSEBUTTONUP:
        if prog.mousedown is not None:
            prog.mouseup = prog.get_mouse_click(p.mouse.get_pos())

            if prog.mouseup.on_the_board:
                # if same square then highlight that pieces moves
                if prog.mouseup == prog.mousedown and prog.piece_selected is\
                        None:
                    prog.piece_selected = prog.piece_held
                    prog.piece_selected_square = prog.piece_held_origin

                elif prog.piece_held is not None:
                    move = engine.Move(prog.piece_held_origin,
                                       (prog.mouseup.row, prog.mouseup.col),
                                       gs.board)

                    prog.attempt_move(move, gs)

                    prog.piece_selected = prog.piece_held
                    prog.piece_selected_square = prog.piece_held_origin

                elif prog.piece_selected is not None:
                    # try to make move to a valid square, other just
                    # unselect the piece
                    move = engine.Move(prog.piece_selected_square,
                                       (prog.mouseup.row, prog.mouseup.col),
                                       gs.board)

                    prog.attempt_move(move, gs)

                    prog.piece_selected = None
                    prog.piece_selected_square = ()

            prog.piece_held = None
            prog.piece_held_origin = ()

            prog.mousedown = None
            prog.mouseup = None

    elif e.type == p.KEYDOWN:
        if e.key == p.K_ESCAPE:
            prog.mousedown = None
            prog.piece_held = None
            prog.piece_held_origin = ()
            prog.piece_selected = None
            prog.piece_selected_square = ()

        elif e.key == p.K_r:
            prog.reset()
            # game_state reset is done in the main function

        elif e.key == p.K_u and prog.undo_moves:
            gs.undo_move()
            prog.move_made = True
            prog.game_over = False

    elif e.type == p.QUIT:
        prog.running = False


def main():
    p.init()

    prog = Programme(human_player_one=True,
                     human_player_two=True,
                     undo_moves=True)

    gs = engine.GameState()

    comp = ai.AI()

    while prog.running:
        prog.human_turn = (gs.white_move and prog.human_player_one) or \
                          (not gs.white_move and prog.human_player_two)

        for e in p.event.get():
            manage_event(e, prog, gs)

            # perform any NON-BOARD actions using prog.mouseup:
            if prog.mouseup is not None and not prog.piece_held:
                # perform whatever action is in that place
                pass

            # check for game reset here because code is a bit ugly :/
            if e.type == p.KEYDOWN and e.key == p.K_r:
                gs = engine.GameState()

        if not prog.game_over and not prog.human_turn and not prog.move_made:
            ai.make_ai_move(prog, gs, comp)


        if not prog.game_over:
            prog.draw_game_state(gs)

            #if prog.mousedown != ():
            #    prog.animate_move(gs)
            if prog.piece_held is not None:
                prog.animate_move(gs.white_move)

            #if prog.move_made:
            #    gs.get_valid_moves()
            #    prog.move_made = False
            prog.move_made = False

        if gs.checkmate:
            prog.game_over = True
            prog.draw_end_game_text(
                '{} wins by checkmate!'.format('Black' if gs.white_move
                                               else 'White'))
            prog.draw_result('1-0' if not gs.white_move else '0-1')

        elif gs.stalemate:
            prog.game_over = True
            prog.draw_end_game_text('Stalemate')
            prog.draw_result('1/2-1/2')

        elif gs.is_three_fold:
            prog.game_over = True
            prog.draw_end_game_text('Three-fold repetition')
            prog.draw_result('1/2-1/2')

        elif gs.is_fifty_rule:
            prog.game_over = True
            prog.draw_end_game_text('Fifty moves rule')
            prog.draw_result('1/2-1/2')

        # TODO: need to include impossibility of checkmate too

        prog.clock.tick(prog.max_fps)

        p.display.flip()



if __name__ == '__main__':
    main()
