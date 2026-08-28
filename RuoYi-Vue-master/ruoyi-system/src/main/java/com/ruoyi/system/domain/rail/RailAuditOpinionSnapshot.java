package com.ruoyi.system.domain.rail;

import com.ruoyi.common.core.domain.BaseEntity;

/** 案例审核意见版本快照 */
public class RailAuditOpinionSnapshot extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long snapshotId;
    private Long workflowId;
    private String sessionId;
    private Integer auditVersion;
    private Integer opinionNo;
    private String opinionType;
    private String title;
    private String riskLevel;
    private String opinionContent;
    private String resultJson;
    private String sourceFilesJson;

    public Long getSnapshotId() { return snapshotId; }
    public void setSnapshotId(Long snapshotId) { this.snapshotId = snapshotId; }
    public Long getWorkflowId() { return workflowId; }
    public void setWorkflowId(Long workflowId) { this.workflowId = workflowId; }
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public Integer getAuditVersion() { return auditVersion; }
    public void setAuditVersion(Integer auditVersion) { this.auditVersion = auditVersion; }
    public Integer getOpinionNo() { return opinionNo; }
    public void setOpinionNo(Integer opinionNo) { this.opinionNo = opinionNo; }
    public String getOpinionType() { return opinionType; }
    public void setOpinionType(String opinionType) { this.opinionType = opinionType; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    public String getOpinionContent() { return opinionContent; }
    public void setOpinionContent(String opinionContent) { this.opinionContent = opinionContent; }
    public String getResultJson() { return resultJson; }
    public void setResultJson(String resultJson) { this.resultJson = resultJson; }
    public String getSourceFilesJson() { return sourceFilesJson; }
    public void setSourceFilesJson(String sourceFilesJson) { this.sourceFilesJson = sourceFilesJson; }
}
