package com.ruoyi.system.service;

import java.util.List;
import java.util.Map;

/** 通用管理 服务层 */
public interface IRailGeneralService
{
    public List<Map<String, Object>> selectItemList(Map<String, Object> params);

    public Map<String, Object> selectItemDetail(Long itemId);

    public int insertItem(Map<String, Object> item, Long userId, String username);

    public int updateItem(Map<String, Object> item, String username);

    public int deleteItemByIds(Long[] itemIds, String username);

    public int submitItem(Long itemId, Map<String, Object> request, Long userId, String username);

    public int reviewItem(Long itemId, Map<String, Object> request, Long userId, String username);

    public int closeItem(Long itemId, Map<String, Object> request, String username);

    public int archiveItem(Long itemId, String username);

    public List<Map<String, Object>> selectReportList(Map<String, Object> params);

    public Map<String, Object> selectReportDetail(Long reportId);

    public int insertReport(Map<String, Object> report, Long userId, String username);

    public int updateReport(Map<String, Object> report, String username);

    public int deleteReportByIds(Long[] reportIds, String username);

    public int submitReport(Long reportId, Map<String, Object> request, Long userId, String username);

    public int reviewReport(Long reportId, Map<String, Object> request, Long userId, String username);

    public int publishReport(Long reportId, Map<String, Object> request, String username);

    public int archiveReport(Long reportId, String username);

    public List<Map<String, Object>> selectAttachmentList(Map<String, Object> params);

    public Map<String, Object> selectAttachmentById(Long attachmentId);

    public int insertAttachment(Map<String, Object> attachment, String username);

    public int deleteAttachmentByIds(Long[] attachmentIds);

    public Map<String, Object> selectStatistics(Map<String, Object> params);

    public List<Map<String, Object>> selectTrend(Map<String, Object> params);
}
