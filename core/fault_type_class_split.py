"""Deterministic class roles for fault-configuration open-set experiments.

Class roles are chosen before any sample/group split.  The nine faulty labels
are screw configurations, not verified physical fault mechanisms.  This module
does not inspect features or test outcomes when choosing combinations.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from core.formal_data import CONFIGS


SCHEMA_VERSION = 1
HEALTHY_LABEL = "8screws"
FAULT_LABELS: tuple[str, ...] = tuple(label for label in CONFIGS if label != HEALTHY_LABEL)
Protocol = Literal["A", "B"]


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rotated(indices: tuple[int, ...], offset: int) -> tuple[int, ...]:
    return tuple(sorted((index + offset) % len(FAULT_LABELS) for index in indices))


def _balanced_thirty(n_known_faults: int, seed: int) -> tuple[tuple[int, ...], ...]:
    """Select 30 unique combinations with known-label frequencies differing by <=1.

    Three complete cyclic orbits contribute 27 combinations and exactly
    ``3 * n_known_faults`` appearances per label.  Three shifts of a fourth
    base combination contribute the remaining balanced appearances.  This
    construction avoids a stochastic search whose balance can vary by seed.
    """

    base = tuple(
        sorted(
            residue + 3 * row
            for residue in range(3)
            for row in range(n_known_faults // 3 + (residue < n_known_faults % 3))
        )
    )
    rng = np.random.default_rng(seed)
    offset = int(rng.integers(0, len(FAULT_LABELS)))
    extra = {_rotated(base, offset + shift) for shift in (0, 3, 6)}
    if len(extra) != 3:
        raise AssertionError("balanced block construction did not produce three combinations")
    reserved_orbit = frozenset(_rotated(base, shift) for shift in range(len(FAULT_LABELS)))

    orbit_by_key: dict[tuple[int, ...], frozenset[tuple[int, ...]]] = {}
    for combination in itertools.combinations(range(len(FAULT_LABELS)), n_known_faults):
        orbit = frozenset(_rotated(combination, shift) for shift in range(len(FAULT_LABELS)))
        if len(orbit) != len(FAULT_LABELS) or orbit == reserved_orbit:
            continue
        orbit_by_key[min(orbit)] = orbit
    orbits = [orbit_by_key[key] for key in sorted(orbit_by_key)]
    if len(orbits) < 3:
        raise AssertionError("not enough disjoint cyclic orbits for balanced sampling")
    chosen = rng.choice(len(orbits), size=3, replace=False)
    combinations = set(extra)
    for index in chosen:
        combinations.update(orbits[int(index)])
    if len(combinations) != 30:
        raise AssertionError("balanced sampler did not produce 30 unique combinations")
    return tuple(sorted(combinations))


def generate_known_fault_combinations(
    n_known_faults: int,
    *,
    class_combination_seed: int = 42,
    enumerate_all: bool = False,
) -> tuple[tuple[str, ...], ...]:
    """Enumerate <=30 possibilities, otherwise return 30 balanced choices.

    ``enumerate_all=True`` is the explicit runtime-backed choice for all 126
    N=5 combinations (and all combinations at any other N).
    """

    if not isinstance(n_known_faults, int) or not 1 <= n_known_faults <= len(FAULT_LABELS):
        raise ValueError("n_known_faults must be an integer from 1 through 9")
    if not isinstance(class_combination_seed, int) or class_combination_seed < 0:
        raise ValueError("class_combination_seed must be a nonnegative integer")
    all_indices = tuple(itertools.combinations(range(len(FAULT_LABELS)), n_known_faults))
    selected = (
        all_indices
        if enumerate_all or len(all_indices) <= 30
        else _balanced_thirty(n_known_faults, class_combination_seed)
    )
    return tuple(tuple(FAULT_LABELS[index] for index in combination) for combination in selected)


@dataclass(frozen=True)
class ClassRoleSplit:
    """Immutable known/unknown label roles; sample split seed lives elsewhere."""

    protocol: Protocol
    healthy_label: str
    known_fault_labels: tuple[str, ...]
    unknown_validation_labels: tuple[str, ...]
    unknown_test_labels: tuple[str, ...]
    class_combination_seed: int
    class_combination_id: str
    split_id: str
    checksum: str
    schema_version: int = SCHEMA_VERSION

    @property
    def n_known_faults(self) -> int:
        return len(self.known_fault_labels)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "protocol": self.protocol,
            "healthy_label": self.healthy_label,
            "faulty_label_universe": list(FAULT_LABELS),
            "known_fault_labels": list(self.known_fault_labels),
            "unknown_validation_labels": list(self.unknown_validation_labels),
            "unknown_test_labels": list(self.unknown_test_labels),
            "n_known_faults": self.n_known_faults,
            "class_combination_seed": self.class_combination_seed,
            "class_combination_id": self.class_combination_id,
            "split_id": self.split_id,
            "checksum": self.checksum,
        }


def generate_class_role_splits(
    n_known_faults: int,
    *,
    class_combination_seed: int = 42,
    protocol: Protocol = "A",
    enumerate_all: bool = False,
) -> list[ClassRoleSplit]:
    """Generate strict A or rotated unknown-validation B class-role splits.

    Protocol A puts every held-out faulty configuration only in final test.
    Protocol B rotates one held-out configuration into unknown validation and
    leaves at least one distinct held-out configuration for final test.
    N=9 is the closed-set A baseline with no unknown-positive test class.
    """

    if protocol not in {"A", "B"}:
        raise ValueError("protocol must be 'A' or 'B'")
    if protocol == "B" and n_known_faults >= len(FAULT_LABELS) - 1:
        raise ValueError("protocol B needs at least two held-out faulty labels (N <= 7)")
    combinations = generate_known_fault_combinations(
        n_known_faults,
        class_combination_seed=class_combination_seed,
        enumerate_all=enumerate_all,
    )
    output: list[ClassRoleSplit] = []
    for known in combinations:
        held_out = tuple(label for label in FAULT_LABELS if label not in known)
        combination_id = "combo-" + _digest(
            {
                "schema_version": SCHEMA_VERSION,
                "class_combination_seed": class_combination_seed,
                "known_fault_labels": known,
            }
        )[:16]
        validation_choices: tuple[str | None, ...] = (None,) if protocol == "A" else held_out
        for validation_label in validation_choices:
            unknown_validation = () if validation_label is None else (validation_label,)
            unknown_test = tuple(label for label in held_out if label != validation_label)
            payload = {
                "schema_version": SCHEMA_VERSION,
                "protocol": protocol,
                "healthy_label": HEALTHY_LABEL,
                "faulty_label_universe": FAULT_LABELS,
                "known_fault_labels": known,
                "unknown_validation_labels": unknown_validation,
                "unknown_test_labels": unknown_test,
                "class_combination_seed": class_combination_seed,
                "class_combination_id": combination_id,
            }
            checksum = _digest(payload)
            output.append(
                ClassRoleSplit(
                    protocol=protocol,
                    healthy_label=HEALTHY_LABEL,
                    known_fault_labels=known,
                    unknown_validation_labels=unknown_validation,
                    unknown_test_labels=unknown_test,
                    class_combination_seed=class_combination_seed,
                    class_combination_id=combination_id,
                    split_id=f"roles-v{SCHEMA_VERSION}-{protocol.lower()}-n{n_known_faults}-{checksum[:16]}",
                    checksum=checksum,
                )
            )
    return output


def build_class_registry(
    *,
    dataset_fingerprint: str,
    class_combination_seed: int = 42,
    sample_split_seeds: tuple[int, int, int] = (42, 123, 2026),
    enumerate_n5: bool = False,
) -> dict:
    """Pre-register every class role and three campaign folds before scoring.

    The checksum excludes a wall-clock timestamp so identical inputs produce
    byte-identical registries.  A different selection policy makes a new
    fingerprint and filename; the writer never overwrites changed content.
    """

    if len(dataset_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in dataset_fingerprint):
        raise ValueError("dataset_fingerprint must be a lower-case SHA-256 digest")
    if len(sample_split_seeds) != 3 or len(set(sample_split_seeds)) != 3:
        raise ValueError("exactly three distinct sample-split seeds are required")
    roles = [
        role.to_dict()
        for n_known in range(1, 10)
        for role in generate_class_role_splits(
            n_known,
            class_combination_seed=class_combination_seed,
            protocol="A",
            enumerate_all=enumerate_n5 and n_known == 5,
        )
    ]
    secondary = [
        role.to_dict()
        for role in generate_class_role_splits(
            5,
            class_combination_seed=class_combination_seed,
            protocol="B",
            enumerate_all=enumerate_n5,
        )
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "dataset_fingerprint": dataset_fingerprint,
        "class_combination_seed": class_combination_seed,
        "sample_split_seeds": list(sample_split_seeds),
        "campaign_folds": [
            {"sample_split_seed": sample_split_seeds[i], "fold_index": i}
            for i in range(3)
        ],
        "selection_policy": "all combinations when count <=30; otherwise balanced 30; N=5 all if enumerate_n5=true",
        "enumerate_n5": enumerate_n5,
        "protocol_a": roles,
        "protocol_b_n5": secondary,
    }
    payload["registry_checksum"] = _digest(payload)
    return payload


def write_class_registry(registry: dict, output_root: Path | str) -> Path:
    checksum = registry.get("registry_checksum")
    if not isinstance(checksum, str) or checksum != _digest({k: v for k, v in registry.items() if k != "registry_checksum"}):
        raise ValueError("registry checksum does not match content")
    destination = Path(output_root) / f"class_roles_v{SCHEMA_VERSION}_{checksum[:16]}.json"
    content = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_text(encoding="utf-8") != content:
            raise ValueError(f"immutable registry already exists with different bytes: {destination}")
        return destination
    destination.write_text(content, encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-register fault-configuration class roles")
    parser.add_argument("--dataset-fingerprint", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--class-seed", type=int, default=42)
    parser.add_argument("--sample-seed", type=int, action="append", default=None)
    parser.add_argument("--enumerate-n5", action="store_true")
    args = parser.parse_args()
    registry = build_class_registry(
        dataset_fingerprint=args.dataset_fingerprint,
        class_combination_seed=args.class_seed,
        sample_split_seeds=tuple(args.sample_seed or [42, 123, 2026]),
        enumerate_n5=args.enumerate_n5,
    )
    path = write_class_registry(registry, args.output_root)
    print(json.dumps({"path": str(path), "checksum": registry["registry_checksum"], "protocol_a": len(registry["protocol_a"]), "protocol_b": len(registry["protocol_b_n5"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
