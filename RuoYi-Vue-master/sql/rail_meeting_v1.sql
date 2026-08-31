-- 会议协调管理 v1：数据库表、菜单与权限初始化
-- 执行库：huashe_database
-- 用途：实现保护区方案评审会、协调会、专题会的线上管理基础结构。
-- 说明：本脚本可重复执行；账号体系继续沿用若依 sys_user、sys_role、sys_user_role、sys_role_menu。

-- 1) 会议主表
create table if not exists rail_meeting (
  meeting_id          bigint(20)      not null auto_increment comment '会议ID',
  meeting_code        varchar(64)     default ''               comment '会议编号',
  meeting_name        varchar(200)    not null                  comment '会议名称',
  meeting_type        varchar(40)     default ''               comment '会议类型：review/coordination/special/expert/technical/other',
  project_id          varchar(64)     default null              comment '关联项目ID',
  project_name        varchar(200)    default ''               comment '关联项目名称',
  audit_id            varchar(64)     default null              comment '关联审核记录ID',
  workflow_id         bigint(20)      default null              comment '关联审核流程ID',
  meeting_time        datetime        default null              comment '会议时间',
  meeting_end_time    datetime        default null              comment '会议结束时间',
  meeting_place       varchar(255)    default ''               comment '会议地点',
  online_url          varchar(500)    default ''               comment '线上会议链接',
  host_unit           varchar(200)    default ''               comment '主持单位',
  organize_unit       varchar(200)    default ''               comment '组织单位',
  meeting_topic       varchar(500)    default ''               comment '会议主题',
  agenda              text                                    comment '会议议程',
  notice_content      text                                    comment '会议通知内容',
  notice_time         datetime        default null              comment '通知发送时间',
  status              varchar(32)     default 'draft'           comment '状态：draft/notified/held/minuting/tracking/archived/cancelled',
  archive_status      char(1)         default '0'               comment '归档状态：0未归档 1已归档',
  archive_time        datetime        default null              comment '归档时间',
  remark              varchar(500)    default ''               comment '备注',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (meeting_id),
  unique key uk_rail_meeting_code (meeting_code),
  key idx_rail_meeting_project (project_id),
  key idx_rail_meeting_status (status),
  key idx_rail_meeting_time (meeting_time),
  key idx_rail_meeting_creator (create_by)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-会议主表';

-- 2) 参会人员表
create table if not exists rail_meeting_participant (
  participant_id      bigint(20)      not null auto_increment comment '参会人员ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  user_id             bigint(20)      default null              comment '系统用户ID',
  participant_name    varchar(80)     not null                  comment '姓名',
  unit_name           varchar(200)    default ''               comment '单位',
  duty                varchar(100)    default ''               comment '职务/岗位',
  phone               varchar(30)     default ''               comment '联系电话',
  email               varchar(100)    default ''               comment '邮箱',
  participant_role    varchar(40)     default ''               comment '参会角色：host/organizer/expert/member/owner/design/construct/supervision/rail/other',
  sign_status         char(1)         default '0'               comment '签到状态：0未签到 1已签到',
  sign_time           datetime        default null              comment '签到时间',
  sign_remark         varchar(255)    default ''               comment '签到备注',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  primary key (participant_id),
  key idx_rail_meeting_participant_meeting (meeting_id),
  key idx_rail_meeting_participant_user (user_id)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-参会人员表';

-- 3) 会议材料表
create table if not exists rail_meeting_file (
  file_id             bigint(20)      not null auto_increment comment '文件ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  file_type           varchar(40)     default 'material'        comment '文件类型：notice/material/minutes/sign/issue/decision/todo/archive/other',
  file_name           varchar(255)    not null                  comment '原文件名',
  stored_name         varchar(255)    default ''               comment '存储文件名',
  file_path           varchar(1000)   not null                  comment '文件路径',
  file_size           bigint(20)      default 0                 comment '文件大小',
  mime_type           varchar(100)    default ''               comment 'MIME类型',
  description         varchar(500)    default ''               comment '文件说明',
  create_by           varchar(64)     default ''               comment '上传者',
  create_time         datetime        default null              comment '上传时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (file_id),
  key idx_rail_meeting_file_meeting (meeting_id),
  key idx_rail_meeting_file_type (file_type)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-会议材料表';

-- 4) 会议纪要表
create table if not exists rail_meeting_minutes (
  minutes_id          bigint(20)      not null auto_increment comment '纪要ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  minutes_title       varchar(200)    default ''               comment '纪要标题',
  minutes_content     longtext                                comment '纪要正文',
  compile_user_id     bigint(20)      default null              comment '编制人ID',
  compile_by          varchar(64)     default ''               comment '编制人',
  compile_time        datetime        default null              comment '编制时间',
  confirm_status      char(1)         default '0'               comment '确认状态：0草稿 1待确认 2已确认 3退回',
  confirm_user_id     bigint(20)      default null              comment '确认人ID',
  confirm_by          varchar(64)     default ''               comment '确认人',
  confirm_time        datetime        default null              comment '确认时间',
  confirm_opinion     varchar(1000)   default ''               comment '确认意见',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  primary key (minutes_id),
  key idx_rail_meeting_minutes_meeting (meeting_id),
  key idx_rail_meeting_minutes_status (confirm_status)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-会议纪要表';

-- 5) 问题清单表
create table if not exists rail_meeting_issue (
  issue_id            bigint(20)      not null auto_increment comment '问题ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  issue_title         varchar(200)    not null                  comment '问题标题',
  issue_content       text                                    comment '问题内容',
  issue_type          varchar(40)     default ''               comment '问题类型：technical/procedure/material/safety/coordination/other',
  risk_level          varchar(20)     default ''               comment '风险等级',
  responsible_unit    varchar(200)    default ''               comment '责任单位',
  responsible_user    varchar(80)     default ''               comment '责任人',
  due_time            datetime        default null              comment '要求完成时间',
  status              varchar(32)     default 'open'            comment '状态：open/processing/resolved/closed',
  close_time          datetime        default null              comment '关闭时间',
  close_remark        varchar(1000)   default ''               comment '关闭说明',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (issue_id),
  key idx_rail_meeting_issue_meeting (meeting_id),
  key idx_rail_meeting_issue_status (status),
  key idx_rail_meeting_issue_due (due_time)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-问题清单表';

-- 6) 决议事项表
create table if not exists rail_meeting_decision (
  decision_id         bigint(20)      not null auto_increment comment '决议ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  decision_title      varchar(200)    not null                  comment '决议标题',
  decision_content    text                                    comment '决议内容',
  responsible_unit    varchar(200)    default ''               comment '责任单位',
  responsible_user    varchar(80)     default ''               comment '责任人',
  due_time            datetime        default null              comment '要求完成时间',
  status              varchar(32)     default 'open'            comment '状态：open/processing/completed/closed',
  close_time          datetime        default null              comment '关闭时间',
  close_remark        varchar(1000)   default ''               comment '关闭说明',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (decision_id),
  key idx_rail_meeting_decision_meeting (meeting_id),
  key idx_rail_meeting_decision_status (status),
  key idx_rail_meeting_decision_due (due_time)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-决议事项表';

-- 7) 待办事项表
create table if not exists rail_meeting_todo (
  todo_id             bigint(20)      not null auto_increment comment '待办ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  source_type         varchar(40)     default 'manual'          comment '来源：issue/decision/manual',
  source_id           bigint(20)      default null              comment '来源ID',
  todo_title          varchar(200)    not null                  comment '待办标题',
  todo_content        text                                    comment '待办内容',
  responsible_unit    varchar(200)    default ''               comment '责任单位',
  responsible_user_id bigint(20)      default null              comment '责任人用户ID',
  responsible_user    varchar(80)     default ''               comment '责任人',
  due_time            datetime        default null              comment '截止时间',
  priority            varchar(20)     default 'normal'          comment '优先级：high/normal/low',
  status              varchar(32)     default 'pending'         comment '状态：pending/processing/done/closed/overdue',
  finish_content      text                                    comment '完成说明',
  finish_time         datetime        default null              comment '完成时间',
  close_time          datetime        default null              comment '闭环时间',
  close_by            varchar(64)     default ''               comment '闭环确认人',
  close_remark        varchar(1000)   default ''               comment '闭环说明',
  create_by           varchar(64)     default ''               comment '创建者',
  create_time         datetime        default null              comment '创建时间',
  update_by           varchar(64)     default ''               comment '更新者',
  update_time         datetime        default null              comment '更新时间',
  del_flag            char(1)         default '0'               comment '删除标志：0存在 2删除',
  primary key (todo_id),
  key idx_rail_meeting_todo_meeting (meeting_id),
  key idx_rail_meeting_todo_responsible (responsible_user_id),
  key idx_rail_meeting_todo_status (status),
  key idx_rail_meeting_todo_due (due_time)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-待办事项表';

-- 8) 操作留痕表
create table if not exists rail_meeting_log (
  log_id              bigint(20)      not null auto_increment comment '日志ID',
  meeting_id          bigint(20)      not null                  comment '会议ID',
  target_type         varchar(40)     default 'meeting'         comment '对象类型：meeting/participant/file/minutes/issue/decision/todo/archive',
  target_id           bigint(20)      default null              comment '对象ID',
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
  key idx_rail_meeting_log_meeting (meeting_id),
  key idx_rail_meeting_log_target (target_type, target_id),
  key idx_rail_meeting_log_time (create_time)
) engine=innodb auto_increment=1 default charset=utf8mb4 comment='会议协调管理-操作留痕表';

-- 9) 菜单顺序：会议协调管理位于现场符合性巡查和知识库之间。
update sys_menu
set order_num = 5, update_by = 'admin', update_time = sysdate()
where menu_id = 2004 and parent_id = 2000;

update sys_menu
set order_num = 6, update_by = 'admin', update_time = sysdate()
where menu_id = 2005 and parent_id = 2000;

insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values (
  2007, '会议协调管理', 2000, 4, 'meeting', 'rail/meeting/index', '', '',
  1, 0, 'C', '0', '0', 'rail:meeting:list', 'peoples',
  'admin', sysdate(), '', null, '会议通知、参会登记、材料上传、纪要编制、问题决议和待办闭环'
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

-- 10) 按钮权限，挂在“会议协调管理”菜单下。
insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values
  (2026, '会议查询',     2007, 1,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:query',       '#', 'admin', sysdate(), '', null, '查看会议详情'),
  (2027, '会议新增',     2007, 2,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:add',         '#', 'admin', sysdate(), '', null, '新建会议'),
  (2028, '会议修改',     2007, 3,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:edit',        '#', 'admin', sysdate(), '', null, '编辑会议基本信息'),
  (2029, '会议删除',     2007, 4,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:remove',      '#', 'admin', sysdate(), '', null, '删除会议记录'),
  (2030, '发送通知',     2007, 5,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:notify',      '#', 'admin', sysdate(), '', null, '发送会议通知'),
  (2031, '参会登记',     2007, 6,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:participant', '#', 'admin', sysdate(), '', null, '维护参会人员和签到信息'),
  (2032, '材料上传',     2007, 7,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:file',        '#', 'admin', sysdate(), '', null, '上传会议通知、材料、签到表和附件'),
  (2033, '纪要编制',     2007, 8,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:minutes',     '#', 'admin', sysdate(), '', null, '编制和修改会议纪要'),
  (2034, '问题决议维护', 2007, 9,  '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:item',        '#', 'admin', sysdate(), '', null, '维护问题清单和决议事项'),
  (2035, '待办闭环',     2007, 10, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:todo',        '#', 'admin', sysdate(), '', null, '办理和关闭会议待办'),
  (2036, '纪要确认',     2007, 11, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:confirm',     '#', 'admin', sysdate(), '', null, '审核确认会议纪要'),
  (2037, '会议归档',     2007, 12, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:meeting:archive',     '#', 'admin', sysdate(), '', null, '将会议全过程资料归档')
on duplicate key update
  menu_name = values(menu_name),
  parent_id = values(parent_id),
  order_num = values(order_num),
  perms = values(perms),
  update_by = 'admin',
  update_time = sysdate(),
  remark = values(remark);

-- 11) 默认授权。
-- 所有普通角色均可看到会议模块并查看自己相关会议。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2007, 2026)
where r.del_flag = '0'
  and r.status = '0'
  and r.role_id <> 1;

-- 经办人：会议创建、通知、参会登记、材料上传、纪要编制、问题/决议/待办维护。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2007, 2026, 2027, 2028, 2030, 2031, 2032, 2033, 2034, 2035)
where r.role_key = 'rail_handler';

-- 审核人：会议查看、纪要确认、问题决议和待办跟踪。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2007, 2026, 2034, 2035, 2036)
where r.role_key = 'rail_reviewer';

-- 终审人：会议查看、纪要确认、归档。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2007, 2026, 2036, 2037)
where r.role_key = 'rail_final_reviewer';
