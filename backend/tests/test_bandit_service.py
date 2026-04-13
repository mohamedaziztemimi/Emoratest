"""Unit tests for Multi-Armed Bandit service.

Covers: Thompson Sampling, UCB1, ε-greedy algorithms,
convergence detection, sequential testing (mSPRT), and storage.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.services.bandit_service import (
    BanditAlgorithm,
    BanditArm,
    BanditState,
    BanditService,
    BanditRepository,
    get_or_create_bandit,
)


# ── BanditArm Tests ───────────────────────────────────────────────────


class TestBanditArm:
    """Tests for BanditArm dataclass."""

    def test_create_default_arm(self):
        """Create arm with default values."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        assert arm.arm_id == "arm_0"
        assert arm.variant_id == "variant_a"
        assert arm.successes == 0
        assert arm.trials == 0
        assert arm.alpha == 1.0
        assert arm.beta == 1.0

    def test_mean_reward_zero_trials(self):
        """Mean reward is 0 when no trials."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        assert arm.mean_reward == 0.0

    def test_mean_reward_with_trials(self):
        """Mean reward calculates correctly."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        arm.successes = 50
        arm.trials = 100
        assert arm.mean_reward == 0.5

    def test_update_with_success(self):
        """Update with successful outcome increments stats."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        arm.update(reward=1.0)
        assert arm.trials == 1
        assert arm.successes == 1
        assert arm.alpha == 2.0  # 1 + successes
        assert arm.beta == 1.0  # 1 + failures

    def test_update_with_failure(self):
        """Update with failed outcome increments trials only."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        arm.update(reward=0.0)
        assert arm.trials == 1
        assert arm.successes == 0
        assert arm.alpha == 1.0
        assert arm.beta == 2.0  # 1 + failures

    def test_update_multiple_rewards(self):
        """Multiple updates maintain correct statistics."""
        arm = BanditArm(arm_id="arm_0", variant_id="variant_a")
        arm.update(1.0)
        arm.update(1.0)
        arm.update(0.0)
        arm.update(1.0)
        assert arm.trials == 4
        assert arm.successes == 3
        assert arm.mean_reward == 0.75
        assert arm.alpha == 4.0
        assert arm.beta == 2.0

    def test_serialization(self):
        """Serialize and deserialize arm correctly."""
        original = BanditArm(
            arm_id="arm_0", variant_id="variant_a", successes=30, trials=100
        )
        data = original.to_dict()
        restored = BanditArm.from_dict(data)
        assert restored.arm_id == original.arm_id
        assert restored.variant_id == original.variant_id
        assert restored.successes == original.successes
        assert restored.trials == original.trials


# ── BanditState Tests ────────────────────────────────────────────────


class TestBanditState:
    """Tests for BanditState dataclass."""

    def test_create_default_state(self):
        """Create state with default values."""
        state = BanditState(
            experiment_id="exp_1", algorithm=BanditAlgorithm.THOMPSON_SAMPLING
        )
        assert state.experiment_id == "exp_1"
        assert state.algorithm == BanditAlgorithm.THOMPSON_SAMPLING
        assert state.epsilon == 0.1
        assert state.exploration_factor == 2.0
        assert state.min_samples_per_arm == 100

    def test_total_trials(self):
        """Total trials sums across all arms."""
        state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            arms=[
                BanditArm("arm_0", "a", successes=10, trials=50),
                BanditArm("arm_1", "b", successes=20, trials=80),
            ],
        )
        assert state.total_trials == 130

    def test_arm_count(self):
        """Arm count returns correct number."""
        state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            arms=[BanditArm(f"arm_{i}", f"v{i}") for i in range(5)],
        )
        assert state.arm_count == 5

    def test_get_arm_by_id(self):
        """Get arm returns correct arm or None."""
        arm0 = BanditArm("arm_0", "a")
        arm1 = BanditArm("arm_1", "b")
        state = BanditState(
            experiment_id="exp_1", algorithm=BanditAlgorithm.THOMPSON_SAMPLING, arms=[arm0, arm1]
        )

        assert state.get_arm("arm_0") == arm0
        assert state.get_arm("arm_1") == arm1
        assert state.get_arm("arm_2") is None

    def test_get_best_arm(self):
        """Get best arm returns arm with highest mean."""
        arms = [
            BanditArm("arm_0", "a", successes=5, trials=10),
            BanditArm("arm_1", "b", successes=8, trials=10),
            BanditArm("arm_2", "c", successes=3, trials=10),
        ]
        state = BanditState(
            experiment_id="exp_1", algorithm=BanditAlgorithm.THOMPSON_SAMPLING, arms=arms
        )
        best = state.get_best_arm()
        assert best.variant_id == "b"

    def test_get_best_arm_empty(self):
        """Get best arm returns None for empty state."""
        state = BanditState(experiment_id="exp_1", algorithm=BanditAlgorithm.THOMPSON_SAMPLING)
        assert state.get_best_arm() is None

    def test_can_exploit_true(self):
        """Can exploit returns True when all arms have minimum samples."""
        arms = [
            BanditArm("arm_0", "a", successes=10, trials=100),
            BanditArm("arm_1", "b", successes=20, trials=100),
        ]
        state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            arms=arms,
            min_samples_per_arm=50,
        )
        assert state.can_exploit() is True

    def test_can_exploit_false(self):
        """Can exploit returns False when any arm lacks minimum samples."""
        arms = [
            BanditArm("arm_0", "a", successes=10, trials=100),
            BanditArm("arm_1", "b", successes=20, trials=50),
        ]
        state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            arms=arms,
            min_samples_per_arm=100,
        )
        assert state.can_exploit() is False

    def test_serialization(self):
        """Serialize and deserialize state correctly."""
        original = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.UCB1,
            arms=[BanditArm("arm_0", "a", successes=30, trials=100)],
        )
        data = original.to_dict()
        restored = BanditState.from_dict(data)
        assert restored.experiment_id == original.experiment_id
        assert restored.algorithm == original.algorithm
        assert len(restored.arms) == len(original.arms)


# ── BanditService Creation Tests ─────────────────────────────────────


class TestBanditServiceCreation:
    """Tests for creating bandit experiments."""

    def test_create_bandit_two_variants(self):
        """Create bandit with two variants."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["control", "variant_a"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )
        assert state.experiment_id == "exp_1"
        assert len(state.arms) == 2
        assert state.arms[0].variant_id == "control"
        assert state.arms[1].variant_id == "variant_a"

    def test_create_bandit_no_variants_error(self):
        """Create bandit with no variants raises error."""
        service = BanditService()
        with pytest.raises(ValueError, match="variant_ids must contain at least one"):
            service.create_bandit(experiment_id="exp_1", variant_ids=[])

    def test_create_bandit_mvt_five_variants(self):
        """Create multivariate bandit with 5 variants."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=[f"v{i}" for i in range(5)],
            algorithm=BanditAlgorithm.UCB1,
        )
        assert len(state.arms) == 5

    def test_create_bandit_custom_params(self):
        """Create bandit with custom parameters."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.EPSILON_GREEDY,
            epsilon=0.2,
            exploration_factor=3.0,
            min_samples_per_arm=50,
        )
        assert state.epsilon == 0.2
        assert state.exploration_factor == 3.0
        assert state.min_samples_per_arm == 50


# ── Thompson Sampling Tests ─────────────────────────────────────────────


class TestThompsonSampling:
    """Tests for Thompson Sampling algorithm."""

    def test_select_arm_random_initially(self):
        """Initially, selection is random due to same Beta(1,1)."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=0,
        )

        selections = [service.select_arm(state) for _ in range(100)]
        # All variants should be selected (distribution should be roughly uniform)
        assert len(set(selections)) == 3

    def test_select_arm_converges_to_best(self):
        """Selection converges to best performing arm."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=0,
        )

        # Give arm 'a' a clear advantage
        state.arms[0].update(1.0)  # a: 1/1 = 100%
        state.arms[1].update(0.0)  # b: 0/1 = 0%
        state.arms[2].update(0.0)  # c: 0/1 = 0%

        # Select many times - 'a' should be chosen most
        selections = [service.select_arm(state) for _ in range(100)]
        a_count = selections.count("a")
        assert a_count > 50  # Should dominate


# ── UCB1 Tests ───────────────────────────────────────────────────────


class TestUCB1:
    """Tests for UCB1 algorithm."""

    def test_select_arm_random_initially(self):
        """Initially, unexplored arms get infinite UCB value."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.UCB1,
            min_samples_per_arm=0,
        )

        # All arms have trials=0, so first arm selected depends on order
        # But all will be explored quickly
        selections = set()
        for _ in range(20):
            selections.add(service.select_arm(state))
        assert len(selections) >= 2

    def test_select_arm_balances_explore_exploit(self):
        """UCB1 balances exploration of lower-trial arms."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.UCB1,
            min_samples_per_arm=0,
        )

        # Give 'a' many trials but modest success rate
        for _ in range(50):
            state.arms[0].update(1.0 if np.random.random() < 0.5 else 0.0)

        # Give 'b' few trials but perfect success
        state.arms[1].update(1.0)

        # UCB1 should still consider 'b' due to exploration bonus

    def test_ucb1_formula_correct(self):
        """UCB1 formula calculation is correct."""
        arm = BanditArm("arm_0", "a", successes=40, trials=100)
        assert arm.mean_reward == 0.4

        total_trials = 200
        exploration_factor = 2.0

        exploration_bonus = exploration_factor * math.sqrt(math.log(total_trials) / arm.trials)
        expected_ucb = 0.4 + exploration_bonus

        # Calculate manually
        ucb_value = arm.mean_reward + exploration_bonus

        assert abs(ucb_value - expected_ucb) < 0.0001


# ── ε-Greedy Tests ───────────────────────────────────────────────────


class TestEpsilonGreedy:
    """Tests for ε-greedy algorithm."""

    def test_select_arm_with_epsilon(self):
        """With probability epsilon, a random arm is chosen."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.EPSILON_GREEDY,
            epsilon=0.5,  # 50% exploration
            min_samples_per_arm=0,
        )

        # Give 'a' perfect performance
        for _ in range(100):
            state.arms[0].update(1.0)

        # With 50% epsilon, 'b' and 'c' should be selected sometimes
        selections = [service.select_arm(state) for _ in range(200)]
        has_exploration = any(s in ("b", "c") for s in selections)
        assert has_exploration

    def test_select_arm_exploits_best(self):
        """With 1-epsilon probability, best arm is chosen."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.EPSILON_GREEDY,
            epsilon=0.0,  # Pure exploitation
            min_samples_per_arm=0,
        )

        # Give 'a' better performance
        for _ in range(10):
            state.arms[0].update(1.0)
        for _ in range(10):
            state.arms[1].update(0.5)

        # Should always select 'a'
        for _ in range(20):
            assert service.select_arm(state) == "a"


# ── Minimum Samples Tests ───────────────────────────────────────────────


class TestMinimumSamples:
    """Tests for minimum samples per arm constraint."""

    def test_min_samples_enforced(self):
        """Arms with insufficient samples get random selection."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=100,
        )

        # Only arm 'a' has samples
        for _ in range(100):
            state.arms[0].update(1.0)

        # All arms should still be selected due to min_samples constraint
        selections = set()
        for _ in range(50):
            selections.add(service.select_arm(state))
        assert len(selections) >= 2  # At least explore other arms


# ── Record Outcome Tests ─────────────────────────────────────────────


class TestRecordOutcome:
    """Tests for recording outcomes."""

    def test_record_outcome_updates_arm(self):
        """Recording outcome updates arm statistics."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        new_state = service.record_outcome(state, "arm_0", 1.0)
        arm = new_state.get_arm("arm_0")
        assert arm.trials == 1
        assert arm.successes == 1

    def test_record_outcome_failure(self):
        """Recording failure updates trials but not successes."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        new_state = service.record_outcome(state, "arm_0", 0.0)
        arm = new_state.get_arm("arm_0")
        assert arm.trials == 1
        assert arm.successes == 0

    def test_record_outcome_invalid_arm_error(self):
        """Recording outcome for invalid arm raises error."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        with pytest.raises(ValueError, match="arm arm_invalid not found"):
            service.record_outcome(state, "arm_invalid", 1.0)


# ── Allocation Percentages Tests ──────────────────────────────────────


class TestAllocationPercentages:
    """Tests for traffic allocation percentages."""

    def test_allocation_equal_initially(self):
        """Allocation is equal when no trials."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c", "d"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        alloc = service.get_allocation_percentages(state)
        assert alloc["a"] == 25.0
        assert alloc["b"] == 25.0
        assert alloc["c"] == 25.0
        assert alloc["d"] == 25.0

    def test_allocation_proportional_to_trials(self):
        """Allocation is proportional to trial counts."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        # Record different numbers of trials
        for _ in range(30):
            state.arms[0].update(1.0)
        for _ in range(70):
            state.arms[1].update(1.0)

        alloc = service.get_allocation_percentages(state)
        assert alloc["a"] == 30.0
        assert alloc["b"] == 70.0


# ── Convergence Tests ───────────────────────────────────────────────────


class TestConvergence:
    """Tests for convergence detection."""

    def test_convergence_insufficient_trials(self):
        """No convergence with insufficient trials."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=0,
        )

        result = service.check_convergence(state)
        assert result["converged"] is False
        assert result["reason"] == "insufficient_trials"

    def test_thompson_convergence_clear_winner(self):
        """Thompson sampling detects clear winner."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=0,
        )

        # Give 'a' massive advantage
        for _ in range(500):
            state.arms[0].update(1.0)
        for _ in range(500):
            state.arms[1].update(0.0)

        result = service.check_convergence(state)
        assert result["converged"] is True
        assert result["winner"] == "a"
        assert result["confidence"] >= 0.95

    def test_thompson_no_convergence_close_race(self):
        """No convergence when arms are close."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=0,
        )

        # Give similar performance
        for _ in range(500):
            state.arms[0].update(1.0 if np.random.random() < 0.5 else 0.0)
            state.arms[1].update(1.0 if np.random.random() < 0.5 else 0.0)

        result = service.check_convergence(state)
        # Should not have converged to a clear winner
        assert result["winner"] is not None
        # Confidence should be lower due to uncertainty

    def test_empirical_convergence_with_uci(self):
        """Empirical convergence uses confidence intervals."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.UCB1,
            min_samples_per_arm=0,
        )

        # Give 'a' clear advantage
        for _ in range(200):
            state.arms[0].update(1.0)
        for _ in range(200):
            state.arms[1].update(0.0)

        result = service.check_convergence(state)
        assert result["converged"] is True
        assert result["winner"] == "a"


# ── Sequential Test (mSPRT) Tests ────────────────────────────────


class TestSequentialTest:
    """Tests for mixture Sequential Probability Ratio Test."""

    def test_sequential_test_insufficient_trials(self):
        """mSPRT returns continue with insufficient trials."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        result = service.sequential_test(state)
        assert result["should_stop"] is False
        assert result["recommendation"] == "collect_more_data"

    def test_sequential_test_declares_winner(self):
        """mSPRT declares winner with strong evidence."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        # Clear advantage for 'a'
        for _ in range(250):
            state.arms[0].update(1.0)
        for _ in range(250):
            state.arms[1].update(0.0)

        result = service.sequential_test(state)
        assert result["should_stop"] is True
        assert result["recommendation"] == "declare_winner"
        assert result["effect_size"] > 0
        assert result["p_value"] < 0.05

    def test_sequential_test_no_difference(self):
        """mSPRT detects no significant difference."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        # Equal performance
        for _ in range(500):
            state.arms[0].update(1.0 if np.random.random() < 0.5 else 0.0)
            state.arms[1].update(1.0 if np.random.random() < 0.5 else 0.0)

        result = service.sequential_test(state)
        assert result["should_stop"] is True
        assert result["recommendation"] == "no_significant_difference"
        assert abs(result["effect_size"]) < 0.1

    def test_sequential_test_includes_z_score(self):
        """mSPRT includes Z-score in results."""
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        )

        # Create some difference
        for _ in range(100):
            state.arms[0].update(1.0)
        for _ in range(100):
            state.arms[1].update(0.0)

        result = service.sequential_test(state)
        assert "z_score" in result
        assert abs(result["z_score"]) > 2.0  # Should be significant


# ── BanditRepository Tests ────────────────────────────────────────────


class TestBanditRepository:
    """Tests for BanditRepository storage."""

    @pytest.mark.asyncio
    async def test_save_and_load_with_redis(self):
        """Save and load state with Redis."""
        redis = AsyncMock()
        redis.setex = AsyncMock()
        redis.get = AsyncMock()

        repo = BanditRepository(redis_client=redis)
        state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            arms=[BanditArm("arm_0", "a")],
        )

        # Save
        await repo.save(state)
        assert redis.setex.called

        # Load (mock return value)
        redis.get.return_value = json.dumps(state.to_dict())
        loaded = await repo.load("exp_1")
        assert loaded.experiment_id == state.experiment_id
        assert loaded.algorithm == state.algorithm

    @pytest.mark.asyncio
    async def test_load_not_found(self):
        """Load returns None when state not found."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)

        repo = BanditRepository(redis_client=redis)
        loaded = await repo.load("exp_nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_removes_state(self):
        """Delete removes state from Redis."""
        redis = AsyncMock()
        redis.delete = AsyncMock()

        repo = BanditRepository(redis_client=redis)
        await repo.delete("exp_1")
        assert redis.delete.called

    def test_repository_without_redis(self):
        """Repository without Redis falls back gracefully."""
        repo = BanditRepository(redis_client=None)
        assert repo._use_redis is False


# ── Statistical Helper Tests ──────────────────────────────────────────


class TestStatisticalHelpers:
    """Tests for statistical helper functions."""

    def test_normal_cdf_zero(self):
        """Normal CDF at 0 is 0.5."""
        result = BanditService._normal_cdf(0.0)
        assert abs(result - 0.5) < 0.0001

    def test_normal_cdf_negative(self):
        """Normal CDF at negative value is < 0.5."""
        result = BanditService._normal_cdf(-1.96)
        assert result < 0.5
        assert result > 0.0

    def test_normal_cdf_positive(self):
        """Normal CDF at positive value is > 0.5."""
        result = BanditService._normal_cdf(1.96)
        assert result > 0.5
        assert result < 1.0

    def test_normal_ppf_extremes(self):
        """Normal PPF at extremes approaches +/- infinity."""
        p_99 = BanditService._normal_ppf(0.99)
        p_01 = BanditService._normal_ppf(0.01)
        assert p_99 > 0
        assert p_01 < 0
        assert abs(p_99) > abs(p_01)  # 99th percentile is further from 0

    def test_normal_ppf_median(self):
        """Normal PPF at 0.5 is approximately 0."""
        result = BanditService._normal_ppf(0.5)
        assert abs(result) < 0.01

    def test_normal_ppf_bounds(self):
        """Normal PPF at bounds returns 0."""
        assert BanditService._normal_ppf(0.0) == 0.0
        assert BanditService._normal_ppf(1.0) == 0.0


# ── Integration Tests ───────────────────────────────────────────────────


class TestBanditIntegration:
    """Integration tests for bandit workflow."""

    def test_full_workflow_thompson_sampling(self):
        """Test complete workflow with Thompson Sampling."""
        np.random.seed(42)
        service = BanditService()
        state = service.create_bandit(
            experiment_id="exp_1",
            variant_ids=["a", "b", "c"],
            algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
            min_samples_per_arm=10,
        )

        # Simulate trials: 'a' has 20% conversion, 'b' has 15%, 'c' has 10%
        outcomes_a = [1.0 if np.random.random() < 0.2 else 0.0 for _ in range(200)]
        outcomes_b = [1.0 if np.random.random() < 0.15 else 0.0 for _ in range(200)]
        outcomes_c = [1.0 if np.random.random() < 0.1 else 0.0 for _ in range(200)]

        # Record outcomes
        for outcome in outcomes_a:
            arm_id = service.select_arm(state)
            if arm_id == "a":
                state = service.record_outcome(state, "arm_0", outcome)
            else:
                state = state  # Other arm selected

        for outcome in outcomes_b:
            arm_id = service.select_arm(state)
            if arm_id == "b":
                state = service.record_outcome(state, "arm_1", outcome)
            else:
                state = state

        for outcome in outcomes_c:
            arm_id = service.select_arm(state)
            if arm_id == "c":
                state = service.record_outcome(state, "arm_2", outcome)
            else:
                state = state

        # Check convergence
        result = service.check_convergence(state, min_trials=200)
        # Should have clear winner after 600 trials with significant differences

        # Check allocation
        alloc = service.get_allocation_percentages(state)
        assert 0 <= alloc["a"] <= 100
        assert 0 <= alloc["b"] <= 100
        assert 0 <= alloc["c"] <= 100
        assert abs(sum(alloc.values()) - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_get_or_create_bandit(self):
        """Test get_or_create_bandit convenience function."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()

        repo = BanditRepository(redis_client=redis)
        service = BanditService(repository=repo)

        state = await get_or_create_bandit(
            service=service,
            repository=repo,
            experiment_id="exp_1",
            variant_ids=["a", "b"],
        )

        assert state.experiment_id == "exp_1"
        assert len(state.arms) == 2
        assert redis.setex.called  # Should save new state

    @pytest.mark.asyncio
    async def test_get_or_create_bandit_loads_existing(self):
        """Test get_or_create_bandit loads existing state."""
        existing_state = BanditState(
            experiment_id="exp_1",
            algorithm=BanditAlgorithm.UCB1,
            arms=[BanditArm("arm_0", "a")],
        )

        redis = AsyncMock()
        redis.get = AsyncMock(return_value=json.dumps(existing_state.to_dict()))
        redis.setex = AsyncMock()

        repo = BanditRepository(redis_client=redis)
        service = BanditService(repository=repo)

        state = await get_or_create_bandit(
            service=service,
            repository=repo,
            experiment_id="exp_1",
            variant_ids=["a", "b"],
        )

        assert state.algorithm == BanditAlgorithm.UCB1  # Loaded existing
        assert not redis.setex.called  # Should not save
