document.addEventListener('DOMContentLoaded', () => {
    // ---- State ----
    let gameHistory = []; // Array of mailbox arrays
    let currentViewIndex = -1; // -1 means "live / latest"
    let isReviewing = false;
    let pendingPromotion = null; // {from, to}

    // ---- Elements ----
    const boardEl = document.getElementById('board');
    const statusEl = document.querySelector('.status');
    const modal = document.getElementById('promotion-modal');
    const historyOverlay = document.getElementById('history-overlay');
    const arrowLayer = document.getElementById('arrow-layer');

    // ---- Initialization ----
    // On load, we might want to fetch initial state to populate history?
    // For now, assume history starts empty or we fetch it?
    // We should probably fetch state on load to be safe.
    fetch('/click/999') // Dummy fetch or dedicated state fetch?
    // Let's create a dedicated init fetch or just rely on the template for first render.
    // BUT we need the history data. The template doesn't provide history easily to JS.
    // We should hit an endpoint.
    // We should hit an endpoint.
    fetchState();

    // Attach listeners to initial HTML pieces
    attachPieceListeners();

    // ---- Event Listeners ----
    document.getElementById('btn-new-game').addEventListener('click', () => postAction('/reset'));
    document.getElementById('btn-mode-pvp').addEventListener('click', () => postAction('/set_mode/pvp'));
    document.getElementById('btn-mode-ai').addEventListener('click', () => postAction('/set_mode/ai'));

    // Promotion Buttons
    document.querySelectorAll('.promo-opt').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const piece = e.target.getAttribute('data-piece');
            handlePromotion(piece);
        });
    });

    // Keyboard (History)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            stepHistory(-1);
        } else if (e.key === 'ArrowRight') {
            stepHistory(1);
        }
    });

    // Board Interactions
    // We delegate to board for perf? Or keeping existing square listeners?
    // Existing logic attached listeners to squares. We need to re-attach if we rebuild DOM?
    // Or just use delegation. Delegation is better for re-rendering.
    // However, our updateBoard creates new elements for pieces but keeps squares?
    // In `updateBoard` we clear pieces. Squares remain.
    // So listeners on squares are fine.

    setupBoardListeners();

    // ---- Logic ----

    function fetchState() {
        fetch('/state')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    handleResponse(data);
                }
            })
            .catch(console.error);
    }

    function attachPieceListeners() {
        document.querySelectorAll('.piece-layer').forEach(p => {
            p.setAttribute('draggable', 'true');
            p.removeEventListener('dragstart', dragStart);
            p.addEventListener('dragstart', dragStart);
        });
    }

    function postAction(url) {
        fetch(url, { method: 'POST' })
            .then(res => res.json())
            .then(handleResponse)
            .catch(console.error);
    }

    function handleResponse(data) {
        if (!data.success) return;

        // Handle Game Mode active state
        if (data.status_text) {
            statusEl.textContent = data.status_text;
            statusEl.classList.toggle('check', data.check);
            statusEl.classList.toggle('game-over', data.game_over);
        }

        // Update History
        if (data.board_data && data.board_data.history) {
            gameHistory = data.board_data.history;
            currentViewIndex = gameHistory.length - 1;
            isReviewing = false;
            updateHistoryView();
        }

        // Update Board (Live)
        if (data.board_data && data.board_data.squares) {
            updateBoardVisuals(data.board_data.squares);
        } else if (data.board) { // Handling various return formats I made
            updateBoardVisuals(data.board.squares || data.board);
        }

        // Promotion?
        if (data.promotion) {
            pendingPromotion = { from: data.from, to: data.to };
            modal.classList.remove('hidden');
        } else {
            modal.classList.add('hidden');
        }

        // AI Trigger
        if (data.ai_trigger || data.ai_turn) {
            setTimeout(makeAIMove, 500);
        }

        // Active Buttons
        if (data.game_mode) {
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            if (data.game_mode === 'pvp') {
                document.getElementById('btn-mode-pvp').classList.add('active');
            } else if (data.game_mode === 'ai') {
                document.getElementById('btn-mode-ai').classList.add('active');
            }
        }
    }

    function makeAIMove() {
        statusEl.textContent = "Computer is thinking...";
        fetch('/ai_move', { method: 'POST' })
            .then(res => res.json())
            .then(handleResponse);
    }

    function handlePromotion(pieceChar) {
        fetch(`/promote/${pieceChar}`, { method: 'POST' })
            .then(res => res.json())
            .then(handleResponse);
    }

    // ---- History Navigation ----

    function stepHistory(direction) {
        if (gameHistory.length === 0) return;

        let newIndex = currentViewIndex + direction;

        // Clamp
        if (newIndex < 0) newIndex = 0;
        if (newIndex >= gameHistory.length) newIndex = gameHistory.length - 1;

        if (newIndex !== currentViewIndex) {
            currentViewIndex = newIndex;
            updateHistoryView();
        }
    }

    function updateHistoryView() {
        if (currentViewIndex === -1 || gameHistory.length === 0) return;

        const isLive = (currentViewIndex === gameHistory.length - 1);
        isReviewing = !isLive;

        if (isReviewing) {
            historyOverlay.classList.remove('hidden');
            document.body.classList.add('reviewing');
        } else {
            historyOverlay.classList.add('hidden');
            document.body.classList.remove('reviewing');
        }

        const mailbox = gameHistory[currentViewIndex];
        renderMailbox(mailbox);
    }

    function renderMailbox(mailbox) {
        // Mailbox is array of ints.
        // We need mapping logic similar to backend `build_board_json` or simple client-side map.
        // Client-side map:
        // PIECE_IMAGES map?

        // Helper to convert int to image URL.
        // We can embed this map or infer it.
        // Since backend was sending image URLs, we might not have them if we only have int history.
        // SOLUTION: We need the piece-to-image map in JS.

        document.querySelectorAll('.square').forEach(sq => {
            const idx = parseInt(sq.getAttribute('data-index'));
            const piece = mailbox[idx];

            // Clear
            const existing = sq.querySelector('.piece-layer');
            if (existing) existing.remove();
            sq.className = sq.className.replace(/\bpiece-\w+\b/g, ''); // start fresh

            if (piece !== -1) { // EMPTY = -1
                const pDiv = document.createElement('div');
                pDiv.className = 'piece-layer';
                // Get Image
                const img = getPieceImage(piece);
                if (img) pDiv.style.backgroundImage = `url('${img}')`;

                // Draggable only if live
                if (!isReviewing) {
                    pDiv.setAttribute('draggable', 'true');
                    pDiv.addEventListener('dragstart', dragStart);
                }

                sq.appendChild(pDiv);
            }
        });
    }

    // Mapping piece ints (0..11) to URLs
    // Copied from backend logic basically
    function getPieceImage(p) {
        const map = {
            0: 'https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg', // P
            1: 'https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg', // N
            2: 'https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg', // B
            3: 'https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg', // R
            4: 'https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg', // Q
            5: 'https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg', // K
            6: 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg', // p
            7: 'https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg', // n
            8: 'https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg', // b
            9: 'https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg', // r
            10: 'https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg', // q
            11: 'https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg'  // k
        };
        return map[p];
    }

    function updateBoardVisuals(squaresDict) {
        // If we get full dict from backend (build_board_json), use that (easier for compatibility)
        // But history uses renderMailbox.
        // Let's standardise: always use renderMailbox if we keep history updated?
        // Yes. `gameHistory` has the latest state at end.
        // So just call `updateHistoryView()`.

        // Wait, does 'squaresDict' contain history? No.
        // But handleResponse updates gameHistory.
        // So we can just call updateHistoryView().
        updateHistoryView();
    }

    // ---- Drag & Drop ----

    let dragSource = null;

    function setupBoardListeners() {
        const squares = document.querySelectorAll('.square');
        squares.forEach(sq => {
            sq.addEventListener('dragover', (e) => e.preventDefault());
            sq.addEventListener('drop', handleDrop);
            sq.addEventListener('mousedown', handleMouseDown);
            sq.addEventListener('mouseup', handleMouseUp);
        });
    }

    function dragStart(e) {
        if (isReviewing) {
            e.preventDefault();
            return;
        }
        const sq = e.target.parentElement;
        dragSource = sq.getAttribute('data-index');
        e.dataTransfer.setData('text/plain', dragSource);
    }

    function handleDrop(e) {
        if (isReviewing) return;
        e.preventDefault();
        const sq = e.target.closest('.square');
        if (!sq) return;

        const to = sq.getAttribute('data-index');
        if (dragSource && dragSource !== to) {
            // Move
            fetch(`/move/${dragSource}/${to}`, { method: 'POST' })
                .then(res => res.json())
                .then(handleResponse);
        }
        dragSource = null;
    }

    // ---- Click Logic ----
    // Simplified click-move (source -> dest)
    let selectedSquare = null;

    function handleMouseDown(e) {
        if (isReviewing) return;
        // Right click logic for arrows?
        if (e.button === 2) {
            // Start arrow
        }
    }

    function handleMouseUp(e) {
        if (isReviewing) return;
        if (e.button !== 0) return; // Only left click for moves

        const sq = e.currentTarget;
        const index = sq.getAttribute('data-index');

        // Determine if selecting or moving
        // Need to know whose turn it is or if piece is friendly?
        // We can just try to move if selected is set?

        // Logic:
        // 1. If nothing selected, select piece (if generic logic or we check backend?)
        // 2. If selected, and clicked new square, try move.
        // 3. If clicked same, deselect.

        if (selectedSquare === null) {
            selectedSquare = index;
            highlightSquare(index);
        } else {
            if (selectedSquare === index) {
                selectedSquare = null;
                clearHighlights();
            } else {
                // Try move
                fetch(`/move/${selectedSquare}/${index}`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            selectedSquare = null;
                            clearHighlights();
                            handleResponse(data);
                        } else {
                            // If failed, maybe it was a selection change?
                            // Simple retry: Select new square
                            selectedSquare = index;
                            clearHighlights();
                            highlightSquare(index);
                        }
                    });
            }
        }
    }

    function highlightSquare(idx) {
        const sq = document.querySelector(`[data-index='${idx}']`);
        if (sq) sq.classList.add('selected');
    }

    function clearHighlights() {
        document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
    }

});
