import copy
import datetime
import math
import pygame as p

import ai
import engine

import _thread


def update_display():
    p.display.flip()


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

    colors = {'fill': p.Color('white'),
              'board1': p.Color(255, 204, 255),
              'board2': p.Color(255, 255, 255),
              'border': p.Color(50, 50, 50),
              'sq_selected': p.Color('purple'),
              'valid_moves': p.Color('yellow'),
              'premoves': p.Color('red'),
              'post_move': p.Color('red'),
              'sidebar': p.Color(50, 50, 50),
              'move_log_text': p.Color('white'),
              'white_score': p.Color('black'),
              'black_score': p.Color('white'),
              'timers': p.Color('white'),
              'end_game_text': p.Color('black'),
              'result': p.Color('white'),

              'black': p.Color('black'),
              'white': p.Color('white')}

    board_colors = [colors['board1'], colors['board2']]

    fonts = {'move_log_text': p.font.SysFont('sfnsmono', size=16,
                                             bold=False, italic=False),

             'scores': p.font.SysFont('sfnsmono', size=14,
                                      bold=True, italic=False),

             'timers': p.font.SysFont('sfnsmono', size=24,
                                      bold=True, italic=False),

             'end_game': p.font.SysFont('Verdana', size=32,
                                        bold=True, italic=False),

             'result': p.font.SysFont('Verdana', size=32,
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

    move_sound = p.mixer.Sound('sounds/move.wav')

    def __init__(self, player, network=None, game_mode='singleplayer',
                 game_type='blitz'):

        self.network = network
        self.game_mode = game_mode
        self.game_type = game_type

        if self.network is not None:
            self.get_game_state()
        else:
            self.game_state = engine.GameState(game_mode=self.game_mode,
                                               game_type=self.game_type)

        self.looking_for_ai_move = False
        self.move_made = False
        self.mouseup = None
        self.mousedown = None
        self.piece_selected = None
        self.piece_selected_square = ()
        self.piece_held = None
        self.piece_held_origin = ()

        #self.human_player_one = human_player_one
        #self.human_player_two = human_player_two
        #self.human_turn = self.human_player_one

        if self.game_mode == 'singleplayer':
            self.comp = ai.AI()
            self.moves_to_execute_ai = []
        else:
            self.comp = None
            self.moves_to_execute_ai = None

        self.player_one = True if player == 0 else False
        self.player_two = not self.player_one
        self.human_turn = self.player_one
        self.moves_to_execute = []
        #self.moves_to_execute_two = [] if game_mode == 'doubleplayer' else
        # None

        self.undo_moves = False  # True if self.game_type == 'standard' else
        # False

        self.prog_running = True

    def get_game_state(self):
        self.game_state = self.network.send('get')

    def tick_clock(self):
        self.clock.tick(self.max_fps)

    def draw_game_state(self):
        self.draw_board()
        self.highlight_squares_pre_move()
        self.highlight_squares_post_move()
        self.draw_pieces()
        self.draw_premoves()

        self.draw_sidebar()
        self.draw_pieces_taken()
        self.draw_move_log()

        if self.game_state.timed_game:
            self.draw_timers()

    def draw_board(self):
        for row in range(self.dimension):
            for col in range(self.dimension):
                color = self.board_colors[(row + col) % 2]
                p.draw.rect(self.screen, color, p.Rect(col * self.sq_size,
                                                       row * self.sq_size,
                                                       self.sq_size,
                                                       self.sq_size))

    def highlight_squares_pre_move(self):
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
            if self.game_state.board[row][col][0] == ('w' if
            self.game_state.white_move else 'b'):
                surface = p.Surface((self.sq_size, self.sq_size))
                surface.set_alpha(100)  # transparency value
                surface.fill(self.colors['sq_selected'])
                self.screen.blit(surface, (col * self.sq_size,
                                           row * self.sq_size))
                surface.fill(self.colors['valid_moves'])
                for move in self.game_state.valid_moves:
                    if move.start_row == row and move.start_col == col:
                        self.screen.blit(surface, (self.sq_size * move.end_col,
                                                   self.sq_size * move.end_row)
                                         )

    def highlight_squares_post_move(self):
        if len(self.game_state.move_log) != 0:
            move = self.game_state.move_log[-1]

            surface = p.Surface((self.sq_size, self.sq_size))
            surface.set_alpha(100)  # transparency value, 0->255 increasing
            surface.fill(self.colors['post_move'])
            self.screen.blit(surface, (move.start_col * self.sq_size,
                                       move.start_row * self.sq_size))
            self.screen.blit(surface, (move.end_col * self.sq_size,
                                       move.end_row * self.sq_size))

    def draw_pieces(self):
        temp_board = copy.deepcopy(self.game_state.board)

        for move in self.moves_to_execute:
            if self.game_mode == 'online':
                temp_board = quick_move_tpl(move, temp_board)
            else:
                temp_board = quick_move_class(move, temp_board)

        for row in range(self.dimension):
            for col in range(self.dimension):
                piece = temp_board[row][col]
                if piece != "--":
                    self.screen.blit(self.pieces_images[piece],
                                     p.Rect(col * self.sq_size,
                                            row * self.sq_size,
                                            self.sq_size,
                                            self.sq_size))

    def draw_premoves(self):
        rad = 2.0 * math.pi / 3.0
        trirad = 7.0
        thickness = 3

        for move in self.moves_to_execute:
            start = self.sq_size * (move.start_col + 0.5), \
                    self.sq_size * (move.start_row + 0.5)
            end = self.sq_size * (move.end_col + 0.5), \
                  self.sq_size * (move.end_row + 0.5)

            p.draw.line(self.screen, self.colors['premoves'], start, end,
                        thickness)
            rotation = (math.atan2(start[1] - end[1],
                                   end[0] - start[0])) + math.pi / 2.0
            p.draw.polygon(self.screen, self.colors['premoves'],
                           ((end[0] + trirad * math.sin(rotation),
                             end[1] + trirad * math.cos(rotation)),
                            (end[0] + trirad * math.sin(rotation - rad),
                             end[1] + trirad * math.cos(
                                 rotation - rad)),
                            (end[0] + trirad * math.sin(rotation + rad),
                             end[1] + trirad * math.cos(
                                 rotation + rad))))

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

    def draw_pieces_taken(self):
        self.draw_pieces_taken_func(self.width_board, 0,
                                    self.game_state.black_taken[:8])

        self.draw_pieces_taken_func(self.width_board, self.sq_size // 2,
                                    self.game_state.black_taken[8:])

        self.draw_pieces_taken_func(self.width_board, self.height_board -
                                    self.sq_size,
                                    self.game_state.white_taken[:8])

        self.draw_pieces_taken_func(self.width_board, self.height_board -
                                    self.sq_size // 2,
                                    self.game_state.white_taken[8:])

        if self.game_state.white_score > 0:
            object_white = self.fonts['scores'].render(
                '{:>+d}'.format(self.game_state.white_score),
                0, self.colors['white_score'])

            loc_white = p.Rect(self.width_board, 0, self.width_sidebar,
                               self.height_board).move(
                self.width_sidebar - self.sq_size // 2,
                self.height_board - self.sq_size // 2 +
                object_white.get_height() // 2)

            self.screen.blit(object_white, loc_white)

        elif self.game_state.black_score > 0:
            object_black = self.fonts['scores'].render(
                '{:>+d}'.format(self.game_state.black_score),
                0, self.colors['black_score'])

            loc_black = p.Rect(self.width_board, 0, self.width_sidebar,
                               self.height_board).move(
                self.width_sidebar - self.sq_size // 2,
                self.sq_size // 2 + object_black.get_height() // 2)

            self.screen.blit(object_black, loc_black)

    def draw_pieces_taken_func(self, x, y, lst):
        for piece in lst:
            r = p.Rect(x, y, self.sq_size // 2, self.sq_size // 2)
            self.screen.blit(self.pieces_images_small[piece], r)
            x += self.sq_size // 2

    def draw_move_log(self):
        text_y = self.move_log_y_padding

        recent_moves = self.game_state.move_log[
                       -(2 * self.num_recent_moves) + len(
                           self.game_state.move_log) % 2:]
        starting_num = max(0, len(self.game_state.move_log) - len(
            recent_moves))

        for move_num in range(0, len(recent_moves), 2):
            string = '{:>3d}. {:>7s} {:>7s}'.format(
                1 + ((move_num + starting_num) // 2),
                str(recent_moves[move_num]),
                str(recent_moves[move_num + 1]) \
                    if move_num + 1 < len(recent_moves) else '')
            text_object = self.fonts['move_log_text'].render(
                string, 0, self.colors['move_log_text'])

            text_location = self.sidebar.move(self.move_log_x_padding, text_y)
            self.screen.blit(text_object, text_location)

            text_y += text_object.get_height() + self.move_log_line_spacing

    def draw_timers(self):
        if self.game_state.white_time < self.game_state.time_alert:
            d = datetime.datetime.utcfromtimestamp(self.game_state.white_time)
            text_white = datetime.datetime.strftime(d, "%M:%S.%f")[:-5]
        else:
            d = datetime.datetime.utcfromtimestamp(self.game_state.white_time)
            text_white = datetime.datetime.strftime(d, "%M:%S")

        if self.game_state.black_time < self.game_state.time_alert:
            d = datetime.datetime.utcfromtimestamp(self.game_state.black_time)
            text_black = datetime.datetime.strftime(d, "%M:%S.%f")[:-5]
        else:
            d = datetime.datetime.utcfromtimestamp(self.game_state.black_time)
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

    def animate_move(self):
        mouse_col, mouse_row = p.mouse.get_pos()

        start_square = p.Rect(self.piece_held_origin[1] * self.sq_size,
                              self.piece_held_origin[0] * self.sq_size,
                              self.sq_size,
                              self.sq_size)

        p.draw.rect(self.screen, self.colors['sq_selected'],
                    start_square)

        rect = p.Rect(mouse_col - self.sq_size // 2,
                      mouse_row - self.sq_size // 2,
                      self.sq_size,
                      self.sq_size)

        self.screen.blit(self.pieces_images[self.piece_held],
                         rect)

        # p.display.update(rect)
        p.display.flip()

    def try_to_hold_piece(self):
        self.piece_selected = None
        self.piece_selected_square = ()

        piece = self.game_state.board[self.mousedown.row][self.mousedown.col]

        #if piece[0] == 'w' if self.player_one else 'b':
        if piece != '--':
            self.piece_held = piece
            self.piece_held_origin = (self.mousedown.row,
                                      self.mousedown.col)

    def get_mouse_click(self, pos):
        x, y = pos

        col = x // self.sq_size
        row = y // self.sq_size

        return Click(x, y, row, col)

    def check_endgame(self):
        if self.game_state.timeout:
            self.game_state.game_over = True
            if not self.game_state.white_move:
                self.draw_end_game_text('Black timeout. White wins!')
                self.draw_result('1-0')
            else:
                self.draw_end_game_text('White timeout. Black wins!')
                self.draw_result('0-1')

        elif self.game_state.checkmate:
            self.game_state.game_over = True
            self.draw_end_game_text(
                '{} wins by checkmate!'.format('Black' if
                                               self.game_state.white_move
                                               else 'White'))
            self.draw_result('1-0' if not self.game_state.white_move else
                             '0-1')

        elif self.game_state.stalemate:
            self.game_state.game_over = True
            self.draw_end_game_text('Stalemate')
            self.draw_result('1/2-1/2')

        elif self.game_state.is_three_fold:
            self.game_state.game_over = True
            self.draw_end_game_text('Three-fold repetition')
            self.draw_result('1/2-1/2')

        elif self.game_state.is_fifty_rule:
            self.game_state.game_over = True
            self.draw_end_game_text('Fifty moves rule')
            self.draw_result('1/2-1/2')

        elif self.game_state.is_impossibility:
            self.game_state.game_over = True
            self.draw_end_game_text('Dead position')
            self.draw_result('1/2-1/2')

    def update_human_turn(self):
        self.human_turn = (self.game_state.white_move and
                           self.player_one) or \
                          (not self.game_state.white_move and
                           self.player_two)

    '''
    def add_online_move(self, move):
        start_row, start_col = move[0], move[1]
        end_row, end_col = move[2], move[3]
        piece_moved = move[4]

        if start_row == end_row and start_col == end_col:
            pass
        else:
            if (piece_moved[0] == 'w' and self.player_one) or \
                    (piece_moved[0] == 'b' and self.player_two):
                self.moves_to_execute.append(move)
    '''

    def add_move(self, move):
        if move.start_row == move.end_row and move.start_col == move.end_col:
            pass
        else:
            if (move.piece_moved[0] == 'w' and self.player_one) or \
                    (move.piece_moved[0] == 'b' and self.player_two):
                self.moves_to_execute.append(move)

    def add_ai_move(self, move):
        self.moves_to_execute_ai.append(move)

    def get_ai_move(self):
        if not self.game_state.game_over and not self.human_turn and not \
                self.move_made and not self.looking_for_ai_move:

            # create a copy of the game stat for the ai to work with freely
            ai_gs = copy.deepcopy(self.game_state)

            _thread.start_new_thread(ai.add_ai_move, (self, ai_gs))

    def try_to_make_move(self):
        if self.game_state.ready and not self.game_state.game_over:

            if self.human_turn and len(self.moves_to_execute) > 0:
                move = self.moves_to_execute[0]

                for m in self.game_state.valid_moves:
                    if move == m:
                        self.game_state.make_move(m)
                        self.move_made = True
                        break

                if self.move_made:
                    self.move_sound.play()
                    self.moves_to_execute.pop(0)

                else:
                    self.moves_to_execute = []

            elif len(self.moves_to_execute_ai) > 0:
                move = self.moves_to_execute_ai[0]

                for m in self.game_state.valid_moves:
                    if move == m:
                        self.game_state.make_move(m)
                        self.move_made = True
                        break

                if self.move_made:
                    self.move_sound.play()
                    self.moves_to_execute_ai.pop(0)
                else:
                    self.moves_to_execute_ai = []

    def try_to_send_move(self):
        # try to execute a move that may be waiting
        if self.game_state.ready and not self.game_state.game_over and \
                ((self.game_state.white_move and self.player_one) or
                 not self.game_state.white_move and self.player_two) and \
                len(self.moves_to_execute) > 0:

            move = self.moves_to_execute[0]
            '''
            start_row, start_col = move[0], move[1]
            end_row, end_col = move[2], move[3]
            '''

            for num, m in enumerate(self.game_state.valid_moves):
                '''
                if str(start_row) + str(start_col) + \
                        str(end_row) + str(end_col) == m.move_id:
                '''
                if move == m:
                    #ntwrk.send(str(num))
                    try:
                        self.network.send(num)
                        #self.network.send(move)
                    except EOFError:
                        print('EOFError')

                    self.move_made = True
                    break

            if self.move_made:
                self.moves_to_execute.pop(0)
            else:
                self.moves_to_execute = []

        #return gs

    def manage_events(self):
        for event in p.event.get():
            # we click the mouse
            if event.type == p.MOUSEBUTTONDOWN:
                self.mousedown = self.get_mouse_click(p.mouse.get_pos())

                if self.mousedown.on_the_board and not \
                        self.game_state.game_over:
                    self.try_to_hold_piece()

            elif event.type == p.MOUSEBUTTONUP:
                if self.mousedown is not None:
                    self.mouseup = self.get_mouse_click(p.mouse.get_pos())

                    if self.mouseup.on_the_board and self.game_state.ready \
                            and not self.game_state.game_over:
                        # if same square then highlight that pieces moves
                        if self.mouseup == self.mousedown and \
                                self.piece_selected is None:
                            self.piece_selected = self.piece_held
                            self.piece_selected_square = self.piece_held_origin

                        elif self.piece_held is not None:
                            '''
                            if self.game_mode == 'online':
                                move = (self.piece_held_origin[0],
                                        self.piece_held_origin[1],
                                        self.mouseup.row,
                                        self.mouseup.col,
                                        self.piece_held[0])

                                self.add_online_move(move)

                            else:
                            '''
                            move = engine.Move(self.piece_held_origin,
                                               (self.mouseup.row,
                                                self.mouseup.col),
                                               self.game_state.board)

                            self.add_move(move)

                            # self.piece_selected = self.piece_held
                            # self.piece_selected_square = self.piece_held_origin
                            self.piece_held = None
                            self.piece_held_origin = ()

                        elif self.piece_selected is not None:
                            # try to make move to a valid square, other just
                            # unselect the piece
                            '''
                            if self.game_mode == 'online':
                                move = (self.piece_selected_square[0],
                                        self.piece_selected_square[1],
                                        self.mouseup.row,
                                        self.mouseup.col,
                                        self.piece_selected[0])

                                self.add_online_move(move)

                            else:
                            '''
                            move = engine.Move(self.piece_selected_square,
                                               (self.mouseup.row,
                                                self.mouseup.col),
                                               self.game_state.board)

                            self.add_move(move)

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

                elif event.key == p.K_c:
                    if len(self.moves_to_execute) > 0:
                        self.moves_to_execute.pop()

                elif event.key == p.K_u and self.undo_moves:
                    self.game_state.moves_to_execute = []
                    self.game_state.undo_move()
                    self.move_made = True
                    self.game_state.game_over = False

                '''
                elif event.key == p.K_r:
                    # prog.reset()
                    self.__init__(0 if self.player_one else 1)
                    # game_state reset is done in the main function
                '''

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



def quick_move_tpl(move, board):
    start_row, start_col = move[0], move[1]
    end_row, end_col = move[2], move[3]
    piece_moved = move[4]

    board[start_row][start_col] = '--'
    board[end_row][end_col] = piece_moved

    if move.is_pawn_promotion:
        board[end_row][end_col] = piece_moved[0] + 'q'

    if move.is_enpassant:
        board[start_row][end_col] = '--'

    if move.is_castling:
        if move.end_col - move.start_col == 2:
            board[move.end_row][move.end_col - 1] = board[
                move.end_row][move.end_col + 1]
            board[move.end_row][move.end_col + 1] = '--'
        else:
            board[move.end_row][move.end_col + 1] = board[
                move.end_row][move.end_col - 2]
            board[move.end_row][move.end_col - 2] = '--'

    return board


def quick_move_class(move, board):
    board[move.start_row][move.start_col] = '--'
    board[move.end_row][move.end_col] = move.piece_moved

    if move.is_pawn_promotion:
        board[move.end_row][move.end_col] = move.piece_moved[0] + 'q'

    if move.is_enpassant:
        board[move.start_row][move.end_col] = '--'

    if move.is_castling:
        if move.end_col - move.start_col == 2:
            board[move.end_row][move.end_col - 1] = board[
                move.end_row][move.end_col + 1]
            board[move.end_row][move.end_col + 1] = '--'
        else:
            board[move.end_row][move.end_col + 1] = board[
                move.end_row][move.end_col - 2]
            board[move.end_row][move.end_col - 2] = '--'

    return board
