from typing import List

import torch
import torch.nn as nn

from .base_brain import RobotBrain


# class _MLP(nn.Module):
#     def __init__(self, in_dim: int, out_dim: int) -> None:
#         super().__init__()
#         self.net = nn.Sequential(nn.Linear(in_dim, 32), nn.ReLU(), nn.Linear(32, out_dim))

#     def forward(self, x):
#         return self.net(x)


class RLBrain(RobotBrain):
    """A brain controlled by a neural network (e.g., for reinforcement learning)."""
    
    def __init__(self, observation_dim: int = 7, action_dim: int = 5):
        """
        observation_dim: size of observation vector
        action_dim: number of possible discrete actions
        """
        super().__init__()
        # define a simple neural network (multilayer perceptron)
        hidden_dim = 32
        self.model = nn.Sequential(
            nn.Linear(observation_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        # TODO In a more complex scenario, we might use a CNN if observations are images.
        # here, observation is a simple vector, so no CNN needed in this minimal example.

        # if we were doing reinforcement learning training, we might also maintain optimizer, etc.
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        # a placeholder for memory or other RL components (like replay buffer) could be here if needed.
    
    def decide_action(self, observation):
        # convert observation to tensor
        obs_tensor = torch.tensor(observation, dtype=torch.float32)
        # forward pass through the neural network
        with torch.no_grad():
            q_values = self.model(obs_tensor)  # assuming a Q-value for each action (like DQN)
        # choose action with highest Q-value (greedy). we could also sample if it were probabilistic output.
        action_index = int(torch.argmax(q_values).item())
        return action_index

    def learn(self, obs, action, reward, next_obs):
        """One step of learning (e.g., Q-learning update or policy gradient). 
        This is a placeholder for integrating an RL algorithm."""
        # TODO: This could implement a Q-learning update or policy gradient update.
        # for simplicity, not implementing a full RL update here.
        pass

    def export_params(self):
        """export parameters (e.g., network weights) for saving."""
        # return the state dict of the model (convert to regular Python types for JSON if needed).
        state = self.model.state_dict()
        # state is a dict of weight tensors; we should convert them to lists for JSON, but that would be large.
        # for now, maybe compress or just indicate we would save this in a real scenario.
        return {k: v.tolist() for k, v in state.items()}
