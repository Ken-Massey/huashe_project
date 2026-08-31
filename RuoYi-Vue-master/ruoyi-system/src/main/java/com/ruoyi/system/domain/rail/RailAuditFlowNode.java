package com.ruoyi.system.domain.rail;

import com.ruoyi.common.core.domain.BaseEntity;

/** 案例审核流程节点配置 */
public class RailAuditFlowNode extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long nodeId;
    private String flowCode;
    private String nodeCode;
    private String nodeName;
    private Integer nodeOrder;
    private String roleKey;
    private String projectType;
    private String stageName;
    private String allowReturn;
    private String status;

    public Long getNodeId() { return nodeId; }
    public void setNodeId(Long nodeId) { this.nodeId = nodeId; }
    public String getFlowCode() { return flowCode; }
    public void setFlowCode(String flowCode) { this.flowCode = flowCode; }
    public String getNodeCode() { return nodeCode; }
    public void setNodeCode(String nodeCode) { this.nodeCode = nodeCode; }
    public String getNodeName() { return nodeName; }
    public void setNodeName(String nodeName) { this.nodeName = nodeName; }
    public Integer getNodeOrder() { return nodeOrder; }
    public void setNodeOrder(Integer nodeOrder) { this.nodeOrder = nodeOrder; }
    public String getRoleKey() { return roleKey; }
    public void setRoleKey(String roleKey) { this.roleKey = roleKey; }
    public String getProjectType() { return projectType; }
    public void setProjectType(String projectType) { this.projectType = projectType; }
    public String getStageName() { return stageName; }
    public void setStageName(String stageName) { this.stageName = stageName; }
    public String getAllowReturn() { return allowReturn; }
    public void setAllowReturn(String allowReturn) { this.allowReturn = allowReturn; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
