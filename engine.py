

class GameState:
    def __init__(self):
        self.board = [['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
                      ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
                      ['--', '--', '--', '--', '--', '--', '--', '--'],
                      ['--', '--', '--', '--', '--', '--', '--', '--'],
                      ['--', '--', '--', '--', '--', '--', '--', '--'],
                      ['--', '--', '--', '--', '--', '--', '--', '--'],
                      ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
                      ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']]

        self.white_move = True
        self.move_log = []

        self.white_king = (7, 4)
        self.black_king = (0, 4)

        self.in_check = False
        self.pins = []
        self.checks = []

        self.enpassant = ()

        self.castling = {'bq': True, 'bk': True, 'wq': True, 'wk': True}
        self.castling_log = [self.castling.copy()]

        self.checkmate = False
        self.statemate = False

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = '--'
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_move = not self.white_move
        if move.piece_moved == 'wk':
            self.white_king = (move.end_row, move.end_col)
        elif move.piece_moved == 'bk':
            self.black_king = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + 'q'

        if move.is_enpassant:
            self.board[move.start_row][move.end_col] = '--'

        if move.piece_moved[1] == 'p' and \
                abs(move.start_row-move.end_row) == 2:
            self.enpassant = ((move.start_row + move.end_row)//2,
                              move.start_col)
        else:
            self.enpassant = ()

        # castling
        if move.piece_moved == 'wk':
            self.castling['wq'] = False
            self.castling['wk'] = False
        elif move.piece_moved == 'bk':
            self.castling['bq'] = False
            self.castling['bk'] = False
        elif move.piece_moved == 'wr':
            if move.start_row == 7:
                if move.start_col == 0:
                    self.castling['wq'] = False
                elif move.start_col == 7:
                    self.castling['wk'] = False
        elif move.piece_moved == 'br':
            if move.start_row == 0:
                if move.start_col == 0:
                    self.castling['bq'] = False
                elif move.start_col == 7:
                    self.castling['bk'] = False

        if move.is_castling:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col-1] = self.board[
                    move.end_row][move.end_col+1]
                self.board[move.end_row][move.end_col+1] = '--'
            else:
                self.board[move.end_row][move.end_col+1] = self.board[
                    move.end_row][move.end_col-2]
                self.board[move.end_row][move.end_col-2] = '--'

        if move.piece_captured == 'wr':
            if move.end_row == 7:
                if move.end_col == 0:
                    self.castling['wq'] = False
                elif move.end_col == 7:
                    self.castling['wk'] = False
        elif move.piece_captured == 'br':
            if move.end_row == 0:
                if move.end_col == 0:
                    self.castling['bq'] = False
                elif move.end_col == 7:
                    self.castling['bk'] = False

        self.castling_log.append(self.castling.copy())

    def undo_move(self):
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_move = not self.white_move
            if move.piece_moved == 'wk':
                self.white_king = (move.start_row, move.start_col)
            elif move.piece_moved == 'bk':
                self.black_king = (move.start_row, move.start_col)

            if move.is_enpassant:
                self.board[move.end_row][move.end_col] = '--'
                self.board[move.start_row][move.end_col] = move.piece_captured
                self.enpassant = (move.end_row, move.end_col)

            if move.piece_moved[1] == 'p' and abs(move.start_row -
                                                  move.end_row) == 2:
                self.enpassant = ()

            if move.is_castling:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col+1] = self.board[
                        move.end_row][move.end_col-1]
                    self.board[move.end_row][move.end_col-1] = '--'
                else:
                    self.board[move.end_row][move.end_col-2] = self.board[
                        move.end_row][move.end_col+1]
                    self.board[move.end_row][move.end_col+1] = '--'

            # castling
            self.castling_log.pop()
            self.castling = self.castling_log[-1].copy()

            if self.checkmate:
                self.checkmate = False

            # TODO: sort this
            #if self.stalemate:
            #    self.stalemate = False

    def get_pins_and_checks(self):
        pins = []
        checks = []
        in_check = False
        enemy_color, ally_color,\
        start_row, start_col = ('b', 'w',
                                self.white_king[0],
                                self.white_king[1]) if self.white_move else \
            ('w', 'b', self.black_king[0], self.black_king[1])
        directions = ((-1,  0), (0, -1), (1,  0), (0, 1), # for rooks
                      (-1, -1), (-1, 1), (1, -1), (1, 1)) # for bishops
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != 'k':
                        # can't be a pin if we already have one
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        type_ = end_piece[1]
                        if (0 <= j <= 3 and type_ == 'r') or \
                                (4 <= j <= 7 and type_ == 'b') or \
                                (i == 1 and type_ == 'p' and ((
                                    enemy_color == 'w' and 6 <= j <= 7) or (
                                        enemy_color == 'b' and 4 <= j <=
                                        5))) or (type_ == 'q') or (i == 1
                                                                   and type_
                                                                   == 'k'):
                            # no piece blocking so check
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row,end_col, d[0], d[1]))
                                break
                            # piece blocking so pin
                            else:
                                pins.append(possible_pin)
                                break
                        # enemy piece not applying check
                        else:
                            break

        # knight checks
        directions = ((-2, -1), (-2, 1), (2, -1), (2, 1),
                      (-1, -2), (-1, 2), (1, -2), (1, 2))
        for d in directions:
            end_row = start_row + d[0]
            end_col = start_col + d[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'n':
                    in_check = True
                    checks.append((end_row, end_col, d[0], d[1]))

        return in_check, pins, checks

    def get_valid_moves(self):
        temp_enpassant = self.enpassant

        moves = [] #self.get_all_moves()

        self.in_check, self.pins, self.checks = self.get_pins_and_checks()

        king_row, king_col = self.white_king if self.white_move else \
            self.black_king

        if self.in_check:
            if len(self.checks) == 1:
                moves = self.get_all_moves()
                check = self.checks[0]
                check_row, check_col = check[0], check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []
                if piece_checking[1] == 'n':
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        # check[2] and check[3] are the check directions
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and \
                            valid_square[1] == check_col:
                            break
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].piece_moved[1] != 'k':
                        if not (moves[i].end_row, moves[i].end_col) in \
                               valid_squares:
                            moves.remove(moves[i])
            else:
                # more than one checking piece means only king moving is valid
                self.get_king_moves(king_row, king_col, moves)
        else:
            moves = self.get_all_moves()
            self.get_castling_moves(moves)

        self.enpassant = temp_enpassant

        if len(moves) == 0:
            self.checkmate = True
            #self.stalemate TODO: sort this.

        return moves

    def get_all_moves(self):
        moves = []

        for row in range(8):
            for col in range(8):
                color = self.board[row][col][0]
                if (color == 'w' and self.white_move) or \
                    (color == 'b' and not self.white_move):
                    piece = self.board[row][col][1]
                    if piece == 'p':
                        self.get_pawn_moves(row, col, moves)
                    elif piece == 'r':
                        self.get_rook_moves(row, col, moves)
                    elif piece == 'n':
                        self.get_knight_moves(row, col, moves)
                    elif piece == 'b':
                        self.get_bishop_moves(row, col, moves)
                    elif piece == 'q':
                        self.get_queen_moves(row, col, moves)
                    elif piece == 'k':
                        self.get_king_moves(row, col, moves)

        return moves

    def check_pinned(self, row, col, rook=False):
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                pin_direction = (self.pins[i][2], self.pins[i][3])
                # can't remove queen from pin on rook moves
                # only remove it on bishop moves
                if rook and self.board[row][col] != 'q':
                    self.pins.remove(self.pins[i])
                return True, pin_direction
        return False, ()

    def get_pawn_moves(self, row, col, moves):
        piece_pinned, pin_direction = self.check_pinned(row, col)

        if self.white_move:
            pawn_promotion = True if row-1 == 0 else False
            if self.board[row-1][col] == '--':
                if not piece_pinned or pin_direction == (-1, 0):
                    moves.append(Move((row, col),
                                      (row-1, col),
                                      self.board,
                                      pawn_promotion=pawn_promotion))
                    if row == 6 and self.board[row-2][col] == '--':
                        moves.append(Move((row, col),
                                          (row-2, col),
                                          self.board))
            if col-1 >= 0:
                if not piece_pinned or pin_direction == (-1, -1):
                    if self.board[row-1][col-1][0] == 'b':
                        moves.append(Move((row, col),
                                          (row-1, col-1),
                                          self.board,
                                          pawn_promotion=pawn_promotion))
                    elif (row-1, col-1) == self.enpassant:
                        moves.append(Move((row, col),
                                          (row-1, col-1),
                                          self.board,
                                          enpassant=True))
            if col+1 <= 7:
                if not piece_pinned or pin_direction == (-1, 1):
                    if self.board[row-1][col+1][0] == 'b':
                        moves.append(Move((row, col),
                                          (row-1, col+1),
                                          self.board,
                                          pawn_promotion=pawn_promotion))
                    elif (row-1, col+1) == self.enpassant:
                        moves.append(Move((row, col),
                                          (row-1, col+1),
                                          self.board,
                                          enpassant=True))

        else:
            pawn_promotion = True if row+1 == 7 else False
            if self.board[row+1][col] == '--':
                if not piece_pinned or pin_direction == (1, 0):
                    moves.append(Move((row, col),
                                      (row+1, col),
                                      self.board,
                                      pawn_promotion=pawn_promotion))
                    if row == 1 and self.board[row+2][col] == '--':
                        moves.append(Move((row, col),
                                          (row+2, col),
                                          self.board))
            if col-1 >= 0:
                if not piece_pinned or pin_direction == (1, -1):
                    if self.board[row+1][col-1][0] == 'w':
                        moves.append(Move((row, col),
                                          (row+1, col-1),
                                          self.board,
                                          pawn_promotion=pawn_promotion))
                    elif (row+1, col-1) == self.enpassant:
                        moves.append(Move((row, col),
                                          (row+1, col-1),
                                          self.board,
                                          enpassant=True))
            if col+1 <= 7:
                if not piece_pinned or pin_direction == (1, 1):
                    if self.board[row+1][col+1][0] == 'w':
                        moves.append(Move((row, col),
                                          (row+1, col+1),
                                          self.board,
                                          pawn_promotion=pawn_promotion))
                    elif (row+1, col+1) == self.enpassant:
                        moves.append(Move((row, col),
                                          (row+1, col+1),
                                          self.board,
                                          enpassant=True))

    def get_rook_moves(self, row, col, moves):
        piece_pinned, pin_direction = self.check_pinned(row, col, rook=True)

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_color = 'b' if self.white_move else 'w'

        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == d or \
                            pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == '--':
                            moves.append(Move((row, col),
                                              (end_row, end_col),
                                              self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((row, col),
                                              (end_row, end_col),
                                              self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_knight_moves(self, row, col, moves):
        piece_pinned, _ = self.check_pinned(row, col)

        directions = ((-2, -1), (-2, 1), (2, -1), (2, 1),
                      (-1, -2), (-1, 2), (1, -2), (1, 2))
        ally_color = 'w' if self.white_move else 'b'

        for d in directions:
            end_row = row + d[0]
            end_col = col + d[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((row, col),
                                          (end_row, end_col),
                                          self.board))

    def get_bishop_moves(self, row, col, moves):
        piece_pinned, pin_direction = self.check_pinned(row, col)

        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        enemy_color = 'b' if self.white_move else 'w'

        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == d or \
                            pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == '--':
                            moves.append(Move((row, col),
                                              (end_row, end_col),
                                              self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((row, col),
                                              (end_row, end_col),
                                              self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_queen_moves(self, row, col, moves):
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_king_moves(self, row, col, moves):
        directions = ((-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1))
        ally_color = 'w' if self.white_move else 'b'

        for d in directions:
            end_row = row + d[0]
            end_col = col + d[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    if ally_color == 'w':
                        self.white_king = (end_row, end_col)
                    else:
                        self.black_king = (end_row, end_col)
                    in_check, pins, checks = self.get_pins_and_checks()
                    if not in_check:
                        moves.append(Move((row, col),
                                          (end_row, end_col),
                                          self.board))
                    if ally_color == 'w':
                        self.white_king = (row, col)
                    else:
                        self.black_king = (row, col)

    def get_castling_moves(self, moves):
        if self.in_check:
            return

        if self.white_move:
            if self.castling['wk']:
                self.get_kingside_castling_moves(7, 4, moves)
            if self.castling['wq']:
                self.get_queenside_castling_moves(7, 4, moves)
        else:
            if self.castling['bk']:
                self.get_kingside_castling_moves(0, 4, moves)
            if self.castling['bq']:
                self.get_queenside_castling_moves(0, 4, moves)

    def get_kingside_castling_moves(self, row, col, moves):
        if self.board[row][col+1] == '--' and self.board[row][col+2] == '--':
            if not self.square_under_attack(row, col+1) and not \
                    self.square_under_attack(row, col+2):
                moves.append(Move((row, col), (row, col+2), self.board,
                                  castling=True))

    def get_queenside_castling_moves(self, row, col, moves):
        if self.board[row][col-1] == '--' and self.board[row][col-2] == '--'\
                and self.board[row][col-3] == '--':
            if not self.square_under_attack(row, col-1) and not \
                    self.square_under_attack(row, col-2):
                moves.append(Move((row, col), (row, col-2), self.board,
                                  castling=True))

    def square_under_attack(self, row, col):
        self.white_move = not self.white_move

        opp_moves = self.get_all_moves()

        self.white_move = not self.white_move

        for move in opp_moves:
            if move.end_row == row and move.end_col == col:
                return True

        return False


class Move:
    ranks_to_rows = {'1': 7, '2': 6, '3': 5, '4': 4,
                     '5': 3, '6': 2, '7': 1, '8': 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}

    files_to_cols = {'a': 0, 'b': 1, 'c': 2, 'd': 3,
                     'e': 4, 'f': 5, 'g': 6, 'h': 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board,
                 pawn_promotion=False, enpassant=False, castling=False):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.is_pawn_promotion = pawn_promotion #self.check_pawn_promotion()
        self.is_enpassant = enpassant #self.check_enpassant(possible_enpassant)
        self.is_castling = castling
        self.move_id = str(self.start_row) + \
            str(self.start_col) + \
            str(self.end_row) + \
            str(self.end_col)

        if self.is_enpassant:
            self.piece_captured = 'wp' if self.piece_moved == 'bp' else 'bp'

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id

        return False

    '''
    def check_pawn_promotion(self):
        return True if ((self.piece_moved == 'wp' and self.end_row == 0) or (
                self.piece_moved == 'bp' and self.end_row == 7)) else False

    def check_enpassant(self, possible_enpassant):
        return True if (self.piece_moved[1] == 'p' and (self.end_row,
                                                       self.end_col) ==
                possible_enpassant) else False
    '''

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + \
               self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]
