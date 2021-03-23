import ai
import engine
import pygame as p

import datetime
import time

#from multiprocessing import Process


def get_pieces_images(pieces, size):
    pieces_images = {}

    for string in pieces:
        pieces_images[string] = p.transform.scale(p.image.load(
            "images/" + string + ".png").convert_alpha(), (size, size))

    return pieces_images


class Programme:
    p.init()

    width_board = 512
    height_board = 512
    dimension = 8
    sq_size = height_board // dimension
    max_fps = 60
    clock = p.time.Clock()

    colors = {'fill'         : p.Color('white'),
              'board1'       : p.Color(255, 204, 255),
              'board2'       : p.Color(255, 255, 255),
              'border'       : p.Color(50, 50, 50),
              'sq_selected'  : p.Color('purple'),
              'valid_moves'  : p.Color('yellow'),
              'post_move'    : p.Color('red'),
              'sidebar'      : p.Color(50, 50, 50),
              'move_log_text': p.Color('white'),
              'timers'       : p.Color('white'),
              'end_game_text': p.Color('black'),
              'result'       : p.Color('white'),

              'black'        : p.Color('black'),
              'white'        : p.Color('white')}

    board_colors = [colors['board1'], colors['board2']]

    fonts = {'move_log_text': p.font.SysFont('sfnsmono', size=16,
                                             bold=False, italic=False),

             'timers'       : p.font.SysFont('sfnsmono', size=24,
                                             bold=True, italic=False),

             'end_game'     : p.font.SysFont('Verdana', size=32,
                                             bold=True,  italic=False),

             'result'       : p.font.SysFont('Verdana', size=32,
                                             bold=True, italic=False)}

    width_sidebar = width_board // 2
    height_sidebar = height_board

    move_log_x_padding = 5
    move_log_y_padding = int(1.5 * sq_size) + 10
    move_log_line_spacing = 2
    move_log_text_object_height = fonts['move_log_text'].render(
        'O-O-O', 0, colors['move_log_text']).get_height()
    num_recent_moves = 8

    screen = p.display.set_mode((width_board + width_sidebar, height_board))
    screen.fill(colors['fill'])

    pieces = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp',
              'bk', 'bq', 'br', 'bb', 'bn', 'bp']

    pieces_images = get_pieces_images(pieces, sq_size)
    pieces_images_small = get_pieces_images(pieces, sq_size // 2)

    def __init__(self, human_player_one=True, human_player_two=False,
                 game_type='rapid'):

        self.move_made = False
        self.mouseup = None
        self.mousedown = None
        self.piece_selected = None
        self.piece_selected_square = ()
        self.piece_held = None
        self.piece_held_origin = ()
        self.game_started = False
        self.game_over = False

        self.human_player_one = human_player_one
        self.human_player_two = human_player_two
        self.human_turn = self.human_player_one

        self.game_type = game_type.lower()
        if self.game_type not in ['rapid', 'blitz', 'bullet', 'standard']:
            print('Game time must be rapid, blitz, bullet or standard.')
            exit(1)

        if (not self.human_player_one or not self.human_player_two) and \
                self.game_type != 'standard':
            print('Cannot have a timed game against the computer.')
            exit(2)

        self.undo_moves = True if self.game_type == 'standard' else False

        self.get_times()

        self.prog_running = True

    '''
    def reset(self):
        self.move_made = False
        self.mouseup = None
        self.mousedown = None
        self.piece_selected = None
        self.piece_selected_square = ()
        self.piece_held = None
        self.piece_held_origin = ()
        self.game_started = False
        self.game_over = False
        self.get_times()
    '''

    def get_times(self):
        self.timed_game = True

        if self.game_type == 'rapid':
            self.time_alert = 30.0
            self.white_time = 600.0
            self.black_time = 600.0
        elif self.game_type == 'blitz':
            self.time_alert = 20.0
            self.white_time = 180.0
            self.black_time = 180.0
        elif self.game_type == 'bullet':
            self.time_alert = 10.0
            self.white_time = 60.0
            self.black_time = 60.0
        elif self.game_type == 'standard':
            self.time_alert = None
            self.white_time = None
            self.black_time = None
            self.timed_game = False

        self.timeout = False

        self.last_time_stamp = None

    def start_timer(self):
        self.last_time_stamp = time.time()

    def update_timers(self, white_move):
        time_diff = time.time() - self.last_time_stamp

        if white_move:
            self.white_time -= time_diff
            if self.white_time <= 0.0:
                self.white_time = 0.0
                self.timeout = True
        else:
            self.black_time -= time_diff
            if self.black_time <= 0.0:
                self.black_time = 0.0
                self.timeout = True

        self.last_time_stamp = time.time()

    def draw_game_state(self, game_state):
        self.draw_board()
        self.highlight_squares_pre_move(game_state)
        self.highlight_squares_post_move(game_state.move_log)
        self.draw_pieces(game_state.board)

        self.draw_sidebar()
        self.draw_pieces_taken(game_state)
        self.draw_move_log(game_state.move_log)

        if self.timed_game:
            self.draw_timers()

    def draw_board(self):
        for row in range(self.dimension):
            for col in range(self.dimension):
                color = self.board_colors[(row + col) % 2]
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
                                                   self.sq_size * move.end_row)
                                         )

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

    def draw_sidebar(self):
        self.sidebar = p.Rect(self.width_board, 0,
                              self.width_sidebar, self.height_board)

        black_bar = p.Rect(self.width_board, 0,
                           self.width_sidebar, self.sq_size)

        white_bar = p.Rect(self.width_board, self.height_board - self.sq_size,
                           self.width_sidebar, self.sq_size)

        p.draw.rect(self.screen, self.colors['sidebar'], self.sidebar)
        p.draw.rect(self.screen, self.colors['black'], black_bar)
        p.draw.rect(self.screen, self.colors['white'], white_bar)

    def draw_pieces_taken(self, game_state):
        self.draw_pieces_taken_func(self.width_board, 0,
                                    game_state.black_taken[:8])

        self.draw_pieces_taken_func(self.width_board, self.sq_size // 2,
                                    game_state.black_taken[8:])

        self.draw_pieces_taken_func(self.width_board, self.height_board -
                                    self.sq_size,
                                    game_state.white_taken[:8])

        self.draw_pieces_taken_func(self.width_board, self.height_board -
                                    self.sq_size // 2,
                                    game_state.white_taken[8:])

    def draw_pieces_taken_func(self, x, y, lst):
        for piece in lst:
            r = p.Rect(x, y, self.sq_size // 2, self.sq_size // 2)
            self.screen.blit(self.pieces_images_small[piece], r)
            x += self.sq_size // 2

    def draw_move_log(self, move_log):
        text_y = self.move_log_y_padding

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

            text_location = self.sidebar.move(self.move_log_x_padding, text_y)
            self.screen.blit(text_object, text_location)

            text_y += text_object.get_height() + self.move_log_line_spacing

    def draw_timers(self):
        if self.white_time < self.time_alert:
            d = datetime.datetime.utcfromtimestamp(self.white_time)
            text_white = datetime.datetime.strftime(d, "%M:%S.%f")[:-5]
        else:
            d = datetime.datetime.utcfromtimestamp(self.white_time)
            text_white = datetime.datetime.strftime(d, "%M:%S")

        if self.black_time < self.time_alert:
            d = datetime.datetime.utcfromtimestamp(self.black_time)
            text_black = datetime.datetime.strftime(d, "%M:%S.%f")[:-5]
        else:
            d = datetime.datetime.utcfromtimestamp(self.black_time)
            text_black = datetime.datetime.strftime(d, "%M:%S")

        object_white = self.fonts['timers'].render(text_white, 0, self.colors[
            'timers'])

        object_black = self.fonts['timers'].render(text_black, 0, self.colors[
            'timers'])

        loc_white = p.Rect(self.width_board, 0, self.width_sidebar,
                           self.height_board).move(
            (self.width_sidebar - object_white.get_width()) / 2,
            self.height_board - int(1.5 * self.sq_size))

        loc_black = p.Rect(self.width_board, 0, self.width_sidebar,
                           self.height_board).move(
            (self.width_sidebar - object_black.get_width()) / 2,
            self.sq_size)

        self.screen.blit(object_white, loc_white)
        self.screen.blit(object_black, loc_black)

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
                               self.width_sidebar, self.height_sidebar).move(
            (self.width_sidebar - text_object.get_width()) / 2,
            self.height_board - int(2.5 * self.sq_size +
                                    text_object.get_height() / 2))

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

                if not self.game_started:
                    self.start_timer()
                    self.game_started = True

                break

    def check_endgame(self, game_state):
        if self.timeout:
            self.game_over = True
            if not game_state.white_move:
                self.draw_end_game_text('Black timeout. White wins!')
                self.draw_result('1-0')
            else:
                self.draw_end_game_text('White timeout. Black wins!')
                self.draw_result('0-1')

        elif game_state.checkmate:
            self.game_over = True
            self.draw_end_game_text(
                '{} wins by checkmate!'.format('Black' if game_state.white_move
                                               else 'White'))
            self.draw_result('1-0' if not game_state.white_move else '0-1')

        elif game_state.stalemate:
            self.game_over = True
            self.draw_end_game_text('Stalemate')
            self.draw_result('1/2-1/2')

        elif game_state.is_three_fold:
            self.game_over = True
            self.draw_end_game_text('Three-fold repetition')
            self.draw_result('1/2-1/2')

        elif game_state.is_fifty_rule:
            self.game_over = True
            self.draw_end_game_text('Fifty moves rule')
            self.draw_result('1/2-1/2')

    def manage_event(self, event, game_state):
        # we click the mouse
        if event.type == p.MOUSEBUTTONDOWN:
            self.mousedown = self.get_mouse_click(p.mouse.get_pos())

            if self.mousedown.on_the_board:
                self.try_to_hold_piece(game_state)

        elif event.type == p.MOUSEBUTTONUP:
            if self.mousedown is not None:
                self.mouseup = self.get_mouse_click(p.mouse.get_pos())

                if self.mouseup.on_the_board:
                    # if same square then highlight that pieces moves
                    if self.mouseup == self.mousedown and self.piece_selected is \
                            None:
                        self.piece_selected = self.piece_held
                        self.piece_selected_square = self.piece_held_origin

                    elif self.piece_held is not None:
                        move = engine.Move(self.piece_held_origin,
                                           (
                                           self.mouseup.row, self.mouseup.col),
                                           game_state.board)

                        self.attempt_move(move, game_state)

                        self.piece_selected = self.piece_held
                        self.piece_selected_square = self.piece_held_origin

                    elif self.piece_selected is not None:
                        # try to make move to a valid square, other just
                        # unselect the piece
                        move = engine.Move(self.piece_selected_square,
                                           (
                                           self.mouseup.row, self.mouseup.col),
                                           game_state.board)

                        self.attempt_move(move, game_state)

                        self.piece_selected = None
                        self.piece_selected_square = ()

                self.piece_held = None
                self.piece_held_origin = ()

                self.mousedown = None
                self.mouseup = None

        elif event.type == p.KEYDOWN:
            if event.key == p.K_ESCAPE:
                self.mousedown = None
                self.piece_held = None
                self.piece_held_origin = ()
                self.piece_selected = None
                self.piece_selected_square = ()

            elif event.key == p.K_r:
                # prog.reset()
                self.__init__(self.human_player_one, self.human_player_two,
                              self.game_type)
                # game_state reset is done in the main function

            elif event.key == p.K_u and self.undo_moves:
                game_state.undo_move()
                self.move_made = True
                self.game_over = False

        elif event.type == p.QUIT:
            self.prog_running = False



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







def main():
    prog = Programme(human_player_one=True,
                     human_player_two=True,
                     game_type='rapid')

    gs = engine.GameState()

    comp = ai.AI()

    while prog.prog_running:
        if prog.timed_game and prog.game_started:
            prog.update_timers(gs.white_move)

        prog.human_turn = (gs.white_move and prog.human_player_one) or \
                          (not gs.white_move and prog.human_player_two)

        for e in p.event.get():
            prog.manage_event(e, gs)

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

        prog.check_endgame(gs)

        # TODO: need to include impossibility of checkmate too

        prog.clock.tick(prog.max_fps)

        p.display.flip()



if __name__ == '__main__':
    main()
