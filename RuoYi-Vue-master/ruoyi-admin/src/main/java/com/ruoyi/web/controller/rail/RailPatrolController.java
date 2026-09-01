package com.ruoyi.web.controller.rail;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.system.service.ISysUserService;
import com.ruoyi.web.service.PythonAuditClient;

import jakarta.servlet.http.HttpServletResponse;

/** 现场符合性巡查：巡查任务、巡查记录、现场媒体与问题隐患整改闭环代理。 */
@RestController
@RequestMapping("/rail/patrol")
public class RailPatrolController
{
    private static final String VIEW_PERMS =
            "rail:patrol:list,rail:patrol:upload,rail:patrol:manage,rail:patrol:review,rail:patrol:dict";
    private static final String UPLOAD_PERMS = "rail:patrol:upload,rail:patrol:manage,rail:patrol:review";

    private final PythonAuditClient python;

    private final ISysUserService userService;

    public RailPatrolController(PythonAuditClient python, ISysUserService userService)
    {
        this.python = python;
        this.userService = userService;
    }

    /** 注入操作者身份：纯平台账号看全部，任何带小程序权限的账号只看被指派的任务。 */
    private Map<String, String> actorHeaders()
    {
        Long userId = SecurityUtils.getUserId();
        String username = SecurityUtils.getUsername();
        LoginUser loginUser = SecurityUtils.getLoginUser();
        String canPlatform = (loginUser != null && loginUser.getUser() != null)
                ? loginUser.getUser().getCanPlatform() : "0";
        String canMini = (loginUser != null && loginUser.getUser() != null)
                ? loginUser.getUser().getCanMini() : "0";
        // 超管 或 纯平台账号（有平台权限且无小程序权限）→ 看全部；其余（含小程序账号）只看被指派
        boolean admin = (userId != null && userId == 1L) || ("1".equals(canPlatform) && !"1".equals(canMini));
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("X-Actor-User-Id", userId == null ? "" : String.valueOf(userId));
        headers.put("X-Actor-Name", username == null ? "" : username);
        headers.put("X-Actor-Is-Admin", admin ? "true" : "false");
        return headers;
    }

    // ---- 字典 ----

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/dicts")
    public Object listDicts(@RequestParam(name = "dictType", defaultValue = "line") String dictType)
    {
        return python.get("/api/v1/patrol/dicts", Map.of("dict_type", dictType));
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:dict')")
    @PostMapping("/dicts")
    public Object createDict(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/dicts", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:dict')")
    @PostMapping("/dicts/{dictId}")
    public Object updateDict(@PathVariable("dictId") String dictId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/dicts/" + dictId, request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:dict')")
    @DeleteMapping("/dicts/{dictId}")
    public Object deleteDict(@PathVariable("dictId") String dictId)
    {
        return python.delete("/api/v1/patrol/dicts/" + dictId, actorHeaders());
    }

    // ---- 任务 ----

    /** 指派账号合法性校验：assigned_user_id 非空时必须是系统内存在的用户，避免出现孤儿指派。 */
    private void validateAssignedUser(Map<String, Object> request)
    {
        Object value = request == null ? null : request.get("assigned_user_id");
        if (value == null)
        {
            return;
        }
        String id = String.valueOf(value).trim();
        if (id.isEmpty())
        {
            return;
        }
        Long userId;
        try
        {
            userId = Long.parseLong(id);
        }
        catch (NumberFormatException exception)
        {
            throw new ServiceException("指派账号ID无效：" + id);
        }
        SysUser user = userService.selectUserById(userId);
        if (user == null)
        {
            throw new ServiceException("指派账号不存在（ID：" + id + "），请先在系统管理中创建该用户。");
        }
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:manage')")
    @PostMapping("/tasks")
    public Object createTask(@RequestBody Map<String, Object> request)
    {
        validateAssignedUser(request);
        return python.post("/api/v1/patrol/tasks", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/tasks")
    public Object listTasks(@RequestParam(name = "page", defaultValue = "1") Integer page,
            @RequestParam(name = "size", defaultValue = "20") Integer size,
            @RequestParam(name = "line", defaultValue = "") String line,
            @RequestParam(name = "status", defaultValue = "") String status,
            @RequestParam(name = "assignedUserId", defaultValue = "") String assignedUserId,
            @RequestParam(name = "keyword", defaultValue = "") String keyword,
            @RequestParam(name = "dateFrom", defaultValue = "") String dateFrom,
            @RequestParam(name = "dateTo", defaultValue = "") String dateTo)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("page", page);
        query.put("size", size);
        query.put("line", line);
        query.put("status", status);
        query.put("assigned_user_id", assignedUserId);
        query.put("keyword", keyword);
        query.put("date_from", dateFrom);
        query.put("date_to", dateTo);
        return python.get("/api/v1/patrol/tasks", query, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/statistics")
    public Object statistics(@RequestParam(name = "line", defaultValue = "") String line,
            @RequestParam(name = "dateFrom", defaultValue = "") String dateFrom,
            @RequestParam(name = "dateTo", defaultValue = "") String dateTo)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("line", line);
        query.put("date_from", dateFrom);
        query.put("date_to", dateTo);
        return python.get("/api/v1/patrol/statistics", query, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/tasks/{taskId}")
    public Object task(@PathVariable("taskId") String taskId)
    {
        return python.get("/api/v1/patrol/tasks/" + taskId, null, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:manage')")
    @PostMapping("/tasks/{taskId}")
    public Object updateTask(@PathVariable("taskId") String taskId, @RequestBody Map<String, Object> request)
    {
        validateAssignedUser(request);
        return python.post("/api/v1/patrol/tasks/" + taskId, request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:manage')")
    @PostMapping("/tasks/{taskId}/status")
    public Object setTaskStatus(@PathVariable("taskId") String taskId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/tasks/" + taskId + "/status", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:manage')")
    @PostMapping("/tasks/{taskId}/reopen")
    public Object reopenTask(@PathVariable("taskId") String taskId)
    {
        return python.post("/api/v1/patrol/tasks/" + taskId + "/reopen", Map.of(), actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:manage')")
    @DeleteMapping("/tasks/{taskId}")
    public Object deleteTask(@PathVariable("taskId") String taskId)
    {
        return python.delete("/api/v1/patrol/tasks/" + taskId, actorHeaders());
    }

    // ---- 巡查记录与媒体 ----

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping("/tasks/{taskId}/records")
    public Object createRecord(@PathVariable("taskId") String taskId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/tasks/" + taskId + "/records", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping("/records/{recordId}")
    public Object updateRecord(@PathVariable("recordId") String recordId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/records/" + recordId, request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping(value = "/records/{recordId}/media", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object addMedia(@PathVariable("recordId") String recordId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "kind", defaultValue = "photo") String kind,
            @RequestParam(name = "takenAt", required = false) String takenAt)
    {
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("kind", kind);
        fields.put("taken_at", takenAt == null ? "" : takenAt);
        return python.postFiles("/api/v1/patrol/records/" + recordId + "/media", Map.of("file", file), fields,
                Map.of(), actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/media/{mediaId}/file")
    public void mediaFile(@PathVariable("mediaId") String mediaId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/patrol/media/" + mediaId + "/file", actorHeaders()), response);
    }

    // ---- 监测方案文档 ----

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping(value = "/tasks/{taskId}/docs", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object addTaskDoc(@PathVariable("taskId") String taskId, @RequestParam("file") MultipartFile file)
    {
        return python.postFiles("/api/v1/patrol/tasks/" + taskId + "/docs", Map.of("file", file), Map.of(),
                Map.of(), actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/docs/{docId}/file")
    public void docFile(@PathVariable("docId") String docId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/patrol/docs/" + docId + "/file", actorHeaders()), response);
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @DeleteMapping("/docs/{docId}")
    public Object deleteTaskDoc(@PathVariable("docId") String docId)
    {
        return python.delete("/api/v1/patrol/docs/" + docId, actorHeaders());
    }

    // ---- 隐患 ----

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping("/tasks/{taskId}/hazards")
    public Object createHazard(@PathVariable("taskId") String taskId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/tasks/" + taskId + "/hazards", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:review')")
    @PostMapping("/hazards/{hazardId}/confirm")
    public Object confirmHazard(@PathVariable("hazardId") String hazardId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/hazards/" + hazardId + "/confirm", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping("/hazards/{hazardId}/submit")
    public Object submitHazard(@PathVariable("hazardId") String hazardId)
    {
        return python.post("/api/v1/patrol/hazards/" + hazardId + "/submit", Map.of(), actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:patrol:review')")
    @PostMapping("/hazards/{hazardId}/review")
    public Object reviewHazard(@PathVariable("hazardId") String hazardId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/hazards/" + hazardId + "/review", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping(value = "/hazards/{hazardId}/shots", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object addHazardShot(@PathVariable("hazardId") String hazardId, @RequestParam("file") MultipartFile file)
    {
        return python.postFiles("/api/v1/patrol/hazards/" + hazardId + "/shots", Map.of("file", file), Map.of(),
                Map.of(), actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @PostMapping("/hazards/{hazardId}")
    public Object updateHazard(@PathVariable("hazardId") String hazardId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/patrol/hazards/" + hazardId, request, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @DeleteMapping("/hazards/{hazardId}")
    public Object deleteHazard(@PathVariable("hazardId") String hazardId)
    {
        return python.delete("/api/v1/patrol/hazards/" + hazardId, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + UPLOAD_PERMS + "')")
    @DeleteMapping("/shots/{shotId}")
    public Object deleteShot(@PathVariable("shotId") String shotId)
    {
        return python.delete("/api/v1/patrol/shots/" + shotId, actorHeaders());
    }

    @PreAuthorize("@ss.hasAnyPermi('" + VIEW_PERMS + "')")
    @GetMapping("/shots/{shotId}/file")
    public void shotFile(@PathVariable("shotId") String shotId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/patrol/shots/" + shotId + "/file", actorHeaders()), response);
    }

    private void copyDownload(ResponseEntity<byte[]> source, HttpServletResponse target) throws IOException
    {
        MediaType type = source.getHeaders().getContentType();
        target.setContentType(type == null ? MediaType.APPLICATION_OCTET_STREAM_VALUE : type.toString());
        String disposition = source.getHeaders().getFirst(HttpHeaders.CONTENT_DISPOSITION);
        if (disposition != null)
        {
            target.setHeader(HttpHeaders.CONTENT_DISPOSITION, disposition);
        }
        byte[] body = source.getBody();
        if (body != null)
        {
            target.setContentLength(body.length);
            target.getOutputStream().write(body);
        }
    }
}
