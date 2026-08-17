# RuoYi-Vue 前端页面与接口对接设计

## 1. 页面结构

系统沿用 RuoYi-Vue 的顶部栏和权限体系，业务区使用“左侧功能导航 + 右侧工作区”。左侧固定四个一级入口：

1. 复函意见生成
2. 案例一键审核
3. 审核意见生成
4. 知识库

不照搬参考软件的品牌栏、个人知识库、订阅区和聊天区。参考图只用于借鉴轻量导航、文件列表和详情分栏方式。

### 1.1 复函意见生成

- 上传函件 PDF。
- 填写第一阶段人工参数。
- 可选上传方案和专家意见附件。
- 提交 `POST /api/v1/stage1/tasks`。
- 展示退让距离、影响等级、安全评估、保护监测、相似回函、注意事项和回函 Word。

### 1.2 案例一键审核

- 上传安全评估报告 PDF、DOCX 或 TXT。
- 提交 `POST /api/v1/stage2/audit/tasks`。
- 展示任务进度、提取属性、调用函数、不符合条文、原文证据和结果文件。

### 1.3 审核意见生成

- 上传新案例文件或选择“一键审核”产生的 case.json。
- 提交 `POST /api/v1/stage2/advice/tasks`。
- 展示最相似案例、总相似度、分项相似度和原样复制的完整评审建议。
- 页面保留“审核并生成意见”命令，调用 `POST /api/v1/stage2/full/tasks` 完成两步串联。

### 1.4 知识库

页面采用三栏结构：

- 左栏：知识库统计、案例分类、全部案例、待复核、已停用。
- 中栏：案例搜索、排序、文件拖放区和案例列表。
- 右栏：选中案例的属性、解析正文、评审建议、原文件下载、停用或恢复命令。

上传 PDF、DOC 或 DOCX 后调用 `POST /api/v1/knowledge/cases`。上传接口返回异步任务编号，前端使用统一任务接口查询解析进度。只有状态为 `ready` 的案例参与后续建议匹配；`review_required` 表示正文已解析，但尚未可靠识别评审建议，需要人工复核。

## 2. 建议路由和组件

| 菜单 | 路由 | Vue 文件建议 |
|---|---|---|
| 复函意见生成 | `/rail/reply` | `src/views/rail/reply/index.vue` |
| 案例一键审核 | `/rail/audit` | `src/views/rail/audit/index.vue` |
| 审核意见生成 | `/rail/advice` | `src/views/rail/advice/index.vue` |
| 知识库 | `/rail/knowledge` | `src/views/rail/knowledge/index.vue` |

公共组件建议：

- `FileDropZone.vue`：拖放、格式和大小校验。
- `TaskProgress.vue`：轮询任务状态并显示当前步骤。
- `ResultFiles.vue`：结果文件列表和下载。
- `ClauseResultTable.vue`：条文、函数、状态和原文证据。
- `CaseDetailPanel.vue`：知识库案例详情。

## 3. RuoYi Java 代理原则

浏览器只访问 RuoYi Java 后端，不直接访问 Python。Java 负责登录鉴权、菜单权限、业务任务记录和文件代理；Python 负责文档解析、规则计算和案例匹配。

建议 Java 控制器：

- `RailReplyController`
- `RailAuditController`
- `RailAdviceController`
- `RailKnowledgeController`
- `RailTaskController`

Java 调 Python 时固定携带 `X-Service-Token`。Python 地址和令牌只写在若依后端配置中，不返回浏览器。上传请求必须由 Java 使用 multipart 转发；任务结果和下载文件也由 Java 代理。

## 4. 知识库接口

| Python 接口 | Java 对外接口建议 | 用途 |
|---|---|---|
| `POST /api/v1/knowledge/cases` | `POST /rail/knowledge/cases` | 上传入库 |
| `GET /api/v1/knowledge/cases` | `GET /rail/knowledge/cases` | 列表和搜索 |
| `GET /api/v1/knowledge/cases/{id}` | `GET /rail/knowledge/cases/{id}` | 属性和建议详情 |
| `GET /api/v1/knowledge/cases/{id}/content` | `GET /rail/knowledge/cases/{id}/content` | 解析正文 |
| `GET /api/v1/knowledge/cases/{id}/file` | `GET /rail/knowledge/cases/{id}/file` | 下载原文 |
| `DELETE /api/v1/knowledge/cases/{id}` | `DELETE /rail/knowledge/cases/{id}` | 软停用 |
| `POST /api/v1/knowledge/cases/{id}/restore` | `PUT /rail/knowledge/cases/{id}/restore` | 恢复参与匹配 |
| `DELETE /api/v1/knowledge/cases/{id}/permanent` | `DELETE /rail/knowledge/cases/{id}/permanent` | 永久删除案例和受管文件 |
| `GET /api/v1/knowledge/stats` | `GET /rail/knowledge/stats` | 左栏统计 |

## 5. 知识库状态

- `ready`：正文和建议已抽取，当前可参与案例匹配。
- `review_required`：正文已读取，但没有可靠抽取到建议，不参与匹配。
- `active=false`：案例被软停用，记录和原文件保留，不参与匹配。

上传文件会计算 SHA-256。相同文件不能重复加入有效知识库。新增、停用或恢复案例后，Python 服务会原子更新现有案例建议匹配数据库，因此“审核意见生成”会自动使用最新知识库。

## 6. 交互细节

- 拖入文件后先显示文件名、大小和类型，不立即提交；用户点击“加入知识库”后开始处理。
- 处理中显示明确步骤，不使用无限转圈：已上传、读取正文、抽取属性与建议、写入知识库、完成。
- 中栏列表使用紧凑行布局，不把每个文件做成大卡片。
- 详情区将“属性”“评审建议”“解析正文”做成标签页。
- `review_required` 使用醒目状态并提供查看正文，避免把未识别到建议误写成成功。
- 删除命令文案使用“停用”，并明确提示案例将退出匹配库但不会删除原文件。
- 所有结果页必须展示来源文件、规则函数或匹配案例，保证可追溯。

## 7. 若依工程接入前需要提供

将完整 RuoYi-Vue 工程放入当前工作区，并明确：

- Java 根目录和基础包名。
- `ruoyi-ui` 目录位置。
- 当前使用的 RuoYi-Vue 版本。
- MySQL 数据库连接是否已配置。

拿到工程后再创建 Java Controller/Service、前端 API 文件、四个 Vue 页面和菜单 SQL，避免因包名、权限前缀或 Vue 版本不同而返工。
