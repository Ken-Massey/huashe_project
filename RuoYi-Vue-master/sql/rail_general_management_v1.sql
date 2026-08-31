-- 通用管理 v1：数据库表、菜单与权限初始化
-- 执行库：huashe_database
-- 用途：支撑临时事项登记、安全隐患台账、月度/年度工作总结、统计报表、态势分析、数据上报等通用保护区管理工作。
-- 说明：本脚本可重复执行；账号体系继续沿用若依 sys_user、sys_role、sys_user_role、sys_role_menu。

start transaction;

-- 1) 通用事项主表
create table if not exists rail_general_item (
  item_id             bigint(20)      not null auto_increment comment '事项ID',
  item_code           varchar(64)     default ''               comment '事项编号',
  item_type           varchar(40)     not null                  comment '事项类型：temporary/hazard/monthly_summary/annual_summary/data_report/other',
  item_title          varchar(200)    not null                  comment '事项标题',
  item_content        longtext                                comment '事项内容',
  project_id          varchar(64)     default null              comment '关联项目ID',
  project_name        varchar(200)    default ''               comment '关联项目名称',
  line_name           varchar(100)    default ''               comment '关联线路',
  location_desc       varchar(500)    default ''               comment '位置描述',
  responsible_unit    varchar(200)    default ''               comment '责任单位',
  responsible_user_id bigint(20)      default null              comment '责任人用户ID',
  responsible_user    varchar(80)     default ''               comment '责任人',
  source_channel      varchar(60)     default ''               comment '来源渠道：manual/patrol/meeting/archive/external/other',
  severity_level      varchar(20)     default ''               comment '严重程度：high/medium/low/tip',
  priority            varchar(20)     default 'normal'          comment '优先级：high/normal/low',
  occur_time          datetime        default null              comment '发生/发现时间',
  due_time            datetime        default null              comment '要求完成时间',
  finish_time         datetime        default null              comment '完成时间',
  close_time          datetime        default null              comment '闭环时间',
  close_by            varchar(64)     default ''               comment '闭环确认人',
  close_remark        varchar(1000)   default ''               comment '闭环说明',
  review_user_id      bigint(20)      default null              comment '审核人用户ID',
  review_by           varchar(64)     default ''               comment '审核人',
  review_time         datetime        default null              comment '审核时间',
  review_opinion      varchar(1000)   default ''               comment '审核意见',
  archive_status      char(1)         default '0'               comment '归档状态：0未归档 1已归档',
  archive_time        datetime        default null              comment '归档时间',
  status              varchar(32)     default 'draft'           comment '状态：draft/submitted/processing/pending_review/completed/closed/archived/returned/cancelled',
  extra_json          longtext                                comment '扩展字段JSON',
  remark              varchar(500)    default ''               comment '备注',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (item_id),
  unique key uk_rail_general_item_code (item_code),
  key idx_rail_general_item_type (item_type),
  key idx_rail_general_item_status (status),
  key idx_rail_general_item_project (project_id),
  key idx_rail_general_item_due (due_time),
  key idx_rail_general_item_responsible (responsible_user_id),
  key idx_rail_general_item_create_by (create_by)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='通用管理-事项主表';

-- 2) 通用附件表
create table if not exists rail_general_attachment (
  attachment_id       bigint(20)      not null auto_increment comment '附件ID',
  item_id             bigint(20)      default null              comment '事项ID',
  report_id           bigint(20)      default null              comment '报表/总结ID',
  file_type           varchar(40)     default 'attachment'      comment '附件类型：image/document/report/proof/archive/other',
  file_name           varchar(255)    not null                  comment '原文件名',
  stored_name         varchar(255)    default ''               comment '存储文件名',
  file_path           varchar(1000)   not null                  comment '文件路径',
  file_size           bigint(20)      default 0                 comment '文件大小',
  mime_type           varchar(100)    default ''               comment 'MIME类型',
  description         varchar(500)    default ''               comment '附件说明',
  create_by           varchar(64)     default ''               comment '上传者',
  create_time         datetime        default null              comment '上传时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (attachment_id),
  key idx_rail_general_attachment_item (item_id),
  key idx_rail_general_attachment_report (report_id),
  key idx_rail_general_attachment_type (file_type)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='通用管理-附件表';

-- 3) 报表、总结、态势分析和数据上报记录表
create table if not exists rail_general_report (
  report_id           bigint(20)      not null auto_increment comment '记录ID',
  report_code         varchar(64)     default ''               comment '记录编号',
  report_type         varchar(40)     not null                  comment '类型：monthly_summary/annual_summary/statistics/situation/data_report/other',
  report_title        varchar(200)    not null                  comment '标题',
  report_period       varchar(40)     default ''               comment '周期：YYYY-MM/YYYY/Qx/YYYY',
  summary_content     longtext                                comment '总结/报表正文',
  statistics_json     longtext                                comment '统计数据JSON',
  analysis_json       longtext                                comment '态势分析JSON',
  submit_unit         varchar(200)    default ''               comment '上报单位',
  receive_unit        varchar(200)    default ''               comment '接收单位',
  submit_time         datetime        default null              comment '上报时间',
  review_user_id      bigint(20)      default null              comment '审核人用户ID',
  review_by           varchar(64)     default ''               comment '审核人',
  review_time         datetime        default null              comment '审核时间',
  review_opinion      varchar(1000)   default ''               comment '审核意见',
  publish_time        datetime        default null              comment '发布时间',
  archive_status      char(1)         default '0'               comment '归档状态：0未归档 1已归档',
  archive_time        datetime        default null              comment '归档时间',
  status              varchar(32)     default 'draft'           comment '状态：draft/submitted/reviewed/published/reported/archived/returned',
  remark              varchar(500)    default ''               comment '备注',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (report_id),
  unique key uk_rail_general_report_code (report_code),
  key idx_rail_general_report_type (report_type),
  key idx_rail_general_report_period (report_period),
  key idx_rail_general_report_status (status),
  key idx_rail_general_report_create_by (create_by)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='通用管理-总结报表上报表';

-- 4) 通用操作留痕表
create table if not exists rail_general_log (
  log_id              bigint(20)      not null auto_increment comment '日志ID',
  target_type         varchar(40)     not null                  comment '对象类型：item/report/attachment',
  target_id           bigint(20)      not null                  comment '对象ID',
  action_code         varchar(40)     not null                  comment '动作编码',
  action_name         varchar(100)    not null                  comment '动作名称',
  from_status         varchar(32)     default ''               comment '原状态',
  to_status           varchar(32)     default ''               comment '新状态',
  operator_id         bigint(20)      default null              comment '操作人ID',
  operator_name       varchar(64)     default ''               comment '操作人',
  opinion             varchar(1000)   default ''               comment '处理意见',
  snapshot_json       longtext                                comment '快照JSON',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  primary key (log_id),
  key idx_rail_general_log_target (target_type, target_id),
  key idx_rail_general_log_time (create_time)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='通用管理-操作留痕表';

-- 5) 菜单顺序：通用管理位于项目档案与账号管理之间。
insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values (
  2040, '通用管理', 2000, 7, 'general', 'rail/general/index', '', 'RailGeneral',
  1, 0, 'C', '0', '0', 'rail:general:list', 'dashboard',
  'admin', sysdate(), '', null, '临时事项、隐患台账、工作总结、统计报表、态势分析和数据上报'
)
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

-- 6) 按钮权限，挂在“通用管理”菜单下。
insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values
  (2041, '通用查询',     2040, 1,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:query',     '#', 'admin', sysdate(), '', null, '查看通用事项和报表详情'),
  (2042, '事项新增',     2040, 2,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:add',       '#', 'admin', sysdate(), '', null, '新增临时事项、隐患、总结和上报记录'),
  (2043, '事项修改',     2040, 3,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:edit',      '#', 'admin', sysdate(), '', null, '编辑通用事项和报表记录'),
  (2044, '事项删除',     2040, 4,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:remove',    '#', 'admin', sysdate(), '', null, '删除通用管理记录'),
  (2045, '附件上传',     2040, 5,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:upload',    '#', 'admin', sysdate(), '', null, '上传佐证材料和报表附件'),
  (2046, '事项提交',     2040, 6,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:submit',    '#', 'admin', sysdate(), '', null, '提交事项、总结或上报记录'),
  (2047, '事项审核',     2040, 7,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:review',    '#', 'admin', sysdate(), '', null, '审核事项、确认隐患整改和审核报表'),
  (2048, '事项闭环',     2040, 8,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:close',     '#', 'admin', sysdate(), '', null, '闭环临时事项、隐患和待办'),
  (2049, '统计分析',     2040, 9,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:statistics','#', 'admin', sysdate(), '', null, '查看统计报表和态势分析'),
  (2050, '数据上报',     2040, 10, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:report',    '#', 'admin', sysdate(), '', null, '生成或提交数据上报'),
  (2051, '归档发布',     2040, 11, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:archive',   '#', 'admin', sysdate(), '', null, '发布报表、归档记录和导出上报数据')
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

-- 7) 所有非超级管理员角色至少能看到通用管理并查询。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2049)
where r.role_id <> 1;

-- 8) 经办人：新增、编辑、上传、提交、闭环、数据上报。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2042, 2043, 2045, 2046, 2048, 2049, 2050)
where r.role_key = 'rail_handler';

-- 9) 审核人：审核事项、确认隐患整改、查看统计。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2043, 2047, 2048, 2049, 2050)
where r.role_key = 'rail_reviewer';

-- 10) 终审人：归档、发布报表、导出上报数据。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2043, 2047, 2048, 2049, 2050, 2051)
where r.role_key = 'rail_final_reviewer';

commit;

-- 11) 执行后检查
select table_name, table_comment
from information_schema.tables
where table_schema = database()
  and table_name in ('rail_general_item', 'rail_general_attachment', 'rail_general_report', 'rail_general_log')
order by table_name;

select menu_id, menu_name, parent_id, order_num, path, component, perms, visible, status
from sys_menu
where menu_id between 2040 and 2051
order by parent_id, order_num, menu_id;

select r.role_id, r.role_name, r.role_key, group_concat(m.menu_id order by m.menu_id) as menu_ids
from sys_role r
left join sys_role_menu rm on rm.role_id = r.role_id
left join sys_menu m on m.menu_id = rm.menu_id and m.menu_id between 2040 and 2051
group by r.role_id, r.role_name, r.role_key
order by r.role_id;
