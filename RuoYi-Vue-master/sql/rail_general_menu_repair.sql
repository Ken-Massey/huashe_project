-- 通用管理菜单权限修复脚本
-- 用途：前端已经添加“通用管理”页面但左侧菜单不显示、普通账号无权限时执行。
-- 执行库：huashe_database

start transaction;

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
  visible = values(visible),
  status = values(status),
  perms = values(perms),
  icon = values(icon),
  update_by = 'admin',
  update_time = sysdate(),
  remark = values(remark);

insert into sys_menu (
  menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
  is_frame, is_cache, menu_type, visible, status, perms, icon,
  create_by, create_time, update_by, update_time, remark
) values
  (2041, '通用查询', 2040, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:query', '#', 'admin', sysdate(), '', null, '查看通用事项和报表详情'),
  (2042, '事项新增', 2040, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:add', '#', 'admin', sysdate(), '', null, '新增临时事项、隐患、总结和上报记录'),
  (2043, '事项修改', 2040, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:edit', '#', 'admin', sysdate(), '', null, '编辑通用事项和报表记录'),
  (2044, '事项删除', 2040, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:remove', '#', 'admin', sysdate(), '', null, '删除通用管理记录'),
  (2045, '附件上传', 2040, 5, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:upload', '#', 'admin', sysdate(), '', null, '上传佐证材料和报表附件'),
  (2046, '事项提交', 2040, 6, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:submit', '#', 'admin', sysdate(), '', null, '提交事项、总结或上报记录'),
  (2047, '事项审核', 2040, 7, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:review', '#', 'admin', sysdate(), '', null, '审核事项、确认隐患整改和审核报表'),
  (2048, '事项闭环', 2040, 8, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:close', '#', 'admin', sysdate(), '', null, '闭环临时事项、隐患和待办'),
  (2049, '统计分析', 2040, 9, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:statistics', '#', 'admin', sysdate(), '', null, '查看统计报表和态势分析'),
  (2050, '数据上报', 2040, 10, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:report', '#', 'admin', sysdate(), '', null, '生成或提交数据上报'),
  (2051, '归档发布', 2040, 11, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:general:archive', '#', 'admin', sysdate(), '', null, '发布报表、归档记录和导出上报数据')
on duplicate key update
  menu_name = values(menu_name),
  parent_id = values(parent_id),
  order_num = values(order_num),
  perms = values(perms),
  visible = values(visible),
  status = values(status),
  update_by = 'admin',
  update_time = sysdate(),
  remark = values(remark);

-- 所有业务账号至少可进入通用管理并查看统计。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2049)
where r.role_id <> 1;

-- 经办人：登记、编辑、上传、提交、闭环、数据上报。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2042, 2043, 2045, 2046, 2048, 2049, 2050)
where r.role_key = 'rail_handler';

-- 审核人：审核、闭环确认、统计、数据上报查看。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2043, 2047, 2048, 2049, 2050)
where r.role_key = 'rail_reviewer';

-- 终审人：审核、归档发布、统计和上报。
insert ignore into sys_role_menu (role_id, menu_id)
select r.role_id, m.menu_id
from sys_role r
join sys_menu m on m.menu_id in (2000, 2040, 2041, 2043, 2047, 2048, 2049, 2050, 2051)
where r.role_key = 'rail_final_reviewer';

commit;

select r.role_key, r.role_name, group_concat(m.menu_id order by m.menu_id) as general_menu_ids
from sys_role r
left join sys_role_menu rm on rm.role_id = r.role_id
left join sys_menu m on m.menu_id = rm.menu_id and m.menu_id between 2040 and 2051
group by r.role_key, r.role_name
order by min(r.role_id);
