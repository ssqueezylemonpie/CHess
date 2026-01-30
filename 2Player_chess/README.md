# 2 player based Chess

A fully interactive Chess game built with Python (Flask) and a custom Bitboard-based Chess Engine. Play against a friend or challenge the AI!

## ✨ Features

*   **Game Modes**:
    *   **PvP**: Play against a friend (pass-and-play).
    *   **Vs Computer**: Challenge the built-in AI (Minimax with Alpha-Beta Pruning).
*   **Interactive UI**:
    *   Drag and Drop pieces.
    *   Click-to-move support.
    *   Visual move hints and last move highlighting.
*   **History Navigation**: Use **Left/Right Arrow Keys** to review past moves during the game.
*   **Advanced Engine**:
    *   Bitboard representation for efficiency.
    *   Move validation (Checks, Pins, En Passant, Castling).
    *   Pawn Promotion (via popup dialog).

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.x installed on your system.

### Steps

1.  **Clone or Download** this folder.

2.  **Install Flask**:
    Open your terminal or command prompt and run:
    ```bash
    pip install flask
    ```

3.  **Run the Game**:
    In the terminal, navigate to the game folder and run:
    ```bash
    python app.py
    ```

4.  **Play**:
    Open your web browser and go to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 🎮 How to Play

*   **Move**: Drag pieces or click source then destination.
*   **AI Mode**: Click "Vs Computer" in the sidebar to switch modes.
*   **Review**: Press `<-` (Left Arrow) to undo/view history. Press `->` (Right Arrow) to catch up to live gameplay.
*   **New Game**: Click the "New Game" button to reset the board.

## 📂 Project Structure

*   `app.py`: Main Flask application server.
*   `chess_engine.py`: Core logic, move generation, and bitboard implementation.
*   `chess_ai.py`: AI algorithms (Minimax, Evaluation).
*   `static/`: CSS styles and JavaScript game logic.
*   `templates/`: HTML files.

Enjoy!

