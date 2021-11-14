import nose
from nose.tools import assert_equal

import rute_puzzle

def test_parse_pieces():
    assert_equal(len(pieces), rute_puzzle.parse_pieces(rute_puzzle.PIECES_STRING))

def test_ascii_to_piece():
    for ascii_original in "hs":
        piece = rute_puzzle.piece_to_ascii(ascii_original)
        ascii_test = rute_puzzle.ascii_to_piece(piece)
        assert_equal(ascii_test, ascii_original)

