package com.ruoyi.system.mapper.rail;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditFlowNode;

/** 案例审核流程节点 数据层 */
public interface RailAuditFlowNodeMapper
{
    public RailAuditFlowNode selectNodeByCode(RailAuditFlowNode node);

    public RailAuditFlowNode selectNextNode(RailAuditFlowNode node);

    public List<RailAuditFlowNode> selectNodeList(RailAuditFlowNode node);
}
