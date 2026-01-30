
import chess_engine as ce
import random

# ============================================================================
# EVALUATION CONSTANTS
# ============================================================================

# Material Values
MATERIAL = {
    ce.P: 100, ce.N: 320, ce.B: 330, ce.R: 500, ce.Q: 900, ce.K: 20000,
    ce.p: -100, ce.n: -320, ce.b: -330, ce.r: -500, ce.q: -900, ce.k: -20000
}

# Piece-Square Tables (PSQT)
# Defined for White. For Black, we mirror the square index (sq ^ 56 for vertical flip).
# Values are integers added to material score.

# Pawns: Encourage center control and advancement
PAWN_PSQT = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

# Knights: Encourage center, discourage edges
KNIGHT_PSQT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

# Bishops: Encourage long diagonals and center
BISHOP_PSQT = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

# Rooks: Encourage 7th rank and open files (simple placement for now)
ROOK_PSQT = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

# Queens: Encourage slight centralization
QUEEN_PSQT = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# King: Encourage safety in middle game (corners)
KING_PSQT = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

# King End Game: Encourage active king
KING_END_PSQT = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# Map piece types to tables
PSQT = {
    ce.P: PAWN_PSQT, ce.N: KNIGHT_PSQT, ce.B: BISHOP_PSQT, 
    ce.R: ROOK_PSQT, ce.Q: QUEEN_PSQT, ce.K: KING_PSQT
}

# ============================================================================
# EVALUATION FUNCTION
# ============================================================================

def evaluate(state):
    """
    Static evaluation of position from White's perspective.
    Returns +score for White advantage, -score for Black advantage.
    """
    if state['game_status'] == 'checkmate':
        return -20000 if state['side_to_move'] == ce.WHITE else 20000
    if state['game_status'] == 'stalemate':
        return 0
        
    score = 0
    mailbox = state['mailbox']
    
    # Iterate through mailbox once? Or iterate bitboards?
    # Iterating bitboards is cleaner for sparse boards, mailbox for full scan.
    # Let's iterate bitboards.
    
    # White pieces
    for p_type in range(ce.P, ce.K + 1):
        bb = state['bitboards'][p_type]
        while bb:
            sq = (bb & -bb).bit_length() - 1
            # Material
            score += MATERIAL[p_type]
            # PSQT
            # Note: 1D array is ranks 8->1 or 1->8? 
            # In chess_engine, Index 0 = a1.
            # Our tables are usually laid out rank 8 to 1 visually in code, 
            # but we need to map index 0 (a1) to the correct table index.
            # If table is 0..63 where 0 is top-left (a8), then map is:
            # a1 (0) -> index 56.
            # Mirror for black?
            
            # Let's standardize:
            # Code uses Little Endian Rank-File: 0=a1, 7=h1, ... 56=a8, 63=h8.
            # Table definitions above: Index 0 is Top-Left (a8). Index 63 is Bottom-Right (h1).
            # This is "Big Endian Rank-File" effectively on the ranks.
            
            # So for a Square 's' (0-63, a1-h8):
            # Rank 0 (a1..h1) corresponds to last row of table.
            # Table index = (7 - rank) * 8 + file
            
            rank, file = sq // 8, sq % 8
            table_idx = (7 - rank) * 8 + file
            
            score += PSQT[p_type][table_idx]
            
            bb &= bb - 1
            
    # Black pieces
    for p_type in range(ce.p, ce.k + 1):
        bb = state['bitboards'][p_type]
        base_type = p_type - 6
        while bb:
            sq = (bb & -bb).bit_length() - 1
            score += MATERIAL[p_type] # Negative value
            
            # PSQT for Black
            # Mirror square: a1 (0) acts like a8 (56) for white.
            # Rank 0 becomes Rank 7.
            # Table index = (7 - (7-rank)) * 8 + file = rank * 8 + file ?
            # Wait. If Black is on Rank 7 (start), it should act like White on Rank 1 (start).
            # White Rank 1 is bottom of table.
            # Black Rank 7 is top of table? No, Black Rank 7 is "Black's 2nd Rank".
            # Setup: White at ranks 0,1. Black at 6,7.
            # White P on rank 1 (index 0 in table logic? No, rank 1 is 2nd row from bottom).
            
            # Let's restart mapping.
            # White Pawn on a2 (sq=8). Should get standard bonus.
            # Table: Row 6 (2nd from bottom).
            
            # Black Pawn on a7 (sq=48). Should get same bonus.
            # Mirror: Relative rank 1.
            # If we flip the board vertically: sq ^ 56.
            # 48 (110000) ^ 56 (111000) = 001000 = 8.
            # So we use the flipped square index to lookup in the White table.
            
            rank, file = sq // 8, sq % 8
            flipped_sq = sq ^ 56 # Vertical flip
            
            # Now map flipped_sq to table index (reversed ranks again)
            f_rank, f_file = flipped_sq // 8, flipped_sq % 8
            table_idx = (7 - f_rank) * 8 + f_file
            
            score -= PSQT[base_type][table_idx] # Subtract because black wants negative score
            
            bb &= bb - 1
            
    return score

# ============================================================================
# SEARCH
# ============================================================================

def get_best_move(state, depth=3):
    """
    Root function for minimax search.
    """
    best_move = None
    moves = ce.generate_moves(state)
    
    # Shuffle for variety if scores are equal
    random.shuffle(moves)
    
    # Optim: Move ordering (captures first)
    # Simple check for capture: occupied destination
    # This happens inside minimax usually, but good for root too.
    
    if not moves:
        return None
        
    # Maximizing for WHITE, Minimizing for BLACK
    maximizing = (state['side_to_move'] == ce.WHITE)
    
    alpha = -float('inf')
    beta = float('inf')
    
    best_score = -float('inf') if maximizing else float('inf')
    
    for move in moves:
        # Clone state (expensive but safe)
        new_state = ce.make_move(state, move)
        
        score = minimax(new_state, depth - 1, alpha, beta, not maximizing)
        
        if maximizing:
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        else:
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, score)
            
        # Root alpha-beta?
        # Typically we don't prune at root loop unless we return early, 
        # but here we just want finding best.
        
    return best_move

def minimax(state, depth, alpha, beta, maximizing_player):
    if depth == 0 or state['game_status'] != 'ongoing':
        return evaluate(state)
        
    moves = ce.generate_moves(state)
    
    if not moves:
        # Checkmate or Stalemate logic was likely handled in make_move setting status,
        # but if generate_moves returns empty and status says ongoing (lag?), check here.
        if ce.is_in_check(state, state['side_to_move']):
            return -20000 + (10 - depth) if maximizing_player else 20000 - (10 - depth) 
            # Prefer faster mate
        return 0 # Stalemate
        
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            new_state = ce.make_move(state, move)
            eval_score = minimax(new_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_state = ce.make_move(state, move)
            eval_score = minimax(new_state, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

