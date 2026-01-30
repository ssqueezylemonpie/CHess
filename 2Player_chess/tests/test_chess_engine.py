"""
Unit tests for the chess engine.
Tests tricky rules: castling, en passant, pinned pieces, promotion.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chess_engine as ce


class TestCastling:
    """Tests for castling rules."""
    
    def setup_castling_position(self):
        """Create a position where castling is possible."""
        state = ce.create_initial_state()
        # Clear squares between king and rooks
        # Kingside: f1, g1
        del state['board'][(0, 5)]  # Bishop
        del state['board'][(0, 6)]  # Knight
        # Queenside: b1, c1, d1
        del state['board'][(0, 1)]  # Knight  
        del state['board'][(0, 2)]  # Bishop
        del state['board'][(0, 3)]  # Queen
        return state
    
    def test_kingside_castling_allowed(self):
        """Test that kingside castling is allowed when path is clear."""
        state = self.setup_castling_position()
        legal_moves = ce.generate_legal_moves(state, (0, 4))  # King at e1
        assert (0, 6) in legal_moves, "Kingside castling should be allowed"
    
    def test_queenside_castling_allowed(self):
        """Test that queenside castling is allowed when path is clear."""
        state = self.setup_castling_position()
        legal_moves = ce.generate_legal_moves(state, (0, 4))  # King at e1
        assert (0, 2) in legal_moves, "Queenside castling should be allowed"
    
    def test_cannot_castle_when_in_check(self):
        """Test that castling is not allowed when king is in check."""
        state = self.setup_castling_position()
        # Remove pawn that blocks e-file check
        del state['board'][(1, 4)]  # Remove e2 pawn
        # Remove black king from e8 if present
        if (7, 4) in state['board']:
            del state['board'][(7, 4)]
        state['board'][(7, 0)] = 'k'  # Move black king to a8
        # Put black rook on e2 to give check to white king on e1
        state['board'][(1, 4)] = 'r'
        
        legal_moves = ce.generate_legal_moves(state, (0, 4))
        assert (0, 6) not in legal_moves, "Cannot castle when in check"
        assert (0, 2) not in legal_moves, "Cannot castle when in check"
    
    def test_cannot_castle_through_check(self):
        """Test that king cannot castle through an attacked square."""
        state = self.setup_castling_position()
        # Remove pawn that blocks f-file attack
        del state['board'][(1, 5)]  # Remove f2 pawn
        # Put a black rook attacking f1 through the cleared pawn
        state['board'][(3, 5)] = 'r'  # Rook on f4 attacks f1
        
        legal_moves = ce.generate_legal_moves(state, (0, 4))
        assert (0, 6) not in legal_moves, "Cannot castle through attacked square"
    
    def test_cannot_castle_into_check(self):
        """Test that king cannot castle into check."""
        state = self.setup_castling_position()
        # Remove pawn that blocks g-file attack
        del state['board'][(1, 6)]  # Remove g2 pawn
        # Put a black rook attacking g1 through the cleared pawn
        state['board'][(3, 6)] = 'r'  # Rook on g4 attacks g1
        
        legal_moves = ce.generate_legal_moves(state, (0, 4))
        assert (0, 6) not in legal_moves, "Cannot castle into check"
    
    def test_castling_moves_rook(self):
        """Test that castling correctly moves the rook."""
        state = self.setup_castling_position()
        
        # Kingside castle
        new_state = ce.apply_move_internal(state, (0, 4), (0, 6))
        assert new_state['board'].get((0, 6)) == 'K', "King should be on g1"
        assert new_state['board'].get((0, 5)) == 'R', "Rook should be on f1"
        assert (0, 7) not in new_state['board'], "h1 should be empty"
        assert (0, 4) not in new_state['board'], "e1 should be empty"
    
    def test_castling_rights_lost_after_king_move(self):
        """Test that castling rights are lost after king moves."""
        state = self.setup_castling_position()
        
        # Move king
        new_state = ce.apply_move_internal(state, (0, 4), (0, 5))
        assert 'WK' not in new_state['castling_rights']
        assert 'WQ' not in new_state['castling_rights']
    
    def test_castling_rights_lost_after_rook_move(self):
        """Test that castling rights are lost after rook moves."""
        state = self.setup_castling_position()
        
        # Move kingside rook
        new_state = ce.apply_move_internal(state, (0, 7), (0, 5))
        assert 'WK' not in new_state['castling_rights']
        assert 'WQ' in new_state['castling_rights']  # Queenside still allowed


class TestEnPassant:
    """Tests for en passant capture."""
    
    def test_en_passant_target_set(self):
        """Test that double pawn push sets en passant target."""
        state = ce.create_initial_state()
        
        # Move e2-e4
        new_state = ce.apply_move_internal(state, (1, 4), (3, 4))
        assert new_state['en_passant_target'] == (2, 4), "En passant target should be e3"
    
    def test_en_passant_capture_allowed(self):
        """Test that en passant capture is legal immediately after double push."""
        state = ce.create_initial_state()
        
        # Set up: white pawn on e5, black just played d7-d5
        state['board'][(4, 4)] = 'P'  # White pawn on e5
        del state['board'][(1, 4)]  # Remove from e2
        state['board'][(4, 3)] = 'p'  # Black pawn on d5
        del state['board'][(6, 3)]  # Remove from d7
        state['en_passant_target'] = (5, 3)  # d6 is en passant target
        
        legal_moves = ce.generate_legal_moves(state, (4, 4))
        assert (5, 3) in legal_moves, "En passant capture should be allowed"
    
    def test_en_passant_expires(self):
        """Test that en passant expires after one move."""
        state = ce.create_initial_state()
        
        # Set up en passant target
        state['en_passant_target'] = (5, 3)  # d6
        
        # Any move should clear en passant target
        new_state = ce.apply_move_internal(state, (1, 0), (2, 0))  # a2-a3
        assert new_state['en_passant_target'] is None, "En passant should expire"
    
    def test_en_passant_removes_pawn(self):
        """Test that en passant capture removes the captured pawn."""
        state = ce.create_initial_state()
        
        # Set up: white pawn on e5, black pawn on d5
        state['board'][(4, 4)] = 'P'  # White pawn on e5
        del state['board'][(1, 4)]
        state['board'][(4, 3)] = 'p'  # Black pawn on d5
        del state['board'][(6, 3)]
        state['en_passant_target'] = (5, 3)  # d6
        
        # Capture en passant
        new_state = ce.apply_move_internal(state, (4, 4), (5, 3))
        
        assert new_state['board'].get((5, 3)) == 'P', "White pawn should be on d6"
        assert (4, 3) not in new_state['board'], "Black pawn should be captured"


class TestPinnedPieces:
    """Tests for pinned pieces."""
    
    def test_pinned_piece_cannot_move(self):
        """Test that a pinned piece cannot move if it exposes the king."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        # White king on e1, white bishop on e3, black rook on e8
        state['board'][(0, 4)] = 'K'  # King on e1
        state['board'][(2, 4)] = 'B'  # Bishop on e3 (pinned vertically)
        state['board'][(7, 4)] = 'r'  # Black rook on e8
        state['board'][(7, 0)] = 'k'  # Black king on a8
        
        legal_moves = ce.generate_legal_moves(state, (2, 4))
        assert len(legal_moves) == 0, "Pinned bishop should not be able to move"
    
    def test_pinned_piece_can_capture_pinner(self):
        """Test that a pinned piece can capture the piece pinning it."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        # White king on e1, white rook on e3, black rook on e8
        state['board'][(0, 4)] = 'K'  # King on e1
        state['board'][(2, 4)] = 'R'  # Rook on e3 (pinned but can capture)
        state['board'][(7, 4)] = 'r'  # Black rook on e8
        state['board'][(7, 0)] = 'k'  # Black king on a8
        
        legal_moves = ce.generate_legal_moves(state, (2, 4))
        assert (7, 4) in legal_moves, "Pinned rook should be able to capture pinner"
    
    def test_pinned_piece_can_move_along_pin_line(self):
        """Test that a pinned piece can move along the pin line."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        # White king on e1, white rook on e3, black rook on e8
        state['board'][(0, 4)] = 'K'  # King on e1
        state['board'][(2, 4)] = 'R'  # Rook on e3
        state['board'][(7, 4)] = 'r'  # Black rook on e8
        state['board'][(7, 0)] = 'k'  # Black king on a8
        
        legal_moves = ce.generate_legal_moves(state, (2, 4))
        # Rook can move to any square on the e-file between king and pinner
        assert (1, 4) in legal_moves, "Should be able to move to e2"
        assert (3, 4) in legal_moves, "Should be able to move to e4"
        assert (4, 4) in legal_moves, "Should be able to move to e5"
        # But not sideways
        assert (2, 3) not in legal_moves, "Should not be able to move to d3"


class TestPromotion:
    """Tests for pawn promotion."""
    
    def test_pawn_on_7th_can_promote(self):
        """Test that a pawn on the 7th rank can move to promote."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(6, 4)] = 'P'  # White pawn on e7
        state['board'][(0, 0)] = 'K'  # White king
        state['board'][(7, 0)] = 'k'  # Black king
        
        legal_moves = ce.generate_legal_moves(state, (6, 4))
        assert (7, 4) in legal_moves, "Pawn should be able to move to e8"
    
    def test_promotion_to_queen(self):
        """Test pawn promotion to queen."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(6, 4)] = 'P'  # White pawn on e7
        state['board'][(0, 0)] = 'K'  # White king
        state['board'][(7, 0)] = 'k'  # Black king
        
        new_state = ce.apply_move_internal(state, (6, 4), (7, 4), 'Q')
        assert new_state['board'].get((7, 4)) == 'Q', "Pawn should promote to queen"
    
    def test_promotion_to_knight(self):
        """Test pawn promotion to knight."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(6, 4)] = 'P'  # White pawn on e7
        state['board'][(0, 0)] = 'K'  # White king
        state['board'][(7, 0)] = 'k'  # Black king
        
        new_state = ce.apply_move_internal(state, (6, 4), (7, 4), 'N')
        assert new_state['board'].get((7, 4)) == 'N', "Pawn should promote to knight"
    
    def test_black_pawn_promotion(self):
        """Test that black pawns promote on rank 1."""
        state = ce.create_initial_state()
        state['board'] = {}
        state['side_to_move'] = 'black'
        
        state['board'][(1, 4)] = 'p'  # Black pawn on e2
        state['board'][(7, 0)] = 'k'  # Black king
        state['board'][(7, 7)] = 'K'  # White king
        
        legal_moves = ce.generate_legal_moves(state, (1, 4))
        assert (0, 4) in legal_moves, "Black pawn should be able to move to e1"
        
        new_state = ce.apply_move_internal(state, (1, 4), (0, 4), 'Q')
        assert new_state['board'].get((0, 4)) == 'q', "Black pawn should promote to black queen"


class TestCheckmate:
    """Tests for checkmate detection."""
    
    def test_simple_queen_mate(self):
        """Test detection of simple checkmate with two rooks (ladder mate)."""
        state = ce.create_initial_state()
        state['board'] = {}
        state['side_to_move'] = 'black'
        
        # Classic ladder mate with two rooks
        state['board'][(7, 4)] = 'k'  # Black king on e8
        state['board'][(7, 0)] = 'R'  # White rook on a8 giving check
        state['board'][(6, 0)] = 'R'  # White rook on a7 blocking escape
        state['board'][(0, 4)] = 'K'  # White king
        
        result = ce.detect_game_end(state)
        assert result == 'checkmate', "Should be checkmate"
    
    def test_back_rank_mate(self):
        """Test detection of back rank mate."""
        state = ce.create_initial_state()
        state['board'] = {}
        state['side_to_move'] = 'black'
        
        # Black king trapped by own pawns, white rook delivers mate
        state['board'][(7, 6)] = 'k'  # Black king on g8
        state['board'][(6, 5)] = 'p'  # Black pawn on f7
        state['board'][(6, 6)] = 'p'  # Black pawn on g7
        state['board'][(6, 7)] = 'p'  # Black pawn on h7
        state['board'][(7, 0)] = 'R'  # White rook on a8 (giving checkmate)
        state['board'][(0, 4)] = 'K'  # White king far away
        
        result = ce.detect_game_end(state)
        assert result == 'checkmate', "Should be back rank mate"


class TestStalemate:
    """Tests for stalemate detection."""
    
    def test_basic_stalemate(self):
        """Test detection of basic stalemate."""
        state = ce.create_initial_state()
        state['board'] = {}
        state['side_to_move'] = 'black'
        
        # King in corner, can't move
        state['board'][(7, 7)] = 'k'  # Black king on h8
        state['board'][(5, 6)] = 'Q'  # White queen on g6
        state['board'][(5, 7)] = 'K'  # White king on h6
        
        result = ce.detect_game_end(state)
        assert result == 'stalemate', "Should be stalemate"


class TestInsufficientMaterial:
    """Tests for insufficient material draw detection."""
    
    def test_king_vs_king(self):
        """Test that K vs K is insufficient material."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(0, 0)] = 'K'
        state['board'][(7, 7)] = 'k'
        
        assert ce.insufficient_material(state) is True
    
    def test_king_bishop_vs_king(self):
        """Test that K+B vs K is insufficient material."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(0, 0)] = 'K'
        state['board'][(0, 2)] = 'B'
        state['board'][(7, 7)] = 'k'
        
        assert ce.insufficient_material(state) is True
    
    def test_king_knight_vs_king(self):
        """Test that K+N vs K is insufficient material."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(0, 0)] = 'K'
        state['board'][(0, 1)] = 'N'
        state['board'][(7, 7)] = 'k'
        
        assert ce.insufficient_material(state) is True
    
    def test_king_rook_vs_king_sufficient(self):
        """Test that K+R vs K is sufficient material."""
        state = ce.create_initial_state()
        state['board'] = {}
        
        state['board'][(0, 0)] = 'K'
        state['board'][(0, 7)] = 'R'
        state['board'][(7, 7)] = 'k'
        
        assert ce.insufficient_material(state) is False


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
