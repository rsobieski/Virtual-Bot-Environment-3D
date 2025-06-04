from typing import List, Dict, Any
import numpy as np
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
    """A brain controlled by a neural network for reinforcement learning.
    
    The neural network takes observations about the environment and outputs
    Q-values for each possible action. The action with the highest Q-value
    is chosen.
    """
    
    def __init__(self, observation_dim: int = 9, action_dim: int = 7):
        """Initialize the RL brain.
        
        Args:
            observation_dim: Size of observation vector (default: 9 for position to nearest resource (3) +
                                                           position to nearest robot (3) +
                                                           energy level (1) +
                                                           connection count (1) +
                                                           state (1))
            action_dim: Number of possible discrete actions (default: 7 for no-op + 6 movement directions)
        """
        super().__init__()
        self.observation_dim = observation_dim
        self.action_dim = action_dim
        
        # Define a simple neural network (multilayer perceptron)
        hidden_dim = 32
        self.model = nn.Sequential(
            nn.Linear(observation_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        # Initialize weights with small values
        for layer in self.model:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)
        
        # Optimizer for learning
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        
        # Placeholder for experience replay buffer
        self.memory: List[Dict[str, Any]] = []
        self.max_memory_size = 10000
    
    def decide_action(self, observation: List[float]) -> int:
        """Decide which action to take based on the current observation.
        
        Args:
            observation: List of observations about the environment.
            
        Returns:
            Integer representing the chosen action.
        """
        # Ensure observation has correct dimension
        if len(observation) != self.observation_dim:
            raise ValueError(f"Expected observation dimension {self.observation_dim}, got {len(observation)}")
            
        # Convert observation to tensor
        obs_tensor = torch.tensor(observation, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
        
        # Forward pass through the neural network
        with torch.no_grad():
            q_values = self.model(obs_tensor)
            
        # Choose action with highest Q-value (greedy)
        action_index = int(torch.argmax(q_values).item())
        return action_index

    def learn(self, obs: List[float], action: int, reward: float, next_obs: List[float]) -> None:
        """Update the neural network using experience replay.
        
        Args:
            obs: Current observation
            action: Action taken
            reward: Reward received
            next_obs: Next observation
        """
        # Store experience in memory
        self.memory.append({
            'obs': obs,
            'action': action,
            'reward': reward,
            'next_obs': next_obs
        })
        
        # Limit memory size
        if len(self.memory) > self.max_memory_size:
            self.memory.pop(0)
            
        # If we have enough samples, perform a learning step
        if len(self.memory) >= 32:  # Batch size
            self._update_network()
    
    def _update_network(self) -> None:
        """Update the neural network using a batch of experiences."""
        # Sample random batch from memory
        batch_size = min(32, len(self.memory))
        indices = np.random.choice(len(self.memory), batch_size, replace=False)
        batch = [self.memory[i] for i in indices]
        
        # Prepare batch data
        obs_batch = torch.tensor([exp['obs'] for exp in batch], dtype=torch.float32)
        action_batch = torch.tensor([exp['action'] for exp in batch], dtype=torch.long)
        reward_batch = torch.tensor([exp['reward'] for exp in batch], dtype=torch.float32)
        next_obs_batch = torch.tensor([exp['next_obs'] for exp in batch], dtype=torch.float32)
        
        # Compute current Q-values
        current_q_values = self.model(obs_batch)
        current_q_values = current_q_values.gather(1, action_batch.unsqueeze(1))
        
        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.model(next_obs_batch)
            max_next_q_values = next_q_values.max(1)[0]
            target_q_values = reward_batch + 0.99 * max_next_q_values  # 0.99 is the discount factor
        
        # Compute loss and update network
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def export_params(self) -> Dict[str, List[float]]:
        """Export network parameters for saving.
        
        Returns:
            Dictionary containing the network parameters.
        """
        state = self.model.state_dict()
        return {
            'type': 'RLBrain',
            'observation_dim': self.observation_dim,
            'action_dim': self.action_dim,
            'weights': {k: v.tolist() for k, v in state.items()}
        }
    
    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> 'RLBrain':
        """Create a brain from saved parameters.
        
        Args:
            params: Dictionary containing the network parameters.
            
        Returns:
            A new RLBrain instance with the saved parameters.
        """
        brain = cls(
            observation_dim=params['observation_dim'],
            action_dim=params['action_dim']
        )
        
        # Convert weights back to tensors
        state_dict = {
            k: torch.tensor(v) for k, v in params['weights'].items()
        }
        brain.model.load_state_dict(state_dict)
        
        return brain
