-- 会议协调管理菜单修复脚本
-- 用途：前端代码已添加但左侧菜单不显示时，补齐 sys_menu 与 sys_role_menu。
-- 执行库：当前系统正在使用的业务库，例如 huashe_database。

START TRANSACTION;

-- 1. 确保模块菜单存在：位于“现场符合性巡查”和“知识库”之间
INSERT INTO sys_menu
(menu_id, menu_name, parent_id, order_num, path, component, `query`, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES
(2007, '会议协调管理', 2000, 4, 'meeting', 'rail/meeting/index', NULL, 'RailMeeting', 1, 0, 'C', '0', '0', 'rail:meeting:list', 'peoples', 'admin', NOW(), '', NULL, '会议协调管理菜单')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  path = VALUES(path),
  component = VALUES(component),
  route_name = VALUES(route_name),
  visible = VALUES(visible),
  status = VALUES(status),
  perms = VALUES(perms),
  icon = VALUES(icon),
  update_by = 'admin',
  update_time = NOW();

-- 2. 调整后续菜单顺序
UPDATE sys_menu SET order_num = 5, update_by = 'admin', update_time = NOW() WHERE menu_id = 2004 AND menu_name = '知识库';
UPDATE sys_menu SET order_num = 6, update_by = 'admin', update_time = NOW() WHERE menu_id = 2005 AND menu_name = '项目档案';

-- 3. 补齐按钮/操作权限
INSERT INTO sys_menu
(menu_id, menu_name, parent_id, order_num, path, component, `query`, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES
(2026, '会议查询', 2007, 1, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:query', '#', 'admin', NOW(), '', NULL, ''),
(2027, '会议新增', 2007, 2, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:add', '#', 'admin', NOW(), '', NULL, ''),
(2028, '会议修改', 2007, 3, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:edit', '#', 'admin', NOW(), '', NULL, ''),
(2029, '会议删除', 2007, 4, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:remove', '#', 'admin', NOW(), '', NULL, ''),
(2030, '会议通知', 2007, 5, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:notify', '#', 'admin', NOW(), '', NULL, ''),
(2031, '参会人员', 2007, 6, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:participant', '#', 'admin', NOW(), '', NULL, ''),
(2032, '会议材料', 2007, 7, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:file', '#', 'admin', NOW(), '', NULL, ''),
(2033, '会议纪要', 2007, 8, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:minutes', '#', 'admin', NOW(), '', NULL, ''),
(2034, '事项记录', 2007, 9, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:item', '#', 'admin', NOW(), '', NULL, ''),
(2035, '待办闭环', 2007, 10, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:todo', '#', 'admin', NOW(), '', NULL, ''),
(2036, '纪要确认', 2007, 11, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:confirm', '#', 'admin', NOW(), '', NULL, ''),
(2037, '会议归档', 2007, 12, '#', '', NULL, '', 1, 0, 'F', '0', '0', 'rail:meeting:archive', '#', 'admin', NOW(), '', NULL, '')
ON DUPLICATE KEY UPDATE
  menu_name = VALUES(menu_name),
  parent_id = VALUES(parent_id),
  order_num = VALUES(order_num),
  perms = VALUES(perms),
  update_by = 'admin',
  update_time = NOW();

-- 4. 让所有非超级管理员角色至少能看到菜单、进入页面、查询列表
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (2000, 2007, 2026)
WHERE r.role_id <> 1;

-- 5. 按业务角色补充操作权限
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (2000, 2007, 2026, 2027, 2028, 2030, 2031, 2032, 2033, 2034, 2035)
WHERE r.role_key = 'rail_handler';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (2000, 2007, 2026, 2028, 2034, 2035, 2036)
WHERE r.role_key = 'rail_reviewer';

INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
FROM sys_role r
JOIN sys_menu m ON m.menu_id IN (2000, 2007, 2026, 2028, 2036, 2037)
WHERE r.role_key = 'rail_final_reviewer';

COMMIT;

-- 6. 执行后检查：应能看到“会议协调管理”及当前角色授权
SELECT menu_id, menu_name, parent_id, order_num, path, component, perms, visible, status
FROM sys_menu
WHERE menu_id IN (2000, 2004, 2005, 2007, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037)
ORDER BY parent_id, order_num, menu_id;

SELECT r.role_id, r.role_name, r.role_key, m.menu_id, m.menu_name, m.perms
FROM sys_role r
JOIN sys_role_menu rm ON rm.role_id = r.role_id
JOIN sys_menu m ON m.menu_id = rm.menu_id
WHERE m.menu_id IN (2007, 2026)
ORDER BY r.role_id, m.menu_id;
