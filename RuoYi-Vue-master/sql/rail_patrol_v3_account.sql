-- 现场符合性巡查 v3：账号限权管理（平台/小程序登录权限）
-- 在 rail_patrol_v2_menu.sql 之后执行；本文件中的 ALTER 执行一次即可（重复执行会因列已存在报错，属安全失败）。

-- 1) 新增登录权限列：can_platform（平台）、can_mini（小程序），可同时为 1
ALTER TABLE sys_user ADD COLUMN can_platform char(1) NOT NULL DEFAULT '1' COMMENT '平台登录权限(0否1是)';
ALTER TABLE sys_user ADD COLUMN can_mini char(1) NOT NULL DEFAULT '0' COMMENT '小程序登录权限(0否1是)';

-- 2) 关闭 Web 登录验证码（小程序走独立 /miniapp/login，免验证码）
update sys_config set config_value = 'false' where config_key = 'sys.account.captchaEnabled';
