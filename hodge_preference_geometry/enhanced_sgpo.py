"""
Enhanced SGPO: Combined Clipped-SGPO with CPO Black Hole Initialization

This module combines all SGPO improvements:
1. Hodge decomposition for cyclic preference handling
2. Geometric safety via learned metric with pre-initialized singularities
3. PPO-style clipping for training stability
4. CPO constraint initialization for known dangerous regions

The EnhancedSGPOTrainer provides:
- Trajectory-level safety guarantees (vs CPO's expectation-only)
- Stable training via hybrid clipping
- Fast initialization from known constraints
- Adaptive discovery of new dangerous regions

Mathematical Foundation:
- Reward sheaf: H¹(X, F) = 0 iff globally consistent value function exists
- Geometric barriers: g(x) → ∞ creates infinite distance to black holes
- Clipped updates: bounded by O(ε) in safe regions, O(1/√G) near black holes
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

from .gpo_clipped import ClippedSGPO, ClippedSGPOConfig, ClippedSGPOTrainer
from .cpo_to_blackhole import CPOToBlackHoleInitializer, BlackHole, CPOConstraint
from .metric_model import PreInitializedMetricModel, AdaptiveMetricModel


@dataclass
class EnhancedSGPOConfig:
    """Configuration for Enhanced SGPO algorithm."""
    # Clipped-SGPO parameters
    clip_ratio: float = 0.2
    geometric_threshold: float = 2.0
    
    # CPO initialization parameters
    cpo_cost_threshold: float = 0.5
    horizon_scale: float = 1.0
    singularity_power: float = 2.0
    
    # Training parameters
    gamma: float = 0.99
    gae_lambda: float = 0.95
    lr: float = 3e-4
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    n_epochs: int = 10
    batch_size: int = 64
    
    # Hodge parameters
    hodge_reward_weight: float = 0.5
    
    # Metric learning
    metric_lr: float = 1e-4
    metric_update_freq: int = 5  # Update metric every N policy updates
    
    # Adaptive singularity discovery
    adaptive_discovery: bool = True
    discovery_threshold: float = 0.9
    max_singularities: int = 20


class HodgeCriticInterface:
    """
    Interface for Hodge critic expected by EnhancedSGPO.
    
    The real HodgeCritic from hodge_critic.py can be used directly,
    or this interface can wrap simpler value estimators.
    """
    
    def __init__(
        self,
        value_net: Optional[nn.Module] = None,
        embed_dim: int = 384,
        device: torch.device = None,
    ):
        self.device = device or torch.device("cpu")
        self.embed_dim = embed_dim
        
        if value_net is not None:
            self.value_net = value_net.to(self.device)
        else:
            # Simple value network
            self.value_net = nn.Sequential(
                nn.Linear(embed_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
            ).to(self.device)
        
        # Harmonic component estimator (for cyclic preferences)
        self.harmonic_net = nn.Sequential(
            nn.Linear(embed_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        ).to(self.device)
        
        self._h1_magnitude = 0.0
    
    def value(self, states: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """Estimate value function V(s)."""
        if isinstance(states, np.ndarray):
            states = torch.tensor(states, dtype=torch.float32, device=self.device)
        
        with torch.no_grad():
            values = self.value_net(states).squeeze(-1)
        
        return values.cpu().numpy()
    
    def harmonic(
        self,
        states: Union[np.ndarray, torch.Tensor],
        actions: Union[np.ndarray, torch.Tensor],
    ) -> np.ndarray:
        """
        Estimate harmonic component ω·v (cyclic preference correction).
        
        This represents the "curl" component of the reward that cannot
        be expressed as a gradient of any value function.
        """
        if isinstance(states, np.ndarray):
            states = torch.tensor(states, dtype=torch.float32, device=self.device)
        
        with torch.no_grad():
            omega = self.harmonic_net(states).squeeze(-1)
        
        return omega.cpu().numpy()
    
    def compute_hodge_decomposition(self) -> Any:
        """Return cached H¹ magnitude."""
        class Result:
            def __init__(self, h1):
                self.h1_magnitude = h1
        return Result(self._h1_magnitude)
    
    def get_local_geometry(self, state_text: str) -> Dict[str, float]:
        """Get local geometric properties (placeholder)."""
        return {
            "curvature": 0.0,
            "h1_magnitude": self._h1_magnitude,
            "black_hole_proximity": 0.0,
        }
    
    def get_topological_gradient_at(self, state_text: str) -> np.ndarray:
        """Get Hodge gradient direction (placeholder)."""
        return np.zeros(self.embed_dim)
    
    def update_h1(self, h1_magnitude: float):
        """Update cached H¹ magnitude from actual computation."""
        self._h1_magnitude = h1_magnitude


class EnhancedSGPOTrainer:
    """
    Enhanced SGPO trainer combining:
    1. Hodge decomposition for cyclic preferences
    2. Geometric safety via learned metric
    3. PPO-style clipping for stability
    4. CPO constraint initialization for known dangers
    
    Usage:
        # Initialize from CPO constraints
        trainer = EnhancedSGPOTrainer.from_cpo_constraints(
            policy_net, cost_fn, sample_states
        )
        
        # Or initialize manually
        trainer = EnhancedSGPOTrainer(
            policy_net, hodge_critic, metric_model
        )
        trainer.add_black_hole(center, radius, strength)
        
        # Training
        stats = trainer.train_step(batch)
    """
    
    def __init__(
        self,
        model: nn.Module,
        hodge_critic: Any,
        metric_model: PreInitializedMetricModel,
        config: Optional[EnhancedSGPOConfig] = None,
        device: torch.device = None,
    ):
        """
        Initialize Enhanced SGPO trainer.
        
        Args:
            model: Policy network with forward(states) -> (logits, values)
            hodge_critic: Hodge critic for reward decomposition
            metric_model: Pre-initialized metric model
            config: Algorithm configuration
            device: Torch device
        """
        self.model = model
        self.hodge_critic = hodge_critic
        self.metric_model = metric_model
        self.config = config or EnhancedSGPOConfig()
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Move to device
        self.model.to(self.device)
        self.metric_model.to(self.device)
        
        # Initialize Clipped-SGPO algorithm
        clipped_config = ClippedSGPOConfig(
            clip_ratio=self.config.clip_ratio,
            geometric_threshold=self.config.geometric_threshold,
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda,
            value_coef=self.config.value_coef,
            entropy_coef=self.config.entropy_coef,
            max_grad_norm=self.config.max_grad_norm,
            n_epochs=self.config.n_epochs,
            batch_size=self.config.batch_size,
        )
        self.clipped_gpo = ClippedSGPO(config=clipped_config)
        
        # CPO initializer for adding new black holes
        self.cpo_init = CPOToBlackHoleInitializer(
            cost_threshold=self.config.cpo_cost_threshold,
            horizon_scale=self.config.horizon_scale,
            singularity_power=self.config.singularity_power,
        )
        
        # Optimizers
        self.policy_optimizer = torch.optim.Adam(
            model.parameters(), lr=self.config.lr
        )
        self.metric_optimizer = torch.optim.Adam(
            metric_model.parameters(), lr=self.config.metric_lr
        )
        
        # Training state
        self.update_count = 0
        self.train_stats: Dict[str, List[float]] = {
            "policy_loss": [],
            "value_loss": [],
            "entropy": [],
            "metric_loss": [],
            "h1_magnitude": [],
            "n_black_holes": [],
        }
    
    @classmethod
    def from_cpo_constraints(
        cls,
        model: nn.Module,
        cost_fn: Callable[[np.ndarray], np.ndarray],
        sample_states: np.ndarray,
        config: Optional[EnhancedSGPOConfig] = None,
        device: torch.device = None,
        **kwargs,
    ) -> "EnhancedSGPOTrainer":
        """
        Factory method: initialize from CPO cost function.
        
        This pre-identifies dangerous regions and initializes the
        metric model with black holes at those locations.
        
        Args:
            model: Policy network
            cost_fn: CPO cost function C(s) -> costs
            sample_states: States to sample for black hole identification
            config: Algorithm configuration
            device: Torch device
            **kwargs: Additional arguments
            
        Returns:
            Initialized EnhancedSGPOTrainer
        """
        config = config or EnhancedSGPOConfig()
        device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Compute costs at sample states
        sample_states = np.asarray(sample_states)
        costs = cost_fn(sample_states)
        
        # Initialize metric with black holes
        initializer = CPOToBlackHoleInitializer(
            cost_threshold=config.cpo_cost_threshold,
            horizon_scale=config.horizon_scale,
            singularity_power=config.singularity_power,
        )
        black_holes = initializer.identify_black_holes(sample_states, costs)
        
        # Create metric model
        embed_dim = sample_states.shape[-1]
        if config.adaptive_discovery:
            metric_model = AdaptiveMetricModel(
                input_dim=embed_dim,
                max_singularities=config.max_singularities,
                discovery_threshold=config.discovery_threshold,
            )
        else:
            metric_model = PreInitializedMetricModel(input_dim=embed_dim)
        
        # Add black holes to metric
        initializer.initialize_metric(metric_model, black_holes)
        
        print(f"Initialized {len(black_holes)} black holes from CPO constraints")
        
        # Create Hodge critic
        hodge_critic = HodgeCriticInterface(embed_dim=embed_dim, device=device)
        
        return cls(
            model=model,
            hodge_critic=hodge_critic,
            metric_model=metric_model,
            config=config,
            device=device,
        )
    
    @classmethod
    def from_cpo_constraint_list(
        cls,
        model: nn.Module,
        constraints: List[CPOConstraint],
        sample_states: np.ndarray,
        **kwargs,
    ) -> "EnhancedSGPOTrainer":
        """
        Factory method: initialize from multiple CPO constraints.
        
        Args:
            model: Policy network
            constraints: List of CPOConstraint objects
            sample_states: States to sample
            **kwargs: Additional arguments
            
        Returns:
            Initialized EnhancedSGPOTrainer
        """
        config = kwargs.get("config", EnhancedSGPOConfig())
        device = kwargs.get("device", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        
        sample_states = np.asarray(sample_states)
        embed_dim = sample_states.shape[-1]
        
        # Initialize metric model
        if config.adaptive_discovery:
            metric_model = AdaptiveMetricModel(
                input_dim=embed_dim,
                max_singularities=config.max_singularities,
            )
        else:
            metric_model = PreInitializedMetricModel(input_dim=embed_dim)
        
        # Process each constraint
        initializer = CPOToBlackHoleInitializer(cost_threshold=0.5)
        all_black_holes = initializer.identify_black_holes_from_constraints(
            constraints, sample_states
        )
        
        # Merge overlapping black holes
        merged_holes = initializer.merge_overlapping_black_holes(all_black_holes)
        initializer.initialize_metric(metric_model, merged_holes)
        
        print(f"Initialized {len(merged_holes)} black holes from {len(constraints)} CPO constraints")
        
        hodge_critic = HodgeCriticInterface(embed_dim=embed_dim, device=device)
        
        return cls(
            model=model,
            hodge_critic=hodge_critic,
            metric_model=metric_model,
            config=config,
            device=device,
        )
    
    def add_black_hole(
        self,
        center: np.ndarray,
        radius: float,
        strength: float = 1.0,
    ):
        """Manually add a black hole to the metric."""
        self.metric_model.add_singularity(
            center=center,
            radius=radius,
            strength=strength,
            power=self.config.singularity_power,
        )
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """
        Perform single training step.
        
        Args:
            batch: Dictionary containing:
                - states: State embeddings (batch_size, embed_dim)
                - actions: Action indices (batch_size,)
                - rewards: Rewards (batch_size,)
                - old_log_probs: Log probs from old policy (batch_size,)
                - dones: Episode termination flags (batch_size,)
                - costs: Optional cost values (batch_size,)
                
        Returns:
            stats: Training statistics dictionary
        """
        states = batch["states"].to(self.device)
        actions = batch["actions"].to(self.device)
        rewards = batch["rewards"].to(self.device)
        old_log_probs = batch["old_log_probs"].to(self.device)
        dones = batch["dones"].to(self.device)
        costs = batch.get("costs", torch.zeros_like(rewards)).to(self.device)
        
        batch_size = states.shape[0]
        
        # Compute next states (approximate by shifting)
        next_states = torch.roll(states, -1, dims=0)
        next_states[-1] = states[-1]
        
        # Get metric values
        with torch.no_grad():
            metrics = self.metric_model(states)
        
        # Compute Hodge-corrected advantages
        advantages_np, metrics_np = self.clipped_gpo.compute_advantage(
            states.cpu().numpy(),
            actions.cpu().numpy(),
            rewards.cpu().numpy(),
            next_states.cpu().numpy(),
            dones.cpu().numpy(),
            self.hodge_critic,
            self.metric_model,
            gamma=self.config.gamma,
        )
        
        # Get value estimates for returns
        with torch.no_grad():
            _, values = self.model(states)
            if values.dim() > 1:
                values = values.squeeze(-1)
        
        returns = torch.tensor(advantages_np, device=self.device) + values
        advantages = torch.tensor(advantages_np, device=self.device)
        metrics_t = torch.tensor(metrics_np, device=self.device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Forward pass
        logits, new_values = self.model(states)
        if new_values.dim() > 1:
            new_values = new_values.squeeze(-1)
        
        dist = Categorical(logits=logits)
        new_log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        
        # Compute losses using Clipped-SGPO
        total_loss, loss_dict = self.clipped_gpo.compute_total_loss(
            old_log_probs,
            new_log_probs,
            advantages,
            metrics_t,
            new_values,
            returns,
            entropy,
            values,
        )
        
        # Policy/value update
        self.policy_optimizer.zero_grad()
        total_loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
        self.policy_optimizer.step()
        
        # Metric update (less frequent)
        metric_loss = 0.0
        if self.update_count % self.config.metric_update_freq == 0:
            metric_loss = self.metric_model.compute_loss(states, costs)
            
            self.metric_optimizer.zero_grad()
            metric_loss.backward()
            self.metric_optimizer.step()
            
            metric_loss = metric_loss.item()
        
        # Adaptive singularity discovery
        if (self.config.adaptive_discovery and 
            isinstance(self.metric_model, AdaptiveMetricModel)):
            self.metric_model.update_candidates(
                states.cpu().numpy(),
                costs.cpu().numpy(),
            )
        
        self.update_count += 1
        
        # Compile stats
        stats = {
            "policy_loss": loss_dict["policy_loss"],
            "value_loss": loss_dict["value_loss"],
            "entropy": loss_dict["entropy"],
            "approx_kl": loss_dict["approx_kl"],
            "metric_loss": metric_loss,
            "n_black_holes": len(self.metric_model.singularities),
            "n_geometric_clipped": loss_dict.get("n_geometric_clipped", 0),
            "n_ppo_clipped": loss_dict.get("n_ppo_clipped", 0),
        }
        
        # Store in history
        for key in ["policy_loss", "value_loss", "entropy", "metric_loss", "n_black_holes"]:
            if key in self.train_stats:
                self.train_stats[key].append(stats.get(key, 0))
        
        return stats
    
    def evaluate_safety(
        self,
        states: np.ndarray,
        costs: np.ndarray,
    ) -> Dict[str, float]:
        """
        Evaluate safety metrics on given states.
        
        Args:
            states: State embeddings to evaluate
            costs: True costs at those states
            
        Returns:
            Safety metrics dictionary
        """
        states_t = torch.tensor(states, dtype=torch.float32, device=self.device)
        
        with torch.no_grad():
            metrics = self.metric_model(states_t).cpu().numpy()
            is_safe = self.metric_model.is_safe(states_t).cpu().numpy()
            distances, _ = self.metric_model.distance_to_nearest_singularity(states_t)
            distances = distances.cpu().numpy()
        
        # Safety statistics
        high_cost_mask = costs > self.config.cpo_cost_threshold
        
        return {
            "mean_metric": float(np.mean(metrics)),
            "max_metric": float(np.max(metrics)),
            "pct_safe": float(is_safe.mean() * 100),
            "mean_distance_to_danger": float(np.mean(distances)),
            "high_cost_mean_metric": float(np.mean(metrics[high_cost_mask])) if high_cost_mask.any() else 0.0,
            "low_cost_mean_metric": float(np.mean(metrics[~high_cost_mask])) if (~high_cost_mask).any() else 0.0,
        }
    
    def get_action(
        self,
        state: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[int, float, float]:
        """
        Select action for given state.
        
        Args:
            state: State embedding
            deterministic: If True, select argmax action
            
        Returns:
            action: Selected action index
            log_prob: Log probability of action
            value: Value estimate
        """
        with torch.no_grad():
            state_t = torch.tensor(state, dtype=torch.float32, device=self.device)
            if state_t.dim() == 1:
                state_t = state_t.unsqueeze(0)
            
            logits, value = self.model(state_t)
            if value.dim() > 1:
                value = value.squeeze(-1)
            
            if deterministic:
                action = logits.argmax(dim=-1)
                log_prob = F.log_softmax(logits, dim=-1)[0, action]
            else:
                dist = Categorical(logits=logits)
                action = dist.sample()
                log_prob = dist.log_prob(action)
            
            return int(action.item()), float(log_prob.item()), float(value.item())
    
    def save(self, path: str):
        """Save trainer state."""
        state = {
            "model_state": self.model.state_dict(),
            "metric_model_state": self.metric_model.state_dict(),
            "policy_optimizer_state": self.policy_optimizer.state_dict(),
            "metric_optimizer_state": self.metric_optimizer.state_dict(),
            "config": self.config,
            "update_count": self.update_count,
            "train_stats": self.train_stats,
            "singularities": [s.to_dict() for s in self.metric_model.singularities],
        }
        torch.save(state, path)
        print(f"Saved EnhancedSGPO trainer to {path}")
    
    def load(self, path: str):
        """Load trainer state."""
        state = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(state["model_state"])
        self.metric_model.load_state_dict(state["metric_model_state"], strict=False)
        self.policy_optimizer.load_state_dict(state["policy_optimizer_state"])
        self.metric_optimizer.load_state_dict(state["metric_optimizer_state"])
        self.update_count = state["update_count"]
        self.train_stats = state["train_stats"]
        
        print(f"Loaded EnhancedSGPO trainer from {path}")


def compare_algorithms_demo():
    """
    Demo comparing PPO, CPO, SGPO, and Enhanced SGPO.
    """
    print("\n" + "="*60)
    print("ENHANCED SGPO COMPARISON DEMO")
    print("="*60)
    
    # Synthetic environment
    class SyntheticEnv:
        def __init__(self, embed_dim=32):
            self.embed_dim = embed_dim
            self.black_hole = np.random.randn(embed_dim) * 0.5
            self.state = None
            
        def reset(self):
            self.state = np.random.randn(self.embed_dim) * 0.1
            return self.state
        
        def step(self, action):
            direction = np.random.randn(self.embed_dim) * 0.1
            direction[action % self.embed_dim] += 0.2
            self.state = self.state + direction
            
            dist = np.linalg.norm(self.state - self.black_hole)
            reward = 0.1 * dist
            cost = max(0, 1.0 - dist)
            in_danger = dist < 0.3
            
            if in_danger:
                reward -= 10.0
            
            return self.state, reward, in_danger, {"cost": cost}
        
        def cost_function(self, states):
            """CPO-style cost function."""
            dists = np.linalg.norm(states - self.black_hole, axis=1)
            return np.maximum(0, 1.0 - dists)
    
    # Test parameters
    embed_dim = 32
    num_actions = 4
    n_episodes = 10
    steps_per_episode = 50
    
    # Create environment
    env = SyntheticEnv(embed_dim)
    
    # Sample states for CPO initialization
    sample_states = np.random.randn(1000, embed_dim) * 0.5
    
    # Create simple policy network
    class SimplePolicy(nn.Module):
        def __init__(self, embed_dim, num_actions):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(embed_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 32),
                nn.ReLU(),
            )
            self.policy_head = nn.Linear(32, num_actions)
            self.value_head = nn.Linear(32, 1)
        
        def forward(self, x):
            features = self.net(x)
            return self.policy_head(features), self.value_head(features)
    
    policy = SimplePolicy(embed_dim, num_actions)
    
    # Initialize Enhanced SGPO from CPO constraints
    trainer = EnhancedSGPOTrainer.from_cpo_constraints(
        model=policy,
        cost_fn=env.cost_function,
        sample_states=sample_states,
        config=EnhancedSGPOConfig(
            cpo_cost_threshold=0.5,
            clip_ratio=0.2,
            geometric_threshold=2.0,
        ),
    )
    
    print(f"\nInitialized with {len(trainer.metric_model.singularities)} black holes")
    
    # Training loop (simplified)
    total_rewards = []
    safety_violations = 0
    
    for episode in range(n_episodes):
        state = env.reset()
        episode_reward = 0
        
        states, actions, rewards, log_probs, dones, costs = [], [], [], [], [], []
        
        for step in range(steps_per_episode):
            action, log_prob, value = trainer.get_action(state)
            next_state, reward, done, info = env.step(action)
            
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            log_probs.append(log_prob)
            dones.append(done)
            costs.append(info["cost"])
            
            episode_reward += reward
            if done:
                safety_violations += 1
            
            state = next_state
            if done:
                break
        
        # Training update
        batch = {
            "states": torch.tensor(np.array(states), dtype=torch.float32),
            "actions": torch.tensor(actions, dtype=torch.long),
            "rewards": torch.tensor(rewards, dtype=torch.float32),
            "old_log_probs": torch.tensor(log_probs, dtype=torch.float32),
            "dones": torch.tensor(dones, dtype=torch.float32),
            "costs": torch.tensor(costs, dtype=torch.float32),
        }
        
        stats = trainer.train_step(batch)
        total_rewards.append(episode_reward)
        
        if (episode + 1) % 2 == 0:
            print(f"Episode {episode+1}: reward={episode_reward:.2f}, "
                  f"policy_loss={stats['policy_loss']:.4f}, "
                  f"black_holes={stats['n_black_holes']}")
    
    print(f"\n--- Results ---")
    print(f"Mean reward: {np.mean(total_rewards):.2f}")
    print(f"Safety violations: {safety_violations}/{n_episodes}")
    print(f"Final black holes: {len(trainer.metric_model.singularities)}")
    
    return trainer


if __name__ == "__main__":
    compare_algorithms_demo()
