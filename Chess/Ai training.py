from ChessEngine import GameState

from reinforcement_learning_ai import DQNAgent, ReplayBuffer
import numpy as np
import torch

def reset_game():
    game_state = GameState()
    return game_state

def take_action(action, game_state):
    move = action
    game_state.makeMove(move)

    if game_state.checkmate:
        reward = 1 if game_state.white_to_move else -2
        done = True
    elif game_state.stalemate or game_state.threefold_repetition:
        reward = -1
        done = True
    else:
        reward = 0
        done = False

    next_state = game_state.getBoardTensor()
    return next_state, reward, done

def load_checkpoint(agent, filename):
    """
    Load model weights and other training states from a checkpoint and continue training.
    """
    checkpoint = torch.load(filename)
    agent.q_network.load_state_dict(checkpoint['model_state_dict'])  # Load model weights
    agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])  # Load optimizer state
    agent.replay_buffer = checkpoint['replay_buffer']  # Load replay buffer state
    agent.epsilon = checkpoint['epsilon']  # Load epsilon value
    starting_episode = checkpoint['episode']  # Load the last episode number
    print(f"Checkpoint loaded from {filename}, resuming from episode {starting_episode}")
    return starting_episode



# Initialize win/loss and reward tracking
win_count = 0
loss_count = 0
draw_count = 0
episode_rewards = []
N = 5

# Initialize the DQN agent
agent = DQNAgent()
batch_size = 64
num_episodes = 2000
update_target_every = 1000

# Load the checkpoint if it exists
starting_episode = load_checkpoint(agent, 'model_episode_900.pth')

# Training loop
for episode in range(starting_episode, num_episodes):
    game_state = reset_game()
    done = False
    state = game_state.getBoardTensor()
    total_episode_reward = 0

    while not done:
        valid_moves = game_state.getValidMoves()

        if len(valid_moves) == 0:
            break

        action = agent.select_action(state, valid_moves)
        next_state, reward, done = take_action(action, game_state)
        total_episode_reward += reward
        agent.replay_buffer.add((state, action, reward, next_state, done))
        agent.train(batch_size)
        state = next_state

    # Track wins/losses/draws
    if reward == 1:
        win_count += 1
    elif reward == -1:
        loss_count += 1
    else:
        draw_count += 1

    episode_rewards.append(total_episode_reward)

    # Every N episodes, update the target network
    if episode % update_target_every == 0:
        agent.update_target_network()

    # Every N episodes, calculate and display performance statistics
    if episode % N == 0 and episode > 0:
        average_reward = np.mean(episode_rewards[-N:])
        win_loss_ratio = win_count / max(1, loss_count)

        print(f"Episode {episode + 1}/{num_episodes}")
        print(f"Win/Loss Ratio: {win_loss_ratio:.2f}")
        print(f"Average Reward (Last {N} Episodes): {average_reward:.2f}")
        print(f"Total Wins: {win_count}, Total Losses: {loss_count}, Total Draws: {draw_count}")

        win_count, loss_count, draw_count = 0, 0, 0

    # **Save the model periodically, every 100 episodes:**
    if episode % 100 == 0:
        torch.save({
            'episode': episode,
            'model_state_dict': agent.q_network.state_dict(),
            'optimizer_state_dict': agent.optimizer.state_dict(),
            'replay_buffer': agent.replay_buffer,  # Save the replay buffer state if necessary
            'epsilon': agent.epsilon,  # Save epsilon to continue exploration correctly
        }, f'model_episode_{episode}.pth')
        print(f"Model and training state saved at episode {episode}")





