package com.ruoyi.system.domain.rail;

import java.io.Serializable;

/** 流程动作请求 */
public class RailAuditWorkflowAction implements Serializable
{
    private static final long serialVersionUID = 1L;

    private Long workflowId;
    private String sessionId;
    private String projectId;
    private String stageId;
    private String projectName;
    private String stageName;
    private Integer auditVersion;
    private String latestSummary;
    private String latestRiskLevel;
    private String latestResultJson;
    private String sourceFilesJson;
    private Long assigneeId;
    private String assigneeName;
    private String opinion;
    private String snapshotJson;
    private Long operatorId;
    private String operatorName;

    public Long getWorkflowId() { return workflowId; }
    public void setWorkflowId(Long workflowId) { this.workflowId = workflowId; }
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
    public String getLatestSummary() { return latestSummary; }
    public void setLatestSummary(String latestSummary) { this.latestSummary = latestSummary; }
    public String getLatestRiskLevel() { return latestRiskLevel; }
    public void setLatestRiskLevel(String latestRiskLevel) { this.latestRiskLevel = latestRiskLevel; }
    public String getLatestResultJson() { return latestResultJson; }
    public void setLatestResultJson(String latestResultJson) { this.latestResultJson = latestResultJson; }
    public String getSourceFilesJson() { return sourceFilesJson; }
    public void setSourceFilesJson(String sourceFilesJson) { this.sourceFilesJson = sourceFilesJson; }
    public Long getAssigneeId() { return assigneeId; }
    public void setAssigneeId(Long assigneeId) { this.assigneeId = assigneeId; }
    public String getAssigneeName() { return assigneeName; }
    public void setAssigneeName(String assigneeName) { this.assigneeName = assigneeName; }
    public String getOpinion() { return opinion; }
    public void setOpinion(String opinion) { this.opinion = opinion; }
    public String getSnapshotJson() { return snapshotJson; }
    public void setSnapshotJson(String snapshotJson) { this.snapshotJson = snapshotJson; }
    public Long getOperatorId() { return operatorId; }
    public void setOperatorId(Long operatorId) { this.operatorId = operatorId; }
    public String getOperatorName() { return operatorName; }
    public void setOperatorName(String operatorName) { this.operatorName = operatorName; }
}
