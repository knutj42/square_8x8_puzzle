import copy
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

logger = logging.getLogger("main")


PIECES_STRING = """
hs
sh

hshs
 h

shs
 s
 h
 
h
shsh

 s
shs
  h

  h
shs
h

h
s
hsh

  hs
shs

 hs
hs
s


 h
hsh
 h
 
shs
hs

shshs
"""


def parse_pieces(pieces_string):
    pieces = []
    current_piece = ""
    for line in pieces_string.splitlines(keepends=True):
        if not line.strip():
            if current_piece:
                pieces.append(piece_to_grid(current_piece))
            current_piece = ""
        else:
            current_piece += line

    if current_piece:
        pieces.append(piece_to_grid(current_piece))

    return pieces



class AsciiBoard:
    def __init__(self):
        self.grid = []
        for row in range(8):
            self.grid.append([])
            for col in range(8):
                self.grid[row].append(" ")

    def __str__(self):
        board_as_string = " ABCDEFGH\n"
        for row in range(8):
            board_as_string += str(row+1)
            for col in range(8):
                board_as_string += self.grid[row][col]
            board_as_string += "\n"
        return board_as_string

    def can_place_piece(self, row0, col0, piece_grid):
        piece_height = len(piece_grid)
        piece_width = len(piece_grid[0])

        if row0 + piece_height > 8:
            # piece doesn't fit
            return False
        if col0 + piece_width > 8:
            # piece doesn't fit
            return False
        for piece_row in range(piece_height):
            for piece_col in range(piece_width):
                piece_value = piece_grid[piece_row][piece_col]
                if piece_value != " ":
                    row = row0 + piece_row
                    col = col0 + piece_col
                    # check for overlap with existing pieces
                    if self.grid[row][col] != " ":
                        # this square is occupied
                        return False

        # check for correct white/black interleaving
        for piece_row in range(piece_height):
            for piece_col in range(piece_width):
                piece_value = piece_grid[piece_row][piece_col]
                if piece_value != " ":
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        row = row0 + piece_row + dy
                        col = col0 + piece_col + dx
                        if col >= 0 and col < 8 and row >= 0 and row < 8:
                            grid_value = self.grid[row][col]
                            if grid_value == piece_value:
                                # white/white or black/black
                                return False

                    for dx, dy in [(-1, -1), (1, 1), (1, -1), (-1, 1)]:
                        row = row0 + piece_row + dy
                        col = col0 + piece_col + dx
                        if col >= 0 and col < 8 and row >= 0 and row < 8:
                            grid_value = self.grid[row][col]
                            if grid_value != " ":
                                if grid_value != piece_value:
                                    # different colors along a diagonal
                                    return False

        return True

    def place_piece(self, row0, col0, piece_grid):
        #logger.info(f"before piece placement: \n{self}")
        piece_height = len(piece_grid)
        piece_width = len(piece_grid[0])
        for piece_row in range(piece_height):
            for piece_col in range(piece_width):
                row = row0 + piece_row
                col = col0 + piece_col
                piece_value = piece_grid[piece_row][piece_col]
                if piece_value != " ":
                    self.grid[row][col] = piece_value
        #logger.info(f"after piece placement: \n{self}")


min_pieces_length = 99
min_pieces_length_total_count = 0

def recursivly_place_pieces(board, pieces):
    global min_pieces_length, min_pieces_length_total_count
    if len(pieces) < min_pieces_length:
        min_pieces_length = len(pieces)
        logger.info(f"min_pieces_length: {min_pieces_length}\n{board}")
    elif len(pieces) <= min_pieces_length:
        min_pieces_length_total_count += 1
        if (min_pieces_length_total_count % 10000) == 0:
            logger.info(f"min_pieces_length: {min_pieces_length} min_pieces_length_total_count:{min_pieces_length_total_count}\n{board}")
            min_pieces_length_count_since_last_logging = 0



    if len(pieces) == 0:
        logger.info(f"""Found a solution:\n{board}""")
        return

    for piece in pieces:
        # Try the piece in all rotations in all locations
        remaining_pieces = copy.copy(pieces)
        remaining_pieces.remove(piece)
        piece_rotation = piece[0]
        piece_height = len(piece_rotation)
        piece_width = len(piece_rotation[0])
        for row in range(9 - piece_height):
            for col in range(9 - piece_width):
                for piece_rotation in piece:
                    if board.can_place_piece(row, col, piece_rotation):
                        next_board = copy.deepcopy(board)
                        next_board.place_piece(row, col, piece_rotation)
                        # the piece fits in this position, so try the next piece
                        recursivly_place_pieces(next_board, remaining_pieces)


def main():
    original_pieces = parse_pieces(PIECES_STRING)

    # The first piece is the special startpiece, which it is pointless to rotate (since we would just 
    # get rotated, but otherwise identical solutions if we did).
    start_piece = original_pieces[0]
    original_pieces = original_pieces[1:]
    pieces_with_rotations = []
    for piece in original_pieces:
        rotations = get_piece_in_all_rotations(piece)
        pieces_with_rotations.append(rotations)


    place_start_piece_in_the_center = True
    pieces_with_rotations_and_placements = []
    if place_start_piece_in_the_center:
        # The start piece is placed in the center position
        board = AsciiBoard()
        board.place_piece(3, 3, start_piece)
        pieces_with_rotations_and_placements.append([board])
    else:
        # place the start piece anywhere, so put the start_piece into the list with the rest of the pieces
        pieces_with_rotations.insert(0, [start_piece])

    for rotations in pieces_with_rotations:
        piece_with_rotations_and_placements = []
        for square_piece_grid in rotations:
            stripped_piece = strip_piece(square_piece_grid)
            for row in range(8):
                for col in range(8):
                    board = AsciiBoard()
                    if board.can_place_piece(row, col, stripped_piece):
                        board.place_piece(row, col, stripped_piece)
                        print(board)
                        piece_with_rotations_and_placements.append(board)
        pieces_with_rotations_and_placements.append(piece_with_rotations_and_placements)
    print(piece_with_rotations_and_placements)

    for piece_with_rotations_and_placements in pieces_with_rotations_and_placements:
        for board in piece_with_rotations_and_placements:
            print(board)

    start_board = AsciiBoard()
    if place_start_piece_in_the_center:
        # The start piece is placed in the center position
        start_board.place_piece(3, 3, start_piece)

    stripped_pieces_with_rotations = []
    for pieces in pieces_with_rotations:
        stripped_pieces = []
        for square_piece_grid in pieces:
            stripped_piece = strip_piece(square_piece_grid)
            stripped_pieces.append(stripped_piece)
        stripped_pieces_with_rotations.append(stripped_pieces)

    recursivly_place_pieces(start_board, stripped_pieces_with_rotations)


def piece_to_grid(piece):
    row = 0
    grid = [[]]
    for character in piece:
        if character == "\n":
            row += 1
            grid.append([])
            continue
        else:
            grid[row].append(character)

    if grid[len(grid)-1] == []:
        # last row is empty, so remove it.
        grid = grid[:-1]

    max_cols = 0
    for row in grid:
        max_cols = max(max_cols, len(row))
    row_count = len(grid)
    square_grid_size = max(max_cols, row_count)
    # pad grid if needed
    while len(grid) < square_grid_size:
        grid.append([])

    for row in grid:
        while len(row) < square_grid_size:
            row.append(" ")
    return grid


def get_piece_in_all_rotations(square_piece_grid):
    rotations = [square_piece_grid]
    square_grid_size = len(square_piece_grid)
    for flip in [False, True]:
        transformed_piece = copy.deepcopy(square_piece_grid)
        if flip:
            for row in range(square_grid_size):
                for col in range(len(square_piece_grid)):
                    flipped_col = square_grid_size - col - 1
                    transformed_piece[row][col] = square_piece_grid[row][flipped_col]

        for rotation in range(4):
            rotated_piece = copy.deepcopy(transformed_piece)
            # we rotate 90 degrees clockwise, so each column becomes a row
            for col in range(square_grid_size):
                new_row = col
                for row in range(square_grid_size):
                    new_col = square_grid_size - row - 1
                    rotated_piece[new_row][new_col] = transformed_piece[row][col]
            if rotated_piece not in rotations:
                rotations.append(rotated_piece)
            transformed_piece = rotated_piece

    return rotations


def strip_piece(square_piece):
    # strip off leading and trailing empty cols and rows
    square_grid_size = len(square_piece)
    empty_cols = []
    for col in range(square_grid_size):
        for row in range(square_grid_size):
            if square_piece[row][col] != " ":
                break
        else:
            empty_cols.append(col)
    empty_rows = []
    for row in range(square_grid_size):
        for col in range(square_grid_size):
            if square_piece[row][col] != " ":
                break
        else:
            empty_rows.append(row)

    stripped_piece = []
    for row in range(square_grid_size):
        if row not in empty_rows:
            stripped_piece.append([])
            for col in range(square_grid_size):
                if col not in empty_cols:
                    stripped_piece[-1].append(square_piece[row][col])
    return stripped_piece



if __name__ == "__main__":
    main()