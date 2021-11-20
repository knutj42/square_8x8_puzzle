import copy
import logging
import math
import textwrap
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

logger = logging.getLogger("main")

PIECES_STRING = """
WB
BW

WBWB
 W

BWB
 B
 W
 
W
BWBW

 B
BWB
  W

  W
BWB
W

W
B
WBW

  WB
BWB

 WB
WB
B


 W
WBW
 W
 
BWB
WB

BWBWB

B B
WBW
"""
use_v1 = False


def parse_pieces(pieces_string):
    white_squares = 0
    black_squares = 0
    for c in pieces_string:
        if c == "W":
            white_squares += 1
        elif c == "B":
            black_squares += 1
    if black_squares != 32 or white_squares != 32:
        raise AssertionError(f"black_squares={black_squares}  white_squares={white_squares}")

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

    white_squares = 0
    black_squares = 0
    for piece in pieces:
        for row in piece:
            for square in row:
                if square == "W":
                    white_squares += 1
                elif square == "B":
                    black_squares += 1

    if black_squares != 32 or white_squares != 32:
        raise AssertionError(f"black_squares={black_squares}  white_squares={white_squares}")
    return pieces


class AsciiBoard:
    """This class is used during setup and when reporting results. It is not used during the actual
    solving of the puzzle, so the code here doesn't need to be fast."""

    def __init__(self):
        self.grid = []
        for row in range(8):
            self.grid.append([])
            for col in range(8):
                self.grid[row].append(" ")

    @staticmethod
    def from_uint64(first_square_is_white, board_as_uint64):
        board = AsciiBoard()
        bitnr = 0
        for row in range(8):
            for col in range(8):
                square_has_same_color_as_first_square = ((row + col) % 2) == 0
                if square_has_same_color_as_first_square:
                    square_is_white = first_square_is_white
                else:
                    square_is_white = not first_square_is_white
                if (board_as_uint64 & (1 << bitnr)) != 0:
                    board.grid[row][col] = "W" if square_is_white else "B"
                bitnr += 1
        return board

    def __str__(self):
        board_as_string = " ABCDEFGH\n"
        for row in range(8):
            board_as_string += str(row + 1)
            for col in range(8):
                board_as_string += self.grid[row][col]
            board_as_string += "\n"
        return board_as_string

    def as_uint64(self):
        board_as_uint64 = 0
        bit_nr = 0
        first_grid_is_white = None
        for row in range(8):
            for col in range(8):
                position_bit = 1 << bit_nr
                if self.grid[row][col] != " ":
                    square_is_white = self.grid[row][col] == "W"
                    square_has_same_color_as_first_square = ((row + col) % 2) == 0
                    if square_has_same_color_as_first_square:
                        first_grid_is_white = square_is_white
                    else:
                        first_grid_is_white = not square_is_white
                    board_as_uint64 |= position_bit
                bit_nr += 1

        return first_grid_is_white, board_as_uint64

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
        # logger.info(f"before piece placement: \n{self}")
        piece_height = len(piece_grid)
        piece_width = len(piece_grid[0])
        for piece_row in range(piece_height):
            for piece_col in range(piece_width):
                row = row0 + piece_row
                col = col0 + piece_col
                piece_value = piece_grid[piece_row][piece_col]
                if piece_value != " ":
                    self.grid[row][col] = piece_value


complete_board_uint64 = (2 ** 64 - 1)


def recursivly_place_pieces(pieces, depth, current_board, current_placements,
                            report_solution):
    """This is the second implementation, which uses precreated for all possible piece-placements."""
    for placement in pieces[depth]:
        if (placement & current_board) == 0:
            # This piece can be placed
            current_placements[depth] = placement
            new_board = placement | current_board

            if new_board == complete_board_uint64:
                report_solution(current_placements)
                return
            else:
                recursivly_place_pieces(pieces, depth + 1,
                                        new_board, current_placements,
                                        report_solution)


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

    if grid[len(grid) - 1] == []:
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
                        piece_with_rotations_and_placements.append(board)
        pieces_with_rotations_and_placements.append(piece_with_rotations_and_placements)

    # We split the placements into two lists: one where the first square (the top left corder) is white, and
    # one where it is black (The "first_square_black" list will not give a solution when we place the start-piece
    # in the center, though, since the start-piece is placed such that the first square must always be white).
    pieces_with_rotations_and_placements_as_uint64_first_square_white = []
    pieces_with_rotations_and_placements_as_uint64_first_square_black = []
    for piece_with_rotations_and_placements in pieces_with_rotations_and_placements:
        piece_with_rotations_and_placements_as_uint64_first_square_white = []
        piece_with_rotations_and_placements_as_uint64_first_square_black = []
        for board in piece_with_rotations_and_placements:
            first_grid_is_white, board_as_uint64 = board.as_uint64()
            if first_grid_is_white:
                if board_as_uint64 not in piece_with_rotations_and_placements_as_uint64_first_square_white:
                    piece_with_rotations_and_placements_as_uint64_first_square_white.append(board_as_uint64)
            else:
                if board_as_uint64 not in piece_with_rotations_and_placements_as_uint64_first_square_black:
                    piece_with_rotations_and_placements_as_uint64_first_square_black.append(board_as_uint64)
        pieces_with_rotations_and_placements_as_uint64_first_square_white.append(
            piece_with_rotations_and_placements_as_uint64_first_square_white)
        pieces_with_rotations_and_placements_as_uint64_first_square_black.append(
            piece_with_rotations_and_placements_as_uint64_first_square_black)

    combinations_first_square_white = math.prod(
        len(pieces) for pieces in pieces_with_rotations_and_placements_as_uint64_first_square_white)
    combinations_first_square_black = math.prod(
        len(pieces) for pieces in pieces_with_rotations_and_placements_as_uint64_first_square_black)
    logger.info(
        f"There are a total of {combinations_first_square_white + combinations_first_square_black} piece placements")

    solutions = []
    for first_square_is_white, pieces_with_rotations_and_placements_as_uint64 in [
        (True, pieces_with_rotations_and_placements_as_uint64_first_square_white),
        (False, pieces_with_rotations_and_placements_as_uint64_first_square_black)]:

        current_progress = [0, 0, 0]
        total_combinations = math.prod(
            len(placements) for placements in pieces_with_rotations_and_placements_as_uint64)
        starttime = time.monotonic()
        placement_counts_at_depth = [len(placements) for placements in
                                     pieces_with_rotations_and_placements_as_uint64]
        max_depth = len(placement_counts_at_depth)
        depth_multipliers = []
        for depth in range(max_depth):
            if depth == max_depth - 1:
                depth_multipliers.append(1)
            else:
                remaining_placement_counts = placement_counts_at_depth[1 + depth - max_depth:]
                multiplier = math.prod(remaining_placement_counts)
                depth_multipliers.append(multiplier)

        def report_progress():
            elapsed_time = time.monotonic() - starttime
            remaining_combinations = []
            remaining_placements = []
            for depth in range(len(current_progress)):
                placement_count_at_depth = placement_counts_at_depth[depth]
                processed_placements_at_depth = current_progress[depth] or 0
                remaining_placements_at_this_depth = placement_count_at_depth - processed_placements_at_depth
                multiplier = depth_multipliers[depth]
                remaining_combinations.append(multiplier * remaining_placements_at_this_depth)
                remaining_placements.append(remaining_placements_at_this_depth)

            total_remaining_combinations = sum(remaining_combinations)
            progress_in_percent = (1 - (total_remaining_combinations / total_combinations)) * 100.0

            estimated_remaining_time = 0
            if elapsed_time> 0 and progress_in_percent > 0 and progress_in_percent < 100:
                percent_per_second = progress_in_percent / elapsed_time
                remaining_work_in_percent = 100.0 - progress_in_percent
                estimated_remaining_time = remaining_work_in_percent / percent_per_second

            msg = f"""Progress for the positions where the first square is {'white' if first_square_is_white else 'black'}: {progress_in_percent:.3f}%. Details:
remaining combinations: {total_remaining_combinations:23d}
total     combinations: {total_combinations:23d}
elapsed time: {int(elapsed_time)} seconds
estimated remaining time: {int(estimated_remaining_time)} seconds
"""
            header_row = "depth           : "
            value_row = "remaining pieces: "
            for depth, remaining_piece_count in enumerate(remaining_placements):
                header_row += f"{depth:4d}"
                value_row += f"{remaining_piece_count:4d}"
            msg += header_row + "\n" + value_row

            logger.info(msg)

        def report_solution(solution_placements):
            solutions.append((first_square_is_white, copy.deepcopy(solution_placements)))
            solution_as_string = textwrap.indent(get_solution_as_string(solutions[-1]), prefix="    ")
            logger.info(f"Found solution#{len(solutions)}:\n{solution_as_string}")

        # We only report progress on the first two depths, since doing it for depths > 2 would mean we used
        # most of the time doing progress tracking and reporting.
        for depth0_piece_nr, depth0_piece_placement in enumerate(
                pieces_with_rotations_and_placements_as_uint64[0], start=1):
            depth_0_board = depth0_piece_placement
            current_progress[0] = depth0_piece_nr

            for depth1_piece_nr, depth1_piece_placement in enumerate(
                    pieces_with_rotations_and_placements_as_uint64[1], start=1):
                current_progress[1] = depth1_piece_nr

                if (depth_0_board & depth1_piece_placement) == 0:
                    depth_1_board = depth_0_board | depth1_piece_placement

                    for depth2_piece_nr, depth2_piece_placement in enumerate(
                            pieces_with_rotations_and_placements_as_uint64[2], start=1):
                        current_progress[2] = depth2_piece_nr
                        report_progress()
                        if (depth_1_board & depth2_piece_placement) == 0:
                            depth_2_board = depth_1_board | depth2_piece_placement
                            current_placements = [depth0_piece_placement, depth1_piece_placement,
                                                  depth2_piece_placement] + [None for _ in range(
                                len(pieces_with_rotations_and_placements_as_uint64) - 3)]

                            depth = 3
                            recursivly_place_pieces(pieces_with_rotations_and_placements_as_uint64,
                                                    depth, depth_2_board, current_placements,
                                                    report_solution
                                                    )

    logger.info(f"Found {len(solutions)} solutions\n{solutions}")
    for solution_nr, solution in enumerate(solutions, start=1):
        solution_as_string = textwrap.indent(get_solution_as_string(solution), prefix="    ")
        logger.info(f"Solution#{solution_nr}/{len(solutions)}:\n{solution_as_string}")


def get_solution_as_string(solution):
    solution_as_string = ""
    first_square_is_white, placements = solution
    total_board = 0
    for movenr, plancement in enumerate(placements, start=1):
        assert (total_board & plancement) == 0
        total_board |= plancement
        solution_as_string += f"""Move¤{movenr}:
{AsciiBoard.from_uint64(first_square_is_white, plancement)}
"""
    return solution_as_string


if __name__ == "__main__":
    main()

# The log of the first successful run:
# 2021-11-17 02:58:43,705 - Found a solution. len(solutions): 4
# 2021-11-17 03:15:40,142 - Found 4 solutions
# [[103481868288, 1077960768, 2207730630656, 216455360897089536, 2282603319132160, 412856877056, 459009, 2019301482922246144, 530480, 2337403390977376256, 1550, 551911719040, 13871297958533660672], [103481868288, 145806245549309952, 963150610432, 2155905216, 540545024, 13211420065792, 9259647124478361600, 24632, 871464120082235392, 265732, 8097472130012151808, 72340172838010880, 196867], [103481868288, 4224323673915392, 538632, 33008, 139052711936, 4534403132817408, 263175, 551915896832, 1112497192960, 18260963992010752, 16974592, 2233785415175766016, 16185937060769562624], [103481868288, 4255744, 1160820396140789760, 1081145385545629696, 13219976445952, 540542976, 16149943448122687488, 566252800049152, 415546474496, 34013696, 54254851516792832, 248, 1287]]
