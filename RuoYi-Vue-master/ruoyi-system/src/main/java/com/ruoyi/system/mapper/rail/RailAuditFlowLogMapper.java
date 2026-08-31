package com.ruoyi.system.mapper.rail;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditFlowLog;

/** 案例审核流转日志 数据层 */
public interface RailAuditFlowLogMapper
{
    public List<RailAuditFlowLog> selectLogList(Long workflowId);

    public int insertLog(RailAuditFlowLog log);
}
