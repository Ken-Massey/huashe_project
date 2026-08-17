# 轨道交通保护区智能审核 Python 接口服务

本服务供 `RuoYi-Vue` 后端调用。浏览器不直接访问Python服务。

## 一、已经接入的能力

1. 第一阶段：函件抽取、人工参数合并、退让距离、影响等级、安全评估、保护监测、历史回函匹配和回函草稿。
2. 第二阶段方案审核：解析案例全文，通过语义向量分别检索案例和技术规程，再由大语言模型进行证据对照、数值比较、表格解释和综合风险审核。
3. 第二阶段建议生成：提取案例属性、执行同一套LLM+RAG审核，再匹配最相似历史案例并返回完整评审建议。
4. 第二阶段完整任务：先执行方案审核，使用生成的 `.case.json` 再执行建议匹配。
5. 案例知识库：上传、解析、停用、恢复和下载PDF/Word案例；成功案例会立即加入建议匹配数据库。

## 二、PyCharm直接启动

1. 使用解释器 `stage1_reply_system/.venv/Scripts/python.exe`。
2. 打开 `audit_api/run_server.py`。
3. 右键选择“运行 'run_server'”。不需要填写程序参数。
4. 启动后访问 `http://127.0.0.1:8000/docs` 查看交互式接口文档。
5. 健康检查地址为 `http://127.0.0.1:8000/health`。

首次部署环境安装依赖：

```powershell
stage1_reply_system\.venv\Scripts\python.exe -m pip install -r audit_api\requirements.txt
```

## 三、环境变量

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `AUDIT_API_HOST` | `127.0.0.1` | 监听地址；跨主机部署改为 `0.0.0.0` |
| `AUDIT_API_PORT` | `8000` | 服务端口 |
| `AUDIT_API_TOKEN` | 空 | Java调用服务时使用的内部令牌 |
| `AUDIT_API_RUNTIME` | `audit_api/runtime` | 上传文件、任务状态和结果根目录 |
| `AUDIT_API_MAX_UPLOAD_BYTES` | `209715200` | 单文件最大字节数，默认200MB |
| `AUDIT_API_MAX_WORKERS` | `2` | 第一阶段和任务调度线程数 |
| `DEEPKE_PYTHON` | 当前解释器 | 第二阶段脚本使用的Python解释器 |
| `STAGE1_HISTORY_DATABASE` | 第一阶段历史回函数据库 | SQLite数据库路径 |
| `MINERU_PARSER_MODE` | `auto` | `cloud`/`auto`使用MinerU官方解析，`local`预留给本地引擎 |
| `MINERU_API_TOKEN` | 空 | MinerU精确解析API密钥，只保存在服务端 |
| `MINERU_MODEL_VERSION` | `vlm` | MinerU解析模型，复杂扫描件和表格推荐`vlm` |
| `MINERU_TASK_TIMEOUT_SECONDS` | `1800` | 单份文档最长等待时间 |
| `MINERU_CACHE_ROOT` | `audit_api/runtime/mineru_cache` | D盘本地解析缓存目录 |

生产环境必须设置 `AUDIT_API_TOKEN`。若设置，Java每次请求都要携带：

```http
X-Service-Token: 与AUDIT_API_TOKEN相同的值
```

MinerU密钥不要写进Python、Vue或Java源码。当前项目可在
`audit_api/runtime/secrets/mineru.env` 中保存私有配置，该目录不会提交到版本库：

```dotenv
MINERU_API_TOKEN=在MinerU控制台生成的密钥
MINERU_PARSER_MODE=cloud
MINERU_MODEL_VERSION=vlm
```

## 四、任务接口

| 方法和地址 | 请求 | 说明 |
|---|---|---|
| `POST /api/v1/stage1/tasks` | multipart：`file`、`payload`，可选`scheme_file`、`expert_opinion_file` | 第一阶段 |
| `POST /api/v1/stage2/audit/tasks` | multipart：`file`、可选`options` | 方案审核和自动审核意见 |
| `POST /api/v1/stage2/advice/tasks` | multipart：`file`、可选`options` | 单独匹配历史建议 |
| `POST /api/v1/stage2/full/tasks` | multipart：`file`、可选`options` | 先审核再匹配建议，推荐 |
| `GET /api/v1/tasks/{taskId}` | 无 | 查询状态和进度 |
| `GET /api/v1/tasks/{taskId}/result` | 无 | 获取成功任务的结构化结果 |
| `GET /api/v1/tasks/{taskId}/files` | 无 | 获取结果文件列表 |
| `GET /api/v1/tasks/{taskId}/files/{fileId}` | 无 | 下载结果文件 |
| `POST /api/v1/knowledge/cases` | multipart：`file`、可选`case_name`、`category` | 上传并解析案例 |
| `GET /api/v1/knowledge/cases` | `keyword`、`include_inactive` | 查询知识库案例 |
| `GET /api/v1/knowledge/cases/{caseId}` | 无 | 查看属性和完整建议 |
| `GET /api/v1/knowledge/cases/{caseId}/content` | 可选`limit` | 查看解析后的案例正文 |
| `DELETE /api/v1/knowledge/cases/{caseId}` | 无 | 停用案例并退出匹配库 |
| `POST /api/v1/knowledge/cases/{caseId}/restore` | 无 | 恢复案例 |
| `DELETE /api/v1/knowledge/cases/{caseId}/permanent` | 无 | 彻底删除案例、解析数据和受管文件 |
| `GET /api/v1/knowledge/cases/{caseId}/file` | 无 | 下载原文件 |
| `GET /api/v1/knowledge/stats` | 无 | 知识库统计 |

第一阶段 `payload` 可以使用扁平JSON，示例见 `examples/stage1_payload.json`。布尔值必须发送 `true`、`false` 或 `null`，不要发送字符串“是”“否”“未知”。数值必须是JSON数字或 `null`，不要附加“m”等单位。

第二阶段 `options` 示例：

```json
{
  "top_k": 5,
  "rebuild_database": false
}
```

Python解释器和数据库路径不能通过HTTP请求指定，只能由服务端配置。

## 五、异步任务状态

提交成功返回HTTP `202`：

```json
{
  "task_id": "c5f6476c6e2c4c9aa1d91cb18aca592b",
  "task_type": "stage2_full",
  "status": "queued",
  "progress": 0,
  "message": "任务已进入队列"
}
```

状态包括：

- `queued`：排队中。
- `running`：处理中。
- `success`：完成，可以读取结果和文件。
- `failed`：失败，读取 `error_code`、`error_message` 和服务端日志。

任务状态以JSON持久化。服务重启时，未完成任务会明确标记失败，不会永久停留在“处理中”。第二阶段任务在单个服务实例内串行执行，避免多个DeepKE任务争抢模型或GPU。

## 六、RuoYi-Vue调用原则

1. Vue只调用若依Java接口。
2. Java保存业务任务记录，再调用本Python服务。
3. Java保存Python返回的 `task_id`。
4. Java定时查询Python任务状态并同步到MySQL。
5. 前端轮询Java任务详情，不直接轮询Python。
6. Java读取结果后，将不符合条文拆入明细表，完整JSON同时归档。
7. 文件下载由Java代理Python下载接口，避免向浏览器暴露Python服务地址和令牌。

## 七、输出重点

第一阶段结果包含四项结论、缺失字段、历史回函匹配和Word草稿。

第二阶段完整结果包含：

- 属性案例JSON；
- 自动审核汇总；
- LLM+RAG审核维度、总体风险等级和综合结论；
- 案例原文证据、规程原文证据、数值比较过程和处置建议；
- 自动生成审核意见；
- 最相似历史案例、相似度分项和完整评审建议；
- 所有JSON、Markdown和Word结果文件。

## 八、知识库入库规则

上传支持 `.pdf`、`.docx` 和旧版 `.doc`。程序会保存原文件，抽取全文、案例属性和评审建议，并记录文件哈希避免重复上传。

- `ready`：属性和建议均已抽取，立即参与后续案例匹配。
- `review_required`：正文已读取，但没有可靠识别到评审建议；保留在知识库中，暂不参与建议匹配。
- 停用：数据库记录和原文件继续保留，但不参与匹配；可以恢复。

知识库SQLite是维护主库，每次新增、停用或恢复后，会原子更新 `deepke_case_extract/data/case_advice_database.json`，现有 `match_new_case_advice` 无需修改即可使用最新案例。

## 九、IMA式LLM+RAG审核

当前正式审核链路不再把技术规程转换成Python判断函数：

1. 在“知识库 > 技术规程”上传PDF、DOCX、TXT或Markdown。系统保留原文件，抽取正文、条款和表格文本；扫描PDF由OCR处理。
   对扫描件、复杂表格和水印PDF，系统优先调用MinerU精确解析API，下载并缓存
   `content_list.json`、Markdown和表格结果；缓存、原文件及最终知识库均位于D盘。
2. 审核时自动将新增或变化的规程片段写入SQLite向量库，使用 `BAAI/bge-m3` 生成语义向量。未变化片段直接复用，不重复调用嵌入接口。
3. 案例文件按段落和页码切分后建立独立向量索引。系统先由大模型制定8至12个审核维度，再分别检索案例证据和规程证据。
4. “关键控制指标与超限值”会补充召回包含超过、超限、比较符等表达的全文片段；“原方案与修改方案”会补充召回方案比选段落，防止关键数值被大表格挤出向量检索前列。
5. 大模型分维度并行阅读证据，完成数值比较、表格查读、条件判断和工程风险推理；随后单独汇总总体风险等级、专业结论和待补资料。
6. 输出质量门只负责证据类型、重复项、排序和内部一致性检查，不承担领域合规判定。明确符合或不符合必须同时引用案例原文和规程原文。

结果中的 `generation_mode` 为 `pure_llm_rag`，`report_method` 为
`semantic_vector_rag+llm_reasoning`。每次审核保存 `ima_rag_audit.json` 和
Markdown报告，包含案例证据块、规程证据块、引用条款、比较过程和建议。

三个业务模块共用这一知识库：

- 复函意见生成：人工参数和函件资料合并后，使用LLM+RAG补充专业审核意见。
- 案例一键审核：只做全文解析和LLM+RAG审核，不调用 `chapter_1_functions`。
- 审核意见生成：先做LLM+RAG审核，再结合历史案例相似度生成建议。

停用规程后，该规程立即退出语义检索；恢复后重新参与。旧动态规则和
`chapter_1_functions` 文件暂时保留用于历史结果兼容和回归对比，但不参与当前正式审核结论。

状态含义：`compliant` 为有双侧证据的符合项，`non_compliant` 为有双侧证据的明确不符合，
`risk` 为工程风险判断，`insufficient` 为确实影响结论的关键资料不足。
