from libc.stdint cimport uint64_t
import math
import numpy
cimport numpy
numpy.import_array()


def recursivly_place_pieces(pieces, depth, current_board, current_placements,
                            report_solution):
    # This function is only called with depth=2, which means that it is called relativly
    # seldom (i.e. less than once a second). It is therefore not performance critical, and
    # it is ok to recreate the c-level datastructures each time this function is called, even
    # though those structured could in theory have been created once and reused. The advantage
    # is that we get to keep more of the code as pure python.
    cdef uint64_t c_current_board = current_board
    max_length = max(len(x) for x in pieces)
    np_pieces = numpy.zeros( (len(pieces), max_length+1), dtype=numpy.uint64 )
    for _depth, placements in enumerate(pieces):
        np_pieces[_depth][0] = len(placements)
        for j, placement in enumerate(placements):
            np_pieces[_depth][j+1] = placement

    cdef uint64_t[:,:] c_pieces = np_pieces
    max_depth = len(pieces)
    np_current_placements = numpy.zeros( [max_depth], dtype=numpy.uint64 )
    for i, placement in enumerate(current_placements):
        np_current_placements[i] = placement
    cdef uint64_t[:] c_current_placements = np_current_placements

    c_recursivly_place_pieces(c_pieces, depth, c_current_board,
                                 c_current_placements,
                                 report_solution)

cdef uint64_t complete_board_uint64 = (2 ** 64 - 1)

cdef c_recursivly_place_pieces(uint64_t[:,:] pieces, int depth, uint64_t current_board,
                               uint64_t[:] current_placements,
                               object report_solution):

    cdef int placement_count = pieces[depth][0]
    cdef uint64_t placement
    cdef uint64_t new_board
    cdef int i
    for i in range(placement_count):
        placement = pieces[depth][i+1]
        if (placement & current_board) == 0:
            # This piece can be placed
            current_placements[depth] = placement
            new_board = placement | current_board

            if new_board == complete_board_uint64:
                py_current_placements = []
                for _depth in range(depth):
                    py_current_placements.append(current_placements[_depth])
                report_solution(py_current_placements)
                return
            else:
                c_recursivly_place_pieces(pieces, depth + 1,
                                        new_board, current_placements,
                                        report_solution)
