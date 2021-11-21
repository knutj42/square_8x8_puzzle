from libc.stdint cimport uint64_t
import math
import numpy
cimport numpy
numpy.import_array()




def run_worker(first_square_is_white, pieces, work_queue, report_solution_queue):
    max_length = max(len(x) for x in pieces)
    np_pieces = numpy.zeros( (len(pieces), max_length+1), dtype=numpy.uint64 )
    for _depth, placements in enumerate(pieces):
        np_pieces[_depth][0] = len(placements)
        for j, placement in enumerate(placements):
            np_pieces[_depth][j+1] = placement
    cdef uint64_t[:,:] c_pieces = np_pieces

    def report_solution(solution_placements):
        py_solution_placements = [int(x) for x in solution_placements]
        report_solution_queue.put((first_square_is_white, py_solution_placements))

    cdef uint64_t c_current_board
    cdef int max_depth
    cdef uint64_t[:] c_current_placements
    while True:
        depth, current_board, current_placements = work_queue.get()
        if depth is None:
            break

        c_current_board = current_board
        max_depth = len(current_placements)
        np_current_placements = numpy.zeros( [max_depth], dtype=numpy.uint64 )
        for i, placement in enumerate(current_placements):
            np_current_placements[i] = placement
        c_current_placements = np_current_placements

        c_recursivly_place_pieces(c_pieces, depth, c_current_board, c_current_placements, report_solution)


cdef uint64_t complete_board_uint64 = (2 ** 64 - 1)

cdef c_recursivly_place_pieces(uint64_t[:,:] c_pieces, int depth, uint64_t current_board,
                               uint64_t[:] current_placements, report_solution_function):
    cdef int placement_count = c_pieces[depth][0]
    cdef uint64_t placement
    cdef uint64_t new_board
    cdef int i
    for i in range(placement_count):
        placement = c_pieces[depth][i+1]
        if (placement & current_board) == 0:
            # This piece can be placed
            current_placements[depth] = placement
            new_board = placement | current_board

            if new_board == complete_board_uint64:
                py_current_placements = []
                for _depth in range(depth+1):
                    py_current_placements.append(current_placements[_depth])
                report_solution_function(py_current_placements)
                return
            else:
                c_recursivly_place_pieces(c_pieces, depth + 1, new_board, current_placements, report_solution_function)
