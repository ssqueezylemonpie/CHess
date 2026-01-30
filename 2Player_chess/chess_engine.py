"""
Chess Engine - Bitboard and 1D Array Implementation
"""

import copy

# ============================================================================
# CONSTANTS & DEFINITIONS
# ============================================================================

# Board representation
# 64 squares: a8=0, b8=1, ... h8=7, ..., a1=56, h1=63
# This is a common "Little Endian Rank-File" mapping often used or similar.
# Let's map strict 0-63 where 0=a1, 1=b1 ... 7=h1, ... 56=a8, 63=h8
# This matches the standard bitboard bits (bit 0 = a1).

SQUARES = [
    'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1',
    'a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2',
    'a3', 'b3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3',
    'a4', 'b4', 'c4', 'd4', 'e4', 'f4', 'g4', 'h4',
    'a5', 'b5', 'c5', 'd5', 'e5', 'f5', 'g5', 'h5',
    'a6', 'b6', 'c6', 'd6', 'e6', 'f6', 'g6', 'h6',
    'a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7',
    'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8'
]

# Create enum-like constants for squares
for i, sq in enumerate(SQUARES):
    globals()[sq.upper()] = i

# Piece encoding
P, N, B, R, Q, K = 0, 1, 2, 3, 4, 5
p, n, b, r, q, k = 6, 7, 8, 9, 10, 11
EMPTY = -1

# Color
WHITE, BLACK = 0, 1
BOTH = 2

PIECE_CHARS = {
    P: 'P', N: 'N', B: 'B', R: 'R', Q: 'Q', K: 'K',
    p: 'p', n: 'n', b: 'b', r: 'r', q: 'q', k: 'k',
    EMPTY: '.'
}

PIECE_FROM_CHAR = {v: k for k, v in PIECE_CHARS.items() if k != EMPTY}

# Bitboard constants
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
RANK_1 = 0x00000000000000FF
RANK_8 = 0xFF00000000000000

# Compass directions for move generation on 1D array
# We will use bitwise operations primarily, but for 1D array logic:
# 0 is a1, 1 is b1 ...
# North = +8, South = -8, East = +1, West = -1

# ============================================================================
# BITBOARD HELPERS
# ============================================================================

def get_bit(bitboard, square):
    """Check if bit at square is set."""
    return (bitboard & (1 << square)) != 0

def set_bit(bitboard, square):
    """Set bit at square."""
    return bitboard | (1 << square)

def pop_bit(bitboard, square):
    """Clear bit at square."""
    return bitboard & ~(1 << square)

def count_bits(bitboard):
    """Count set bits using bin().count('1')."""
    return bin(bitboard).count('1')

def print_bitboard(bitboard):
    """Debug print a bitboard."""
    print("Bitboard:")
    for rank in range(7, -1, -1):
        line = ""
        for file in range(8):
            sq = rank * 8 + file
            if get_bit(bitboard, sq):
                line += "1 "
            else:
                line += "0 "
        print(line)
    print(f"Decimal: {bitboard}\n")

# ============================================================================
# BOARD STATE
# ============================================================================

def create_initial_state():
    """
    Create the initial chess position.
    state = {
        'bitboards': [int] * 12, # P, N, B, R, Q, K, p, n, b, r, q, k
        'occupancies': [int] * 3, # WHITE, BLACK, BOTH
        'mailbox': [int] * 64, # Piece at each square or EMPTY
        'side_to_move': WHITE,
        'castling_rights': 0b1111, # WK, WQ, bk, bq
        'en_passant': -1, # Square index or -1
        'halfmove': 0,
        'fullmove': 1,
        'game_status': 'ongoing',
        'selected_square': None # (saved as index)
    }
    """
    bitboards = [0] * 12
    occupancies = [0] * 3
    mailbox = [EMPTY] * 64
    
    # Setup standard board string map for parsing
    # White pieces
    setup_pieces(bitboards, mailbox, P, [A2, B2, C2, D2, E2, F2, G2, H2])
    setup_pieces(bitboards, mailbox, R, [A1, H1])
    setup_pieces(bitboards, mailbox, N, [B1, G1])
    setup_pieces(bitboards, mailbox, B, [C1, F1])
    setup_pieces(bitboards, mailbox, Q, [D1])
    setup_pieces(bitboards, mailbox, K, [E1])
    
    # Black pieces
    setup_pieces(bitboards, mailbox, p, [A7, B7, C7, D7, E7, F7, G7, H7])
    setup_pieces(bitboards, mailbox, r, [A8, H8])
    setup_pieces(bitboards, mailbox, n, [B8, G8])
    setup_pieces(bitboards, mailbox, b, [C8, F8])
    setup_pieces(bitboards, mailbox, q, [D8])
    setup_pieces(bitboards, mailbox, k, [E8])
    
    # Update occupancies
    update_occupancies(bitboards, occupancies)
    
    return {
        'bitboards': bitboards,
        'occupancies': occupancies,
        'mailbox': mailbox,
        'side_to_move': WHITE,
        'castling_rights': 0b1111, # Bitmask: K(bit 0), Q(bit 1), k(bit 2), q(bit 3)
        'en_passant': -1,
        'halfmove': 0,
        'fullmove': 1,
        'game_status': 'ongoing',
        'selected_square': None,
        'history': [list(mailbox)] # Track history (list of mailbox snapshots)
    }

def setup_pieces(bitboards, mailbox, piece_type, squares):
    for sq in squares:
        bitboards[piece_type] = set_bit(bitboards[piece_type], sq)
        mailbox[sq] = piece_type

def update_occupancies(bitboards, occupancies):
    occupancies[WHITE] = 0
    occupancies[BLACK] = 0
    
    for p_type in range(P, K + 1):
        occupancies[WHITE] |= bitboards[p_type]
    for p_type in range(p, k + 1):
        occupancies[BLACK] |= bitboards[p_type]
        
    occupancies[BOTH] = occupancies[WHITE] | occupancies[BLACK]

def get_piece_at(state, square_index):
    if 0 <= square_index < 64:
        return state['mailbox'][square_index]
    return EMPTY

def get_piece_color(piece):
    if piece == EMPTY: return None
    return WHITE if piece <= K else BLACK

# ============================================================================
# ATTACK TABLES (PRE-CALCULATED)
# ============================================================================

# We need to generate attack tables on import
pawn_attacks = [[0] * 64 for _ in range(2)] # [color][square]
knight_attacks = [0] * 64
king_attacks = [0] * 64

def init_leapers():
    for sq in range(64):
        # Pawns
        # White (moves "north" +7/+9 for capture)
        wp = 0
        if (sq // 8) < 7: # Not on 8th rank
            if (sq % 8) > 0: wp |= (1 << (sq + 7)) # Capture left
            if (sq % 8) < 7: wp |= (1 << (sq + 9)) # Capture right
        pawn_attacks[WHITE][sq] = wp
        
        # Black (moves "south" -7/-9 for capture)
        bp = 0
        if (sq // 8) > 0: # Not on 1st rank
            if (sq % 8) > 0: bp |= (1 << (sq - 9))
            if (sq % 8) < 7: bp |= (1 << (sq - 7))
        pawn_attacks[BLACK][sq] = bp
        
        # Knights
        kn = 0
        rank, file = sq // 8, sq % 8
        moves = [
            (rank + 2, file - 1), (rank + 2, file + 1),
            (rank + 1, file - 2), (rank + 1, file + 2),
            (rank - 2, file - 1), (rank - 2, file + 1),
            (rank - 1, file - 2), (rank - 1, file + 2)
        ]
        for r, f in moves:
            if 0 <= r <= 7 and 0 <= f <= 7:
                kn |= (1 << (r * 8 + f))
        knight_attacks[sq] = kn
        
        # King
        k = 0
        moves = [
            (rank + 1, file - 1), (rank + 1, file), (rank + 1, file + 1),
            (rank, file - 1),                     (rank, file + 1),
            (rank - 1, file - 1), (rank - 1, file), (rank - 1, file + 1)
        ]
        for r, f in moves:
            if 0 <= r <= 7 and 0 <= f <= 7:
                k |= (1 << (r * 8 + f))
        king_attacks[sq] = k

init_leapers()

# Sliding pieces attack generation (on the fly for now for simplicity, can optim later)
def get_bishop_attacks(square, occupancy):
    attacks = 0
    rank, file = square // 8, square % 8
    for dr, df in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        r, f = rank + dr, file + df
        while 0 <= r <= 7 and 0 <= f <= 7:
            sq = r * 8 + f
            attacks |= (1 << sq)
            if (occupancy & (1 << sq)): break
            r += dr
            f += df
    return attacks

def get_rook_attacks(square, occupancy):
    attacks = 0
    rank, file = square // 8, square % 8
    for dr, df in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, f = rank + dr, file + df
        while 0 <= r <= 7 and 0 <= f <= 7:
            sq = r * 8 + f
            attacks |= (1 << sq)
            if (occupancy & (1 << sq)): break
            r += dr
            f += df
    return attacks

def get_queen_attacks(square, occupancy):
    return get_bishop_attacks(square, occupancy) | get_rook_attacks(square, occupancy)

# ============================================================================
# MOVE GENERATION
# ============================================================================

def is_square_attacked(state, square, by_color):
    """Check if square is attacked by 'by_color'."""
    # If attacked by pawn
    # Attack table is "squares that a pawn on X attacks".
    # Conversely, to check if SQ is attacked BY a pawn, we check if a pawn on a source square attacks SQ.
    # THIS bitboard table is [color][from_sq] -> attack_mask.
    # Symmetry: If pawn at A attacks B, then pawn at B (opposite color) attacks A.
    opp_pawn_color = BLACK if by_color == WHITE else WHITE
    # If we put a pawn of OPPOSITE color on valid 'square', where would it attack?
    # Those valid attacks are squares where if a friendly pawn existed, it would be attacking 'square'.
    
    # Actually simpler: Look at pawns of 'by_color'.
    # Bitwise AND their attacks with our square? No.
    # We want to know if ANY piece of 'by_color' attacks 'square'.
    
    bitboards = state['bitboards']
    occupancy = state['occupancies'][BOTH]
    
    # 1. Attacked by Pawn?
    # Check if a pawn of 'by_color' is on a square that attacks 'square'.
    # This is equivalent to: Place a pawn of 'opponent_color(by_color)' at 'square', and see if it lands on any 'by_color' pawn.
    attacking_pawns = bitboards[P] if by_color == WHITE else bitboards[p]
    # Use the table for the DEFENDER's color to project attacks backwards
    defender_color = BLACK if by_color == WHITE else WHITE 
    if (pawn_attacks[defender_color][square] & attacking_pawns):
        return True
        
    # 2. Attacked by Knight?
    attacking_knights = bitboards[N] if by_color == WHITE else bitboards[n]
    if (knight_attacks[square] & attacking_knights):
        return True
        
    # 3. Attacked by King?
    attacking_king = bitboards[K] if by_color == WHITE else bitboards[k]
    if (king_attacks[square] & attacking_king):
        return True
        
    # 4. Attacked by Bishop/Queen? (Diagonals)
    attacking_bishops = bitboards[B] if by_color == WHITE else bitboards[b]
    attacking_queens = bitboards[Q] if by_color == WHITE else bitboards[q]
    diagonal_attackers = attacking_bishops | attacking_queens
    if get_bishop_attacks(square, occupancy) & diagonal_attackers:
        return True
        
    # 5. Attacked by Rook/Queen? (Straights)
    attacking_rooks = bitboards[R] if by_color == WHITE else bitboards[r]
    # queens already included? No, separate bitboard
    straight_attackers = attacking_rooks | attacking_queens
    if get_rook_attacks(square, occupancy) & straight_attackers:
        return True
        
    return False

def generate_moves(state, only_captures=False):
    """
    Generate legal moves.
    Returns list of {'from': int, 'to': int, 'promotion': int/None}
    """
    moves = []
    side = state['side_to_move']
    bitboards = state['bitboards']
    occupancies = state['occupancies']
    
    # Define friendly/enemy pieces
    if side == WHITE:
        friendly = occupancies[WHITE]
        enemy = occupancies[BLACK]
        pieces = range(P, K + 1)
        pawn_type = P
    else:
        friendly = occupancies[BLACK]
        enemy = occupancies[WHITE]
        pieces = range(p, k + 1)
        pawn_type = p
        
    # Loop over all friendly pieces
    for p_type in pieces:
        piece_bb = bitboards[p_type]
        
        while piece_bb:
            # Get LS1B index
            from_sq = (piece_bb & -piece_bb).bit_length() - 1
            
            # Generate pseudo-legal moves for this piece
            attacks = 0
            
            if p_type == P or p_type == p:
                attacks = get_pawn_moves(state, from_sq, side, enemy, occupancies[BOTH])
            elif p_type == N or p_type == n:
                attacks = knight_attacks[from_sq] & ~friendly
            elif p_type == B or p_type == b:
                attacks = get_bishop_attacks(from_sq, occupancies[BOTH]) & ~friendly
            elif p_type == R or p_type == r:
                attacks = get_rook_attacks(from_sq, occupancies[BOTH]) & ~friendly
            elif p_type == Q or p_type == q:
                attacks = get_queen_attacks(from_sq, occupancies[BOTH]) & ~friendly
            elif p_type == K or p_type == k:
                attacks = king_attacks[from_sq] & ~friendly
                # Add Castling moves (special handling later or here)
            
            # Filter captures if needed
            if only_captures:
                attacks &= enemy
            
            # Verify legality (does not leave king in check)
            while attacks:
                to_sq = (attacks & -attacks).bit_length() - 1
                
                # Create move object
                move = {'from': from_sq, 'to': to_sq, 'promote': None}
                
                # Handle Pawn Promotion
                if (p_type == P and (7 * 8 <= to_sq <= 7 * 8 + 7)) or \
                   (p_type == p and (0 <= to_sq <= 7)):
                    # Add 4 promotion moves
                    for promo in [Q, R, B, N]: # Use int constants or chars? Use ints.
                        # Adjust for black
                        real_promo = promo if side == WHITE else promo + 6
                        m = move.copy()
                        m['promote'] = real_promo
                        if is_legal(state, m):
                            moves.append(m)
                else:
                    if is_legal(state, move):
                        moves.append(move)
                        
                attacks &= attacks - 1 # Pop bit
            
            piece_bb &= piece_bb - 1 # Pop bit
            
    # Add Castling (if not only_captures)
    if not only_captures:
        moves.extend(generate_castling_moves(state, side))
        
    return moves

def get_pawn_moves(state, sq, side, enemy, both):
    moves = 0
    rank = sq // 8
    
    if side == WHITE:
        # Push 1
        target = sq + 8
        if target < 64 and not get_bit(both, target):
            moves |= (1 << target)
            # Push 2
            if rank == 1:
                target2 = sq + 16
                if not get_bit(both, target2):
                    moves |= (1 << target2)
        
        # Captures
        attacks = pawn_attacks[WHITE][sq] & enemy
        moves |= attacks
        
        # En Passant
        if state['en_passant'] != -1:
            ep_sq = state['en_passant']
            # Check if pawn attacks ep_sq
            if get_bit(pawn_attacks[WHITE][sq], ep_sq):
                 moves |= (1 << ep_sq)
                 
    else: # BLACK
        # Push 1
        target = sq - 8
        if target >= 0 and not get_bit(both, target):
            moves |= (1 << target)
            # Push 2
            if rank == 6:
                target2 = sq - 16
                if not get_bit(both, target2):
                    moves |= (1 << target2)
                    
        # Captures
        attacks = pawn_attacks[BLACK][sq] & enemy
        moves |= attacks
        
        # En Passant
        if state['en_passant'] != -1:
            ep_sq = state['en_passant']
            if get_bit(pawn_attacks[BLACK][sq], ep_sq):
                 moves |= (1 << ep_sq)
                 
    return moves

def generate_castling_moves(state, side):
    moves = []
    if is_in_check(state, side):
        return moves
        
    bitboards = state['bitboards']
    occupancy = state['occupancies'][BOTH]
    
    # Castling Rights: WK=1, WQ=2, bk=4, bq=8
    rights = state['castling_rights']
    
    if side == WHITE:
        # Kingside (e1 -> g1)
        if (rights & 1) and not get_bit(occupancy, F1) and not get_bit(occupancy, G1):
            if not is_square_attacked(state, F1, BLACK) and not is_square_attacked(state, G1, BLACK):
                 moves.append({'from': E1, 'to': G1, 'promote': None, 'castle': 'K'})
        # Queenside (e1 -> c1)
        if (rights & 2) and not get_bit(occupancy, D1) and not get_bit(occupancy, C1) and not get_bit(occupancy, B1):
            if not is_square_attacked(state, D1, BLACK) and not is_square_attacked(state, C1, BLACK):
                 moves.append({'from': E1, 'to': C1, 'promote': None, 'castle': 'Q'})
    else:
        # Kingside (e8 -> g8)
        if (rights & 4) and not get_bit(occupancy, F8) and not get_bit(occupancy, G8):
            if not is_square_attacked(state, F8, WHITE) and not is_square_attacked(state, G8, WHITE):
                 moves.append({'from': E8, 'to': G8, 'promote': None, 'castle': 'k'})
        # Queenside (e8 -> c8)
        if (rights & 8) and not get_bit(occupancy, D8) and not get_bit(occupancy, C8) and not get_bit(occupancy, B8):
            if not is_square_attacked(state, D8, WHITE) and not is_square_attacked(state, C8, WHITE):
                 moves.append({'from': E8, 'to': C8, 'promote': None, 'castle': 'q'})
                 
    return moves

def is_legal(state, move):
    # Make move on copy, check if king attacked
    new_state = make_move(state, move, test_only=True)
    return not is_in_check(new_state, state['side_to_move']) # King of ORIGINAL side

def is_in_check(state, side):
    # Find king
    k_type = K if side == WHITE else k
    k_bb = state['bitboards'][k_type]
    if not k_bb: return True # Should not happen (king captured?)
    
    k_sq = (k_bb & -k_bb).bit_length() - 1
    return is_square_attacked(state, k_sq, BLACK if side == WHITE else WHITE)

# ============================================================================
# MOVE MAKING
# ============================================================================

def make_move(state, move, test_only=False):
    """
    Apply a move and return new state.
    move: {'from', 'to', 'promote', 'castle'}
    """
    # Simple copy for now (dicts are immutable-ish if deepcopied)
    # Optim: Manual copy of arrays is faster
    new_bitboards = list(state['bitboards'])
    new_occupancies = list(state['occupancies'])
    new_mailbox = list(state['mailbox'])
    
    new_state = {
        'bitboards': new_bitboards,
        'occupancies': new_occupancies,
        'mailbox': new_mailbox,
        'side_to_move': state['side_to_move'],
        'castling_rights': state['castling_rights'],
        'en_passant': -1,
        'halfmove': state['halfmove'] + 1,
        'fullmove': state['fullmove'],
        'game_status': 'ongoing',
        'selected_square': None
    }
    
    frm, to = move['from'], move['to']
    piece = new_mailbox[frm]
    captured = new_mailbox[to]
    side = state['side_to_move']
    
    # 0. Handle capture (remove from tables)
    if captured != EMPTY:
        new_bitboards[captured] = pop_bit(new_bitboards[captured], to)
        new_state['halfmove'] = 0 # Capture resets clock
        
    # 1. Move piece
    new_bitboards[piece] = pop_bit(new_bitboards[piece], frm)
    new_bitboards[piece] = set_bit(new_bitboards[piece], to)
    new_mailbox[frm] = EMPTY
    new_mailbox[to] = piece
    
    # 2. Handle Promotion
    if move['promote'] is not None:
        new_bitboards[piece] = pop_bit(new_bitboards[piece], to)
        new_bitboards[move['promote']] = set_bit(new_bitboards[move['promote']], to)
        new_mailbox[to] = move['promote']
    
    # 3. Handle En Passant Capture
    if (piece == P or piece == p) and to == state['en_passant']:
        # Captured pawn is "behind" the to_sq
        cap_sq = to - 8 if side == WHITE else to + 8
        captured_pawn = new_mailbox[cap_sq]
        new_bitboards[captured_pawn] = pop_bit(new_bitboards[captured_pawn], cap_sq)
        new_mailbox[cap_sq] = EMPTY
        
    # 4. Handle Castling (Move Rook)
    if 'castle' in move:
        if move['castle'] == 'K': # White Kingside
            # Move R from h1 to f1
            rook, r_from, r_to = R, H1, F1
        elif move['castle'] == 'Q':
            rook, r_from, r_to = R, A1, D1
        elif move['castle'] == 'k':
            rook, r_from, r_to = r, H8, F8
        elif move['castle'] == 'q':
            rook, r_from, r_to = r, A8, D8
            
        new_bitboards[rook] = pop_bit(new_bitboards[rook], r_from)
        new_bitboards[rook] = set_bit(new_bitboards[rook], r_to)
        new_mailbox[r_from] = EMPTY
        new_mailbox[r_to] = rook
    
    # 5. Update En Passant Target
    if (piece == P or piece == p) and abs(frm - to) == 16:
        new_state['en_passant'] = (frm + to) // 2
        
    # 6. Update Castling Rights
    # If K moves, lose rights
    if piece == K: new_state['castling_rights'] &= 0b1100
    if piece == k: new_state['castling_rights'] &= 0b0011
    
    # If R moves or is captured, lose rights
    # Simplify: If corner squares change, remove rights
    # WR rights (bits 0, 1)
    if frm == H1 or to == H1: new_state['castling_rights'] &= ~1
    if frm == A1 or to == A1: new_state['castling_rights'] &= ~2
    if frm == H8 or to == H8: new_state['castling_rights'] &= ~4
    if frm == A8 or to == A8: new_state['castling_rights'] &= ~8
    
    # 7. Update Occupancies
    update_occupancies(new_bitboards, new_occupancies)
    
    # 8. Switch Side
    new_state['side_to_move'] = BLACK if side == WHITE else WHITE
    if new_state['side_to_move'] == WHITE:
        new_state['fullmove'] += 1
        
    # 9. Check Game End (only if not test)
    # 9. Update History (Before recursion check)
    if not test_only and 'history' in state:
        new_state['history'] = list(state['history'])
        new_state['history'].append(list(new_mailbox))
        
    # 10. Check Game End (only if not test)
    if not test_only:
        # Optim: This is expensive, maybe do it lazily or separately
        if not generate_moves(new_state):
            if is_in_check(new_state, new_state['side_to_move']):
                new_state['game_status'] = 'checkmate'
            else:
                new_state['game_status'] = 'stalemate'

    return new_state

# ============================================================================
# API ADAPTERS (For backwards compatibility / ease of use)
# ============================================================================

def get_game_status_text(state):
    status = state['game_status']
    side = 'White' if state['side_to_move'] == WHITE else 'Black'
    if status == 'checkmate':
        winner = 'Black' if side == 'White' else 'White'
        return f"Checkmate! {winner} wins!"
    if status == 'stalemate':
        return "Stalemate!"
    if is_in_check(state, state['side_to_move']):
        return f"{side} is in Check!"
    return f"{side} to move"

def get_piece_symbol(piece_int):
    return PIECE_CHARS.get(piece_int, '')

def get_piece_image(piece_int):
    # Map int back to char for URL lookup (or just use new map)
    # Using existing URLs from previous implementation
    if piece_int == EMPTY: return None
    char = PIECE_CHARS[piece_int]
    return f'https://upload.wikimedia.org/wikipedia/commons/{"b/b1" if char=="B" else "4/42" if char=="K" else "1/15" if char=="Q" else "7/70" if char=="N" else "4/45" if char=="P" else "7/72" if char=="R" else "9/98" if char=="b" else "f/f0" if char=="k" else "4/47" if char=="q" else "e/ef" if char=="n" else "c/c7" if char=="p" else "f/ff"}.svg'.replace("b/b1", "b/b1/Chess_blt45").replace("4/42", "4/42/Chess_klt45").replace("1/15", "1/15/Chess_qlt45").replace("7/70", "7/70/Chess_nlt45").replace("4/45", "4/45/Chess_plt45").replace("7/72", "7/72/Chess_rlt45").replace("9/98", "9/98/Chess_bdt45").replace("f/f0", "f/f0/Chess_kdt45").replace("4/47", "4/47/Chess_qdt45").replace("e/ef", "e/ef/Chess_ndt45").replace("c/c7", "c/c7/Chess_pdt45").replace("f/ff", "f/ff/Chess_rdt45")
    # Quick hack to restore URLs. cleaner: use dictionary.

PIECE_IMAGES = {
    P: 'https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg',
    N: 'https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg',
    B: 'https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg',
    R: 'https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg',
    Q: 'https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg',
    K: 'https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg',
    p: 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg',
    n: 'https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg',
    b: 'https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg',
    r: 'https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg',
    q: 'https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg',
    k: 'https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg'
}

def get_piece_image(piece_int):
    return PIECE_IMAGES.get(piece_int)

def opponent_color(color):
    return BLACK if color == WHITE else WHITE

