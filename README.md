# Chess Engine AI

A sophisticated chess engine with AI capabilities, built using Python and Pygame. This project implements a complete chess game with both human and AI players, featuring advanced chess logic, move validation, and reinforcement learning-based AI.

## Features

- Complete chess game implementation with all standard rules
- Beautiful graphical interface using Pygame
- Support for both human vs human and human vs AI gameplay
- Advanced AI opponent using reinforcement learning
- Move validation and legal move generation
- Move history and game state tracking
- Support for special moves (castling, en passant, pawn promotion)
- Threefold repetition detection
- Checkmate and stalemate detection
- Move animation and visual feedback
- Undo move functionality

## Requirements

- Python 3.x
- Pygame
- PyTorch (for AI functionality)
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd chess-engine-ai
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main game:
```bash
python Chess/ChessMain.py
```

### Game Controls

- **Mouse**: Click to select and move pieces
- **Left Arrow**: Undo the last move
- **R**: Reset the game
- **Close Window**: Exit the game

### Game Modes

The game supports two modes:
1. Human vs Human
2. Human vs AI

The AI opponent uses a reinforcement learning model that has been trained on thousands of games to develop strategic play.

## Project Structure

- `ChessMain.py`: Main game driver and UI implementation
- `ChessEngine.py`: Core chess logic and game state management
- `ChessAI.py`: AI implementation and move generation
- `Ai training.py`: Reinforcement learning model training
- `RookMagicBitboard.py`: Optimized move generation for rooks
- `images/`: Directory containing chess piece images
- `model_episode_*.pth`: Trained AI model checkpoints

## AI Implementation

The chess AI uses a combination of:
- Reinforcement learning
- Deep neural networks
- Position evaluation
- Move prediction
- Strategic decision making

The AI model is trained using self-play and can be further trained using the provided training script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
