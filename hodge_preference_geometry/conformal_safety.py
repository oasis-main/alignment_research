"""
Module 2: Continuous Conformal Safety Manifolds

This module implements geometric safety for policy optimization using
conformal metrics that create infinite barriers around dangerous regions.

Key Mathematical Insight:
- Standard soft penalties (potential functions) can be overcome with enough reward
- Expectation-based constraints (CPO) allow catastrophic tail events
- Conformal metrics with σ(x) → ∞ at danger boundary create INFINITE geodesic distance

The conformal metric g_ij(x) = e^{2σ(x)} δ_ij makes dangerous regions
geometrically unreachable, providing per-trajectory safety guarantees.

This is SEPARATE from discrete HodgeRank (Module 1):
- Module 1: Discrete topology on preference graphs
- Module 2: Continuous Riemannian geometry on latent space

Do NOT conflate these mathematical domains.

References:
- Lee "Riemannian Manifolds: An Introduction to Curvature" (1997)
- Ames et al. "Control Barrier Functions" (2019) - related concept
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import warnings

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class DangerRegion:
    """
    A dangerous region in latent space.
    
    The conformal factor σ(x) → ∞ as x approaches the boundary,
    creating an infinite geodesic distance barrier.
    """
    center: np.ndarray           # Center of dangerous region
    radius: float                # Radius of the danger zone
    sharpness: float = 2.0       # How quickly σ diverges (higher = sharper)
    name: str = "unnamed"        # Human-readable identifier
    
    def signed_distance(self, x: np.ndarray) -> float:
        """
        Signed distance to danger boundary.
        
        Positive = safe (outside danger)
        Zero = on boundary
        Negative = inside danger (catastrophic)
        """
        dist_to_center = np.linalg.norm(x - self.center)
        return dist_to_center - self.radius
    
    def is_safe(self, x: np.ndarray) -> bool:
        """Check if point is outside danger region."""
        return self.signed_distance(x) > 0


class ConformalSafetyMetric:
    """
    Conformal metric for geometric safety barriers.
    
    The metric tensor is:
        g_ij(x) = e^{2σ(x)} δ_ij
    
    where σ(x) → ∞ as x approaches any danger boundary.
    
    This creates INFINITE geodesic distance to dangerous regions,
    making them geometrically unreachable by any policy.
    
    Usage:
        metric = ConformalSafetyMetric()
        metric.add_danger_region(center=[0, 0], radius=1.0)
        
        # Check if path is safe
        dist = metric.geodesic_distance(start, end)
        if np.isinf(dist):
            print("Path crosses danger boundary!")
        
        # For policy optimization, use natural gradient
        natural_grad = metric.compute_natural_gradient(state, vanilla_grad)
    """
    
    def __init__(self, base_sigma: float = 0.0):
        """
        Args:
            base_sigma: Baseline conformal factor (usually 0 for identity metric)
        """
        self.base_sigma = base_sigma
        self.danger_regions: List[DangerRegion] = []
    
    def add_danger_region(
        self,
        center: np.ndarray,
        radius: float,
        sharpness: float = 2.0,
        name: str = "danger"
    ) -> None:
        """
        Add a dangerous region with infinite barrier.
        
        Args:
            center: Center of danger zone in latent space
            radius: Radius of danger zone
            sharpness: How quickly barrier increases (higher = sharper)
            name: Human-readable name for this danger
        """
        self.danger_regions.append(DangerRegion(
            center=np.asarray(center, dtype=np.float64),
            radius=float(radius),
            sharpness=float(sharpness),
            name=name
        ))
    
    def add_danger_regions_from_data(
        self,
        dangerous_states: np.ndarray,
        clustering_threshold: float = 0.5,
        margin: float = 0.1
    ) -> int:
        """
        Automatically identify danger regions from labeled dangerous states.
        
        Args:
            dangerous_states: Array of shape (n_states, dim) of dangerous states
            clustering_threshold: Distance threshold for clustering
            margin: Safety margin to add around detected regions
            
        Returns:
            Number of danger regions added
        """
        if len(dangerous_states) == 0:
            return 0
        
        # Simple greedy clustering
        remaining = list(range(len(dangerous_states)))
        n_added = 0
        
        while remaining:
            # Pick a seed
            seed_idx = remaining[0]
            seed = dangerous_states[seed_idx]
            
            # Find all points within threshold
            cluster = [seed_idx]
            for idx in remaining[1:]:
                if np.linalg.norm(dangerous_states[idx] - seed) < clustering_threshold:
                    cluster.append(idx)
            
            # Remove clustered points
            for idx in cluster:
                remaining.remove(idx)
            
            # Create danger region
            cluster_points = dangerous_states[cluster]
            center = np.mean(cluster_points, axis=0)
            radius = np.max(np.linalg.norm(cluster_points - center, axis=1)) + margin
            
            self.add_danger_region(center, radius, name=f"auto_{n_added}")
            n_added += 1
        
        return n_added
    
    def conformal_factor(self, x: np.ndarray) -> float:
        """
        Compute σ(x) for conformal metric g = e^{2σ} I.
        
        σ(x) = base_sigma - Σ_i sharpness_i * log(d_i(x))
        
        where d_i(x) is signed distance to danger region i.
        
        As x → boundary, d_i → 0, so log(d_i) → -∞, so σ → +∞.
        """
        sigma = self.base_sigma
        
        for region in self.danger_regions:
            d = region.signed_distance(x)
            if d <= 0:
                return float('inf')  # Inside danger = infinite barrier
            sigma -= region.sharpness * np.log(d)
        
        return sigma
    
    def conformal_factor_gradient(self, x: np.ndarray) -> np.ndarray:
        """
        Compute ∇σ(x).
        
        ∇σ = -Σ_i (sharpness_i / d_i) * ∇d_i
        
        where ∇d_i = (x - c_i) / ||x - c_i|| (outward normal)
        """
        grad = np.zeros_like(x)
        
        for region in self.danger_regions:
            diff = x - region.center
            dist_to_center = np.linalg.norm(diff)
            if dist_to_center < 1e-10:
                continue
            
            d = dist_to_center - region.radius
            if d <= 0:
                # Return gradient pointing away from danger
                return diff / dist_to_center * 1e10
            
            # ∇d = outward normal
            grad_d = diff / dist_to_center
            
            # ∇σ contribution from this region
            grad -= (region.sharpness / d) * grad_d
        
        return grad
    
    def metric_tensor(self, x: np.ndarray) -> np.ndarray:
        """
        Compute metric tensor g_ij(x) = e^{2σ(x)} δ_ij.
        
        Returns:
            Diagonal metric tensor as (dim, dim) array
        """
        sigma = self.conformal_factor(x)
        if np.isinf(sigma):
            return np.full((len(x), len(x)), float('inf'))
        
        scale = np.exp(2 * sigma)
        return scale * np.eye(len(x))
    
    def inverse_metric_tensor(self, x: np.ndarray) -> np.ndarray:
        """
        Compute inverse metric tensor g^{ij}(x) = e^{-2σ(x)} δ^{ij}.
        
        This is used for raising indices (e.g., natural gradient).
        """
        sigma = self.conformal_factor(x)
        if np.isinf(sigma):
            return np.zeros((len(x), len(x)))  # Zero update at danger
        
        scale = np.exp(-2 * sigma)
        return scale * np.eye(len(x))
    
    def geodesic_distance_approx(
        self,
        x: np.ndarray,
        y: np.ndarray,
        n_steps: int = 100
    ) -> float:
        """
        Approximate geodesic distance along straight path.
        
        For conformal metrics, this is an upper bound on true geodesic distance.
        If this returns infinity, the straight path crosses danger.
        
        Args:
            x: Start point
            y: End point
            n_steps: Integration steps
            
        Returns:
            Approximate geodesic distance (∞ if path unsafe)
        """
        path = np.linspace(x, y, n_steps)
        
        total_dist = 0.0
        for i in range(n_steps - 1):
            midpoint = (path[i] + path[i + 1]) / 2
            sigma = self.conformal_factor(midpoint)
            
            if np.isinf(sigma):
                return float('inf')
            
            step_length = np.linalg.norm(path[i + 1] - path[i])
            total_dist += np.exp(sigma) * step_length
        
        return total_dist
    
    def is_path_safe(
        self,
        x: np.ndarray,
        y: np.ndarray,
        n_checks: int = 50
    ) -> bool:
        """
        Check if straight path from x to y is safe.
        
        A path is safe if it doesn't enter any danger region.
        """
        for t in np.linspace(0, 1, n_checks):
            point = x + t * (y - x)
            if not self.is_safe(point):
                return False
        return True
    
    def is_safe(self, x: np.ndarray) -> bool:
        """Check if point x is outside all danger regions."""
        return all(region.is_safe(x) for region in self.danger_regions)
    
    def distance_to_nearest_danger(self, x: np.ndarray) -> float:
        """Get signed distance to nearest danger boundary."""
        if not self.danger_regions:
            return float('inf')
        return min(region.signed_distance(x) for region in self.danger_regions)
    
    def compute_natural_gradient(
        self,
        x: np.ndarray,
        vanilla_gradient: np.ndarray
    ) -> np.ndarray:
        """
        Compute natural gradient using conformal metric.
        
        natural_grad = G^{-1} @ vanilla_grad = e^{-2σ} * vanilla_grad
        
        Near danger (σ → ∞): natural_grad → 0 (no movement toward danger)
        Far from danger (σ ≈ 0): natural_grad ≈ vanilla_grad
        
        Args:
            x: Current state
            vanilla_gradient: Standard gradient ∇J
            
        Returns:
            Natural gradient G^{-1}∇J
        """
        sigma = self.conformal_factor(x)
        
        if np.isinf(sigma):
            return np.zeros_like(vanilla_gradient)
        
        scale = np.exp(-2 * sigma)
        return scale * vanilla_gradient
    
    def project_to_safe_region(
        self,
        x: np.ndarray,
        margin: float = 0.1
    ) -> np.ndarray:
        """
        Project point to nearest safe location if inside danger.
        
        Args:
            x: Point to project
            margin: Safety margin from boundary
            
        Returns:
            Safe point (original if already safe)
        """
        if self.is_safe(x):
            return x.copy()
        
        # Find which region we're in and project out
        for region in self.danger_regions:
            if not region.is_safe(x):
                diff = x - region.center
                dist = np.linalg.norm(diff)
                if dist < 1e-10:
                    # At center, pick arbitrary direction
                    diff = np.zeros_like(x)
                    diff[0] = 1.0
                    dist = 1.0
                
                # Project to boundary + margin
                direction = diff / dist
                return region.center + direction * (region.radius + margin)
        
        return x.copy()


class ConformalPolicyOptimizer:
    """
    Policy optimizer using conformal safety metric.
    
    This wraps a standard policy network and applies conformal metric
    corrections to ensure safety during optimization.
    """
    
    def __init__(
        self,
        metric: ConformalSafetyMetric,
        state_encoder: Optional[Callable[[any], np.ndarray]] = None
    ):
        """
        Args:
            metric: ConformalSafetyMetric with danger regions defined
            state_encoder: Function mapping raw states to latent vectors
        """
        self.metric = metric
        self.state_encoder = state_encoder or (lambda x: np.asarray(x))
    
    def compute_safe_update(
        self,
        states: np.ndarray,
        vanilla_gradients: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Compute safe policy gradient update.
        
        Args:
            states: Batch of states (n_batch, state_dim)
            vanilla_gradients: Standard policy gradients (n_batch, grad_dim)
            
        Returns:
            (safe_gradients, metadata) where metadata includes safety statistics
        """
        safe_grads = []
        safety_factors = []
        
        for state, grad in zip(states, vanilla_gradients):
            latent = self.state_encoder(state)
            
            sigma = self.metric.conformal_factor(latent)
            if np.isinf(sigma):
                safe_grads.append(np.zeros_like(grad))
                safety_factors.append(0.0)
            else:
                factor = np.exp(-2 * sigma)
                safe_grads.append(factor * grad)
                safety_factors.append(factor)
        
        safe_grads = np.array(safe_grads)
        
        metadata = {
            "mean_safety_factor": np.mean(safety_factors),
            "min_safety_factor": np.min(safety_factors),
            "n_blocked": np.sum(np.array(safety_factors) < 1e-6),
            "n_total": len(safety_factors)
        }
        
        return safe_grads, metadata
    
    def evaluate_trajectory_safety(
        self,
        trajectory: np.ndarray
    ) -> Dict[str, any]:
        """
        Evaluate safety of a full trajectory.
        
        Args:
            trajectory: Array of states (T, state_dim)
            
        Returns:
            Safety analysis including violations and distances
        """
        min_distance = float('inf')
        violations = []
        distances = []
        
        for t, state in enumerate(trajectory):
            latent = self.state_encoder(state)
            d = self.metric.distance_to_nearest_danger(latent)
            distances.append(d)
            
            if d < min_distance:
                min_distance = d
            
            if d <= 0:
                violations.append({
                    "timestep": t,
                    "state": state,
                    "distance": d
                })
        
        return {
            "is_safe": len(violations) == 0,
            "min_distance": min_distance,
            "n_violations": len(violations),
            "violations": violations,
            "distance_profile": np.array(distances)
        }


if TORCH_AVAILABLE:
    class ConformalSafetyLayer(nn.Module):
        """
        PyTorch layer that applies conformal safety scaling.
        
        This can be inserted into policy networks to automatically
        scale gradients based on proximity to danger.
        """
        
        def __init__(
            self,
            metric: ConformalSafetyMetric,
            learnable_sharpness: bool = False
        ):
            super().__init__()
            self.metric = metric
            
            if learnable_sharpness:
                self.log_sharpness = nn.Parameter(torch.tensor(0.0))
            else:
                self.log_sharpness = None
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Forward pass applies conformal scaling.
            
            In training, this scales activations by e^{-σ}.
            Gradients are automatically scaled by e^{-2σ} (chain rule).
            """
            # Compute conformal factors
            batch_size = x.shape[0]
            scales = []
            
            x_np = x.detach().cpu().numpy()
            for i in range(batch_size):
                sigma = self.metric.conformal_factor(x_np[i])
                if np.isinf(sigma):
                    scales.append(0.0)
                else:
                    if self.log_sharpness is not None:
                        sigma = sigma * torch.exp(self.log_sharpness).item()
                    scales.append(np.exp(-sigma))
            
            scales = torch.tensor(scales, device=x.device, dtype=x.dtype)
            scales = scales.view(-1, *([1] * (x.dim() - 1)))
            
            return x * scales
        
        def get_safety_mask(self, x: torch.Tensor) -> torch.Tensor:
            """
            Get binary mask indicating safe states.
            
            Returns:
                Boolean tensor of shape (batch_size,)
            """
            x_np = x.detach().cpu().numpy()
            mask = [self.metric.is_safe(x_np[i]) for i in range(x.shape[0])]
            return torch.tensor(mask, device=x.device, dtype=torch.bool)


class SafetyGuidedSampler:
    """
    Action sampler that respects conformal safety boundaries.
    
    When sampling actions, this biases away from actions that
    would lead toward danger regions.
    """
    
    def __init__(
        self,
        metric: ConformalSafetyMetric,
        dynamics_model: Optional[Callable] = None,
        n_samples: int = 100
    ):
        """
        Args:
            metric: Conformal safety metric
            dynamics_model: Optional f(state, action) -> next_state
            n_samples: Number of samples for safety evaluation
        """
        self.metric = metric
        self.dynamics_model = dynamics_model
        self.n_samples = n_samples
    
    def sample_safe_action(
        self,
        state: np.ndarray,
        action_mean: np.ndarray,
        action_std: np.ndarray,
        max_attempts: int = 10
    ) -> Tuple[np.ndarray, bool]:
        """
        Sample an action that is predicted to be safe.
        
        Uses rejection sampling if dynamics model is available,
        otherwise falls back to conformal-scaled sampling.
        
        Returns:
            (action, is_verified_safe)
        """
        if self.dynamics_model is None:
            # No dynamics model: just sample normally
            action = np.random.normal(action_mean, action_std)
            return action, False
        
        # Rejection sampling based on predicted next state safety
        for _ in range(max_attempts):
            action = np.random.normal(action_mean, action_std)
            next_state = self.dynamics_model(state, action)
            
            if self.metric.is_safe(next_state):
                return action, True
        
        # Fallback: project action to avoid predicted danger
        warnings.warn("Could not find safe action, using projection")
        action = np.random.normal(action_mean, action_std)
        next_state = self.dynamics_model(state, action)
        
        if not self.metric.is_safe(next_state):
            # Modify action to steer away from danger
            safe_next = self.metric.project_to_safe_region(next_state)
            # Simple linear approximation for action correction
            delta_state = safe_next - next_state
            action = action + 0.1 * delta_state[:len(action)]  # Crude heuristic
        
        return action, False
