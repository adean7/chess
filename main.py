import engine
import pygame as p


class Setup:
    def __init__(self, colors=None,
                 width=512, height=512, dimension=8, max_fps=30):
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
             'end_game_text': 'black'}

        self.screen = p.display.set_mode((self.width, self.height))
        self.screen.fill(p.Color('white'))

        self.pieces = ['wk', 'wq', 'wr', 'wb', 'wn', 'wp', 'bk', 'bq', 'br',
                       'bb', 'bn', 'bp']
        self.get_pieces_images()

    def get_pieces_images(self):
        self.pieces_images = {}
        for string in self.pieces:
            self.pieces_images[string] = p.transform.scale(p.image.load(
                "images/" + string + ".png"), (self.sq_size, self.sq_size))

def draw_board(setup):
    colors = [p.Color(setup.colors['board1']),
              p.Color(setup.colors['board2'])]

    for row in range(setup.dimension):
        for col in range(setup.dimension):
            color = colors[(row + col) % 2]
            p.draw.rect(setup.screen, color, p.Rect(col * setup.sq_size,
                                                    row * setup.sq_size,
                                                    setup.sq_size,
                                                    setup.sq_size))

def draw_pieces(board, setup):
    for row in range(setup.dimension):
        for col in range(setup.dimension):
            piece = board[row][col]
            if piece != "--":
                setup.screen.blit(setup.pieces_images[piece],
                                  p.Rect(col * setup.sq_size,
                                         row * setup.sq_size,
                                         setup.sq_size,
                                         setup.sq_size))

def highlight_squares(game_state, setup,
                      valid_moves, square_selected):
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_move
        else 'b'):
            surface = p.Surface((setup.sq_size, setup.sq_size))
            surface.set_alpha(100) # transparency value, 0->255 increasing
            surface.fill(p.Color(setup.colors['sq_selected']))
            setup.screen.blit(surface, (col*setup.sq_size, row*setup.sq_size))
            surface.fill(p.Color(setup.colors['valid_moves']))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    setup.screen.blit(surface, (setup.sq_size * move.end_col,
                                                setup.sq_size * move.end_row))


def draw_game_state(game_state, setup, valid_moves, square_selected):
    draw_board(setup)
    highlight_squares(game_state, setup, valid_moves, square_selected)
    draw_pieces(game_state.board, setup)

'''
def animate_move(move, board, setup):
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col

    frames_per_square = 10
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square

    color = [p.Color(setup.colors['board1']),
             p.Color(setup.colors['board2'])][(move.end_row +
                                               move.end_col) % 2]

    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count,
                    move.start_col + d_col * frame / frame_count)

        draw_board(setup)
        draw_pieces(board, setup)

        end_square = p.Rect(move.end_col * setup.sq_size,
                            move.end_row * setup.sq_size,
                            setup.sq_size,
                            setup.sq_size)
        p.draw.rect(setup.screen, color, end_square)

        if move.piece_captured != '--':
            setup.screen.blit(setup.pieces_images[move.piece_captured],
                              end_square)

        setup.screen.blit(setup.pieces_images[move.piece_moved],
                          p.Rect(col * setup.sq_size,
                                 row * setup.sq_size,
                                 setup.sq_size,
                                 setup.sq_size))
        p.display.flip()
        setup.clock.tick(60)
'''

def animate_move(game_state, sq_selected, mouse_pos, setup):
    row = sq_selected[0]
    col = sq_selected[1]

    piece_selected = game_state.board[row][col]

    if piece_selected != '--':
        if game_state.board[row][col][0] == ('w' if game_state.white_move
        else 'b'):
            color = p.Color(setup.colors['sq_selected'])

            start_square = p.Rect(col * setup.sq_size,
                                  row * setup.sq_size,
                                  setup.sq_size,
                                  setup.sq_size)

            p.draw.rect(setup.screen, color, start_square)

            setup.screen.blit(setup.pieces_images[piece_selected],
                              p.Rect(mouse_pos[0] - setup.sq_size//2,
                                     mouse_pos[1] - setup.sq_size//2,
                                     setup.sq_size,
                                     setup.sq_size))

    p.display.flip()

def draw_text(setup, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, 0, p.Color(setup.colors['end_game_text']))
    text_location = p.Rect(0, 0, setup.width, setup.height).move(
        (setup.width  - text_object.get_width()) /2,
        (setup.height - text_object.get_height())/2)
    setup.screen.blit(text_object, text_location)



def main():
    p.init()

    s = Setup()

    gs = engine.GameState()

    running = True
    #sq_selected = () # (row, column)
    #player_clicks = [] # e.g. [(6,4), (4,4)] moving from (6,4) to (4,4)
    valid_moves = gs.get_valid_moves()
    move_made = False

    mousedown = ()

    game_over = False

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.KEYDOWN:
                if e.key == p.K_r:
                    gs = engine.GameState()
                    valid_moves = gs.get_valid_moves()
                    move_made = False
                    mousedown = ()
                    game_over = False
                elif e.key == p.K_u:
                    gs.undo_move()
                    move_made = True
                    if game_over:
                        game_over = False

            if not game_over:
                if e.type == p.MOUSEBUTTONDOWN:
                    '''
                    location = p.mouse.get_pos()
                    col = location[0] // s.sq_size
                    row = location[1] // s.sq_size
                    if sq_selected == (row, col): # clicked same square twice
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)
    
                    if len(player_clicks) == 2: # after second click
                        move = engine.Move(player_clicks[0], player_clicks[1],
                                           gs.board)
                        for m in valid_moves:
                            if move == m:
                                gs.make_move(m)
                                move_made = True
                                sq_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [sq_selected]
                    '''

                    location = p.mouse.get_pos()

                    col = location[0] // s.sq_size
                    row = location[1] // s.sq_size

                    mousedown = (row, col)

                elif e.type == p.MOUSEBUTTONUP:
                    location = p.mouse.get_pos()

                    col = location[0] // s.sq_size
                    row = location[1] // s.sq_size

                    mouseup = (row, col)

                    move = engine.Move(mousedown, mouseup, gs.board)

                    for m in valid_moves:
                        if move == m:
                            gs.make_move(m)
                            move_made = True

                    mousedown = ()

        if move_made:
            #animate_move(gs.move_log[-1], gs.board, s)
            valid_moves = gs.get_valid_moves()
            move_made = False

        #draw_game_state(gs, s, valid_moves, sq_selected)
        if not game_over:
            draw_game_state(gs, s, valid_moves, mousedown)

            if mousedown != ():
                animate_move(gs, mousedown, p.mouse.get_pos(), s)

        if gs.checkmate:
            game_over = True
            draw_text(s, '{} wins by checkmate!'.format('Black' if
                                                        gs.white_move else
                                                        'White'))
        elif gs.statemate:
            game_over = True
            draw_text(s, 'Stalemate!')

        s.clock.tick(s.max_fps)

        p.display.flip()




if __name__ == '__main__':
    main()

