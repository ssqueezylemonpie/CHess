
import unittest
import sys
import os

# Add parent dir to path to import chess_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess_engine as ce

class TestBitboardEngine(unittest.TestCase):
    def test_initial_setup(self):
        state = ce.create_initial_state()
        
        # Check piece counts
        self.assertEqual(ce.count_bits(state['bitboards'][ce.P]), 8)
        self.assertEqual(ce.count_bits(state['bitboards'][ce.N]), 2)
        self.assertEqual(ce.count_bits(state['bitboards'][ce.K]), 1)
        self.assertEqual(ce.count_bits(state['bitboards'][ce.p]), 8)
        
        # Check initial occupancy
        self.assertEqual(ce.count_bits(state['occupancies'][ce.WHITE]), 16)
        self.assertEqual(ce.count_bits(state['occupancies'][ce.BLACK]), 16)
        
    def test_initial_moves(self):
        state = ce.create_initial_state()
        moves = ce.generate_moves(state)
        
        # Initial position: 20 moves (16 pawn moves + 4 knight moves)
        self.assertEqual(len(moves), 20)
        
        # Test e4 (pawn at E2 (12) -> E4 (28))
        e2 = ce.E2
        e4 = ce.E4
        
        e4_moves = [m for m in moves if m['from'] == e2 and m['to'] == e4]
        self.assertTrue(len(e4_moves) == 1)
        
    def test_make_move(self):
        state = ce.create_initial_state()
        # Move e2-e4
        move = {'from': ce.E2, 'to': ce.E4, 'promote': None}
        new_state = ce.make_move(state, move)
        
        # Check piece migrated
        self.assertEqual(ce.get_piece_at(new_state, ce.E2), ce.EMPTY)
        self.assertEqual(ce.get_piece_at(new_state, ce.E4), ce.P)
        
        # Check occupancy updated
        self.assertFalse(ce.get_bit(new_state['occupancies'][ce.WHITE], ce.E2))
        self.assertTrue(ce.get_bit(new_state['occupancies'][ce.WHITE], ce.E4))
        
        # Check side to move
        self.assertEqual(new_state['side_to_move'], ce.BLACK)
        
    def test_knight_moves(self):
        # Place Knight at empty board center
        state = ce.create_initial_state()
        # Clear board
        state['bitboards'] = [0] * 12
        state['occupancies'] = [0] * 3
        state['mailbox'] = [ce.EMPTY] * 64
        
        # Place White Knight at d4
        d4 = ce.D4
        state['bitboards'][ce.N] = ce.set_bit(0, d4)
        state['mailbox'][d4] = ce.N
        
        # Place White King at e1 (safe)
        e1 = ce.E1
        state['bitboards'][ce.K] = ce.set_bit(0, e1)
        state['mailbox'][e1] = ce.K
        
        ce.update_occupancies(state['bitboards'], state['occupancies'])
        state['side_to_move'] = ce.WHITE
        
        moves = ce.generate_moves(state)
        # Filter only Knight moves (from d4)
        knight_moves = [m for m in moves if m['from'] == d4]
        
        # Center knight has 8 moves
        self.assertEqual(len(knight_moves), 8)

if __name__ == '__main__':
    unittest.main()
