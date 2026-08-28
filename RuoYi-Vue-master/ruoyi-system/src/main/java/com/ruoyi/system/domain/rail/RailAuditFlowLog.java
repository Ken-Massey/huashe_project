package com.ruoyi.system.domain.rail;

import com.ruoyi.common.core.domain.BaseEntity;

/** 案例审核流转日志 */
public class RailAuditFlowLog extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long logId;
    private Long workflowId;
    private Long taskId;
    private String actionCode;
    private String actionName;
    private String fromNodeCode;
    private String toNodeCode;
    private Long operatorId;
    private String operatorName;
    private String opinion;
    private String snapshotJson;

    public Long getLogId() { return logId; }
    public void setLogId(Long logId) { this.logId = logId; }
    public Long getWorkflowId() { return workflowId; }
    public void setWorkflowId(Long workflowId) { this.workflowId = workflowId; }
    public Long getTaskId() { return taskId; }
    public void setTaskId(Long taskId) { this.taskId = taskId; }
    public String getActionCode() { return actionCode; }
    public void setActionCode(String actionCode) { this.actionCode = actionCode; }
    public String getActionName() { return actionName; }
    public void setActionName(String actionName) { this.actionName = actionName; }
    public String getFromNodeCode() { return fromNodeCode; }
    public void setFromNodeCode(String fromNodeCode) { this.fromNodeCode = fromNodeCode; }
    public String getToNodeCode() { return toNodeCode; }
    public void setToNodeCode(String toNodeCode) { this.toNodeCode = toNodeCode; }
    public Long getOperatorId() { return operatorId; }
    public void setOperatorId(Long operatorId) { this.operatorId = operatorId; }
    public String getOperatorName() { return operatorName; }
    public void setOperatorName(String operatorName) { this.operatorName = operatorName; }
    public String getOpinion() { return opinion; }
    public void setOpinion(String opinion) { this.opinion = opinion; }
    public String getSnapshotJson() { return snapshotJson; }
    public void setSnapshotJson(String snapshotJson) { this.snapshotJson = snapshotJson; }
}
