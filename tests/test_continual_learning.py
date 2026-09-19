import unittest

from experiments.continual_learning import arrival_order, nested_arrivals, select_replay


def _record(index: int, condition: str) -> dict:
    return {"sample_id": f"s{index}", "condition": condition}


class ContinualLearningTests(unittest.TestCase):
    def test_budgets_are_nested(self):
        records = [_record(index, "6screws" if index < 6 else "5screws") for index in range(12)]
        prefixes = nested_arrivals(records, (2, 5, 10))
        self.assertEqual([item["sample_id"] for item in prefixes[2]], [item["sample_id"] for item in prefixes[5]][:2])
        self.assertEqual([item["sample_id"] for item in prefixes[5]], [item["sample_id"] for item in prefixes[10]][:5])

    def test_orders_and_replay_are_deterministic(self):
        records = [_record(index, "6screws" if index % 2 == 0 else "5screws") for index in range(20)]
        first = arrival_order(records, "random", seed=42)
        second = arrival_order(records, "random", seed=42)
        self.assertEqual([item["sample_id"] for item in first], [item["sample_id"] for item in second])
        memory = select_replay(first, capacity=6, strategy="fixed_capacity_class_balanced", seed=42)
        self.assertEqual(len(memory), 6)
        self.assertEqual({item["condition"] for item in memory}, {"5screws", "6screws"})

    def test_new_class_only_and_oracle_are_explicit(self):
        records = [_record(0, "6screws"), _record(1, "5screws")]
        self.assertEqual({item["condition"] for item in select_replay(records, capacity=50, strategy="new_class_only", seed=1)}, {"5screws"})
        self.assertEqual(len(select_replay(records, capacity=1, strategy="full_pool_oracle", seed=1)), 2)


if __name__ == "__main__":
    unittest.main()
