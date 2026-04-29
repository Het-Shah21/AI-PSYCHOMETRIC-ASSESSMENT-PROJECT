"""Phase 4 Tests — actual API signatures from inspection."""

import time, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.scoring_engine import BayesianScoringEngine, BetaParams
from src.calibration.validity import VALIDITY_MATRIX, generate_validity_report, required_sample_size
from src.calibration.fairness import (
    GroupScores, compute_effect_size, classify_dif, compute_demographic_parity, run_fairness_audit,
)
from src.core.constructs import CONSTRUCTS, ConstructID


# ═══ TASK 4.1 — Bayesian Scoring ═══

class TestTask41BayesianScoring:
    def test_engine_initializes(self):
        engine = BayesianScoringEngine()
        summary = engine.get_posterior_summary()
        assert len(summary) == 4

    def test_score_construct(self):
        engine = BayesianScoringEngine()
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {ind.id: (ind.min_value + ind.max_value) / 2
                   for sf in construct.sub_facets for ind in sf.indicators}
        result = engine.score_construct("confidence", signals)
        assert 1.0 <= result.scaled_score <= 10.0

    def test_score_full_assessment(self):
        engine = BayesianScoringEngine()
        signals = {}
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    signals[ind.id] = (ind.min_value + ind.max_value) / 2
        result = engine.score_full_assessment("test-session", signals)
        assert len(result.construct_scores) == 4
        assert result.completion_pct == 100.0

    def test_high_values_high_scores(self):
        engine = BayesianScoringEngine()
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = ind.max_value if ind.polarity > 0 else ind.min_value
        result = engine.score_construct("confidence", signals)
        assert result.scaled_score >= 6.0

    def test_low_values_low_scores(self):
        engine = BayesianScoringEngine()
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = ind.min_value if ind.polarity > 0 else ind.max_value
        result = engine.score_construct("confidence", signals)
        assert result.scaled_score <= 5.0

    def test_confidence_interval_contains_score(self):
        engine = BayesianScoringEngine()
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {ind.id: (ind.min_value + ind.max_value) / 2
                   for sf in construct.sub_facets for ind in sf.indicators}
        result = engine.score_construct("confidence", signals)
        assert result.confidence_lower <= result.scaled_score <= result.confidence_upper

    def test_beta_params(self):
        bp = BetaParams(alpha=6.0, beta=4.0)
        assert abs(bp.alpha / (bp.alpha + bp.beta) - 0.6) < 0.01


class TestTask41Performance:
    def test_full_scoring_speed(self):
        engine = BayesianScoringEngine()
        signals = {}
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    signals[ind.id] = (ind.min_value + ind.max_value) / 2
        start = time.perf_counter()
        for _ in range(100):
            engine.score_full_assessment("perf", signals)
        elapsed = time.perf_counter() - start
        per_call = elapsed / 100 * 1000
        assert per_call < 50, f"Scoring: {per_call:.1f}ms/call"


# ═══ TASK 4.2 — Validity ═══

class TestTask42Validity:
    def test_validity_matrix_populated(self):
        assert len(VALIDITY_MATRIX) >= 4

    def test_each_construct_has_reference(self):
        constructs = {"confidence", "curiosity", "emotional_safety", "exploratory_power"}
        mapped = {vm.our_construct for vm in VALIDITY_MATRIX}
        assert constructs.issubset(mapped)

    def test_expected_correlations_positive(self):
        for vm in VALIDITY_MATRIX:
            assert vm.expected_correlation > 0

    def test_sample_size_computation(self):
        n = required_sample_size(expected_r=0.5, alpha=0.05, power=0.80)
        assert 25 <= n <= 40

    def test_smaller_effect_needs_more(self):
        n_large = required_sample_size(expected_r=0.7, alpha=0.05, power=0.80)
        n_small = required_sample_size(expected_r=0.3, alpha=0.05, power=0.80)
        assert n_small > n_large

    def test_report_generation(self):
        report = generate_validity_report()
        assert report is not None


# ═══ TASK 4.3 — Fairness ═══

class TestTask43Fairness:
    def test_effect_size_zero(self):
        ga = GroupScores(group_label="A", scores=[5.0, 5.0, 5.0])
        gb = GroupScores(group_label="B", scores=[5.0, 5.0, 5.0])
        d = compute_effect_size(ga, gb)
        assert abs(d) < 0.01

    def test_effect_size_positive(self):
        ga = GroupScores(group_label="A", scores=[10.0, 11.0, 9.0])
        gb = GroupScores(group_label="B", scores=[5.0, 6.0, 4.0])
        d = compute_effect_size(ga, gb)
        assert d > 0

    def test_effect_size_large(self):
        ga = GroupScores(group_label="A", scores=[10.0, 11.0, 9.0, 10.5])
        gb = GroupScores(group_label="B", scores=[1.0, 2.0, 1.5, 2.5])
        d = compute_effect_size(ga, gb)
        assert abs(d) > 0.8

    def test_classify_dif_negligible(self):
        label, flagged = classify_dif(0.2)
        assert label == "negligible"
        assert not flagged

    def test_classify_dif_moderate(self):
        label, flagged = classify_dif(0.7)
        assert label == "moderate"
        assert flagged

    def test_classify_dif_large(self):
        label, flagged = classify_dif(1.5)
        assert label == "large"
        assert flagged

    def test_parity_equal_groups(self):
        ga = GroupScores(group_label="A", scores=[5.0, 6.0, 5.5, 5.8, 6.2])
        gb = GroupScores(group_label="B", scores=[5.1, 5.9, 5.6, 5.7, 6.1])
        result = compute_demographic_parity(ga, gb)
        assert result.passes

    def test_parity_unequal_groups(self):
        ga = GroupScores(group_label="A", scores=[8.0, 8.5, 9.0, 8.8, 8.2])
        gb = GroupScores(group_label="B", scores=[3.0, 3.5, 4.0, 3.8, 3.2])
        result = compute_demographic_parity(ga, gb)
        assert not result.passes

    def test_full_audit(self):
        groups = {
            "Male": GroupScores(group_label="Male", scores=[5.5, 6.0, 5.8]),
            "Female": GroupScores(group_label="Female", scores=[5.4, 5.9, 5.7]),
        }
        report = run_fairness_audit("confidence", groups)
        assert report is not None


class TestTask43Performance:
    def test_effect_size_speed(self):
        import random
        ga = GroupScores(group_label="A", scores=[random.gauss(5, 1) for _ in range(1000)])
        gb = GroupScores(group_label="B", scores=[random.gauss(5, 1) for _ in range(1000)])
        start = time.perf_counter()
        for _ in range(1000):
            compute_effect_size(ga, gb)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1k effect sizes: {elapsed:.3f}s"
