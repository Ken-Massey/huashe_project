-- 现场符合性巡查 v2：任务驱动 + 小程序账号 + 整改闭环（菜单权限、巡查员角色、关闭验证码）
-- 可重复执行；在 v1（rail_patrol_menu.sql）基础上重映射按钮权限，并新增巡查员角色。

-- 1) 现场符合性巡查菜单（2006，权限 rail:patrol:list）
insert into sys_menu (
    menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
) values (
    2006, '现场符合性巡查', 2000, 3, 'patrol', 'rail/patrol/index', '', '',
    1, 0, 'C', '0', '0', 'rail:patrol:list', 'location',
    'admin', sysdate(), '', null, '巡查任务派发、现场媒体上报、问题隐患整改闭环'
)
on duplicate key update
    menu_name = values(menu_name), parent_id = values(parent_id), order_num = values(order_num),
    path = values(path), component = values(component), query = values(query),
    route_name = values(route_name), is_frame = values(is_frame), is_cache = values(is_cache),
    menu_type = values(menu_type), visible = values(visible), status = values(status),
    perms = values(perms), icon = values(icon), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

-- 2) 按钮权限（2014-2017 复用 v1 的 ID，权限串重映射）
insert into sys_menu (
    menu_id, menu_name, parent_id, order_num, path, component, query, route_name,
    is_frame, is_cache, menu_type, visible, status, perms, icon,
    create_by, create_time, update_by, update_time, remark
) values
    (2014, '巡查上传', 2006, 1, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:upload', '#', 'admin', sysdate(), '', null, '上传现场媒体、记录隐患、提交整改复核'),
    (2015, '任务管理', 2006, 2, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:manage', '#', 'admin', sysdate(), '', null, '新建/派发/改派/状态/删除巡查任务'),
    (2016, '隐患核查', 2006, 3, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:review',  '#', 'admin', sysdate(), '', null, '确认隐患、下发整改要求、复核闭环'),
    (2017, '字典维护', 2006, 4, '#', '', '', '', 1, 0, 'F', '0', '0', 'rail:patrol:dict',    '#', 'admin', sysdate(), '', null, '维护线路、施工类型、隐患类型、风险等级')
on duplicate key update
    menu_name = values(menu_name), parent_id = values(parent_id), order_num = values(order_num),
    path = values(path), component = values(component), query = values(query),
    route_name = values(route_name), is_frame = values(is_frame), is_cache = values(is_cache),
    menu_type = values(menu_type), visible = values(visible), status = values(status),
    perms = values(perms), icon = values(icon), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

-- 3) 巡查员角色（小程序账号专用）
insert into sys_role (
    role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly,
    status, del_flag, create_by, create_time, update_by, update_time, remark
) values (
    100, '巡查员', 'patrol', 3, '1', 1, 1, '0', '0', 'admin', sysdate(), '', null,
    '现场符合性巡查小程序账号角色（仅查看被指派任务并上报）'
)
on duplicate key update
    role_name = values(role_name), role_key = values(role_key), update_by = 'admin',
    update_time = sysdate(), remark = values(remark);

-- 4) 巡查员角色：查看 + 上传
insert ignore into sys_role_menu (role_id, menu_id) values (100, 2006);
insert ignore into sys_role_menu (role_id, menu_id) values (100, 2014);

-- 5) 已拥有“案例审核”（2001）的既有角色获得全部巡查权限
insert ignore into sys_role_menu (role_id, menu_id) select role_id, 2006 from sys_role_menu where menu_id = 2001;
insert ignore into sys_role_menu (role_id, menu_id) select role_id, 2014 from sys_role_menu where menu_id = 2001;
insert ignore into sys_role_menu (role_id, menu_id) select role_id, 2015 from sys_role_menu where menu_id = 2001;
insert ignore into sys_role_menu (role_id, menu_id) select role_id, 2016 from sys_role_menu where menu_id = 2001;
insert ignore into sys_role_menu (role_id, menu_id) select role_id, 2017 from sys_role_menu where menu_id = 2001;

-- 6) 关闭 Web 登录验证码（小程序走独立 /miniapp/login，免验证码）
update sys_config set config_value = 'false' where config_key = 'sys.account.captchaEnabled';
