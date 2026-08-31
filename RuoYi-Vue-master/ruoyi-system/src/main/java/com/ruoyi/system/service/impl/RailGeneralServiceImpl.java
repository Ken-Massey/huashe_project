package com.ruoyi.system.service.impl;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.mapper.rail.RailGeneralMapper;
import com.ruoyi.system.service.IRailGeneralService;

/** 通用管理 服务实现 */
@Service
public class RailGeneralServiceImpl implements IRailGeneralService
{
    @Autowired
    private RailGeneralMapper generalMapper;

    @Override
    public List<Map<String, Object>> selectItemList(Map<String, Object> params)
    {
        return generalMapper.selectItemList(params);
    }

    @Override
    public Map<String, Object> selectItemDetail(Long itemId)
    {
        Map<String, Object> item = generalMapper.selectItemById(itemId);
        if (item == null)
        {
            throw new ServiceException("事项不存在");
        }
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("itemId", itemId);
        item.put("attachments", generalMapper.selectAttachmentList(query));
        query.put("targetType", "item");
        query.put("targetId", itemId);
        item.put("logs", generalMapper.selectLogList(query));
        return item;
    }

    @Override
    @Transactional
    public int insertItem(Map<String, Object> item, Long userId, String username)
    {
        if (StringUtils.isEmpty(asString(item.get("itemTitle"))))
        {
            throw new ServiceException("事项标题不能为空");
        }
        if (StringUtils.isEmpty(asString(item.get("itemType"))))
        {
            item.put("itemType", "temporary");
        }
        item.putIfAbsent("itemCode", buildCode("GI"));
        item.putIfAbsent("sourceChannel", "manual");
        item.putIfAbsent("status", "draft");
        item.putIfAbsent("priority", "normal");
        item.put("createBy", username);
        int rows = generalMapper.insertItem(item);
        Long itemId = toLong(item.get("itemId"));
        addLog("item", itemId, "create", "创建事项", "", "draft", userId, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateItem(Map<String, Object> item, String username)
    {
        Long itemId = toLong(item.get("itemId"));
        if (itemId == null)
        {
            throw new ServiceException("事项ID不能为空");
        }
        item.put("updateBy", username);
        int rows = generalMapper.updateItem(item);
        addLog("item", itemId, "update", "修改事项", "", "", null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int deleteItemByIds(Long[] itemIds, String username)
    {
        int rows = generalMapper.deleteItemByIds(itemIds);
        if (itemIds != null)
        {
            for (Long itemId : itemIds)
            {
                addLog("item", itemId, "delete", "删除事项", "", "deleted", null, username, "");
            }
        }
        return rows;
    }

    @Override
    @Transactional
    public int submitItem(Long itemId, Map<String, Object> request, Long userId, String username)
    {
        Map<String, Object> item = requireItem(itemId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("itemId", itemId);
        params.put("status", "submitted");
        params.put("updateBy", username);
        int rows = generalMapper.updateItemStatus(params);
        addLog("item", itemId, "submit", "提交事项", asString(item.get("status")), "submitted", userId, username, asString(request.get("opinion")));
        return rows;
    }

    @Override
    @Transactional
    public int reviewItem(Long itemId, Map<String, Object> request, Long userId, String username)
    {
        Map<String, Object> item = requireItem(itemId);
        String nextStatus = normalizeReviewStatus(request, "processing");
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("itemId", itemId);
        params.put("status", nextStatus);
        params.put("reviewUserId", userId);
        params.put("reviewBy", username);
        params.put("reviewOpinion", asString(request.get("reviewOpinion"), asString(request.get("opinion"))));
        params.put("updateBy", username);
        int rows = generalMapper.updateItemStatus(params);
        addLog("item", itemId, "review", "审核事项", asString(item.get("status")), nextStatus, userId, username, asString(params.get("reviewOpinion")));
        return rows;
    }

    @Override
    @Transactional
    public int closeItem(Long itemId, Map<String, Object> request, String username)
    {
        Map<String, Object> item = requireItem(itemId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("itemId", itemId);
        params.put("status", "closed");
        params.put("closeBy", username);
        params.put("closeRemark", asString(request.get("closeRemark"), asString(request.get("opinion"), "已闭环")));
        params.put("updateBy", username);
        int rows = generalMapper.updateItemStatus(params);
        addLog("item", itemId, "close", "事项闭环", asString(item.get("status")), "closed", null, username, asString(params.get("closeRemark")));
        return rows;
    }

    @Override
    @Transactional
    public int archiveItem(Long itemId, String username)
    {
        Map<String, Object> item = requireItem(itemId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("itemId", itemId);
        params.put("status", "archived");
        params.put("archiveStatus", "1");
        params.put("updateBy", username);
        int rows = generalMapper.updateItemStatus(params);
        addLog("item", itemId, "archive", "事项归档", asString(item.get("status")), "archived", null, username, "");
        return rows;
    }

    @Override
    public List<Map<String, Object>> selectReportList(Map<String, Object> params)
    {
        return generalMapper.selectReportList(params);
    }

    @Override
    public Map<String, Object> selectReportDetail(Long reportId)
    {
        Map<String, Object> report = generalMapper.selectReportById(reportId);
        if (report == null)
        {
            throw new ServiceException("报表记录不存在");
        }
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("reportId", reportId);
        report.put("attachments", generalMapper.selectAttachmentList(query));
        query.put("targetType", "report");
        query.put("targetId", reportId);
        report.put("logs", generalMapper.selectLogList(query));
        return report;
    }

    @Override
    @Transactional
    public int insertReport(Map<String, Object> report, Long userId, String username)
    {
        if (StringUtils.isEmpty(asString(report.get("reportTitle"))))
        {
            throw new ServiceException("标题不能为空");
        }
        if (StringUtils.isEmpty(asString(report.get("reportType"))))
        {
            report.put("reportType", "data_report");
        }
        report.putIfAbsent("reportCode", buildCode("GR"));
        report.putIfAbsent("status", "draft");
        report.put("createBy", username);
        int rows = generalMapper.insertReport(report);
        Long reportId = toLong(report.get("reportId"));
        addLog("report", reportId, "create", "创建报表", "", "draft", userId, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateReport(Map<String, Object> report, String username)
    {
        Long reportId = toLong(report.get("reportId"));
        if (reportId == null)
        {
            throw new ServiceException("记录ID不能为空");
        }
        report.put("updateBy", username);
        int rows = generalMapper.updateReport(report);
        addLog("report", reportId, "update", "修改报表", "", "", null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int deleteReportByIds(Long[] reportIds, String username)
    {
        int rows = generalMapper.deleteReportByIds(reportIds);
        if (reportIds != null)
        {
            for (Long reportId : reportIds)
            {
                addLog("report", reportId, "delete", "删除报表", "", "deleted", null, username, "");
            }
        }
        return rows;
    }

    @Override
    @Transactional
    public int submitReport(Long reportId, Map<String, Object> request, Long userId, String username)
    {
        Map<String, Object> report = requireReport(reportId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("reportId", reportId);
        params.put("status", "submitted");
        params.put("updateBy", username);
        int rows = generalMapper.updateReportStatus(params);
        addLog("report", reportId, "submit", "提交报表", asString(report.get("status")), "submitted", userId, username, asString(request.get("opinion")));
        return rows;
    }

    @Override
    @Transactional
    public int reviewReport(Long reportId, Map<String, Object> request, Long userId, String username)
    {
        Map<String, Object> report = requireReport(reportId);
        String nextStatus = normalizeReviewStatus(request, "reviewed");
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("reportId", reportId);
        params.put("status", nextStatus);
        params.put("reviewUserId", userId);
        params.put("reviewBy", username);
        params.put("reviewOpinion", asString(request.get("reviewOpinion"), asString(request.get("opinion"))));
        params.put("updateBy", username);
        int rows = generalMapper.updateReportStatus(params);
        addLog("report", reportId, "review", "审核报表", asString(report.get("status")), nextStatus, userId, username, asString(params.get("reviewOpinion")));
        return rows;
    }

    @Override
    @Transactional
    public int publishReport(Long reportId, Map<String, Object> request, String username)
    {
        Map<String, Object> report = requireReport(reportId);
        String nextStatus = asString(request.get("status"), "published");
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("reportId", reportId);
        params.put("status", nextStatus);
        params.put("updateBy", username);
        int rows = generalMapper.updateReportStatus(params);
        addLog("report", reportId, "publish", "发布或上报", asString(report.get("status")), nextStatus, null, username, asString(request.get("opinion")));
        return rows;
    }

    @Override
    @Transactional
    public int archiveReport(Long reportId, String username)
    {
        Map<String, Object> report = requireReport(reportId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("reportId", reportId);
        params.put("status", "archived");
        params.put("archiveStatus", "1");
        params.put("updateBy", username);
        int rows = generalMapper.updateReportStatus(params);
        addLog("report", reportId, "archive", "报表归档", asString(report.get("status")), "archived", null, username, "");
        return rows;
    }

    @Override
    public List<Map<String, Object>> selectAttachmentList(Map<String, Object> params)
    {
        return generalMapper.selectAttachmentList(params);
    }

    @Override
    public Map<String, Object> selectAttachmentById(Long attachmentId)
    {
        return generalMapper.selectAttachmentById(attachmentId);
    }

    @Override
    @Transactional
    public int insertAttachment(Map<String, Object> attachment, String username)
    {
        attachment.put("createBy", username);
        int rows = generalMapper.insertAttachment(attachment);
        Long itemId = toLong(attachment.get("itemId"));
        Long reportId = toLong(attachment.get("reportId"));
        if (itemId != null)
        {
            addLog("item", itemId, "upload", "上传附件", "", "", null, username, asString(attachment.get("fileName")));
        }
        if (reportId != null)
        {
            addLog("report", reportId, "upload", "上传附件", "", "", null, username, asString(attachment.get("fileName")));
        }
        return rows;
    }

    @Override
    public int deleteAttachmentByIds(Long[] attachmentIds)
    {
        return generalMapper.deleteAttachmentByIds(attachmentIds);
    }

    @Override
    public Map<String, Object> selectStatistics(Map<String, Object> params)
    {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", generalMapper.selectItemStatistics(params));
        result.put("reports", generalMapper.selectReportStatistics(params));
        return result;
    }

    @Override
    public List<Map<String, Object>> selectTrend(Map<String, Object> params)
    {
        return generalMapper.selectItemTrend(params);
    }

    private Map<String, Object> requireItem(Long itemId)
    {
        Map<String, Object> item = generalMapper.selectItemById(itemId);
        if (item == null)
        {
            throw new ServiceException("事项不存在");
        }
        return item;
    }

    private Map<String, Object> requireReport(Long reportId)
    {
        Map<String, Object> report = generalMapper.selectReportById(reportId);
        if (report == null)
        {
            throw new ServiceException("报表记录不存在");
        }
        return report;
    }

    private String normalizeReviewStatus(Map<String, Object> request, String defaultStatus)
    {
        Object approved = request.get("approved");
        String status = asString(request.get("status"));
        if (Boolean.FALSE.equals(approved) || "false".equalsIgnoreCase(asString(approved)) || "returned".equals(status))
        {
            return "returned";
        }
        if (StringUtils.isNotEmpty(status))
        {
            return status;
        }
        return defaultStatus;
    }

    private String buildCode(String prefix)
    {
        return prefix + new SimpleDateFormat("yyyyMMddHHmmssSSS").format(new Date());
    }

    private Long toLong(Object value)
    {
        if (value == null)
        {
            return null;
        }
        if (value instanceof Number)
        {
            return ((Number) value).longValue();
        }
        try
        {
            return Long.valueOf(String.valueOf(value));
        }
        catch (NumberFormatException ex)
        {
            return null;
        }
    }

    private String asString(Object value)
    {
        return value == null ? "" : String.valueOf(value);
    }

    private String asString(Object value, String defaultValue)
    {
        String text = asString(value);
        return StringUtils.isEmpty(text) ? defaultValue : text;
    }

    private void addLog(String targetType, Long targetId, String actionCode, String actionName,
            String fromStatus, String toStatus, Long operatorId, String operatorName, String opinion)
    {
        if (targetId == null)
        {
            return;
        }
        Map<String, Object> log = new LinkedHashMap<>();
        log.put("targetType", targetType);
        log.put("targetId", targetId);
        log.put("actionCode", actionCode);
        log.put("actionName", actionName);
        log.put("fromStatus", fromStatus);
        log.put("toStatus", toStatus);
        log.put("operatorId", operatorId);
        log.put("operatorName", operatorName);
        log.put("opinion", opinion);
        log.put("createBy", operatorName);
        generalMapper.insertLog(log);
    }
}
