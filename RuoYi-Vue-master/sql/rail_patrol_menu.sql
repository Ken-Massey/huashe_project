-- 现场符合性巡查菜单与按钮权限增量迁移
-- 可重复执行：安装“现场符合性巡查”菜单（2006）及其按钮权限（2014-2017），
-- 并给已拥有“案例审核”（2001）的角色自动授予查看、核查、归档权限。
-- 删除（rail:patrol:remove）与字典维护（rail:patrol:dict）默认仅管理员分配。

insert into sys_menu (
    menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
) values (
    2006, '现场符合性巡查', 2000, 3, 'patrol', 'rail/patrol/index', '', '',
    1, 0, 'C', '0', '0', 'rail:patrol:list', 'location',
    'admin', sysdate(), '', null, '施工事件、现场照片上传与人工符合性核查'
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
    (2014, '巡查事件核查', 2006, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:review',  '#', 'admin', sysdate(), '', null, '对施工事件给出符合/不符合结论与核查意见'),
    (2015, '巡查事件归档', 2006, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:archive', '#', 'admin', sysdate(), '', null, '归档已核查的施工事件'),
    (2016, '巡查事件删除', 2006, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:remove',  '#', 'admin', sysdate(), '', null, '软删除待核查的施工事件'),
    (2017, '巡查字典维护', 2006, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:dict',    '#', 'admin', sysdate(), '', null, '维护线路、施工类型等巡查字典')
on duplicate key update
    menu_name = values(menu_name), parent_id = values(parent_id), order_num = values(order_num),
    path = values(path), component = values(component), query = values(query),
    route_name = values(route_name), is_frame = values(is_frame), is_cache = values(is_cache),
    menu_type = values(menu_type), visible = values(visible), status = values(status),
    perms = values(perms), icon = values(icon), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

-- 已拥有“案例审核”的非管理员角色自动获得巡查查看、核查、归档权限。
-- 删除与字典维护仍由管理员在角色管理中单独分配。
insert ignore into sys_role_menu (role_id, menu_id)
select role_id, 2006 from sys_role_menu where menu_id = 2001;

insert ignore into sys_role_menu (role_id, menu_id)
select role_id, 2014 from sys_role_menu where menu_id = 2001;

insert ignore into sys_role_menu (role_id, menu_id)
select role_id, 2015 from sys_role_menu where menu_id = 2001;
