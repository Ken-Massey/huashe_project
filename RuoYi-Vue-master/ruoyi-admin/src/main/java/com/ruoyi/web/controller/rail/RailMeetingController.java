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
import com.ruoyi.system.service.IRailMeetingService;

/** 会议协调管理控制器 */
@RestController
@RequestMapping("/rail/meeting")
public class RailMeetingController extends BaseController
{
    @Autowired
    private IRailMeetingService meetingService;

    @Autowired
    private ServerConfig serverConfig;

    /** 查询会议列表 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/list")
    public TableDataInfo list(@RequestParam Map<String, Object> query)
    {
        startPage();
        List<Map<String, Object>> list = meetingService.selectMeetingList(query);
        return getDataTable(list);
    }

    /** 获取会议详情 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/{meetingId}")
    public AjaxResult getInfo(@PathVariable Long meetingId)
    {
        return success(meetingService.selectMeetingDetail(meetingId));
    }

    /** 新增会议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:add')")
    @Log(title = "会议协调管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody Map<String, Object> meeting)
    {
        return toAjax(meetingService.insertMeeting(meeting, getUserId(), getUsername()));
    }

    /** 修改会议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:edit')")
    @Log(title = "会议协调管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody Map<String, Object> meeting)
    {
        return toAjax(meetingService.updateMeeting(meeting, getUsername()));
    }

    /** 删除会议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:remove')")
    @Log(title = "会议协调管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{meetingIds}")
    public AjaxResult remove(@PathVariable Long[] meetingIds)
    {
        return toAjax(meetingService.deleteMeetingByIds(meetingIds, getUsername()));
    }

    /** 发送会议通知 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:notify')")
    @Log(title = "会议协调管理", businessType = BusinessType.UPDATE)
    @PostMapping("/{meetingId}/notify")
    public AjaxResult notifyMeeting(@PathVariable Long meetingId, @RequestBody Map<String, Object> request)
    {
        return toAjax(meetingService.notifyMeeting(meetingId, request, getUsername()));
    }

    /** 标记会议已召开 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:edit')")
    @Log(title = "会议协调管理", businessType = BusinessType.UPDATE)
    @PostMapping("/{meetingId}/held")
    public AjaxResult markMeetingHeld(@PathVariable Long meetingId)
    {
        return toAjax(meetingService.markMeetingHeld(meetingId, getUsername()));
    }

    /** 会议归档 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:archive')")
    @Log(title = "会议协调管理", businessType = BusinessType.UPDATE)
    @PostMapping("/{meetingId}/archive")
    public AjaxResult archiveMeeting(@PathVariable Long meetingId)
    {
        return toAjax(meetingService.archiveMeeting(meetingId, getUsername()));
    }

    /** 查询参会人员 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/{meetingId}/participants")
    public AjaxResult participants(@PathVariable Long meetingId)
    {
        return success(meetingService.selectParticipantList(meetingId));
    }

    /** 新增参会人员 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:participant')")
    @PostMapping("/{meetingId}/participants")
    public AjaxResult addParticipant(@PathVariable Long meetingId, @RequestBody Map<String, Object> participant)
    {
        return toAjax(meetingService.insertParticipant(meetingId, participant, getUsername()));
    }

    /** 修改参会人员 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:participant')")
    @PutMapping("/participants")
    public AjaxResult editParticipant(@RequestBody Map<String, Object> participant)
    {
        return toAjax(meetingService.updateParticipant(participant, getUsername()));
    }

    /** 删除参会人员 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:participant')")
    @DeleteMapping("/participants/{participantIds}")
    public AjaxResult removeParticipant(@PathVariable Long[] participantIds)
    {
        return toAjax(meetingService.deleteParticipantByIds(participantIds));
    }

    /** 查询会议材料 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/{meetingId}/files")
    public AjaxResult files(@PathVariable Long meetingId)
    {
        return success(meetingService.selectFileList(meetingId));
    }

    /** 上传会议材料 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:file')")
    @PostMapping(value = "/{meetingId}/files", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public AjaxResult uploadFile(@PathVariable Long meetingId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "fileType", defaultValue = "material") String fileType,
            @RequestParam(name = "description", defaultValue = "") String description) throws Exception
    {
        String storedPath = FileUploadUtils.upload(RuoYiConfig.getUploadPath() + "/meeting", file);
        Map<String, Object> record = new LinkedHashMap<>();
        record.put("fileType", fileType);
        record.put("fileName", file.getOriginalFilename());
        record.put("storedName", FileUtils.getName(storedPath));
        record.put("filePath", storedPath);
        record.put("fileSize", file.getSize());
        record.put("mimeType", file.getContentType());
        record.put("description", description);
        meetingService.insertFile(meetingId, record, getUsername());
        AjaxResult ajax = success(record);
        ajax.put("url", serverConfig.getUrl() + storedPath);
        return ajax;
    }

    /** 下载会议材料 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/files/{fileId}/download")
    public void downloadFile(@PathVariable Long fileId, HttpServletResponse response) throws Exception
    {
        Map<String, Object> file = meetingService.selectFileById(fileId);
        if (file == null)
        {
            throw new ServiceException("文件不存在");
        }
        String filePath = String.valueOf(file.get("filePath"));
        String fileName = String.valueOf(file.get("fileName"));
        response.setContentType(MediaType.APPLICATION_OCTET_STREAM_VALUE);
        response.setHeader("Content-Disposition", "attachment; filename=" + FileUtils.setFileDownloadHeader(ServletUtils.getRequest(), fileName));
        FileUtils.writeBytes(RuoYiConfig.getProfile() + filePath.replace("/profile", ""), response.getOutputStream());
    }

    /** 删除会议材料 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:file')")
    @DeleteMapping("/files/{fileIds}")
    public AjaxResult removeFile(@PathVariable Long[] fileIds)
    {
        return toAjax(meetingService.deleteFileByIds(fileIds));
    }

    /** 保存会议纪要 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:minutes')")
    @PostMapping("/{meetingId}/minutes")
    public AjaxResult saveMinutes(@PathVariable Long meetingId, @RequestBody Map<String, Object> minutes)
    {
        return success(meetingService.saveMinutes(meetingId, minutes, getUserId(), getUsername()));
    }

    /** 确认会议纪要 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:confirm')")
    @PostMapping("/{meetingId}/minutes/confirm")
    public AjaxResult confirmMinutes(@PathVariable Long meetingId, @RequestBody Map<String, Object> minutes)
    {
        return toAjax(meetingService.confirmMinutes(meetingId, minutes, getUserId(), getUsername()));
    }

    /** 查询问题清单 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/{meetingId}/issues")
    public AjaxResult issues(@PathVariable Long meetingId)
    {
        return success(meetingService.selectIssueList(meetingId));
    }

    /** 新增问题 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @PostMapping("/{meetingId}/issues")
    public AjaxResult addIssue(@PathVariable Long meetingId, @RequestBody Map<String, Object> issue)
    {
        return toAjax(meetingService.insertIssue(meetingId, issue, getUsername()));
    }

    /** 修改问题 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @PutMapping("/issues")
    public AjaxResult editIssue(@RequestBody Map<String, Object> issue)
    {
        return toAjax(meetingService.updateIssue(issue, getUsername()));
    }

    /** 删除问题 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @DeleteMapping("/issues/{issueIds}")
    public AjaxResult removeIssue(@PathVariable Long[] issueIds)
    {
        return toAjax(meetingService.deleteIssueByIds(issueIds));
    }

    /** 查询决议事项 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/{meetingId}/decisions")
    public AjaxResult decisions(@PathVariable Long meetingId)
    {
        return success(meetingService.selectDecisionList(meetingId));
    }

    /** 新增决议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @PostMapping("/{meetingId}/decisions")
    public AjaxResult addDecision(@PathVariable Long meetingId, @RequestBody Map<String, Object> decision)
    {
        return toAjax(meetingService.insertDecision(meetingId, decision, getUsername()));
    }

    /** 修改决议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @PutMapping("/decisions")
    public AjaxResult editDecision(@RequestBody Map<String, Object> decision)
    {
        return toAjax(meetingService.updateDecision(decision, getUsername()));
    }

    /** 删除决议 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:item')")
    @DeleteMapping("/decisions/{decisionIds}")
    public AjaxResult removeDecision(@PathVariable Long[] decisionIds)
    {
        return toAjax(meetingService.deleteDecisionByIds(decisionIds));
    }

    /** 查询待办事项 */
    @PreAuthorize("@ss.hasAnyPermi('rail:meeting:list,rail:meeting:query')")
    @GetMapping("/todos")
    public TableDataInfo todos(@RequestParam Map<String, Object> query)
    {
        startPage();
        List<Map<String, Object>> list = meetingService.selectTodoList(query);
        return getDataTable(list);
    }

    /** 新增待办事项 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:todo')")
    @PostMapping("/{meetingId}/todos")
    public AjaxResult addTodo(@PathVariable Long meetingId, @RequestBody Map<String, Object> todo)
    {
        return toAjax(meetingService.insertTodo(meetingId, todo, getUsername()));
    }

    /** 修改待办事项 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:todo')")
    @PutMapping("/todos")
    public AjaxResult editTodo(@RequestBody Map<String, Object> todo)
    {
        return toAjax(meetingService.updateTodo(todo, getUsername()));
    }

    /** 删除待办事项 */
    @PreAuthorize("@ss.hasPermi('rail:meeting:todo')")
    @DeleteMapping("/todos/{todoIds}")
    public AjaxResult removeTodo(@PathVariable Long[] todoIds)
    {
        return toAjax(meetingService.deleteTodoByIds(todoIds));
    }
}
