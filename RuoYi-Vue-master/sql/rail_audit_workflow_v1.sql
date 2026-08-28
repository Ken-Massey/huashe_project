-- 案例审核多级流转 v1：流程表、任务表、日志表、意见快照、角色与按钮权限
-- 账号体系沿用若依自带 sys_user、sys_role、sys_user_role、sys_role_menu，不新增账号表。
-- 本脚本不创建外键，避免跨环境导入时因字符集、排序规则或导入顺序导致失败。

-- 1) 流程节点配置：后续可按项目类型或阶段配置不同审核链路
create table if not exists rail_audit_flow_node (
  node_id             bigint(20)      not null auto_increment    comment '节点ID',
  flow_code           varchar(64)     not null default 'BASEMENT_AUDIT' comment '流程编码',
  node_code           varchar(64)     not null                   comment '节点编码',
  node_name           varchar(64)     not null                   comment '节点名称',
  node_order          int(4)          not null                   comment '节点顺序',
  role_key            varchar(100)    default null               comment '处理角色，对应sys_role.role_key',
  project_type        varchar(64)     default null               comment '适用项目类型，空表示通用',
  stage_name          varchar(64)     default null               comment '适用阶段，空表示通用',
  allow_return        char(1)         default '1'                comment '是否允许退回（0否 1是）',
  status              char(1)         default '0'                comment '状态（0正常 1停用）',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default null               comment '备注',
  primary key (node_id),
  unique key uk_rail_flow_node (flow_code, node_code, project_type, stage_name),
  key idx_rail_flow_order (flow_code, node_order, status),
  key idx_rail_flow_role (role_key)
) engine=innodb comment = '案例审核流程节点配置表';

-- 2) 审核流程实例：一条记录对应一个项目阶段的一次流转主线
create table if not exists rail_audit_workflow (
  workflow_id          bigint(20)      not null auto_increment    comment '流程实例ID',
  flow_code            varchar(64)     not null default 'BASEMENT_AUDIT' comment '流程编码',
  session_id           varchar(64)     default null               comment '智能审核会话ID',
  project_id           varchar(64)     default null               comment '项目档案ID',
  stage_id             varchar(64)     default null               comment '项目阶段ID',
  project_name         varchar(255)    default ''                 comment '项目名称',
  stage_name           varchar(64)     default ''                 comment '阶段名称',
  audit_version        int(4)          not null default 1         comment '当前审核版本号',
  workflow_status      varchar(32)     not null default 'DRAFT'   comment '流程状态',
  current_node_code    varchar(64)     default null               comment '当前节点编码',
  current_node_name    varchar(64)     default null               comment '当前节点名称',
  current_assignee_id  bigint(20)      default null               comment '当前处理人ID，对应sys_user.user_id',
  current_assignee     varchar(64)     default ''                 comment '当前处理人名称',
  initiator_id         bigint(20)      default null               comment '发起人ID，对应sys_user.user_id',
  initiator_name       varchar(64)     default ''                 comment '发起人名称',
  latest_summary       text                                       comment '最新综合评价',
  latest_risk_level    varchar(16)     default ''                 comment '最新总体风险等级',
  latest_result_json   longtext                                   comment '最新审核结果JSON快照',
  submitted_time       datetime                                   comment '提交审核时间',
  approved_time        datetime                                   comment '最终通过时间',
  archived_time        datetime                                   comment '归档时间',
  create_by            varchar(64)     default ''                 comment '创建者',
  create_time          datetime                                   comment '创建时间',
  update_by            varchar(64)     default ''                 comment '更新者',
  update_time          datetime                                   comment '更新时间',
  remark               varchar(500)    default null               comment '备注',
  primary key (workflow_id),
  key idx_rail_workflow_session (session_id),
  key idx_rail_workflow_project_stage (project_id, stage_id),
  key idx_rail_workflow_status (workflow_status),
  key idx_rail_workflow_assignee (current_assignee_id),
  key idx_rail_workflow_create_time (create_time)
) engine=innodb comment = '案例审核流程实例表';

-- 3) 审核待办任务：每到一个节点生成一条待办
create table if not exists rail_audit_task (
  task_id             bigint(20)      not null auto_increment    comment '任务ID',
  workflow_id         bigint(20)      not null                   comment '流程实例ID',
  node_code           varchar(64)     not null                   comment '节点编码',
  node_name           varchar(64)     not null                   comment '节点名称',
  task_status         varchar(32)     not null default 'TODO'    comment '任务状态（TODO待办 PASS通过 RETURN退回 CANCEL取消）',
  assignee_id         bigint(20)      default null               comment '处理人ID，对应sys_user.user_id',
  assignee_name       varchar(64)     default ''                 comment '处理人名称',
  role_key            varchar(100)    default null               comment '候选处理角色，对应sys_role.role_key',
  received_time       datetime                                   comment '接收时间',
  handled_time        datetime                                   comment '处理时间',
  handle_opinion      text                                       comment '处理意见',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default null               comment '备注',
  primary key (task_id),
  key idx_rail_task_workflow (workflow_id),
  key idx_rail_task_assignee (assignee_id, task_status),
  key idx_rail_task_role (role_key, task_status),
  key idx_rail_task_node (workflow_id, node_code)
) engine=innodb comment = '案例审核待办任务表';

-- 4) 流转日志：记录提交、审核、退回、归档等操作
create table if not exists rail_audit_flow_log (
  log_id              bigint(20)      not null auto_increment    comment '日志ID',
  workflow_id         bigint(20)      not null                   comment '流程实例ID',
  task_id             bigint(20)      default null               comment '任务ID',
  action_code         varchar(32)     not null                   comment '动作编码',
  action_name         varchar(64)     not null                   comment '动作名称',
  from_node_code      varchar(64)     default null               comment '来源节点',
  to_node_code        varchar(64)     default null               comment '目标节点',
  operator_id         bigint(20)      default null               comment '操作人ID，对应sys_user.user_id',
  operator_name       varchar(64)     default ''                 comment '操作人名称',
  opinion             text                                       comment '流转意见',
  snapshot_json       longtext                                   comment '操作时业务快照',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  remark              varchar(500)    default null               comment '备注',
  primary key (log_id),
  key idx_rail_flow_log_workflow (workflow_id),
  key idx_rail_flow_log_task (task_id),
  key idx_rail_flow_log_time (create_time)
) engine=innodb comment = '案例审核流转日志表';

-- 5) 审核意见快照：保留每版综合评价与条目，支撑历史追溯和归档展示
create table if not exists rail_audit_opinion_snapshot (
  snapshot_id         bigint(20)      not null auto_increment    comment '意见快照ID',
  workflow_id         bigint(20)      default null               comment '流程实例ID',
  session_id          varchar(64)     default null               comment '智能审核会话ID',
  audit_version       int(4)          not null default 1         comment '审核版本号',
  opinion_no          int(4)          default 0                  comment '意见序号，0表示综合评价',
  opinion_type        varchar(32)     not null default 'ITEM'    comment '意见类型（SUMMARY综合评价 ITEM审核意见 RETURN退回意见）',
  title               varchar(255)    default ''                 comment '标题',
  risk_level          varchar(16)     default ''                 comment '风险等级',
  opinion_content     text                                       comment '意见正文',
  result_json         longtext                                   comment '结构化结果JSON',
  source_files_json   longtext                                   comment '本版引用文件JSON',
  create_by           varchar(64)     default ''                 comment '创建者',
  create_time         datetime                                   comment '创建时间',
  update_by           varchar(64)     default ''                 comment '更新者',
  update_time         datetime                                   comment '更新时间',
  remark              varchar(500)    default null               comment '备注',
  primary key (snapshot_id),
  key idx_rail_snapshot_workflow_version (workflow_id, audit_version),
  key idx_rail_snapshot_session_version (session_id, audit_version),
  key idx_rail_snapshot_type (opinion_type)
) engine=innodb comment = '案例审核意见版本快照表';

-- 6) 默认流程节点：经办人提交 -> 审核人复核 -> 终审归档
insert into rail_audit_flow_node (
  flow_code, node_code, node_name, node_order, role_key, project_type, stage_name,
  allow_return, status, create_by, create_time, remark
) values
  ('BASEMENT_AUDIT', 'SUBMIT', '经办人提交', 1, 'rail_handler', null, null, '0', '0', 'admin', sysdate(), '经办人发起资料审核、补充材料并提交流转'),
  ('BASEMENT_AUDIT', 'REVIEW', '审核人复核', 2, 'rail_reviewer', null, null, '1', '0', 'admin', sysdate(), '审核人复核AI意见、修改条目并决定通过或退回'),
  ('BASEMENT_AUDIT', 'FINAL', '终审归档', 3, 'rail_final_reviewer', null, null, '1', '0', 'admin', sysdate(), '终审确认最终意见并写入项目档案')
on duplicate key update
  node_name = values(node_name),
  node_order = values(node_order),
  role_key = values(role_key),
  allow_return = values(allow_return),
  status = values(status),
  update_by = 'admin',
  update_time = sysdate(),
  remark = values(remark);

-- 7) 默认角色：仅初始化角色，不自动给任何用户分配角色
set @next_role_id := (select ifnull(max(role_id), 100) + 1 from sys_role);
insert into sys_role (
  role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
  status, del_flag, create_by, create_time, update_by, update_time, remark
)
select @next_role_id, '经办人', 'rail_handler', 10, '1', 1, 1, '0', '0', 'admin', sysdate(), '', null, '案例审核流程发起、资料补充、退回修改'
where not exists (select 1 from sys_role where role_key = 'rail_handler');

set @next_role_id := (select ifnull(max(role_id), 100) + 1 from sys_role);
insert into sys_role (
  role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
  status, del_flag, create_by, create_time, update_by, update_time, remark
)
select @next_role_id, '审核人', 'rail_reviewer', 11, '1', 1, 1, '0', '0', 'admin', sysdate(), '', null, '案例审核流程复核、修改、退回'
where not exists (select 1 from sys_role where role_key = 'rail_reviewer');

set @next_role_id := (select ifnull(max(role_id), 100) + 1 from sys_role);
insert into sys_role (
  role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
  status, del_flag, create_by, create_time, update_by, update_time, remark
)
select @next_role_id, '终审人', 'rail_final_reviewer', 12, '1', 1, 1, '0', '0', 'admin', sysdate(), '', null, '案例审核最终确认、归档'
where not exists (select 1 from sys_role where role_key = 'rail_final_reviewer');

-- 8) 案例审核流程按钮权限，挂在“案例审核”菜单下
insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values
  (2018, '流程待办查看', 2001, 10, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:list',    '#', 'admin', sysdate(), '', null, '查看案例审核流程待办和历史流转'),
  (2019, '提交审核',     2001, 11, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:submit',  '#', 'admin', sysdate(), '', null, '经办人提交审核流程'),
  (2020, '审核通过',     2001, 12, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:approve', '#', 'admin', sysdate(), '', null, '审核人通过复核节点'),
  (2021, '退回修改',     2001, 13, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:return',  '#', 'admin', sysdate(), '', null, '审核人或终审人退回经办人修改'),
  (2022, '流程归档',     2001, 14, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:archive', '#', 'admin', sysdate(), '', null, '终审通过后归档到项目档案'),
  (2023, '流程配置',     2001, 15, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:config',  '#', 'admin', sysdate(), '', null, '维护审核流程节点和角色规则'),
  (2024, '提交终审',     2001, 16, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:submitFinal',  '#', 'admin', sysdate(), '', null, '审核人提交至终审节点'),
  (2025, '终审通过',     2001, 17, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:final',  '#', 'admin', sysdate(), '', null, '终审人确认通过流程')
on duplicate key update
  menu_name = values(menu_name),
  parent_id = values(parent_id),
  order_num = values(order_num),
  path = values(path),
  component = values(component),
  query = values(query),
  route_name = values(route_name),
  is_frame = values(is_frame),
  is_cache = values(is_cache),
  menu_type = values(menu_type),
  visible = values(visible),
  status = values(status),
  perms = values(perms),
  icon = values(icon),
  update_by = 'admin',
  update_time = sysdate(),
  remark = values(remark);

-- 9) 默认角色授权：角色建好后，可在“账号管理”中给用户分配对应角色
delete rm
from sys_role_menu rm
join sys_role r on r.role_id = rm.role_id
where r.role_key in ('rail_handler', 'rail_reviewer', 'rail_final_reviewer')
  and rm.menu_id in (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025);

insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2019)
where r.role_key = 'rail_handler';

insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2020, 2021, 2024)
where r.role_key = 'rail_reviewer';

insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2022, 2025)
where r.role_key = 'rail_final_reviewer';
