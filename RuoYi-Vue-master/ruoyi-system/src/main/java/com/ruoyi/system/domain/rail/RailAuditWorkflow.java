package com.ruoyi.system.domain.rail;

import java.util.Date;
import com.ruoyi.common.core.domain.BaseEntity;

/** 案例审核流程实例 */
public class RailAuditWorkflow extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long workflowId;
    private String flowCode;
    private String sessionId;
    private String projectId;
    private String stageId;
    private String projectName;
    private String stageName;
    private Integer auditVersion;
    private String workflowStatus;
    private String currentNodeCode;
    private String currentNodeName;
    private Long currentAssigneeId;
    private String currentAssignee;
    private Long initiatorId;
    private String initiatorName;
    private String latestSummary;
    private String latestRiskLevel;
    private String latestResultJson;
    private Date submittedTime;
    private Date approvedTime;
    private Date archivedTime;
    private Long currentUserId;

    public Long getWorkflowId() { return workflowId; }
    public void setWorkflowId(Long workflowId) { this.workflowId = workflowId; }
    public String getFlowCode() { return flowCode; }
    public void setFlowCode(String flowCode) { this.flowCode = flowCode; }
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public String getProjectId() { return projectId; }
    public void setProjectId(String projectId) { this.projectId = projectId; }
    public String getStageId() { return stageId; }
    public void setStageId(String stageId) { this.stageId = stageId; }
    public String getProjectName() { return projectName; }
    public void setProjectName(String projectName) { this.projectName = projectName; }
    public String getStageName() { return stageName; }
    public void setStageName(String stageName) { this.stageName = stageName; }
    public Integer getAuditVersion() { return auditVersion; }
    public void setAuditVersion(Integer auditVersion) { this.auditVersion = auditVersion; }
    public String getWorkflowStatus() { return workflowStatus; }
    public void setWorkflowStatus(String workflowStatus) { this.workflowStatus = workflowStatus; }
    public String getCurrentNodeCode() { return currentNodeCode; }
    public void setCurrentNodeCode(String currentNodeCode) { this.currentNodeCode = currentNodeCode; }
    public String getCurrentNodeName() { return currentNodeName; }
    public void setCurrentNodeName(String currentNodeName) { this.currentNodeName = currentNodeName; }
    public Long getCurrentAssigneeId() { return currentAssigneeId; }
    public void setCurrentAssigneeId(Long currentAssigneeId) { this.currentAssigneeId = currentAssigneeId; }
    public String getCurrentAssignee() { return currentAssignee; }
    public void setCurrentAssignee(String currentAssignee) { this.currentAssignee = currentAssignee; }
    public Long getInitiatorId() { return initiatorId; }
    public void setInitiatorId(Long initiatorId) { this.initiatorId = initiatorId; }
    public String getInitiatorName() { return initiatorName; }
    public void setInitiatorName(String initiatorName) { this.initiatorName = initiatorName; }
    public String getLatestSummary() { return latestSummary; }
    public void setLatestSummary(String latestSummary) { this.latestSummary = latestSummary; }
    public String getLatestRiskLevel() { return latestRiskLevel; }
    public void setLatestRiskLevel(String latestRiskLevel) { this.latestRiskLevel = latestRiskLevel; }
    public String getLatestResultJson() { return latestResultJson; }
    public void setLatestResultJson(String latestResultJson) { this.latestResultJson = latestResultJson; }
    public Date getSubmittedTime() { return submittedTime; }
    public void setSubmittedTime(Date submittedTime) { this.submittedTime = submittedTime; }
    public Date getApprovedTime() { return approvedTime; }
    public void setApprovedTime(Date approvedTime) { this.approvedTime = approvedTime; }
    public Date getArchivedTime() { return archivedTime; }
    public void setArchivedTime(Date archivedTime) { this.archivedTime = archivedTime; }
    public Long getCurrentUserId() { return currentUserId; }
    public void setCurrentUserId(Long currentUserId) { this.currentUserId = currentUserId; }
}
