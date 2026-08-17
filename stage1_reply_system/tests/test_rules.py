import copy
import json
import unittest
from pathlib import Path

from stage1_reply_system.rules.assessment import evaluate_safety_assessment_need
from stage1_reply_system.rules.engine import evaluate_project
from stage1_reply_system.rules.impact_level import evaluate_impact_level
from stage1_reply_system.rules.monitoring import evaluate_monitoring_need
from stage1_reply_system.rules.setback import evaluate_setback_distance


ROOT = Path(__file__).resolve().parents[1]


def demo_data() -> dict:
    return json.loads((ROOT / "examples" / "synthetic_calculation.example.json").read_text(encoding="utf-8"))


class SetbackTests(unittest.TestCase):
    def test_retaining_pile_boundary_passes(self):
        data = demo_data()
        data["pit"]["minimum_horizontal_clearance_m"] = 7.0
        result = evaluate_setback_distance(data)
        self.assertEqual(result["result"], "满足常规净距控制值")

    def test_retaining_pile_below_boundary_fails(self):
        data = demo_data()
        data["pit"]["minimum_horizontal_clearance_m"] = 6.99
        result = evaluate_setback_distance(data)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["requires_special_study"])

    def test_above_pit_uses_one_d_and_four_metre_minimum(self):
        data = demo_data()
        data["pit"]["support_components"] = ["上方基坑"]
        data["pit"]["minimum_vertical_clearance_m"] = 6.0
        result = evaluate_setback_distance(data)
        self.assertEqual(result["control_items"][0]["applied_limit_m"], 6.0)
        self.assertEqual(result["status"], "pass")

    def test_soft_soil_does_not_invent_numeric_multiplier(self):
        data = demo_data()
        data["geology"]["is_soft_soil"] = True
        result = evaluate_setback_distance(data)
        self.assertEqual(result["status"], "review")
        self.assertIn("从严复核", result["result"])


class ImpactLevelTests(unittest.TestCase):
    def test_shield_approach_boundary(self):
        data = demo_data()
        data["pit"]["minimum_horizontal_clearance_m"] = 6.0
        result = evaluate_impact_level(data)
        self.assertEqual(result["approach_degree"], "非常接近")

    def test_matrix_result_for_demo(self):
        result = evaluate_impact_level(demo_data())
        self.assertEqual(result["approach_degree"], "接近")
        self.assertEqual(result["engineering_influence_zone"], "B")
        self.assertEqual(result["final_impact_level"], "一级")

    def test_multiple_raise_reasons_raise_only_once(self):
        data = demo_data()
        data["pit"]["confined_water_drawdown"] = True
        data["geology"]["is_complex_geology_or_hydrology"] = True
        result = evaluate_impact_level(data)
        self.assertEqual(result["initial_impact_level"], "一级")
        self.assertEqual(result["final_impact_level"], "特级")
        self.assertEqual(len(result["mandatory_level_raise_reasons"]), 2)

    def test_large_pit_discretionary_raise_is_traceable(self):
        data = demo_data()
        data["pit"]["pit_length_m"] = 101.0
        result = evaluate_impact_level(data)
        self.assertEqual(result["status"], "review")
        self.assertTrue(result["discretionary_level_raise_reasons"])


class RequirementTests(unittest.TestCase):
    def test_major_work_requires_assessment(self):
        data = demo_data()
        impact = evaluate_impact_level(data)
        result = evaluate_safety_assessment_need(data, impact)
        self.assertEqual(result["result"], "必须进行")

    def test_control_zone_always_requires_monitoring(self):
        data = demo_data()
        impact = {"final_impact_level": "四级", "is_major_impact_work": False}
        result = evaluate_monitoring_need(data, impact)
        self.assertEqual(result["result"], "必须监测")

    def test_first_grade_recommends_automatic_monitoring(self):
        data = demo_data()
        impact = evaluate_impact_level(data)
        result = evaluate_monitoring_need(data, impact)
        self.assertEqual(result["result"], "必须监测且建议自动化")

    def test_outside_control_zone_does_not_trigger(self):
        data = demo_data()
        data["review_context"]["is_in_control_protection_zone"] = False
        impact = evaluate_impact_level(data)
        assessment = evaluate_safety_assessment_need(data, impact)
        monitoring = evaluate_monitoring_need(data, impact)
        self.assertEqual(assessment["result"], "通常不要求")
        self.assertEqual(monitoring["result"], "通常不触发")


class EndToEndTests(unittest.TestCase):
    def test_engine_summary_and_traceability(self):
        result = evaluate_project(copy.deepcopy(demo_data()))
        self.assertEqual(result["summary"]["setback_distance"], "满足常规净距控制值")
        self.assertEqual(result["summary"]["impact_level"], "一级")
        self.assertEqual(result["summary"]["safety_assessment"], "必须进行")
        self.assertEqual(result["summary"]["protective_monitoring"], "必须监测且建议自动化")
        for decision in result["decisions"].values():
            self.assertTrue(decision["function"])
            self.assertTrue(decision["regulation_clauses"])


if __name__ == "__main__":
    unittest.main()
