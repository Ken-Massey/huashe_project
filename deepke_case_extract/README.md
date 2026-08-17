# DeepKE 案例属性抽取工程

本工程用于从安全影响评价报告、方案文件、施工方案等文档中，抽取《案例属性描述(1).docx》中的案例属性，形成可追溯、可复核、可进入规程审核模块的结构化案例 JSON。

当前目标是：

1. 从属性描述文件中整理字段 Schema。
2. 从方案文档中抽取项目、轨道交通、空间关系、基坑工程、支护降水、地质水文、计算评估、监测保护等属性。
3. 输出带有 `source_text`、`source_page`、`source_paragraph`、`confidence` 的结构化 JSON。
4. 支持两种抽取路线：
   - 规则抽取路线：当前可直接运行，用于快速得到第一版结果。
   - DeepKE-LLM/OneKE 路线：把分段文本和 Schema 送入 OneKE，由大模型抽取属性。

## 一、目录结构

```text
deepke_case_extract/
├─ data/
│  ├─ raw_docs/              # 原始方案文档，放 docx/pdf/txt
│  ├─ texts/                 # 解析后的纯文本和段落 JSONL
│  ├─ chunks/                # 按章节/模块切分后的文本
│  └─ schema/
│     └─ case_schema.json    # 从案例属性描述文件整理出的属性 Schema
│
├─ outputs/
│  ├─ deepke_inputs/         # DeepKE/LLM 通用输入
│  ├─ oneke_inputs/          # OneKE 推理输入
│  ├─ oneke_outputs/         # OneKE 推理输出，首次运行前可手动创建
│  ├─ raw_extract/           # 原始抽取结果
│  ├─ normalized/            # 标准化后的抽取结果
│  └─ final_json/            # 最终案例 JSON
│
├─ prompts/
│  ├─ project_info_prompt.txt
│  ├─ metro_asset_prompt.txt
│  ├─ spatial_relation_prompt.txt
│  ├─ external_work_prompt.txt
│  └─ assessment_prompt.txt
│
└─ scripts/
   ├─ 00_build_schema.py
   ├─ 01_doc_to_text.py
   ├─ 02_text_chunk.py
   ├─ 03_build_deepke_inputs.py
   ├─ 04_rule_extract.py
   ├─ 05_normalize.py
   ├─ 06_merge_result.py
   ├─ 07_prepare_oneke_input.py
   └─ common.py
```

## 二、输入文件准备

把要抽取的方案文件放入：

```text
D:\桌面\华设项目\deepke_case_extract\data\raw_docs
```

当前已经放入的 4 个案例是：

```text
华贸安全影响评价报告20200322.pdf
南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.docx
未来出行产业园基坑工程安全影响评价报告20220908（含专家意见回复）(1)(2).pdf
银城中央门NO.2019G38地块安全影响评价报告20200210y正式版.pdf
```

支持格式：

```text
.docx
.pdf
.txt
```

注意：PDF 必须是“可复制文字”的文本型 PDF。如果是扫描件图片 PDF，需要先 OCR 成可复制文字的 PDF 或 txt，否则程序无法稳定提取文本。

## 三、Python 环境

推荐使用 Codex 自带 Python 做文档解析，因为它已经包含 PDF 解析库：

```powershell
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

如果你的机器上路径不同，可以用自己的 Python，但需要具备：

```text
pdfplumber
python-docx 或脚本内置 docx 解析能力
```

本工程的 docx 解析主要使用内置 XML 方式，PDF 解析使用 `pdfplumber`。

## 四、完整流程总览

整体流程如下：

```text
案例属性描述(1).docx
    ↓
00_build_schema.py
    ↓
data/schema/case_schema.json

方案 docx/pdf/txt
    ↓
01_doc_to_text.py
    ↓
data/texts/*.txt
data/texts/*.paragraphs.jsonl
    ↓
02_text_chunk.py
    ↓
data/chunks/*.chunks.jsonl
    ↓
03_build_deepke_inputs.py
    ↓
outputs/deepke_inputs/*.deepke_input.jsonl
    ↓
07_prepare_oneke_input.py
    ↓
outputs/oneke_inputs/*.oneke_input.jsonl
    ↓
DeepKE-LLM/OneKE 推理
    ↓
outputs/oneke_outputs/*.oneke_output.jsonl
    ↓
解析为 raw_extract
    ↓
05_normalize.py
    ↓
outputs/normalized/*.normalized.jsonl
    ↓
06_merge_result.py
    ↓
outputs/final_json/*.case.json
```

当前工程也提供一条“规则兜底路线”：

```text
data/chunks/*.chunks.jsonl
    ↓
04_rule_extract.py
    ↓
outputs/raw_extract/*.raw_extract.jsonl
```

这条路线不依赖 OneKE 模型，适合先快速得到第一版结果。

## 五、步骤 1：从属性描述文件生成 Schema

属性描述文件位置：

```text
D:\桌面\华设项目\案例属性描述(1).docx
```

执行：

```powershell
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $py scripts\00_build_schema.py "..\案例属性描述(1).docx" -o data\schema\case_schema.json
```

输出：

```text
data/schema/case_schema.json
```

这个文件是后续抽取的字段字典，包含模块、属性名、属性说明等信息。

建议第一阶段不要一次抽 421 个字段，而是先抽核心字段，例如：

```text
项目名称
建设地点
建设单位
案例类型
外部作业类型
基坑深度
基坑尺寸
支护形式
降水方式
轨道交通线路
轨道交通区间
轨道交通设施类型
是否进入控制保护区
是否进入特别保护区
最小净距
相对位置关系
保护措施
评估结论
```

原因是：421 个属性中有些字段在单个方案里并不会出现，有些需要计算或人工判断。先把核心字段跑通，再逐步扩展，效果更稳。

## 六、步骤 2：将方案文档转成纯文本

执行：

```powershell
& $py scripts\01_doc_to_text.py data\raw_docs -o data\texts
```

输出两类文件：

```text
data/texts/案例名.txt
data/texts/案例名.paragraphs.jsonl
```

其中：

```text
.txt
```

是完整纯文本。

```text
.paragraphs.jsonl
```

是按段落保存的结构化文本，每一行包含：

```json
{
  "doc_id": "案例名",
  "source_file": "原始文件路径",
  "source_page": 1,
  "source_paragraph": 1,
  "text": "段落文本"
}
```

`source_page` 对 PDF 很重要，后续人工复核时可以回到原文页码查证。

## 七、步骤 3：按章节和模块切分文本

执行：

```powershell
& $py scripts\02_text_chunk.py data\texts -o data\chunks
```

输出：

```text
data/chunks/*.chunks.jsonl
```

每一行是一个文本块，包含：

```json
{
  "doc_id": "案例名",
  "module": "ProjectInfo",
  "source_page": 1,
  "source_paragraph": 10,
  "source_section": "工程概况",
  "text": "文本块"
}
```

当前模块大致包括：

```text
ProjectInfo              项目基本信息
MetroAsset               轨道交通设施
SpatialRelation          与轨道交通空间关系
ExternalWork             外部作业
ExcavationWork           基坑工程
RetainingSupportSystem   围护支护
DewateringWork           降水工程
GeologyHydrology         地质水文
AssessmentCalculation    计算评估
MonitoringPlan           监测方案
ProtectionMeasures       保护措施
ReviewConclusion         评估结论/专家意见
```

切分的目的不是把文档切碎，而是让每个模块只处理相关文本，降低误抽和漏抽。

## 八、步骤 4：生成 DeepKE 通用输入

执行：

```powershell
& $py scripts\03_build_deepke_inputs.py data\chunks data\schema\case_schema.json -o outputs\deepke_inputs
```

输出：

```text
outputs/deepke_inputs/*.deepke_input.jsonl
```

每一行结构类似：

```json
{
  "doc_id": "南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624",
  "module": "ExternalWork",
  "instruction": "你是外部作业与基坑工程抽取专家...",
  "schema": {
    "external_work_type": "外部作业类型",
    "case_type": "案例类型/外部作业类别"
  },
  "input": "地下车库基坑挖深约4.15m，基坑采用轻型井点降水...",
  "source_file": "data\\raw_docs\\xxx.pdf",
  "source_page": 12,
  "source_paragraph": 85,
  "source_section": "工程概况"
}
```

这个文件是“通用 DeepKE-LLM 输入”，包含：

```text
instruction  抽取任务说明
schema       要抽取的字段
input        文档原文片段
source_*     原文追溯信息
```

## 九、步骤 5：生成 OneKE 输入

OneKE 的 `inference.py` 读取 JSONL，每一行至少需要：

```text
instruction
input
output
```

因此需要把 `schema` 合并进 `instruction`。

执行：

```powershell
& $py scripts\07_prepare_oneke_input.py outputs\deepke_inputs -o outputs\oneke_inputs
```

输出：

```text
outputs/oneke_inputs/*.oneke_input.jsonl
```

每一行结构类似：

```json
{
  "instruction": "你是外部作业与基坑工程抽取专家...请严格根据下面的属性 Schema 从 input 中抽取信息...",
  "input": "地下车库基坑挖深约4.15m，基坑采用轻型井点降水...",
  "output": "test",
  "doc_id": "南通R18032...",
  "module": "ExternalWork",
  "source_page": 12,
  "source_paragraph": 85,
  "source_section": "工程概况"
}
```

这就是可以送入 OneKE 的输入文件。

## 十、步骤 6：进入 DeepKE 环境

DeepKE 安装目录：

```text
D:\DeepKE\2026-06-13\github-github-c-users-28030-codex
```

进入环境：

```powershell
cd D:\DeepKE\2026-06-13\github-github-c-users-28030-codex\outputs
.\enter-deepke.ps1
```

进入 OneKE 推理目录：

```powershell
cd D:\DeepKE\2026-06-13\github-github-c-users-28030-codex\work\DeepKE\example\llm\InstructKGC
```

确认 Python 能工作：

```powershell
python -c "import torch; print(torch.__version__)"
```

如果能输出版本号，说明 DeepKE 环境已进入。

## 十一、步骤 7：准备 OneKE 模型

OneKE 需要模型文件，例如放在：

```text
D:\models\OneKE
```

推理命令中对应：

```text
--model_name_or_path "D:\models\OneKE"
```

OneKE 模型来源通常是：

```text
zjunlp/OneKE
```

注意：

1. OneKE 是大模型，官方建议至少约 20GB 显存。
2. 如果没有 GPU，CPU 可以尝试，但会非常慢。
3. 如果显存不足，可以使用 `--bits 4` 量化。
4. 如果 `bitsandbytes`、`transformers`、`datasets` 缺失，需要先安装 OneKE 推理依赖。

## 十二、步骤 8：调用 OneKE 抽取一个案例

先创建输出目录：

```powershell
mkdir D:\桌面\华设项目\deepke_case_extract\outputs\oneke_outputs
mkdir D:\桌面\华设项目\deepke_case_extract\outputs\oneke_tmp
```

建议先只跑南通 R18032 一个案例测试：

```powershell
python src\inference.py `
  --stage sft `
  --model_name_or_path "D:\models\OneKE" `
  --model_name llama `
  --template llama2_zh `
  --do_predict `
  --input_file "D:\桌面\华设项目\deepke_case_extract\outputs\oneke_inputs\南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.oneke_input.jsonl" `
  --output_file "D:\桌面\华设项目\deepke_case_extract\outputs\oneke_outputs\南通R18032.oneke_output.jsonl" `
  --output_dir "D:\桌面\华设项目\deepke_case_extract\outputs\oneke_tmp" `
  --predict_with_generate `
  --cutoff_len 2048 `
  --max_new_tokens 512 `
  --bits 4
```

输出：

```text
D:\桌面\华设项目\deepke_case_extract\outputs\oneke_outputs\南通R18032.oneke_output.jsonl
```

输出文件中每一行会保留原始输入，并新增：

```json
{
  "output": "{\"pit_depth\":\"4.15m\",\"dewatering_type\":\"轻型井点降水\"}"
}
```

`output` 字段就是 OneKE 的抽取结果。

## 十三、步骤 9：四个案例分别送入 OneKE

输入文件都在：

```text
D:\桌面\华设项目\deepke_case_extract\outputs\oneke_inputs
```

每个案例一个输入文件：

```text
华贸安全影响评价报告20200322.oneke_input.jsonl
南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.oneke_input.jsonl
未来出行产业园基坑工程安全影响评价报告20220908（含专家意见回复）(1)(2).oneke_input.jsonl
银城中央门NO.2019G38地块安全影响评价报告20200210y正式版.oneke_input.jsonl
```

每跑一个案例，把命令里的：

```text
--input_file
--output_file
```

换成对应文件即可。

建议输出命名为：

```text
outputs/oneke_outputs/华贸.oneke_output.jsonl
outputs/oneke_outputs/南通R18032.oneke_output.jsonl
outputs/oneke_outputs/未来出行产业园.oneke_output.jsonl
outputs/oneke_outputs/银城中央门.oneke_output.jsonl
```

## 十四、步骤 10：如果暂时跑不动 OneKE，使用规则兜底抽取

如果你的电脑暂时没有足够显存，或者 OneKE 模型还没有下载，可以先运行规则抽取：

```powershell
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $py scripts\04_rule_extract.py data\chunks -o outputs\raw_extract
```

输出：

```text
outputs/raw_extract/*.raw_extract.jsonl
```

规则抽取适合先抽这些字段：

```text
project_name
project_location
construction_unit
total_land_area
total_building_area
underground_area
metro_line_name
metro_section_name
metro_asset_type
metro_structure_method
metro_buried_depth
relation_type
relative_position
minimum_horizontal_clearance
minimum_vertical_clearance
is_in_control_protection_zone
is_in_special_protection_zone
external_work_type
pit_depth
pit_size
support_type
dewatering_type
soil_layer
groundwater_type
calculation_method
software_name
max_settlement
max_horizontal_displacement
monitoring_required
protection_measures
overall_conclusion
final_review_opinion
```

规则抽取的好处是快、稳定、可解释；缺点是覆盖不了所有 421 个属性。

## 十五、步骤 11：标准化抽取结果

无论结果来自 OneKE，还是来自规则兜底，最终都需要进入标准化。

如果使用规则抽取，直接执行：

```powershell
& $py scripts\05_normalize.py outputs\raw_extract -o outputs\normalized
```

输出：

```text
outputs/normalized/*.normalized.jsonl
```

标准化会处理：

```text
单位统一，例如 m、mm、m2、平方米
布尔值统一，例如 true/false
作业类型统一，例如 基坑工程、桩基工程、道路工程
保护区判断统一，例如 是否进入控制保护区、是否进入特别保护区
```

如果使用 OneKE，需要先把 `outputs/oneke_outputs/*.oneke_output.jsonl` 解析成与 `raw_extract` 相同结构的 JSONL，再运行 `05_normalize.py`。

raw_extract 推荐结构如下：

```json
{
  "doc_id": "案例名",
  "module": "ExternalWork",
  "field_name": "pit_depth",
  "field_value": "4.15m",
  "source_file": "原文文件",
  "source_page": 12,
  "source_paragraph": 85,
  "source_section": "工程概况",
  "source_text": "地下车库基坑挖深约4.15m...",
  "confidence": 0.85,
  "extraction_method": "oneke"
}
```

## 十六、步骤 12：合并成最终案例 JSON

执行：

```powershell
& $py scripts\06_merge_result.py outputs\normalized -o outputs\final_json
```

输出：

```text
outputs/final_json/*.case.json
```

每个方案文件生成一个最终案例 JSON。

例如：

```text
outputs/final_json/南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.case.json
```

最终 JSON 结构：

```json
{
  "doc_id": "案例名",
  "attributes": {
    "project_name": "中海·R18032地块项目",
    "pit_depth": "4.15m",
    "metro_line_name": "1号线"
  },
  "field_detail": {
    "pit_depth": {
      "value": "4.15m",
      "module": "ExternalWork",
      "source_page": 8,
      "source_paragraph": 46,
      "source_text": "地下车库基坑挖深约4.15m...",
      "confidence": 0.88,
      "extraction_method": "rule"
    }
  },
  "evidence": [],
  "manual_review_required": [],
  "rule_check_payload": {}
}
```

字段说明：

```text
attributes
```

合并后的案例属性，是最主要的结果。

```text
field_detail
```

每个字段的详细来源，包括页码、段落、原文、置信度。

```text
evidence
```

所有候选证据，不只保留最终值。

```text
manual_review_required
```

置信度较低、需要人工复核的字段。

```text
rule_check_payload
```

后续送入技术规程审核模块的关键字段。

## 十七、建议的人工复核方法

打开最终 JSON：

```text
outputs/final_json/*.case.json
```

优先检查：

```text
manual_review_required
```

然后检查关键字段：

```text
project_name
project_location
construction_unit
metro_line_name
metro_section_name
metro_asset_type
pit_depth
support_type
dewatering_type
minimum_horizontal_clearance
minimum_vertical_clearance
is_in_control_protection_zone
is_in_special_protection_zone
overall_conclusion
```

复核时根据：

```text
source_page
source_paragraph
source_text
```

回到原报告查证。

如果字段值正确，但格式不统一，可以在 `05_normalize.py` 中增加标准化规则。

如果字段经常漏抽，可以在：

```text
prompts/*.txt
scripts/04_rule_extract.py
scripts/03_build_deepke_inputs.py
```

中扩展字段、关键词或提示词。

## 十八、当前四个案例已生成的结果

当前已经生成：

```text
outputs/final_json/华贸安全影响评价报告20200322.case.json
outputs/final_json/南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.case.json
outputs/final_json/未来出行产业园基坑工程安全影响评价报告20220908（含专家意见回复）(1)(2).case.json
outputs/final_json/银城中央门NO.2019G38地块安全影响评价报告20200210y正式版.case.json
```

其中南通 R18032 案例已抽取出一批核心字段，例如：

```json
{
  "project_name": "中海·R18032地块项目",
  "project_location": "南通市开发区新开北路以东，源兴路以北",
  "construction_unit": "南通市中海海富房地产开发有限公司",
  "metro_line_name": "1号线",
  "metro_section_name": "小海停车场出入场线盾构区间",
  "metro_asset_type": "盾构区间",
  "pit_depth": "4.15m",
  "support_type": "1：1放坡的围护结构形式，基坑采用轻型井点降水",
  "dewatering_type": "轻型井点进行坑内浅层潜水降水，降水至坑底1.0m方可开挖",
  "minimum_horizontal_clearance": "20m",
  "is_in_control_protection_zone": true,
  "is_in_special_protection_zone": true
}
```

## 十九、常见问题

### 1. README 或终端显示乱码怎么办？

文件本身按 UTF-8 保存。PowerShell 显示乱码时，可以先执行：

```powershell
chcp 65001
```

或者用 VS Code / 记事本打开 README。

### 2. PDF 解析出来为空怎么办？

大概率是扫描版 PDF。需要先 OCR。

可以用 Adobe Acrobat、WPS、ABBYY 或其他 OCR 工具，将 PDF 转成可复制文字的 PDF 或 txt。

### 3. OneKE 报显存不足怎么办？

可以先尝试：

```text
--bits 4
```

或者减少：

```text
--cutoff_len
--max_new_tokens
```

例如：

```text
--cutoff_len 1024
--max_new_tokens 256
```

如果仍然不行，先使用 `04_rule_extract.py` 规则路线。

### 4. OneKE 输出不是 JSON 怎么办？

说明模型没有严格遵循提示词。处理方法：

1. 在 prompt 中强调“只输出 JSON”。
2. 缩短 input 文本。
3. 减少一次抽取的字段数量。
4. 后处理时只截取第一个 `{...}` JSON 片段。

### 5. 为什么不能一次稳定抽完 421 个属性？

原因有三个：

1. 不是每个报告都包含 421 个属性。
2. 有些属性需要由多处文本综合判断。
3. 有些属性不是原文直接给出，而是需要计算或按规程判断。

建议策略：

```text
第一阶段：抽核心字段 30-60 个
第二阶段：按模块扩展到 100-150 个
第三阶段：结合规程和人工复核扩展到 421 个
```

## 二十、推荐工作方式

每新增一个案例，按以下顺序做：

```powershell
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $py scripts\00_build_schema.py "..\案例属性描述(1).docx" -o data\schema\case_schema.json
& $py scripts\01_doc_to_text.py data\raw_docs -o data\texts
& $py scripts\02_text_chunk.py data\texts -o data\chunks
& $py scripts\03_build_deepke_inputs.py data\chunks data\schema\case_schema.json -o outputs\deepke_inputs
& $py scripts\07_prepare_oneke_input.py outputs\deepke_inputs -o outputs\oneke_inputs
```

如果使用规则抽取：

```powershell
& $py scripts\04_rule_extract.py data\chunks -o outputs\raw_extract
& $py scripts\05_normalize.py outputs\raw_extract -o outputs\normalized
& $py scripts\06_merge_result.py outputs\normalized -o outputs\final_json
```

如果使用 OneKE：

```text
outputs/oneke_inputs/*.oneke_input.jsonl
    ↓
DeepKE example/llm/InstructKGC/src/inference.py
    ↓
outputs/oneke_outputs/*.oneke_output.jsonl
    ↓
解析成 outputs/raw_extract/*.raw_extract.jsonl
    ↓
05_normalize.py
    ↓
06_merge_result.py
```

最终以：

```text
outputs/final_json/*.case.json
```

作为案例库入库、人工复核和规程审核模块的输入。

## 二十一、从零开始完整操作步骤（可直接复制）

本节是最推荐照着执行的版本。每次新增或修改案例后，按下面顺序运行即可。

### 1. 打开 PowerShell 并进入工程目录

```powershell
chcp 65001
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

说明：

```text
chcp 65001
```

用于减少中文显示乱码。

```text
$py
```

是本工程推荐使用的 Python 路径。

### 2. 放入原始方案文件

把要处理的方案文件放到：

```text
D:\桌面\华设项目\deepke_case_extract\data\raw_docs
```

支持：

```text
docx
pdf
txt
```

如果 PDF 是扫描图片版，需要先 OCR。

### 3. 从属性描述文档生成字段 Schema

```powershell
& $py scripts\00_build_schema.py "..\案例属性描述(1).docx" -o data\schema\case_schema.json
```

输出：

```text
data\schema\case_schema.json
```

这个文件就是从《案例属性描述(1).docx》中整理出来的属性模板。

### 4. 将方案文件转成纯文本

```powershell
& $py scripts\01_doc_to_text.py data\raw_docs -o data\texts
```

输出：

```text
data\texts\*.txt
data\texts\*.paragraphs.jsonl
```

其中：

```text
*.txt
```

是完整文本。

```text
*.paragraphs.jsonl
```

是带页码、段落号的结构化文本。

### 5. 按章节和模块切分文本

```powershell
& $py scripts\02_text_chunk.py data\texts -o data\chunks
```

输出：

```text
data\chunks\*.chunks.jsonl
```

这一步会把文本分成项目概况、轨道交通设施、空间关系、基坑工程、支护降水、监测保护、评估结论等模块。

### 6. 生成 DeepKE/LLM 输入

```powershell
& $py scripts\03_build_deepke_inputs.py data\chunks data\schema\case_schema.json -o outputs\deepke_inputs
```

输出：

```text
outputs\deepke_inputs\*.deepke_input.jsonl
```

这是 DeepKE-LLM 通用输入。

### 7. 生成 OneKE 输入

```powershell
& $py scripts\07_prepare_oneke_input.py outputs\deepke_inputs -o outputs\oneke_inputs
```

输出：

```text
outputs\oneke_inputs\*.oneke_input.jsonl
```

如果后面要接 OneKE，就使用这个文件夹里的输入。

### 8. 使用规则抽取生成第一版属性

如果暂时不跑 OneKE，直接用规则兜底抽取：

```powershell
& $py scripts\04_rule_extract.py data\chunks -o outputs\raw_extract
```

输出：

```text
outputs\raw_extract\*.raw_extract.jsonl
```

### 9. 标准化属性值

```powershell
& $py scripts\05_normalize.py outputs\raw_extract -o outputs\normalized
```

输出：

```text
outputs\normalized\*.normalized.jsonl
```

这一步会统一单位、布尔值、作业类型等。

### 10. 合并成完整版案例 JSON

```powershell
& $py scripts\06_merge_result.py outputs\normalized -o outputs\final_json --schema data\schema\case_schema.json
```

输出：

```text
outputs\final_json\*.case.json
```

这是完整版案例属性 JSON。

它的特点：

```text
attributes
包含 Schema 中的全部属性字段，未抽取到的字段为 null。

field_detail
记录每个字段的来源页码、段落、原文和置信度。

evidence
保留所有候选证据。

rule_check_payload
给规程审核程序使用的核心字段。
```

## 二十二、生成清爽版规则输入 JSON

如果觉得完整版太复杂，可以生成清爽版。

```powershell
& $py scripts\08_build_rule_json.py outputs\final_json -o outputs\rule_json
```

输出：

```text
outputs\rule_json\*.rule.json
```

清爽版结构是：

```json
{
  "format_version": "rule_check_input_v1",
  "doc_id": "...",
  "source_file": "...",
  "measured_values": {},
  "confirmed_items": [],
  "notes": [],
  "sources": []
}
```

其中：

```text
measured_values
案例关键属性。

confirmed_items
把属性翻译成简单事实。

notes
备注。
```

这个文件适合人工查看，也适合后续送入规程函数。

## 二十三、使用 chapter_1_functions 进行规程校验

这里使用的是：

```text
D:\桌面\华设项目\chapter_1_functions
```

这个文件夹里的程序，包括：

```text
chapter_1_functions.py
chapter_2_functions.py
chapter_3_functions.py
chapter_4_functions.py
chapter_5_functions.py
chapter_6_functions.py
chapter_7_functions.py
chapter_8_functions.py
```

### 1. 跑通版规则校验

这个版本用于确认规则函数能不能加载、能不能调用。

```powershell
& $py scripts\09_run_rule_check_from_full_json.py outputs\final_json --chapter-dir ..\chapter_1_functions -o outputs\rule_check_results
```

输出：

```text
outputs\rule_check_results\*.rule_check.json
```

如果命令行显示：

```text
clauses=181
```

说明 181 条规程函数都被调用了。

打开结果文件，重点看：

```json
"module_load_errors": []
```

和：

```json
"call_errors": []
```

如果这两个都是空数组，说明规则函数加载和调用没有错误。

### 2. 自动审核版

这个版本会根据案例属性自动判断：

```text
compliant
符合

non_compliant
不符合

not_applicable
不适用

pending_review
待人工复核
```

运行：

```powershell
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results
```

输出：

```text
outputs\auto_audit_results\*.auto_audit.json
```

这是最重要的审核结果文件。

## 二十四、怎么看自动审核结果

打开：

```text
outputs\auto_audit_results\某案例.auto_audit.json
```

先看：

```json
"summary": {
  "compliant": 52,
  "not_applicable": 68,
  "pending_review": 61
}
```

含义：

```text
compliant
程序判断符合的条文数量。

non_compliant
程序判断不符合的条文数量。

not_applicable
程序判断不适用的条文数量。

pending_review
程序暂时无法判断，需要人工复核的条文数量。
```

再看：

```json
"clause_results": []
```

这里每一项是一条规程条文的审核结果。

重点看：

```text
clause
条文号。

status
审核状态。

result
通俗解释。

audit_basis
程序采用的判断规则。

audit_evidence
程序用于判断的案例属性。

basis
规程原文依据。
```

例如：

```json
{
  "clause": "7.1.1",
  "status": "non_compliant",
  "result": "控制保护区内外部作业未抽取到安全监测要求。",
  "audit_basis": "monitoring_required_check",
  "audit_evidence": {
    "monitoring_required": false,
    "main_external_work_type": "基础工程",
    "pit_depth": "4.15m"
  }
}
```

意思是：

```text
第 7.1.1 条，程序判断不符合。
原因是：案例位于控制保护区内，但监测要求为 false。
```

## 二十五、如何测试自动审核能否识别不合格

建议不要直接改原始结果，而是复制一份测试目录。

### 1. 复制测试目录

```powershell
Copy-Item outputs\final_json outputs\final_json_test -Recurse -Force
```

测试目录：

```text
outputs\final_json_test
```

### 2. 打开测试 JSON 修改字段

例如打开：

```text
outputs\final_json_test\南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.case.json
```

重点修改：

```json
"attributes": {
  ...
}
```

不要主要修改 `field_detail` 或 `evidence`。

### 3. 测试监测规则

把：

```json
"monitoring_required": true
```

改成：

```json
"monitoring_required": false
```

然后运行：

```powershell
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json_test --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results_test
```

输出：

```text
outputs\auto_audit_results_test\*.auto_audit.json
```

打开测试结果，看：

```json
"summary": {
  "non_compliant": 29
}
```

如果出现 `non_compliant`，说明程序检测到了你人为制造的不符合项。

### 4. 测试保护措施规则

把下面字段改成 `null`：

```json
"measure_for_excavation": null,
"measure_for_support": null,
"measure_for_dewatering": null,
"measure_for_emergency": null,
"overall_conclusion": null,
"final_review_opinion": null
```

然后重新运行：

```powershell
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json_test --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results_test
```

预期：

```text
保护方案、保护措施相关条文可能变成 non_compliant。
```

### 5. 测试控制保护区适用性

把：

```json
"is_in_control_protection_zone": true
```

改成：

```json
"is_in_control_protection_zone": false
```

然后重新运行：

```powershell
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json_test --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results_test
```

预期：

```text
很多控制保护区相关条文会变成 not_applicable。
```

### 6. 测试计算评估规则

把下面字段改成 `null`：

```json
"calculation_methods": null,
"software_used": null,
"max_metro_vertical_displacement": null,
"max_metro_horizontal_displacement": null,
"max_metro_differential_settlement": null
```

然后重新运行：

```powershell
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json_test --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results_test
```

预期：

```text
计算评估相关条文可能从 compliant 变成 pending_review。
```

### 7. 查看不合格条文

打开：

```text
outputs\auto_audit_results_test\某案例.auto_audit.json
```

搜索：

```text
"status": "non_compliant"
```

每个不合格条文重点看：

```text
clause
result
audit_basis
audit_evidence
basis
```

## 二十六、推荐的日常完整命令

如果你只是想从头重新跑一遍全部流程，可以直接复制下面这一整段：

```powershell
chcp 65001
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $py scripts\00_build_schema.py "..\案例属性描述(1).docx" -o data\schema\case_schema.json
& $py scripts\01_doc_to_text.py data\raw_docs -o data\texts
& $py scripts\02_text_chunk.py data\texts -o data\chunks
& $py scripts\03_build_deepke_inputs.py data\chunks data\schema\case_schema.json -o outputs\deepke_inputs
& $py scripts\07_prepare_oneke_input.py outputs\deepke_inputs -o outputs\oneke_inputs
& $py scripts\04_rule_extract.py data\chunks -o outputs\raw_extract
& $py scripts\05_normalize.py outputs\raw_extract -o outputs\normalized
& $py scripts\06_merge_result.py outputs\normalized -o outputs\final_json --schema data\schema\case_schema.json
& $py scripts\08_build_rule_json.py outputs\final_json -o outputs\rule_json
& $py scripts\09_run_rule_check_from_full_json.py outputs\final_json --chapter-dir ..\chapter_1_functions -o outputs\rule_check_results
& $py scripts\10_auto_audit_from_full_json.py outputs\final_json --chapter-dir ..\chapter_1_functions -o outputs\auto_audit_results
```

运行完成后，重点看：

```text
outputs\final_json
```

完整版案例属性。

```text
outputs\rule_json
```

清爽版规则输入。

```text
outputs\auto_audit_results
```

自动审核结果。

## 二十七、目前自动审核的能力边界

当前自动审核已经能识别：

```text
是否涉及轨道交通结构安全保护
是否位于控制保护区/特别保护区
是否有基坑作业
是否有监测要求
是否有保护措施
是否有计算评估结果
明显不适用的专项条文，如爆破、油气管线、接口改造、水下作业、病害治理等
```

当前仍需继续完善：

```text
具体净距控制值的数值比较
影响等级自动判定
更多条文与属性之间的精确映射
更多 non_compliant 判断规则
```

因此：

```text
compliant / non_compliant / not_applicable
```

可以作为当前自动审核结果参考。

```text
pending_review
```

表示需要人工复核，或后续继续补充规则。

## 二十八、一键审核一个方案文件

如果你不想一步一步运行前面的脚本，可以直接使用一键入口：

```text
scripts\11_audit_one_plan.py
```

它会自动完成：

```text
1. 复制方案文件到本次运行目录
2. 从案例属性描述文档生成 Schema
3. 方案文档转纯文本
4. 文本按章节/模块切分
5. 生成 DeepKE 输入
6. 生成 OneKE 输入
7. 使用当前规则抽取器抽取属性
8. 标准化属性
9. 合并成完整版 case.json
10. 生成清爽版 rule.json
11. 调用 chapter_1_functions 自动审核
12. 输出不符合操作规程条文清单
```

### 1. 一键审核命令

打开 PowerShell，直接复制：

```powershell
chcp 65001
cd D:\桌面\华设项目\deepke_case_extract
$py="C:\Users\28030\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $py scripts\11_audit_one_plan.py "D:\桌面\华设项目\安全评估报告\南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.docx"
```

如果你要换成别的方案，只改最后一行里的文件路径：

```powershell
& $py scripts\11_audit_one_plan.py "你的方案文件完整路径"
```

例如：

```powershell
& $py scripts\11_audit_one_plan.py "D:\桌面\华设项目\安全评估报告\华贸安全影响评价报告20200322.pdf"
```

### 2. 指定本次运行目录名称

如果你希望输出目录固定，方便查找，可以加 `--run-id`：

```powershell
& $py scripts\11_audit_one_plan.py "D:\桌面\华设项目\安全评估报告\南通R18032地块项目与轨道交通1号线盾构区间相互影响安全评估报告20190624.docx" --run-id r18032_test
```

输出目录会是：

```text
outputs\one_click_audit\r18032_test
```

### 3. 一键审核输出在哪里

运行结束后，终端会输出类似：

```json
{
  "run_dir": "D:\\桌面\\华设项目\\deepke_case_extract\\outputs\\one_click_audit\\r18032_test",
  "case_json": "...\\outputs\\final_json\\xxx.case.json",
  "auto_audit_json": "...\\outputs\\auto_audit_results\\xxx.auto_audit.json",
  "non_compliant_report_json": "...\\reports\\non_compliant_report.json",
  "non_compliant_report_md": "...\\reports\\non_compliant_report.md",
  "audit_summary": {
    "compliant": 52,
    "not_applicable": 68,
    "pending_review": 61
  }
}
```

重点看这几个文件：

```text
outputs\one_click_audit\本次运行目录\outputs\final_json\*.case.json
```

完整版案例属性。

```text
outputs\one_click_audit\本次运行目录\outputs\auto_audit_results\*.auto_audit.json
```

自动审核完整结果。

```text
outputs\one_click_audit\本次运行目录\reports\non_compliant_report.json
```

不符合操作规程条文清单，JSON 版。

```text
outputs\one_click_audit\本次运行目录\reports\non_compliant_report.md
```

不符合操作规程条文清单，Markdown 版，比较适合人工阅读。

### 4. 如何看不符合操作规程的地方

打开：

```text
reports\non_compliant_report.md
```

如果没有不符合项，会显示：

```text
未发现自动判定的不符合条文。
```

如果有不符合项，会按条文列出来，例如：

```text
## 1. 条文 7.1.1

- 状态：non_compliant
- 判断：控制保护区内外部作业未抽取到安全监测要求。
- 自动判断依据：monitoring_required_check

### 使用的案例属性
- monitoring_required：false
- main_external_work_type：基础工程
- pit_depth：4.15m

### 原文来源
- monitoring_required：页码 10，段落 88，置信度 0.75
  - 原文：……

### 规程依据
7.1.1 在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测……
```

这就是你要找的：

```text
哪里不符合操作规程
为什么不符合
用到了哪些案例属性
这些属性来自报告哪里
对应哪条规程原文
```

### 5. 一键审核目前是否调用 OneKE

当前一键脚本会生成 OneKE 输入：

```text
outputs\oneke_inputs\*.oneke_input.jsonl
```

但默认不会直接启动 OneKE 大模型推理。

原因是 OneKE 需要本地大模型和显卡环境，不同电脑配置差异较大。当前一键脚本默认使用的是：

```text
04_rule_extract.py
```

也就是规则抽取器，保证在普通电脑上可以直接跑通。

如果后续你已经配置好 OneKE 模型，可以再把：

```text
outputs\oneke_inputs
```

送入 OneKE，得到更强的抽取结果，再进入后续标准化和审核流程。
