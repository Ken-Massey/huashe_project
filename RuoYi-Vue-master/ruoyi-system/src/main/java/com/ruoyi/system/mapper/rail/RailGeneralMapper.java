package com.ruoyi.system.mapper.rail;

import java.util.List;
import java.util.Map;

/** 通用管理 数据层 */
public interface RailGeneralMapper
{
    public List<Map<String, Object>> selectItemList(Map<String, Object> params);

    public Map<String, Object> selectItemById(Long itemId);

    public int insertItem(Map<String, Object> item);

    public int updateItem(Map<String, Object> item);

    public int deleteItemByIds(Long[] itemIds);

    public int updateItemStatus(Map<String, Object> params);

    public List<Map<String, Object>> selectReportList(Map<String, Object> params);

    public Map<String, Object> selectReportById(Long reportId);

    public int insertReport(Map<String, Object> report);

    public int updateReport(Map<String, Object> report);

    public int deleteReportByIds(Long[] reportIds);

    public int updateReportStatus(Map<String, Object> params);

    public List<Map<String, Object>> selectAttachmentList(Map<String, Object> params);

    public Map<String, Object> selectAttachmentById(Long attachmentId);

    public int insertAttachment(Map<String, Object> attachment);

    public int deleteAttachmentByIds(Long[] attachmentIds);

    public int insertLog(Map<String, Object> log);

    public List<Map<String, Object>> selectLogList(Map<String, Object> params);

    public List<Map<String, Object>> selectItemStatistics(Map<String, Object> params);

    public List<Map<String, Object>> selectItemTrend(Map<String, Object> params);

    public List<Map<String, Object>> selectReportStatistics(Map<String, Object> params);
}
