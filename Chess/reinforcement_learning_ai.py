import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque



# Define the neural network architecture (e.g., CNN)
class ChessDQN(nn.Module):
    def __init__(self):
        super(ChessDQN, self).__init__()
        # Convolutional layers to process the board state
        self.conv1 = nn.Conv2d(12, 64, kernel_size=3, padding=1)  # 12 channels for pieces
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(128 * 8 * 8, 1024)  # Flatten and fully connected layer
        self.fc2 = nn.Linear(1024, 4096)  # Output layer for all possible moves (encoded)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = x.view(x.size(0), -1)  # Flatten for fully connected layer
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


# Replay buffer to store experiences
# Modify the replay buffer add method to ensure proper data format
class ReplayBuffer:
    def __init__(self, max_size=10000):
        self.buffer = deque(maxlen=max_size)

    def add(self, experience):
        # Add experiences to the replay buffer
        self.buffer.append(experience)

    def sample(self, batch_size):
        # Randomly sample a batch of experiences from the buffer
        return random.sample(self.buffer, batch_size)

    def size(self):
        return len(self.buffer)


# DQN agent
class DQNAgent:
    def __init__(self):
        self.q_network = ChessDQN()
        self.target_network = ChessDQN()
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        self.replay_buffer = ReplayBuffer()
        self.gamma = 0.99
        self.epsilon = 0.9
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

    def select_action(self, state, valid_moves):
        if len(valid_moves) == 0:
            # No valid moves, handle accordingly
            raise ValueError("No valid moves available")

        if random.random() < self.epsilon:
            # Random action (exploration)
            return random.choice(valid_moves)
        else:
            # Exploit the best known action (based on Q-values)
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float).unsqueeze(0)
                q_values = self.q_network(state_tensor)

                # Get the move indices for valid moves
                move_indices = [self.convert_move_to_index(move) for move in valid_moves]

                if len(move_indices) == 0:
                    # If there are no valid move indices, return a random move as a fallback
                    return random.choice(valid_moves)

                # Filter q_values for valid moves only
                q_values_filtered = q_values[:, move_indices]

                if q_values_filtered.numel() == 0:
                    # If q_values_filtered is empty, fallback to random move
                    return random.choice(valid_moves)

                # Select the best move (highest Q-value)
                best_move_idx = torch.argmax(q_values_filtered).item()
                return valid_moves[best_move_idx]

    def train(self, batch_size):
        if len(self.replay_buffer.buffer) < batch_size:
            return

        # Sample a batch from replay buffer
        batch = self.replay_buffer.sample(batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Ensure all states are numpy arrays (fixed-size tensors)
        states = np.array(states, dtype=np.float32)
        next_states = np.array(next_states, dtype=np.float32)

        # Convert actions (which are Move objects) to integers using convert_move_to_index
        actions = [self.convert_move_to_index(action) for action in actions]

        # Convert other elements to tensors
        actions = torch.tensor(actions, dtype=torch.long)
        rewards = torch.tensor(rewards, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)

        # Compute Q-values for current states
        q_values = self.q_network(torch.tensor(states, dtype=torch.float32))
        q_values = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.target_network(torch.tensor(next_states, dtype=torch.float32)).max(1)[0]
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # Compute loss and update the Q-network
        loss = nn.MSELoss()(q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        """
        Synchronize the target network weights with the Q-network weights.
        """
        self.target_network.load_state_dict(self.q_network.state_dict())

    def convert_move_to_index(self, move):
        """
        Convert a chess move to a unique index.
        This could be based on row/col positions or an encoded format.
        """
        # This is just an example: convert the move's start/end square to an index.
        start_square = move.start_row * 8 + move.start_col
        end_square = move.end_row * 8 + move.end_col
        return start_square * 64 + end_square  # Encode both start and end into a single index
