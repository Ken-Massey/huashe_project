-- 将已有数据库中的三个审核入口合并为“案例审核”。
-- 执行前请备份数据库；执行后重新登录系统以刷新动态菜单。

update sys_menu
set menu_name = '案例审核',
    order_num = '1',
    path = 'audit',
    component = 'rail/audit/index',
    perms = 'rail:audit:run',
    icon = 'checkbox',
    remark = '函件识别、案例审核、审核意见与复函生成'
where menu_id = 2001;

delete from sys_role_menu where menu_id in (2002, 2003);
delete from sys_menu where menu_id in (2002, 2003);

update sys_menu set order_num = '2' where menu_id = 2004;
