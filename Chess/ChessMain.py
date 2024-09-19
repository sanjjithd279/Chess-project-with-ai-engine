"""
This file is the main driver for the chess game.
It will handle user input and draw the current game state to the screen.
"""

import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue

# Board size and other UI settings
BOARD_WIDTH = BOARD_HEIGHT = 512  # Size of the chess board
MOVE_LOG_PANEL_WIDTH = 250  # Space for move log
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8  # Chess board is 8x8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION  # Size of each square
MAX_FPS = 120  # Frames per second (for smooth animations)
IMAGES = {}  # Dictionary to hold piece images


def loadImages():
    """
    Loads all piece images so we can use them later.
    This only happens once at the start.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        # Resize and load the images to fit the squares
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():
    """
    The main function where everything happens:
    Initializes the game, handles user input, updates the game state, and displays it.
    """
    p.init()  # Initialize pygame
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))  # Create screen
    clock = p.time.Clock()  # Set up clock for smooth animations
    screen.fill(p.Color("white"))  # Fill screen with white to start
    game_state = ChessEngine.GameState()  # Create a new GameState object (the board)
    valid_moves = game_state.getValidMoves()  # Get the list of valid moves at the start
    move_made = False  # Flag for when a move is made
    animate = False  # Flag to animate the move
    loadImages()  # Load all images before the game starts
    running = True  # Game loop control
    square_selected = ()  # Tracks the last square clicked by the player
    player_clicks = []  # Tracks player clicks (for making moves)
    game_over = False  # Game over flag
    ai_thinking = False  # AI thinking flag
    move_undone = False  # Track if a move was undone
    move_finder_process = None  # For AI multiprocessing
    move_log_font = p.font.SysFont("Arial", 14, False, False)  # Font for move log
    player_one = True  # True, as this is the player
    player_two = True  # Is player two a human?, false for ai

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()  # Quit the game
                sys.exit()

            # Handle mouse clicks
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # Get mouse coordinates
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # If the same square is clicked twice
                        square_selected = ()  # Deselect
                        player_clicks = []  # Clear clicks
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # Append to clicks (2 clicks = move)
                    if len(player_clicks) == 2 and human_turn:  # If 2 clicks (a move is made)
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  # Reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # Handle keyboard input
            elif e.type == p.KEYDOWN:
                if e.key == p.K_LEFT:  # Undo the last move when left arrow is pressed
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_r:  # Reset the game when 'r' is pressed
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    game_state.position_count = {}  # Reset position count
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # Handle AI moves
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # Used to pass data between threads
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()  # Recalculate valid moves after the move
            move_made = False
            animate = False
            move_undone = False

            # Check for threefold repetition
            if game_state.threefold_repetition:
                game_over = True
                drawEndGameText(screen, "Draw by threefold repetition")
            elif game_state.checkmate:
                game_over = True
                if game_state.white_to_move:
                    drawEndGameText(screen, "Black wins by checkmate")
                else:
                    drawEndGameText(screen, "White wins by checkmate")
            elif game_state.stalemate:
                game_over = True
                drawEndGameText(screen, "Stalemate")

        # Only draw game state if game is not over
        if not game_over:
            drawGameState(screen, game_state, valid_moves, square_selected)
            drawMoveLog(screen, game_state, move_log_font)

        clock.tick(MAX_FPS)  # Control the FPS
        p.display.flip()  # Update the display


def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    Draws the game state on the screen, including the board and pieces.
    """
    drawBoard(screen)  # Draw the board squares
    highlightSquares(screen, game_state, valid_moves, square_selected)  # Highlight valid moves
    drawPieces(screen, game_state.board)  # Draw the pieces on top of the board


def drawBoard(screen):
    """
    Draw the board squares. Alternate colors for a classic chessboard look.
    """
    global colors
    colors = [p.Color("white"), p.Color("#A9C66C")]  # Light and dark squares
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]  # Alternate color for each square
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight the selected square and valid moves for the selected piece.
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):
            # Highlight the square the player clicked
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # Highlight valid moves from the selected square
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    """
    Draw the chess pieces on the board based on the current game state.
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":  # If there's a piece on this square, draw it
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    """
    Draw the log of moves on the right-hand side of the screen.
    """
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    """
    Display the end game message (checkmate, stalemate, etc.).
    """
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Handles the animation of a piece moving across the board.
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 3  # Control the speed of the animation
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # Erase the piece from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # Draw the captured piece if needed
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # Draw the moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()



