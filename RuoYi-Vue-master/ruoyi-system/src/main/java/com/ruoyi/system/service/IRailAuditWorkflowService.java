package com.ruoyi.system.service;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditFlowNode;
import com.ruoyi.system.domain.rail.RailAuditFlowLog;
import com.ruoyi.system.domain.rail.RailAuditOpinionSnapshot;
import com.ruoyi.system.domain.rail.RailAuditTask;
import com.ruoyi.system.domain.rail.RailAuditWorkflow;
import com.ruoyi.system.domain.rail.RailAuditWorkflowAction;

/** 案例审核多级流转 服务层 */
public interface IRailAuditWorkflowService
{
    public RailAuditWorkflow selectWorkflowById(Long workflowId);

    public List<RailAuditWorkflow> selectWorkflowList(RailAuditWorkflow workflow);

    public List<RailAuditWorkflow> selectTodoWorkflowList(RailAuditWorkflow workflow);

    public List<RailAuditTask> selectTaskList(Long workflowId);

    public List<RailAuditFlowLog> selectLogList(Long workflowId);

    public List<RailAuditOpinionSnapshot> selectSnapshotList(Long workflowId);

    public List<RailAuditFlowNode> selectNodeList(RailAuditFlowNode node);

    public RailAuditWorkflow submit(RailAuditWorkflowAction action);

    public RailAuditWorkflow approve(RailAuditWorkflowAction action);

    public RailAuditWorkflow returnBack(RailAuditWorkflowAction action);

    public RailAuditWorkflow archive(RailAuditWorkflowAction action);
}
