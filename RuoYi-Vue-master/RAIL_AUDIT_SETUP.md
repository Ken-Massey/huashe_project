# 轨道保护智能审核：部署与使用说明

## 1. 系统组成

- Python 审核服务：`D:\桌面\华设项目\audit_api`
- 若依 Java 后端：`RuoYi-Vue-master\ruoyi-admin`
- Vue 2 前端：`RuoYi-Vue-master\ruoyi-ui`
- 菜单增量脚本：`RuoYi-Vue-master\sql\rail_audit_menu.sql`
- 通用管理脚本：`RuoYi-Vue-master\sql\rail_general_management_v1.sql`
- 项目档案数据库：`runtime\project_archive\project_archive.sqlite3`

浏览器只访问若依系统。若依后端负责权限校验并代理 Python 审核服务，项目档案由 Python 服务持久化。

## 2. 项目档案业务规则

1. 一个项目可以人工新增任意数量、任意名称的阶段。
2. 每个阶段只有一份审核记录；审核成功后不能再次提交。
3. 审核失败允许重试，并沿用同一条阶段审核记录累计尝试次数。
4. 审核任务创建后阶段立即进入占用状态，避免并发重复提交。
5. 审核当前阶段时，只参考同一项目中排序更早且审核成功的阶段。
6. 历史审核记录只作为综合判断的辅助背景，不能代替当前送审材料和现行规程依据。
7. 归档项目或阶段属于软归档，不会删除历史审核结果和附件信息。
8. 永久删除项目会同时删除该项目的阶段和审核档案；存在排队中或执行中任务时禁止删除。

## 3. 首次配置

1. 创建 MySQL 数据库并执行 `sql/ry_20260417.sql`。
2. 执行 `sql/rail_audit_menu.sql`。该脚本为幂等增量迁移，不会删除原有审核菜单或角色授权。
3. 执行 `sql/rail_general_management_v1.sql`，创建“通用管理”表、菜单和角色权限。
4. 如只需要修复菜单显示或权限，可单独执行 `sql/rail_general_menu_repair.sql`。
5. 检查 `ruoyi-admin/src/main/resources/application-druid.yml` 的 MySQL 连接。
6. 启动 MySQL 和 Redis。
7. Python 与 Java 在同一台电脑运行时，Python 地址保持默认值即可。

生产环境建议为 Python 和 Java 设置同一个内部调用令牌：

```text
AUDIT_API_TOKEN=请替换为随机长字符串
```

跨主机部署时，Java 服务额外设置：

```text
AUDIT_PYTHON_URL=http://Python服务IP:8000
```

## 4. 启动顺序

### 4.1 Python 审核服务

在项目根目录运行：

```powershell
stage1_reply_system\.venv\Scripts\python.exe audit_api\run_server.py
```

健康检查：`http://127.0.0.1:8000/health`。

### 4.2 若依 Java 后端

使用项目配置的 JDK 24 运行：

```text
ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java
```

默认地址：`http://127.0.0.1:8080`。

### 4.3 Vue 前端

```powershell
cd RuoYi-Vue-master\ruoyi-ui
npm install
npm run dev
```

生产构建使用：

```powershell
npm run build:prod
```

## 5. 项目档案使用流程

### 新项目首次审核

1. 打开“案例审核”。
2. 上传函件、案例或补充附件，系统自动识别并回填“项目名称”和“项目阶段”。
3. 项目名称和阶段既可从历史档案中选择，也可直接输入或人工修改。
4. 提交审核时，系统按名称自动匹配项目和阶段；不存在时自动创建，无需单独建档。
5. 审核完成后结果自动写入对应项目和阶段。

### 历史项目后续阶段审核

1. 在“项目档案”中打开历史项目并新增阶段。
2. 可点击该阶段的“前往审核”，也可直接在审核页选择历史项目和阶段。
3. 审核页会显示可参考的前序阶段数量和风险摘要。
4. 完成审核后返回项目档案查看结论、风险、历史参考和相关文件。

### 失败重试

项目档案中失败阶段会显示错误信息和尝试次数。点击“重新审核”后可再次提交；成功阶段不会提供重复审核入口。

### 项目重命名与删除

在项目档案中打开项目右上角菜单：

- “重命名/编辑项目”可以修改项目名称、编号、地点和说明。
- “永久删除项目”会在二次确认后删除项目、全部阶段和审核档案，且不可恢复。
- 正在排队或执行审核的项目不能删除，应等待任务结束后再操作。

## 6. 权限说明

| 权限 | 用途 |
|---|---|
| `rail:audit:run` | 发起审核；同时允许在审核页读取档案并快速新建项目/阶段 |
| `rail:archive:list` | 查看项目档案菜单和项目阶段 |
| `rail:archive:add` | 在项目档案页新增项目或阶段 |
| `rail:archive:edit` | 编辑、排序和恢复项目或阶段 |
| `rail:archive:remove` | 软归档项目或阶段 |
| `rail:archive:audit:list` | 查看阶段审核详情和前序历史 |
| `rail:general:list` | 查看通用管理菜单 |
| `rail:general:query` | 查询通用事项、总结报表和详情 |
| `rail:general:add` | 新增临时事项、安全隐患、总结和上报记录 |
| `rail:general:edit` | 编辑通用事项和报表 |
| `rail:general:remove` | 删除通用事项和报表 |
| `rail:general:upload` | 上传或删除通用管理附件 |
| `rail:general:submit` | 提交通用事项、总结或上报记录 |
| `rail:general:review` | 审核或退回通用事项、总结和报表 |
| `rail:general:close` | 闭环临时事项和安全隐患 |
| `rail:general:statistics` | 查看统计分析和态势数据 |
| `rail:general:report` | 生成、发布或提交数据上报 |
| `rail:general:archive` | 归档通用事项和报表记录 |

菜单脚本会让已经拥有“案例一键审核”菜单的非管理员角色自动获得“项目档案”和“审核记录查看”。其他管理权限需要在“系统管理 → 角色管理”中按需分配。

“通用管理”角色建议：

- 普通角色：查看通用管理和统计。
- 经办人：登记事项、上传附件、提交、闭环和数据上报。
- 审核人：查看、编辑、审核、闭环确认和统计。
- 终审人：审核、数据上报、归档发布和统计。

## 7. 接口对应关系

| 功能 | 若依接口 |
|---|---|
| 案例审核与综合意见 | `/rail/full/tasks` |
| 函件审核与复函 | `/rail/reply/tasks` |
| 项目、阶段与审核历史 | `/rail/archives/**` |
| 案例知识库 | `/rail/knowledge/**` |
| 通用事项、隐患、总结和上报 | `/rail/general/**` |

Python 原始档案接口统一位于 `/api/v1/project-archives/**`，不建议浏览器直接调用。

## 8. 验收测试

```powershell
stage1_reply_system\.venv\Scripts\python.exe -m pytest audit_api\tests -q
```

重点覆盖：自定义阶段排序、单阶段唯一审核、并发占用、失败重试、前序阶段筛选、历史上下文注入、任务成功自动归档以及接口异常状态。

## 9. 常见问题

- 看不到“项目档案”：执行菜单脚本后重新登录，并检查角色的 `rail:archive:list` 权限。
- 项目列表为空：尚未创建真实项目档案，可在审核页或项目档案页新建。
- 页面提示服务连接失败：先检查 Python `/health`，再检查 `AUDIT_PYTHON_URL`。
- 内部接口返回 401：确认 Python 与 Java 的 `AUDIT_API_TOKEN` 完全一致。
- 阶段无法选择：该阶段可能已经审核成功、正在排队、正在审核或已归档。
- 阶段审核失败：可在项目档案中查看错误并重新提交，成功后仍只保留该阶段唯一记录。
- 大文件上传失败：Java 当前单文件上限为 200 MB、单请求上限为 220 MB，反向代理也应配置对应限制。
- 看不到“通用管理”：先执行 `sql/rail_general_menu_repair.sql`，再退出账号重新登录，刷新前端权限缓存。
- 通用管理提示无权限：检查当前账号角色是否拥有 `rail:general:list` 或 `rail:general:query`；经办、审核、终审动作还需要对应按钮权限。
