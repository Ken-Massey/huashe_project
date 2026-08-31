package com.ruoyi.web.controller.rail;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.config.RuoYiConfig;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.ServletUtils;
import com.ruoyi.common.utils.file.FileUploadUtils;
import com.ruoyi.common.utils.file.FileUtils;
import com.ruoyi.framework.config.ServerConfig;
import com.ruoyi.system.service.IRailGeneralService;

/** 通用管理控制器 */
@RestController
@RequestMapping("/rail/general")
public class RailGeneralController extends BaseController
{
    @Autowired
    private IRailGeneralService generalService;

    @Autowired
    private ServerConfig serverConfig;

    @PreAuthorize("@ss.hasAnyPermi('rail:general:list,rail:general:query')")
    @GetMapping("/items/list")
    public TableDataInfo itemList(@RequestParam Map<String, Object> query)
    {
        startPage();
        List<Map<String, Object>> list = generalService.selectItemList(query);
        return getDataTable(list);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:general:list,rail:general:query')")
    @GetMapping("/items/{itemId}")
    public AjaxResult getItem(@PathVariable Long itemId)
    {
        return success(generalService.selectItemDetail(itemId));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:add')")
    @Log(title = "通用管理-事项", businessType = BusinessType.INSERT)
    @PostMapping("/items")
    public AjaxResult addItem(@RequestBody Map<String, Object> item)
    {
        return toAjax(generalService.insertItem(item, getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:edit')")
    @Log(title = "通用管理-事项", businessType = BusinessType.UPDATE)
    @PutMapping("/items")
    public AjaxResult editItem(@RequestBody Map<String, Object> item)
    {
        return toAjax(generalService.updateItem(item, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:remove')")
    @Log(title = "通用管理-事项", businessType = BusinessType.DELETE)
    @DeleteMapping("/items/{itemIds}")
    public AjaxResult removeItem(@PathVariable Long[] itemIds)
    {
        return toAjax(generalService.deleteItemByIds(itemIds, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:submit')")
    @PostMapping("/items/{itemId}/submit")
    public AjaxResult submitItem(@PathVariable Long itemId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.submitItem(itemId, safeMap(request), getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:review')")
    @PostMapping("/items/{itemId}/review")
    public AjaxResult reviewItem(@PathVariable Long itemId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.reviewItem(itemId, safeMap(request), getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:close')")
    @PostMapping("/items/{itemId}/close")
    public AjaxResult closeItem(@PathVariable Long itemId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.closeItem(itemId, safeMap(request), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:archive')")
    @PostMapping("/items/{itemId}/archive")
    public AjaxResult archiveItem(@PathVariable Long itemId)
    {
        return toAjax(generalService.archiveItem(itemId, getUsername()));
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:general:list,rail:general:query')")
    @GetMapping("/reports/list")
    public TableDataInfo reportList(@RequestParam Map<String, Object> query)
    {
        startPage();
        List<Map<String, Object>> list = generalService.selectReportList(query);
        return getDataTable(list);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:general:list,rail:general:query')")
    @GetMapping("/reports/{reportId}")
    public AjaxResult getReport(@PathVariable Long reportId)
    {
        return success(generalService.selectReportDetail(reportId));
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:general:add,rail:general:report')")
    @Log(title = "通用管理-报表", businessType = BusinessType.INSERT)
    @PostMapping("/reports")
    public AjaxResult addReport(@RequestBody Map<String, Object> report)
    {
        return toAjax(generalService.insertReport(report, getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:edit')")
    @Log(title = "通用管理-报表", businessType = BusinessType.UPDATE)
    @PutMapping("/reports")
    public AjaxResult editReport(@RequestBody Map<String, Object> report)
    {
        return toAjax(generalService.updateReport(report, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:remove')")
    @Log(title = "通用管理-报表", businessType = BusinessType.DELETE)
    @DeleteMapping("/reports/{reportIds}")
    public AjaxResult removeReport(@PathVariable Long[] reportIds)
    {
        return toAjax(generalService.deleteReportByIds(reportIds, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:submit')")
    @PostMapping("/reports/{reportId}/submit")
    public AjaxResult submitReport(@PathVariable Long reportId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.submitReport(reportId, safeMap(request), getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:review')")
    @PostMapping("/reports/{reportId}/review")
    public AjaxResult reviewReport(@PathVariable Long reportId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.reviewReport(reportId, safeMap(request), getUserId(), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:report')")
    @PostMapping("/reports/{reportId}/publish")
    public AjaxResult publishReport(@PathVariable Long reportId, @RequestBody(required = false) Map<String, Object> request)
    {
        return toAjax(generalService.publishReport(reportId, safeMap(request), getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:archive')")
    @PostMapping("/reports/{reportId}/archive")
    public AjaxResult archiveReport(@PathVariable Long reportId)
    {
        return toAjax(generalService.archiveReport(reportId, getUsername()));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:upload')")
    @PostMapping(value = "/items/{itemId}/attachments", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public AjaxResult uploadItemAttachment(@PathVariable Long itemId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "fileType", defaultValue = "attachment") String fileType,
            @RequestParam(name = "description", defaultValue = "") String description) throws Exception
    {
        return uploadAttachment(itemId, null, file, fileType, description);
    }

    @PreAuthorize("@ss.hasPermi('rail:general:upload')")
    @PostMapping(value = "/reports/{reportId}/attachments", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public AjaxResult uploadReportAttachment(@PathVariable Long reportId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "fileType", defaultValue = "attachment") String fileType,
            @RequestParam(name = "description", defaultValue = "") String description) throws Exception
    {
        return uploadAttachment(null, reportId, file, fileType, description);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:general:list,rail:general:query')")
    @GetMapping("/attachments/{attachmentId}/download")
    public void downloadAttachment(@PathVariable Long attachmentId, HttpServletResponse response) throws Exception
    {
        Map<String, Object> attachment = generalService.selectAttachmentById(attachmentId);
        if (attachment == null)
        {
            throw new ServiceException("附件不存在");
        }
        String filePath = String.valueOf(attachment.get("filePath"));
        String fileName = String.valueOf(attachment.get("fileName"));
        response.setContentType(MediaType.APPLICATION_OCTET_STREAM_VALUE);
        response.setHeader("Content-Disposition", "attachment; filename=" + FileUtils.setFileDownloadHeader(ServletUtils.getRequest(), fileName));
        FileUtils.writeBytes(RuoYiConfig.getProfile() + filePath.replace("/profile", ""), response.getOutputStream());
    }

    @PreAuthorize("@ss.hasPermi('rail:general:upload')")
    @DeleteMapping("/attachments/{attachmentIds}")
    public AjaxResult removeAttachment(@PathVariable Long[] attachmentIds)
    {
        return toAjax(generalService.deleteAttachmentByIds(attachmentIds));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:statistics')")
    @GetMapping("/statistics")
    public AjaxResult statistics(@RequestParam Map<String, Object> query)
    {
        return success(generalService.selectStatistics(query));
    }

    @PreAuthorize("@ss.hasPermi('rail:general:statistics')")
    @GetMapping("/trend")
    public AjaxResult trend(@RequestParam Map<String, Object> query)
    {
        return success(generalService.selectTrend(query));
    }

    private AjaxResult uploadAttachment(Long itemId, Long reportId, MultipartFile file, String fileType, String description) throws Exception
    {
        String storedPath = FileUploadUtils.upload(RuoYiConfig.getUploadPath() + "/general", file);
        Map<String, Object> record = new LinkedHashMap<>();
        record.put("itemId", itemId);
        record.put("reportId", reportId);
        record.put("fileType", fileType);
        record.put("fileName", file.getOriginalFilename());
        record.put("storedName", FileUtils.getName(storedPath));
        record.put("filePath", storedPath);
        record.put("fileSize", file.getSize());
        record.put("mimeType", file.getContentType());
        record.put("description", description);
        generalService.insertAttachment(record, getUsername());
        AjaxResult ajax = success(record);
        ajax.put("url", serverConfig.getUrl() + storedPath);
        return ajax;
    }

    private Map<String, Object> safeMap(Map<String, Object> request)
    {
        return request == null ? new LinkedHashMap<>() : request;
    }
}
