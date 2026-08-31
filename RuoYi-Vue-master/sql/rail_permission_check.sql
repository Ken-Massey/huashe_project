-- 权限排查脚本：确认某个账号是否拿到了轨道智审菜单权限。
-- 使用前把 @user_name 改成要排查的登录账号，例如 'ry'、'admin' 或你的普通用户账号。

set @user_name := '普通用户账号';

select
  u.user_name,
  r.role_name,
  r.role_key,
  m.menu_id,
  m.menu_name,
  m.perms,
  m.visible,
  m.status
from sys_user u
join sys_user_role ur on ur.user_id = u.user_id
join sys_role r on r.role_id = ur.role_id
join sys_role_menu rm on rm.role_id = r.role_id
join sys_menu m on m.menu_id = rm.menu_id
where u.user_name = @user_name
  and (
    m.menu_id in (2000, 2001, 2004, 2005, 2006, 2013, 2018, 2019, 2020, 2021, 2022, 2024, 2025)
    or m.perms like 'rail:%'
  )
order by r.role_sort, m.parent_id, m.order_num, m.menu_id;

-- 如果开始审核仍提示“当前操作没有权限”，重点看结果中是否存在：
-- menu_id = 2001 且 perms = rail:audit:run
-- 如果现场符合性巡查仍提示“当前操作没有权限”，重点看结果中是否存在：
-- menu_id = 2006 且 perms = rail:patrol:list
