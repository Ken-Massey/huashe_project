-- 轨道交通保护区智能审核菜单增量迁移
-- 可重复执行：保留现有 2000-2004 菜单和角色授权，仅安装项目档案及其按钮权限。

-- 项目档案排在知识库之前；仅在目标记录仍是知识库时调整排序。
update sys_menu
set order_num = 5, update_by = 'admin', update_time = sysdate()
where menu_id = 2004 and parent_id = 2000 and path = 'knowledge';

insert into sys_menu (
    menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
) values (
    2005, '项目档案', 2000, 4, 'archive', 'rail/archive/index', '', '',
    1, 0, 'C', '0', '0', 'rail:archive:list', 'documentation',
    'admin', sysdate(), '', null, '按项目和自定义阶段管理唯一审核记录'
)
on duplicate key update
    menu_name = values(menu_name), parent_id = values(parent_id), order_num = values(order_num),
    path = values(path), component = values(component), query = values(query),
    route_name = values(route_name), is_frame = values(is_frame), is_cache = values(is_cache),
    menu_type = values(menu_type), visible = values(visible), status = values(status),
    perms = values(perms), icon = values(icon), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

insert into sys_menu (
    menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
) values
    (2010, '项目阶段新增', 2005, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:archive:add',        '#', 'admin', sysdate(), '', null, '新增项目或人工阶段'),
    (2011, '项目阶段编辑', 2005, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:archive:edit',       '#', 'admin', sysdate(), '', null, '编辑、排序或恢复项目阶段'),
    (2012, '项目阶段归档', 2005, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:archive:remove',     '#', 'admin', sysdate(), '', null, '软归档项目或阶段，不删除审核历史'),
    (2013, '审核记录查看', 2005, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:archive:audit:list', '#', 'admin', sysdate(), '', null, '查看阶段审核详情、历史上下文和任务结果')
on duplicate key update
    menu_name = values(menu_name), parent_id = values(parent_id), order_num = values(order_num),
    path = values(path), component = values(component), query = values(query),
    route_name = values(route_name), is_frame = values(is_frame), is_cache = values(is_cache),
    menu_type = values(menu_type), visible = values(visible), status = values(status),
    perms = values(perms), icon = values(icon), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

-- 已拥有“案例一键审核”的非管理员角色自动获得项目档案入口和审核记录查看权限。
-- 项目/阶段的编辑、归档权限仍由管理员在角色管理中单独分配。
insert ignore into sys_role_menu (role_id, menu_id)
select role_id, 2005 from sys_role_menu where menu_id = 2002;

insert ignore into sys_role_menu (role_id, menu_id)
select role_id, 2013 from sys_role_menu where menu_id = 2002;
