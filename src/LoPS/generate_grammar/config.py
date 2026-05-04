from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_STRATEGY_SEQUENCE_DIR = Path(
    "/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StrategySequence"
)
DEFAULT_STATE_GRAPH_DIR = Path(
    "/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StateGraph"
)
DEFAULT_BASELINE_GRAMMAR_DIR = Path(
    "/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/grammar2"
)
DEFAULT_OUTPUT_DIR = Path(".planning/runs/2026-05-04-generateGrammar/refactored-output/grammar2")
DEFAULT_STATE_NAMES = ("IS1", "IS2", "PG1", "PG2", "PE", "BN5")


@dataclass(frozen=True)
class GrammarLearningParams:
    state_names: tuple[str, ...] = DEFAULT_STATE_NAMES
    chunk_alpha: float = 0.5
    condition_alpha: float = 0.5
    skip_gram_alpha: float = 0.5
    max_iterations: int = 100000
    convergence_window: int = 5
    convergence_kl_threshold: float = 0.05
    candidate_ratio_min: float = 1.0
    candidate_ratio_keep: float = 0.85
    min_pair_frequency: float = 0.05
    removed_token: str = "N"
    skip_gram_target: str = "E-A"
    skip_gram_min_offset: int = 2
    skip_gram_max_offset: int = 5
    skip_gram_min_frequency: float = 0.025
    excluded_child_tokens: tuple[str, ...] = ("V", "1", "2", "N", "S", "e")
    excluded_parent_tokens: tuple[str, ...] = ("V", "N")
    reject_shared_base_tokens: bool = True


@dataclass(frozen=True)
class GenerateGrammarConfig:
    strategy_sequence_dir: Path = DEFAULT_STRATEGY_SEQUENCE_DIR
    state_graph_dir: Path = DEFAULT_STATE_GRAPH_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    baseline_grammar_dir: Path | None = DEFAULT_BASELINE_GRAMMAR_DIR
    learning: GrammarLearningParams = field(default_factory=GrammarLearningParams)

    def validate(self) -> None:
        if not self.strategy_sequence_dir.is_dir():
            raise FileNotFoundError(f"StrategySequence directory not found: {self.strategy_sequence_dir}")
        if not self.state_graph_dir.is_dir():
            raise FileNotFoundError(f"StateGraph directory not found: {self.state_graph_dir}")
        if self.baseline_grammar_dir is not None and not self.baseline_grammar_dir.is_dir():
            raise FileNotFoundError(f"Baseline grammar directory not found: {self.baseline_grammar_dir}")

        output = self.output_dir
        if self.baseline_grammar_dir is not None and output.resolve() == self.baseline_grammar_dir.resolve():
            raise ValueError("output_dir must not be the original baseline grammar directory")
        output.mkdir(parents=True, exist_ok=True)
