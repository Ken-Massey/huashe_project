-- 案例审核流转表结构修复脚本
-- 执行库：huashe_database
-- 用途：修复已跑过旧版流程脚本的数据库，补齐 rail_audit_flow_log 缺失字段。

set @ddl := (
  select if(count(*) = 0,
    'alter table rail_audit_flow_log add column update_by varchar(64) default '''' comment ''更新者'' after create_time',
    'select 1'
  )
  from information_schema.columns
  where table_schema = database()
    and table_name = 'rail_audit_flow_log'
    and column_name = 'update_by'
);
prepare stmt from @ddl;
execute stmt;
deallocate prepare stmt;

set @ddl := (
  select if(count(*) = 0,
    'alter table rail_audit_flow_log add column update_time datetime comment ''更新时间'' after update_by',
    'select 1'
  )
  from information_schema.columns
  where table_schema = database()
    and table_name = 'rail_audit_flow_log'
    and column_name = 'update_time'
);
prepare stmt from @ddl;
execute stmt;
deallocate prepare stmt;
