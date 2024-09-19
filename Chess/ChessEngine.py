class GameState:
    def __init__(self):
        """
        Initializes the game state (board setup, player turns, etc.).

        The board is an 8x8 list. Each element is a piece, with the first letter
        representing the color ('b' for black, 'w' for white) and the second letter
        for the piece type ('R' for rook, 'N' for knight, etc.). "--" means an empty square.
        """
        # Standard chess starting positions for both sides
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        # Map pieces to their respective move functions
        self.moveFunctions = {
            "p": self.getPawnMoves,
            "R": self.getRookMoves,
            "N": self.getKnightMoves,
            "B": self.getBishopMoves,
            "Q": self.getQueenMoves,
            "K": self.getKingMoves
        }

        # Game status variables
        self.white_to_move = True  # White moves first
        self.move_log = []  # Track all the moves
        self.white_king_location = (7, 4)  # White king starting position
        self.black_king_location = (0, 4)  # Black king starting position
        self.checkmate = False  # Checkmate flag
        self.stalemate = False  # Stalemate flag
        self.in_check = False  # Is the current player in check?
        self.pins = []  # Pieces pinned to the king
        self.checks = []  # Pieces checking the king
        self.enpassant_possible = ()  # Track en passant possibilities
        self.enpassant_possible_log = [self.enpassant_possible]  # Log en passant history

        # Track castling rights and history
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks,
                                               self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs,
                                               self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
        Makes a move on the board and updates the game state.
        """
        # Move piece from start to end position
        self.board[move.start_row][move.start_col] = "--"  # Clear start position
        self.board[move.end_row][move.end_col] = move.piece_moved  # Place piece at destination

        # Log the move for undo purposes
        self.move_log.append(move)

        # Switch turns after every move
        self.white_to_move = not self.white_to_move

        # Update king's location if it moved
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # Handle pawn promotion (default to queen)
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # Handle en passant captures
        if move.is_enpassant_move:
            if move.piece_moved == "wp":  # White captures black pawn
                self.board[move.end_row + 1][move.end_col] = "--"
            else:  # Black captures white pawn
                self.board[move.end_row - 1][move.end_col] = "--"

        # Update en passant possibilities for next turn
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # Pawn moves two squares
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # Handle castling moves
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # King-side castling
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # Queen-side castling
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        # Log en passant status for undo purposes
        self.enpassant_possible_log.append(self.enpassant_possible)

        # Update castling rights after the move (rooks/kings can affect this)
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks,
                                                   self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs,
                                                   self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Reverts the last move and restores the previous game state.
        """
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            # Restore the original positions
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # Switch turns back

            # Update king's position if necessary
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)

            # Undo en passant
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured

            # Undo en passant possibility
            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # Undo castling rights
            self.castle_rights_log.pop()
            self.current_castling_rights = self.castle_rights_log[-1]

            # Undo castling moves
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # Undo king-side castling
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = "--"
                else:  # Undo queen-side castling
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = "--"
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Updates castling rights after each move. If the rook or king moves, it affects castling rights.
        """
        # If a white rook gets captured
        if move.piece_captured == "wR":
            if move.end_col == 0:
                self.current_castling_rights.wqs = False  # No more queen-side castling for white
            elif move.end_col == 7:
                self.current_castling_rights.wks = False  # No more king-side castling for white

        # If a black rook gets captured
        elif move.piece_captured == "bR":
            if move.end_col == 0:
                self.current_castling_rights.bqs = False  # No more queen-side castling for black
            elif move.end_col == 7:
                self.current_castling_rights.bks = False  # No more king-side castling for black

        # If white king moves, white loses both castling rights
        if move.piece_moved == 'wK':
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False

        # If black king moves, black loses both castling rights
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False

        # If a white rook moves, check which one and update castling rights
        elif move.piece_moved == 'wR':
            if move.start_col == 0:
                self.current_castling_rights.wqs = False
            elif move.start_col == 7:
                self.current_castling_rights.wks = False

        # If a black rook moves, check which one and update castling rights
        elif move.piece_moved == 'bR':
            if move.start_col == 0:
                self.current_castling_rights.bqs = False
            elif move.start_col == 7:
                self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Returns all valid moves, taking checks into account.
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks,
                                          self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs,
                                          self.current_castling_rights.bqs)

        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        # Get the king's position based on the current player's turn
        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        if self.in_check:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()  # Get all possible moves
                # Handle blocking or capturing the checking piece
                check = self.checks[0]
                valid_squares = []
                if self.board[check[0]][check[1]][1] == "N":  # If a knight is checking, must capture
                    valid_squares = [(check[0], check[1])]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square == (check[0], check[1]):
                            break
                moves = [move for move in moves if
                         move.piece_moved[1] == "K" or (move.end_row, move.end_col) in valid_squares]
            else:
                # If there are two checks, the king must move
                self.getKingMoves(king_row, king_col, moves)
        else:
            moves = self.getAllPossibleMoves()  # Get all moves when not in check
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True  # No valid moves and in check = checkmate
            else:
                self.stalemate = True  # No valid moves and not in check = stalemate

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Check if the current player is in check.
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Check if a square is under attack by the opponent.
        """
        self.white_to_move = not self.white_to_move  # Switch to the opponent's perspective
        opponents_moves = self.getAllPossibleMoves()  # Get opponent's moves
        self.white_to_move = not self.white_to_move  # Switch back to the current player
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # Check if the move attacks the square
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Get all possible moves without considering checks.
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # Call appropriate move function
        return moves

    def checkForPinsAndChecks(self):
        """
        Look for pins and checks on the king.
        """
        pins = []
        checks = []
        in_check = False

        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row, start_col = self.white_king_location
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row, start_col = self.black_king_location

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # 8 possible directions
        for j, direction in enumerate(directions):
            possible_pin = ()
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        if (0 <= j <= 3 and enemy_type == "R") or \
                                (4 <= j <= 7 and enemy_type == "B") or \
                                (i == 1 and enemy_type == "p" and (
                                        (enemy_color == "w" and 6 <= j <= 7) or (
                                        enemy_color == "b" and 4 <= j <= 5))) or \
                                enemy_type == "Q" or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                            else:
                                pins.append(possible_pin)
                            break
                        break
                else:
                    break

        knight_moves = [(-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2)]  # Knight's move
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))

        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        Get all possible moves for a pawn at (row, col).
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"

        if self.board[row + move_amount][col] == "--":  # Move 1 square forward
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # Move 2 squares forward
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))

        if col - 1 >= 0:  # Capture to the left
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                elif (row + move_amount, col - 1) == self.enpassant_possible:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))

        if col + 1 <= 7:  # Capture to the right
            if not piece_pinned or pin_direction == (move_amount, 1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                elif (row + move_amount, col + 1) == self.enpassant_possible:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):
        """
        Get all possible moves for a rook at (row, col).
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]  # Rook moves: up, down, left, right
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                    -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # Empty square
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # Capture enemy piece
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getKnightMoves(self, row, col, moves):
        """
        Get all possible moves for a knight at (row, col).
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = [(-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2)]
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
        Get all possible moves for a bishop at (row, col).
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = [(-1, -1), (-1, 1), (1, 1), (1, -1)]  # Bishop moves: diagonals
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                    -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getQueenMoves(self, row, col, moves):
        """
        Get all possible moves for a queen at (row, col).
        The queen moves like both a rook and a bishop.
        """
        self.getRookMoves(row, col, moves)
        self.getBishopMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Get all possible moves for a king at (row, col).
        """
        row_moves = [-1, -1, -1, 0, 0, 1, 1, 1]
        col_moves = [-1, 0, 1, -1, 1, -1, 0, 1]
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    # Move the king temporarily and check if it's in check
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # Move the king back to its original position
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Generate all valid castle moves for the king at (row, col).
        """
        if self.squareUnderAttack(row, col):
            return  # Can't castle while in check
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        """
        Handle king-side castling moves.
        """
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        """
        Handle queen-side castling moves.
        """
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    """
    Class to track castling rights.
    """

    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks  # White king-side
        self.bks = bks  # Black king-side
        self.wqs = wqs  # White queen-side
        self.bqs = bqs  # Black queen-side


class Move:
    """
    Class for handling chess moves and their notation.
    """
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # Check for pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or \
                                 (self.piece_moved == "bp" and self.end_row == 7)

        # Check for en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"

        # Check for castling
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
        Override the equals method to compare moves by their unique ID.
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        """
        Returns the move in standard chess notation.
        """
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

    def getRankFile(self, row, col):
        """
        Converts the row and column into standard chess notation.
        """
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        """
        Returns a string representation of the move.
        """
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"
        end_square = self.getRankFile(self.end_row, self.end_col)
        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square
        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square

