import argparse
import re
from pathlib import Path
from common import ensure_dir, read_jsonl, write_jsonl


MODULE_KEYWORDS = {
    "ProjectInfo": ["工程名称", "项目名称", "建设地点", "委托单位", "建设单位", "建筑面积", "用地面积", "工程概况"],
    "MetroAsset": ["轨道交通", "地铁", "盾构", "区间", "车站", "出入场线", "埋深"],
    "SpatialRelation": ["控制保护区", "特别保护区", "保护区", "最小净距", "相对位置", "侵入", "上跨", "下穿", "侧穿", "邻近", "毗邻"],
    "ExternalWork": ["外部作业", "基坑", "桩基", "管线", "道路", "施工方案", "基础"],
    "ExcavationWork": ["基坑", "挖深", "开挖", "坑底", "地下车库", "土方"],
    "RetainingSupportSystem": ["支护", "围护", "放坡", "钢板桩", "地下连续墙", "排桩", "支撑"],
    "DewateringWork": ["降水", "井点", "地下水", "承压水", "潜水", "水位"],
    "GeologyHydrology": ["地质", "水文", "土层", "粉土", "粉砂", "淤泥", "地下水"],
    "AssessmentCalculation": ["理论计算", "数值模拟", "MIDAS", "Midas", "Peck", "最大沉降", "水平位移", "倾斜"],
    "MonitoringPlan": ["监测", "报警", "预警", "巡查", "监测频率"],
    "ProtectionMeasures": ["保护措施", "应急", "回填", "减震", "隔振", "加固", "控制措施"],
    "ReviewConclusion": ["结论", "建议", "影响可控", "不满足", "满足"],
}


def detect_section(text, current):
    if re.match(r"^\s*\d+(\.\d+)*\s*[\u4e00-\u9fffA-Za-z].*", text):
        return text
    return current


def modules_for(text):
    modules = [m for m, kws in MODULE_KEYWORDS.items() if any(k in text for k in kws)]
    return modules or ["General"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("texts_dir")
    parser.add_argument("-o", "--output", default="data/chunks")
    args = parser.parse_args()
    ensure_dir(args.output)
    for path in Path(args.texts_dir).glob("*.paragraphs.jsonl"):
        section = "unknown"
        out = []
        for row in read_jsonl(path):
            text = row["text"]
            section = detect_section(text, section)
            for module in modules_for(text):
                out.append({**row, "section": section, "module": module})
        out_path = Path(args.output) / path.name.replace(".paragraphs.jsonl", ".chunks.jsonl")
        write_jsonl(out_path, out)
        print(f"chunked: {path.name}, chunks={len(out)}")


if __name__ == "__main__":
    main()

