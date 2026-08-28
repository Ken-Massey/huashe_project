-- 轨道智审角色权限同步脚本
-- 执行库：huashe_database
-- 用途：
-- 1. 所有普通角色都能看到案例审核、现场符合性巡查、知识库、项目档案模块。
-- 2. 经办人、审核人、终审人按流程职责分配按钮权限。
-- 3. 账号体系沿用若依 sys_user、sys_role、sys_user_role、sys_role_menu。

set @handler_role_id := (select role_id from sys_role where role_key = 'rail_handler' limit 1);
set @reviewer_role_id := (select role_id from sys_role where role_key = 'rail_reviewer' limit 1);
set @final_role_id := (select role_id from sys_role where role_key = 'rail_final_reviewer' limit 1);

-- 确保三个流程角色存在。
insert into sys_role
  (role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
select '经办人', 'rail_handler', 10, '1', 1, 1, '0', '0', 'admin', sysdate(), '案例审核上传、发起审核、查看结果、提交审核'
where @handler_role_id is null;

insert into sys_role
  (role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
select '审核人', 'rail_reviewer', 11, '1', 1, 1, '0', '0', 'admin', sysdate(), '审核流转通过、退回、提交终审'
where @reviewer_role_id is null;

insert into sys_role
  (role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
select '终审人', 'rail_final_reviewer', 12, '1', 1, 1, '0', '0', 'admin', sysdate(), '终审确认、流程归档'
where @final_role_id is null;

set @handler_role_id := (select role_id from sys_role where role_key = 'rail_handler' limit 1);
set @reviewer_role_id := (select role_id from sys_role where role_key = 'rail_reviewer' limit 1);
set @final_role_id := (select role_id from sys_role where role_key = 'rail_final_reviewer' limit 1);

update sys_role
set role_name = '经办人',
    remark = '案例审核上传、发起审核、查看结果、提交审核'
where role_key = 'rail_handler';

update sys_role
set role_name = '审核人',
    remark = '审核流转通过、退回、提交终审'
where role_key = 'rail_reviewer';

update sys_role
set role_name = '终审人',
    remark = '终审确认、流程归档'
where role_key = 'rail_final_reviewer';

-- 新增更细的流程按钮权限。
insert into sys_menu
  (menu_id, menu_name, parent_id, order_num, path, component, query, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
values
  (2024, '提交终审', 2001, 15, '#', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:submitFinal', '#', 'admin', sysdate(), '审核人提交至终审节点'),
  (2025, '终审通过', 2001, 16, '#', '', '', 1, 0, 'F', '0', '0', 'rail:audit:workflow:final', '#', 'admin', sysdate(), '终审人确认通过流程')
on duplicate key update
  menu_name = values(menu_name),
  parent_id = values(parent_id),
  order_num = values(order_num),
  perms = values(perms),
  remark = values(remark);

update sys_menu
set menu_name = '审核通过',
    perms = 'rail:audit:workflow:approve',
    remark = '审核人通过复核节点'
where menu_id = 2020;

update sys_menu
set menu_name = '流程归档',
    perms = 'rail:audit:workflow:archive',
    remark = '终审通过后归档到项目档案'
where menu_id = 2022;

-- 所有普通角色开放基础模块入口。AI智能体为前端静态入口，无需 sys_menu 权限。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013)
where r.del_flag = '0'
  and r.status = '0'
  and r.role_id <> 1;

-- 先清理三个流程角色的业务按钮权限，避免旧授权残留导致越权。
delete rm
from sys_role_menu rm
join sys_role r on r.role_id = rm.role_id
where r.role_key in ('rail_handler', 'rail_reviewer', 'rail_final_reviewer')
  and rm.menu_id in (
    2010, 2011, 2012, 2013,
    2014, 2015, 2016, 2017,
    2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
  );

-- 清理后重新补回公共模块入口和项目档案审核记录查看权限，确保流程角色仍能使用基础页面。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013)
where r.del_flag = '0'
  and r.status = '0'
  and r.role_id <> 1;

-- 经办人：案例审核上传、发起审核、查看结果；审核流转提交审核、查看自己相关流程。
insert ignore into sys_role_menu (role_id, menu_id)
select @handler_role_id, m.menu_id
from sys_menu m
where @handler_role_id is not null
  and m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2019);

-- 审核人：通过、退回、提交终审。
insert ignore into sys_role_menu (role_id, menu_id)
select @reviewer_role_id, m.menu_id
from sys_menu m
where @reviewer_role_id is not null
  and m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2020, 2021, 2024);

-- 终审人：终审、归档。
insert ignore into sys_role_menu (role_id, menu_id)
select @final_role_id, m.menu_id
from sys_menu m
where @final_role_id is not null
  and m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2022, 2025);
