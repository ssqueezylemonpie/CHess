"""
Flask Chess Application
2-Player pass-and-play chess game with no JavaScript (mostly).
Uses session to maintain game state.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import chess_engine as ce
import chess_ai
import os
import time

app = Flask(__name__)
# Use fixed key for development to prevent session invalidation on reload
app.secret_key = 'dev_key_for_chess_app_123'

def get_game_state():
    if 'game_state' not in session:
        return ce.create_initial_state()
    
    state = session['game_state']
    # Migration: Add history if missing (for pre-update moves)
    if 'history' not in state:
        state['history'] = [list(state['mailbox'])]
        session['game_state'] = state
        
    return state

def save_game_state(state):
    """Save game state to session."""
    session['game_state'] = state

@app.route('/')
def index():
    return redirect(url_for('game'))

@app.route('/game')
def game():
    # ... existing game route renders template ...
    # We keep this for the HTML shell.
    # But we can also init session here if needed.
    state = get_game_state()
    mode = session.get('game_mode', 'pvp')
    
    # Prepare board data for frontend (Grid Structure)
    # We need to render the 64 squares so JS has targets.
    flip = (state['side_to_move'] == ce.BLACK and mode == 'pvp') 
    
    board_display = []
    for r in range(8):
        row_display = []
        for c in range(8):
            if flip:
                internal_r = r
                internal_c = 7 - c
            else:
                internal_r = 7 - r
                internal_c = c
                
            sq_index = internal_r * 8 + internal_c
            is_light = (internal_r + internal_c) % 2 == 1 
            
            # We can leave pieces empty and let JS fetch? 
            # Or render them for "immediate paint" (better UX)
            piece_int = state['mailbox'][sq_index]
            piece_img = ce.get_piece_image(piece_int) if piece_int != ce.EMPTY else None
            
            row_display.append({
                'index': sq_index,
                'is_light': is_light,
                'piece_image': piece_img
            })
        board_display.append(row_display)
    
    return render_template('game.html',
                           board=board_display,
                           status_text="Loading...",
                           game_mode=mode)

@app.route('/state')
def get_state_json():
    state = get_game_state()
    return jsonify({
        'success': True,
        'board_data': build_board_json(state),
        'status_text': ce.get_game_status_text(state),
        'check': ce.is_in_check(state, state['side_to_move']),
        'game_over': state['game_status'] != 'ongoing',
        'game_mode': session.get('game_mode', 'pvp')
    })

# ... (click_square route if keeping it, but we use JS fetch mostly now) ...

@app.route('/click/<int:sq_index>', methods=['POST'])
def click_square(sq_index):
    # Fallback for non-JS or if used
    state = get_game_state()
    # ... logic same as before ...
    # but strictly we use fetch for moves now so ensuring this works is secondary but good.
    return redirect(url_for('game')) 

@app.route('/move/<int:frm>/<int:to>', methods=['POST'])
def move_piece(frm, to):
    state = get_game_state()
    if state['game_status'] != 'ongoing':
         return jsonify({'success': False})
         
    moves = ce.generate_moves(state)
    
    # Check promotion
    promo_moves = [m for m in moves if m['from'] == frm and m['to'] == to and m['promote'] is not None]
    if promo_moves:
        session['pending_promotion'] = {'from': frm, 'to': to}
        save_game_state(state)
        return jsonify({'success': True, 'promotion': True, 'from': frm, 'to': to})

    valid_move = None
    for m in moves:
        if m['from'] == frm and m['to'] == to:
            valid_move = m
            break
            
    if valid_move:
        state = ce.make_move(state, valid_move)
        save_game_state(state)
        
        # Check if AI should move
        mode = session.get('game_mode', 'pvp')
        ai_turn = False
        
        # Assume AI plays Black
        if mode == 'ai' and state['side_to_move'] == ce.BLACK and state['game_status'] == 'ongoing':
            ai_turn = True
            
        return jsonify({
            'success': True,
            'board_data': build_board_json(state), # Wrapper
            'status_text': ce.get_game_status_text(state),
            'check': ce.is_in_check(state, state['side_to_move']),
            'game_over': state['game_status'] != 'ongoing',
            'ai_turn': ai_turn
        })
        
    return jsonify({'success': False})

@app.route('/ai_move', methods=['POST'])
def ai_move():
    """Trigger AI to make a move."""
    state = get_game_state()
    if state['game_status'] != 'ongoing':
        return jsonify({'success': False})
        
    start_time = time.time()
    move = chess_ai.get_best_move(state, depth=3)
    duration = time.time() - start_time
    print(f"AI thought for {duration:.2f}s")
    
    if move:
        state = ce.make_move(state, move)
        save_game_state(state)
        
        return jsonify({
            'success': True,
            'board_data': build_board_json(state),
            'status_text': ce.get_game_status_text(state),
            'check': ce.is_in_check(state, state['side_to_move']),
            'game_over': state['game_status'] != 'ongoing',
            'from': move['from'],
            'to': move['to']
        })
        
    return jsonify({'success': False})

@app.route('/promote/<piece_char>', methods=['POST'])
def promote(piece_char):
    if 'pending_promotion' not in session: return redirect(url_for('game'))
    pending = session['pending_promotion']
    state = get_game_state()
    
    mapping = {'Q': ce.Q, 'R': ce.R, 'B': ce.B, 'N': ce.N}
    piece_type = mapping.get(piece_char.upper())

    if piece_type is None:
        return redirect(url_for('game'))

    side = state['side_to_move']
    real_promo = piece_type if side == ce.WHITE else piece_type + 6
    
    move = {
        'from': pending['from'],
        'to': pending['to'],
        'promote': real_promo
    }
    
    state = ce.make_move(state, move)
    session['game_state'] = state
    del session['pending_promotion']
    session['move_made'] = True
    
    # AI check after promotion
    mode = session.get('game_mode', 'pvp')
    if mode == 'ai' and state['side_to_move'] == ce.BLACK:
        # We can't easily trigger JS from redirect.
        # But render_template can pass a flag
        session['ai_trigger'] = True
    
    return jsonify({
        'success': True,
        'board': build_board_json(state),
        'status_text': ce.get_game_status_text(state),
        'check': ce.is_in_check(state, state['side_to_move']),
        'game_over': state['game_status'] != 'ongoing',
        'ai_trigger': mode == 'ai' and state['side_to_move'] == ce.BLACK
    })

@app.route('/set_mode/<mode>', methods=['POST'])
def set_mode(mode):
    if mode in ['pvp', 'ai']:
        session.clear()
        session['game_mode'] = mode
        # Create new state immediately
        state = get_game_state()
        save_game_state(state)
        
    return jsonify({
        'success': True,
        'board': build_board_json(get_game_state()), # Now returns full object
        'status_text': ce.get_game_status_text(get_game_state()),
        'check': False,
        'game_over': False,
        'game_mode': mode
    })

@app.route('/reset', methods=['POST'])
def reset():
    mode = session.get('game_mode', 'pvp')
    session.clear()
    session['game_mode'] = mode
    
    state = get_game_state() # Create new
    save_game_state(state)
    
    return jsonify({
        'success': True,
        'board': build_board_json(state),
        'status_text': ce.get_game_status_text(state),
        'check': False,
        'game_over': False,
        'game_mode': mode
    })

def build_board_json(state):
    board_json = {}
    for i, piece in enumerate(state['mailbox']):
        if piece != ce.EMPTY:
            board_json[str(i)] = {
                'piece': ce.get_piece_symbol(piece),
                'image': ce.get_piece_image(piece),
                'color': ce.get_piece_color(piece)
            }
    return {
        'squares': board_json,
        'turn': 'white' if state['side_to_move'] == ce.WHITE else 'black',
        'history': state.get('history', [state['mailbox']]) # Send full history of mailboxes
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
