package com.ruoyi.system.mapper.rail;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditWorkflow;

/** 案例审核流程实例 数据层 */
public interface RailAuditWorkflowMapper
{
    public RailAuditWorkflow selectWorkflowById(Long workflowId);

    public RailAuditWorkflow selectWorkflowByBusinessKey(RailAuditWorkflow workflow);

    public List<RailAuditWorkflow> selectWorkflowList(RailAuditWorkflow workflow);

    public List<RailAuditWorkflow> selectTodoWorkflowList(RailAuditWorkflow workflow);

    public int insertWorkflow(RailAuditWorkflow workflow);

    public int updateWorkflow(RailAuditWorkflow workflow);
}
