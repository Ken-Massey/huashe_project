package com.ruoyi.system.domain.rail;

import java.util.Date;
import com.ruoyi.common.core.domain.BaseEntity;

/** 案例审核待办任务 */
public class RailAuditTask extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long taskId;
    private Long workflowId;
    private String nodeCode;
    private String nodeName;
    private String taskStatus;
    private Long assigneeId;
    private String assigneeName;
    private String roleKey;
    private Date receivedTime;
    private Date handledTime;
    private String handleOpinion;

    public Long getTaskId() { return taskId; }
    public void setTaskId(Long taskId) { this.taskId = taskId; }
    public Long getWorkflowId() { return workflowId; }
    public void setWorkflowId(Long workflowId) { this.workflowId = workflowId; }
    public String getNodeCode() { return nodeCode; }
    public void setNodeCode(String nodeCode) { this.nodeCode = nodeCode; }
    public String getNodeName() { return nodeName; }
    public void setNodeName(String nodeName) { this.nodeName = nodeName; }
    public String getTaskStatus() { return taskStatus; }
    public void setTaskStatus(String taskStatus) { this.taskStatus = taskStatus; }
    public Long getAssigneeId() { return assigneeId; }
    public void setAssigneeId(Long assigneeId) { this.assigneeId = assigneeId; }
    public String getAssigneeName() { return assigneeName; }
    public void setAssigneeName(String assigneeName) { this.assigneeName = assigneeName; }
    public String getRoleKey() { return roleKey; }
    public void setRoleKey(String roleKey) { this.roleKey = roleKey; }
    public Date getReceivedTime() { return receivedTime; }
    public void setReceivedTime(Date receivedTime) { this.receivedTime = receivedTime; }
    public Date getHandledTime() { return handledTime; }
    public void setHandledTime(Date handledTime) { this.handledTime = handledTime; }
    public String getHandleOpinion() { return handleOpinion; }
    public void setHandleOpinion(String handleOpinion) { this.handleOpinion = handleOpinion; }
}
