import unittest

from audit_api.reply_writer import _extract_second_point, generate_formal_reply_content


class _FakeAgent:
    def complete_json(self, system, prompt, max_tokens):
        self.system = system
        self.prompt = prompt
        self.max_tokens = max_tokens
        return {
            "lead": "我部原则同意该方案。为确保地铁结构及运营安全，请贵司注意如下事项：",
            "items": [
                "应根据审核意见完善基坑支护和降水方案",
                "施工期间须落实地铁结构变形监测及信息反馈要求",
                "施工图设计和施工方案应按规定履行后续报审程序",
            ],
        }


class _BadToneAgent:
    def complete_json(self, system, prompt, max_tokens):
        return {
            "lead": "当前方案不予通过，存在重大安全风险，需重点复核。",
            "items": ["应补充监测方案。"],
        }


class _FailingAgent:
    def complete_json(self, system, prompt, max_tokens):
        raise RuntimeError("model unavailable")


class ReplyWriterTest(unittest.TestCase):
    def test_generates_formal_reply_from_current_audit_and_historical_style(self):
        agent = _FakeAgent()
        package = {
            "project_facts": [],
            "historical_advice": {
                "source_project": "历史回函A",
                "source_similarity": 0.82,
                "attention_text": "我部原则同意该方案。为确保地铁结构及运营安全，请贵司注意如下事项。",
            },
            "audit_opinions": [
                {
                    "topic": "保护监测",
                    "result": "必须监测",
                    "conclusion": "项目施工期间应实施地铁结构变形监测。",
                    "regulation_clauses": ["7.1.1"],
                }
            ],
        }
        data = {
            "project": {
                "project_name": "太新路泵站及进出水管道改扩建工程",
                "applicant": "南京水务集团有限公司",
                "project_stage": "规划",
                "project_address": "太新路沿线",
                "construction_content": "拟实施泵站及进出水管道改扩建",
                "relative_relationship": "交叉",
            },
            "metro_structure": {
                "metro_line_name": "地铁1号线",
                "structure_method": "盾构",
            },
            "pit": {
                "pit_depth_m": 6.0,
                "minimum_horizontal_clearance_m": 8.4,
            },
        }
        dynamic_audit = {
            "risk_report": {
                "overall_risk_level": "中",
                "overall_conclusion": "有条件通过",
                "findings": [
                    {
                        "title": "监测要求",
                        "risk_level": "中",
                        "judgement": "risk",
                        "analysis": "施工期间需加强地铁结构监测。",
                        "recommendation": "完善监测方案。",
                    }
                ],
            }
        }

        reply = generate_formal_reply_content(package, data, dynamic_audit, agent=agent)

        self.assertEqual(reply["recipient"], "南京水务集团有限公司")
        self.assertIn("太新路泵站及进出水管道改扩建工程", reply["title"])
        self.assertIn("监测", reply["attention_items"][1])
        self.assertEqual(reply["generation_method"], "llm_stage_aware_reply_style_transfer")
        self.assertIn("本次审核结论", agent.prompt)
        self.assertIn("同阶段历史复函第2点样例", agent.prompt)
        self.assertIn("不得逐句照搬到复函第2点", agent.prompt)
        self.assertIn("历史复函只用于学习同阶段语言风格", agent.system)
        self.assertIn("第2点不是审核意见清单", agent.system)
        self.assertIn("规划阶段", agent.system)

    def test_high_risk_without_hard_rejection_keeps_formal_approval_tone(self):
        package = {"project_facts": [], "historical_advice": {}, "audit_opinions": []}
        data = {
            "project": {
                "project_name": "测试项目",
                "applicant": "测试单位",
                "project_stage": "规划",
            },
            "metro_structure": {},
            "pit": {},
        }
        dynamic_audit = {
            "risk_report": {
                "overall_risk_level": "高",
                "overall_conclusion": "需完善保护措施",
                "findings": [{
                    "judgement": "risk",
                    "recommendation": "施工前应完善监测和保护措施。",
                }],
            }
        }

        reply = generate_formal_reply_content(package, data, dynamic_audit, agent=_BadToneAgent())

        self.assertIn("原则同意", reply["attention_lead"])
        self.assertNotIn("不予通过", reply["attention_lead"])
        self.assertNotIn("重大安全风险", reply["attention_lead"])
        self.assertEqual(reply["issuing_organization"], "南京市地下铁道工程建设指挥部")

    def test_construction_stage_uses_construction_closing_and_title(self):
        package = {"project_facts": [], "historical_advice": {}, "audit_opinions": []}
        data = {
            "project": {
                "project_name": "测试施工项目",
                "applicant": "测试单位",
                "project_stage": "施工阶段",
            },
            "metro_structure": {},
            "pit": {},
        }
        dynamic_audit = {
            "risk_report": {
                "overall_risk_level": "中",
                "overall_conclusion": "需完善施工控制措施",
                "findings": [],
            }
        }

        reply = generate_formal_reply_content(package, data, dynamic_audit, agent=_BadToneAgent())

        self.assertIn("施工方案", reply["title"])
        self.assertIn("施工期间地铁设施保护工作人员", reply["closing_requirement"])
        self.assertIn("施工阶段", reply["reply_stage_key"].replace("施工", "施工阶段"))

    def test_first_point_uses_stage_specific_description_style(self):
        package = {"project_facts": [], "historical_advice": {}, "audit_opinions": []}
        dynamic_audit = {"risk_report": {"overall_risk_level": "低", "overall_conclusion": "原则同意", "findings": []}}
        base_data = {
            "project": {
                "project_name": "江心洲污水管线工程",
                "applicant": "南京水务集团有限公司",
                "project_address": "兴隆大街至夹江段",
                "construction_content": "拟新建DN2200污水压力管线",
                "relative_relationship": "交叉",
            },
            "metro_structure": {
                "metro_line_name": "地铁2号线",
                "metro_section_name": "奥体东站~兴隆大街站区间",
                "structure_method": "盾构",
                "buried_depth_m": 12.8,
            },
            "pit": {
                "pit_depth_m": 9.1,
                "minimum_horizontal_clearance_m": 9.0,
                "minimum_vertical_clearance_m": 3.7,
                "support_components": ["围护桩"],
                "dewatering_method": "井点降水",
            },
        }

        plan_data = {
            **base_data,
            "project": {**base_data["project"], "project_stage": "规划阶段"},
        }
        design_data = {
            **base_data,
            "project": {**base_data["project"], "project_stage": "设计阶段"},
        }
        construction_data = {
            **base_data,
            "project": {**base_data["project"], "project_stage": "施工阶段"},
        }

        plan = generate_formal_reply_content(package, plan_data, dynamic_audit, agent=_BadToneAgent())
        design = generate_formal_reply_content(package, design_data, dynamic_audit, agent=_BadToneAgent())
        construction = generate_formal_reply_content(package, construction_data, dynamic_audit, agent=_BadToneAgent())

        self.assertIn("主要建设内容", plan["project_description"])
        self.assertIn("相对关系", plan["project_description"])
        self.assertIn("本次设计方案主要内容", design["project_description"])
        self.assertIn("本次施工内容", construction["project_description"])
        self.assertIn("井点降水", construction["project_description"])

    def test_extracts_only_second_point_from_historical_reply(self):
        text = """
1. 项目主要建设内容为管线迁改，其与地铁结构相对关系详见资料。
2. 鉴于本项目处于规划阶段，请贵司进一步优化规划线位，尽量加大与地铁结构安全净距。后续设计阶段应补充专项保护方案并按程序报审。
（1）须补充安全评估。
（2）须完善监测方案。
3. 根据《南京市轨道交通条例》的规定，后续施工方案应征求我部意见。
"""

        second = _extract_second_point(text)

        self.assertIn("规划线位", second)
        self.assertIn("安全评估", second)
        self.assertNotIn("项目主要建设内容", second)
        self.assertNotIn("南京市轨道交通条例", second)

    def test_fallback_second_point_is_stage_specific_and_not_raw_audit_copy(self):
        package = {"project_facts": [], "historical_advice": {}, "audit_opinions": []}
        dynamic_audit = {
            "risk_report": {
                "overall_risk_level": "高",
                "overall_conclusion": "需补充",
                "findings": [{
                    "judgement": "risk",
                    "recommendation": "立即补充精确到0.001mm的沉降计算并重新判定高风险。",
                }],
            }
        }
        data = {
            "project": {
                "project_name": "测试设计项目",
                "applicant": "测试单位",
                "project_stage": "设计阶段",
            },
            "metro_structure": {},
            "pit": {},
        }

        reply = generate_formal_reply_content(package, data, dynamic_audit, agent=_FailingAgent())

        self.assertEqual(reply["generation_method"], "stage_aware_fallback")
        self.assertTrue(any("设计" in item or "计算分析" in item for item in reply["attention_items"]))
        self.assertFalse(any("0.001mm" in item for item in reply["attention_items"]))


if __name__ == "__main__":
    unittest.main()
