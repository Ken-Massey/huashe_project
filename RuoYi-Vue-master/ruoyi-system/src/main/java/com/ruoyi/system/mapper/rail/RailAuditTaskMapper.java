package com.ruoyi.system.mapper.rail;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditTask;

/** 案例审核待办任务 数据层 */
public interface RailAuditTaskMapper
{
    public RailAuditTask selectTodoTaskByWorkflowId(Long workflowId);

    public List<RailAuditTask> selectTaskList(RailAuditTask task);

    public int insertTask(RailAuditTask task);

    public int updateTask(RailAuditTask task);

    public int cancelTodoTasks(Long workflowId);
}
