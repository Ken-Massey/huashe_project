package com.ruoyi.system.mapper.rail;

import java.util.List;
import com.ruoyi.system.domain.rail.RailAuditOpinionSnapshot;

/** 案例审核意见快照 数据层 */
public interface RailAuditOpinionSnapshotMapper
{
    public List<RailAuditOpinionSnapshot> selectSnapshotList(RailAuditOpinionSnapshot snapshot);

    public int insertSnapshot(RailAuditOpinionSnapshot snapshot);
}
