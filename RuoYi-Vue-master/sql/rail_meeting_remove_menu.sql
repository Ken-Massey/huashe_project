-- 移除“会议协调管理”菜单与权限。
-- 说明：本脚本只清理 sys_menu / sys_role_menu 中的菜单入口和按钮权限，
-- 不删除 rail_meeting 等业务数据表，避免误删已有会议历史数据。

START TRANSACTION;

CREATE TEMPORARY TABLE tmp_rail_meeting_menu_ids AS
SELECT menu_id
FROM sys_menu
WHERE menu_id = 2007
   OR parent_id = 2007
   OR path = 'meeting'
   OR component = 'rail/meeting/index'
   OR perms LIKE 'rail:meeting:%';

DELETE rm
FROM sys_role_menu rm
JOIN tmp_rail_meeting_menu_ids t ON rm.menu_id = t.menu_id;

DELETE m
FROM sys_menu m
JOIN tmp_rail_meeting_menu_ids t ON m.menu_id = t.menu_id;

DROP TEMPORARY TABLE tmp_rail_meeting_menu_ids;

COMMIT;
