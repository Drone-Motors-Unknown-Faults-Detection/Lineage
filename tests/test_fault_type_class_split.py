"""Research-semantic checks for deterministic fault-configuration class roles."""

from __future__ import annotations

import itertools
import math
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from core.fault_type_class_split import (
    FAULT_LABELS,
    HEALTHY_LABEL,
    build_class_registry,
    generate_class_role_splits,
    generate_known_fault_combinations,
    write_class_registry,
)


class FaultTypeClassSplitTests(unittest.TestCase):
    def test_all_known_counts_are_complete_or_balanced(self) -> None:
        self.assertEqual(len(FAULT_LABELS), 9)
        self.assertNotIn(HEALTHY_LABEL, FAULT_LABELS)
        for n_known in range(1, 10):
            with self.subTest(n_known=n_known):
                combinations = generate_known_fault_combinations(n_known, class_combination_seed=17)
                total_possible = math.comb(9, n_known)
                self.assertEqual(len(combinations), min(total_possible, 30))
                self.assertEqual(len(set(combinations)), len(combinations))
                self.assertTrue(all(len(known) == n_known for known in combinations))
                self.assertTrue(all(set(known) <= set(FAULT_LABELS) for known in combinations))
                if total_possible <= 30:
                    self.assertEqual(
                        set(combinations),
                        set(itertools.combinations(FAULT_LABELS, n_known)),
                    )
                else:
                    counts = Counter(label for known in combinations for label in known)
                    self.assertEqual(sum(counts.values()), 30 * n_known)
                    self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_n5_strict_roles_are_five_known_four_unseen(self) -> None:
        roles = generate_class_role_splits(5, class_combination_seed=123, protocol="A")
        self.assertEqual(len(roles), 30)
        for role in roles:
            self.assertEqual(role.healthy_label, "8screws")
            self.assertEqual(len(role.known_fault_labels), 5)
            self.assertEqual(len(role.unknown_test_labels), 4)
            self.assertEqual(role.unknown_validation_labels, ())
            self.assertEqual(set(role.known_fault_labels) | set(role.unknown_test_labels), set(FAULT_LABELS))
            self.assertFalse(set(role.known_fault_labels) & set(role.unknown_test_labels))

    def test_protocol_b_rotates_unknown_validation_without_overlap(self) -> None:
        roles_a = generate_class_role_splits(5, class_combination_seed=9, protocol="A")
        roles_b = generate_class_role_splits(5, class_combination_seed=9, protocol="B")
        self.assertEqual(len(roles_b), 30 * 4)
        for role_a in roles_a:
            matching = [role for role in roles_b if role.class_combination_id == role_a.class_combination_id]
            self.assertEqual(len(matching), 4)
            self.assertEqual(
                {role.unknown_validation_labels[0] for role in matching},
                set(role_a.unknown_test_labels),
            )
            for role in matching:
                self.assertEqual(len(role.unknown_validation_labels), 1)
                self.assertEqual(len(role.unknown_test_labels), 3)
                self.assertFalse(set(role.known_fault_labels) & set(role.unknown_validation_labels))
                self.assertFalse(set(role.known_fault_labels) & set(role.unknown_test_labels))
                self.assertFalse(set(role.unknown_validation_labels) & set(role.unknown_test_labels))

    def test_seeds_and_checksums_are_stable_without_sample_seed(self) -> None:
        first = generate_class_role_splits(5, class_combination_seed=42)
        again = generate_class_role_splits(5, class_combination_seed=42)
        other = generate_class_role_splits(5, class_combination_seed=43)
        self.assertEqual([role.to_dict() for role in first], [role.to_dict() for role in again])
        self.assertNotEqual([role.checksum for role in first], [role.checksum for role in other])
        self.assertEqual(len({role.split_id for role in first}), 30)
        self.assertTrue(all(len(role.checksum) == 64 for role in first))
        self.assertNotIn("sample_split_seed", first[0].to_dict())
        self.assertNotIn("created_at", first[0].to_dict())
        a = first[0]
        b = next(role for role in generate_class_role_splits(5, class_combination_seed=42, protocol="B")
                 if role.class_combination_id == a.class_combination_id)
        self.assertNotEqual(a.checksum, b.checksum)
        self.assertEqual(a.class_combination_id, b.class_combination_id)

    def test_nine_known_is_closed_set_and_full_n5_enumeration_is_available(self) -> None:
        closed = generate_class_role_splits(9, protocol="A")
        self.assertEqual(len(closed), 1)
        self.assertEqual(set(closed[0].known_fault_labels), set(FAULT_LABELS))
        self.assertEqual(closed[0].unknown_test_labels, ())
        self.assertEqual(closed[0].unknown_validation_labels, ())
        self.assertEqual(len(generate_class_role_splits(5, enumerate_all=True)), 126)
        with self.assertRaisesRegex(ValueError, "at least two held-out"):
            generate_class_role_splits(8, protocol="B")
        with self.assertRaisesRegex(ValueError, "at least two held-out"):
            generate_class_role_splits(9, protocol="B")

    def test_invalid_protocol_and_range_fail_before_manifest_creation(self) -> None:
        with self.assertRaisesRegex(ValueError, "protocol"):
            generate_class_role_splits(5, protocol="C")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "1 through 9"):
            generate_known_fault_combinations(0)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            generate_known_fault_combinations(5, class_combination_seed=-1)

    def test_registry_is_preregistered_and_immutable(self) -> None:
        registry = build_class_registry(dataset_fingerprint="a" * 64)
        self.assertEqual(len(registry["protocol_a"]), 199)
        self.assertEqual(len(registry["protocol_b_n5"]), 120)
        self.assertEqual([fold["fold_index"] for fold in registry["campaign_folds"]], [0, 1, 2])
        self.assertEqual(registry, build_class_registry(dataset_fingerprint="a" * 64))
        with tempfile.TemporaryDirectory() as temp:
            path = write_class_registry(registry, Path(temp))
            self.assertEqual(path, write_class_registry(registry, Path(temp)))
            altered = dict(registry)
            altered["enumerate_n5"] = True
            with self.assertRaisesRegex(ValueError, "checksum"):
                write_class_registry(altered, Path(temp))


if __name__ == "__main__":
    unittest.main()
