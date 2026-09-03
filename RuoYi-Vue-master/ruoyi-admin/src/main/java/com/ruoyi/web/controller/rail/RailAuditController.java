package com.ruoyi.web.controller.rail;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.web.service.PythonAuditClient;

/** RuoYi-facing proxy for the intelligent rail protection workflows. */
@RestController
@RequestMapping("/rail")
public class RailAuditController
{
    private static final String TASK_PERMISSIONS =
            "rail:reply:generate,rail:audit:run,rail:advice:generate,rail:knowledge:list,rail:archive:audit:list";

    private final PythonAuditClient python;

    public RailAuditController(PythonAuditClient python)
    {
        this.python = python;
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/reply/tasks", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object createReplyTask(@RequestParam("file") MultipartFile file,
            @RequestParam("payload") String payload,
            @RequestParam(value = "schemeFile", required = false) MultipartFile schemeFile,
            @RequestParam(value = "expertOpinionFile", required = false) MultipartFile expertOpinionFile,
            @RequestParam(value = "attachmentFiles", required = false) MultipartFile[] attachmentFiles)
    {
        Map<String, MultipartFile> files = new LinkedHashMap<>();
        files.put("file", file);
        files.put("scheme_file", schemeFile);
        files.put("expert_opinion_file", expertOpinionFile);
        return python.postFiles("/api/v1/stage1/tasks", files, Map.of("payload", payload),
                optionalFiles("attachmentFiles", attachmentFiles));
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/reply/recognize", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object recognizeReplyLetter(@RequestParam("file") MultipartFile file)
    {
        return python.postFiles("/api/v1/stage1/recognize", Map.of("file", file), Map.of());
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit/tasks", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object createAuditTask(@RequestParam("file") MultipartFile file,
            @RequestParam(value = "options", required = false) String options,
            @RequestParam(value = "attachmentFiles", required = false) MultipartFile[] attachmentFiles)
    {
        return python.postFiles("/api/v1/stage2/audit/tasks", Map.of("file", file), optional("options", options),
                optionalFiles("attachmentFiles", attachmentFiles));
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/advice/tasks", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object createAdviceTask(@RequestParam("file") MultipartFile file,
            @RequestParam(value = "options", required = false) String options)
    {
        return python.postFiles("/api/v1/stage2/advice/tasks", Map.of("file", file), optional("options", options));
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/full/tasks", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object createFullTask(@RequestParam("file") MultipartFile file,
            @RequestParam(value = "options", required = false) String options,
            @RequestParam(value = "attachmentFiles", required = false) MultipartFile[] attachmentFiles)
    {
        return python.postFiles("/api/v1/stage2/full/tasks", Map.of("file", file), optional("options", options),
                optionalFiles("attachmentFiles", attachmentFiles));
    }

    @PreAuthorize("@ss.hasAnyPermi('" + TASK_PERMISSIONS + "')")
    @GetMapping("/tasks")
    public Object tasks(@RequestParam(name = "limit", defaultValue = "100") Integer limit)
    {
        return python.get("/api/v1/tasks", Map.of("limit", limit));
    }

    @PreAuthorize("@ss.hasAnyPermi('" + TASK_PERMISSIONS + "')")
    @GetMapping("/tasks/{taskId}")
    public Object task(@PathVariable("taskId") String taskId)
    {
        return python.get("/api/v1/tasks/" + taskId);
    }

    @PreAuthorize("@ss.hasAnyPermi('" + TASK_PERMISSIONS + "')")
    @GetMapping("/tasks/{taskId}/result")
    public Object taskResult(@PathVariable("taskId") String taskId)
    {
        return python.get("/api/v1/tasks/" + taskId + "/result");
    }

    @PreAuthorize("@ss.hasAnyPermi('" + TASK_PERMISSIONS + "')")
    @GetMapping("/tasks/{taskId}/files")
    public Object taskFiles(@PathVariable("taskId") String taskId)
    {
        return python.get("/api/v1/tasks/" + taskId + "/files");
    }

    @PreAuthorize("@ss.hasAnyPermi('" + TASK_PERMISSIONS + "')")
    @GetMapping("/tasks/{taskId}/files/{fileId}")
    public void taskFile(@PathVariable("taskId") String taskId, @PathVariable("fileId") String fileId,
            HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/tasks/" + taskId + "/files/" + fileId), response);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object createAuditSession(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @GetMapping("/audit-sessions/{sessionId}")
    public Object auditSession(@PathVariable("sessionId") String sessionId)
    {
        return python.get("/api/v1/audit-sessions/" + sessionId);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @GetMapping("/audit-sessions/{sessionId}/items")
    public Object auditSessionItems(@PathVariable("sessionId") String sessionId)
    {
        return python.get("/api/v1/audit-sessions/" + sessionId + "/items");
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions/{sessionId}/items", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object createAuditSessionItem(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions/" + sessionId + "/items", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions/{sessionId}/items/{itemId}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object updateAuditSessionItem(@PathVariable("sessionId") String sessionId,
            @PathVariable("itemId") String itemId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions/" + sessionId + "/items/" + itemId, request);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @DeleteMapping("/audit-sessions/{sessionId}/items/{itemId}")
    public Object deleteAuditSessionItem(@PathVariable("sessionId") String sessionId,
            @PathVariable("itemId") String itemId)
    {
        return python.delete("/api/v1/audit-sessions/" + sessionId + "/items/" + itemId);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @GetMapping("/audit-sessions/{sessionId}/messages")
    public Object auditSessionMessages(@PathVariable("sessionId") String sessionId)
    {
        return python.get("/api/v1/audit-sessions/" + sessionId + "/messages");
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions/{sessionId}/messages", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object createAuditSessionMessage(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions/" + sessionId + "/messages", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions/{sessionId}/chat", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object reviseAuditSession(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions/" + sessionId + "/chat", request);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:audit:run,rail:archive:add')")
    @PostMapping(value = "/audit-sessions/{sessionId}/archive", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object writeAuditSessionToArchive(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/audit-sessions/" + sessionId + "/archive", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:audit:run')")
    @PostMapping(value = "/audit-sessions/{sessionId}/reply", consumes = MediaType.APPLICATION_JSON_VALUE)
    public void generateAuditSessionReply(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request, HttpServletResponse response) throws IOException
    {
        copyDownload(python.postDownload("/api/v1/audit-sessions/" + sessionId + "/reply", request), response);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/cases")
    public Object knowledgeCases(@RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "includeInactive", defaultValue = "false") Boolean includeInactive)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("keyword", keyword);
        query.put("include_inactive", includeInactive);
        return python.get("/api/v1/knowledge/cases", query);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/case-folders")
    public Object caseFolders()
    {
        return python.get("/api/v1/knowledge/case-folders");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/case-folders")
    public Object createCaseFolder(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/case-folders", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/case-folders/{folderId}/rename")
    public Object renameCaseFolder(@PathVariable("folderId") String folderId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/case-folders/" + folderId + "/rename", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/case-folders/{folderId}")
    public Object deleteCaseFolder(@PathVariable("folderId") String folderId)
    {
        return python.delete("/api/v1/knowledge/case-folders/" + folderId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/cases/{caseId}")
    public Object knowledgeCase(@PathVariable("caseId") String caseId)
    {
        return python.get("/api/v1/knowledge/cases/" + caseId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/cases/{caseId}/content")
    public Object knowledgeContent(@PathVariable("caseId") String caseId,
            @RequestParam(name = "limit", defaultValue = "50000") Integer limit)
    {
        return python.get("/api/v1/knowledge/cases/" + caseId + "/content", Map.of("limit", limit));
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping(value = "/knowledge/cases", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object importKnowledge(@RequestParam("file") MultipartFile file,
            @RequestParam(name = "caseName", required = false) String caseName,
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "folder_id", required = false) String folderId)
    {
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("case_name", caseName);
        fields.put("category", category);
        fields.put("folder_id", folderId);
        return python.postFiles("/api/v1/knowledge/cases", Map.of("file", file), fields);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/cases/{caseId}/folder")
    public Object moveCase(@PathVariable("caseId") String caseId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/cases/" + caseId + "/folder", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/cases/{caseId}/rename")
    public Object renameCase(@PathVariable("caseId") String caseId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/cases/" + caseId + "/rename", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/cases/{caseId}")
    public Object disableKnowledge(@PathVariable("caseId") String caseId)
    {
        return python.delete("/api/v1/knowledge/cases/" + caseId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @PostMapping("/knowledge/cases/{caseId}/restore")
    public Object restoreKnowledge(@PathVariable("caseId") String caseId)
    {
        return python.post("/api/v1/knowledge/cases/" + caseId + "/restore");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/cases/{caseId}/permanent")
    public Object deleteKnowledge(@PathVariable("caseId") String caseId)
    {
        return python.delete("/api/v1/knowledge/cases/" + caseId + "/permanent");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/cases/{caseId}/file")
    public void knowledgeFile(@PathVariable("caseId") String caseId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/knowledge/cases/" + caseId + "/file"), response);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/assets")
    public Object libraryAssets(@RequestParam(name = "library_type") String libraryType,
            @RequestParam(name = "folder_id", required = false) String folderId,
            @RequestParam(name = "keyword", required = false) String keyword)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("library_type", libraryType);
        query.put("folder_id", folderId);
        query.put("keyword", keyword);
        return python.get("/api/v1/knowledge/assets", query);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping(value = "/knowledge/assets", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object uploadLibraryAsset(@RequestParam("file") MultipartFile file,
            @RequestParam(name = "library_type") String libraryType,
            @RequestParam(name = "folder_id", required = false) String folderId,
            @RequestParam(name = "display_name", required = false) String displayName)
    {
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("library_type", libraryType);
        fields.put("folder_id", folderId);
        fields.put("display_name", displayName);
        return python.postFiles("/api/v1/knowledge/assets", Map.of("file", file), fields);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/assets/{assetId}/rename")
    public Object renameLibraryAsset(@PathVariable("assetId") String assetId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/assets/" + assetId + "/rename", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/assets/{assetId}/folder")
    public Object moveLibraryAsset(@PathVariable("assetId") String assetId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/assets/" + assetId + "/folder", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/assets/{assetId}")
    public Object deleteLibraryAsset(@PathVariable("assetId") String assetId)
    {
        return python.delete("/api/v1/knowledge/assets/" + assetId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/assets/{assetId}/file")
    public void libraryAssetFile(@PathVariable("assetId") String assetId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/knowledge/assets/" + assetId + "/file"), response);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/stats")
    public Object knowledgeStats()
    {
        return python.get("/api/v1/knowledge/stats");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulations")
    public Object regulations(@RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "includeInactive", defaultValue = "false") Boolean includeInactive,
            @RequestParam(name = "folder_id", required = false) String folderId)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("keyword", keyword);
        query.put("include_inactive", includeInactive);
        query.put("folder_id", folderId);
        return python.get("/api/v1/knowledge/regulations", query);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulation-folders")
    public Object regulationFolders()
    {
        return python.get("/api/v1/knowledge/regulation-folders");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/regulation-folders")
    public Object createRegulationFolder(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/regulation-folders", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/regulation-folders/{folderId}/rename")
    public Object renameRegulationFolder(@PathVariable("folderId") String folderId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/regulation-folders/" + folderId + "/rename", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/regulation-folders/{folderId}")
    public Object deleteRegulationFolder(@PathVariable("folderId") String folderId)
    {
        return python.delete("/api/v1/knowledge/regulation-folders/" + folderId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulations/stats")
    public Object regulationStats()
    {
        return python.get("/api/v1/knowledge/regulations/stats");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulations/{regulationId}")
    public Object regulation(@PathVariable("regulationId") String regulationId)
    {
        return python.get("/api/v1/knowledge/regulations/" + regulationId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulations/{regulationId}/content")
    public Object regulationContent(@PathVariable("regulationId") String regulationId,
            @RequestParam(name = "limit", defaultValue = "100000") Integer limit)
    {
        return python.get("/api/v1/knowledge/regulations/" + regulationId + "/content", Map.of("limit", limit));
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping(value = "/knowledge/regulations", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Object importRegulation(@RequestParam("file") MultipartFile file,
            @RequestParam(name = "title", required = false) String title,
            @RequestParam(name = "version", required = false) String version,
            @RequestParam(name = "folder_id", required = false) String folderId)
    {
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("title", title);
        fields.put("version", version);
        fields.put("folder_id", folderId);
        return python.postFiles("/api/v1/knowledge/regulations", Map.of("file", file), fields);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/regulations/{regulationId}/folder")
    public Object moveRegulation(@PathVariable("regulationId") String regulationId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/regulations/" + regulationId + "/folder", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/regulations/{regulationId}/rename")
    public Object renameRegulation(@PathVariable("regulationId") String regulationId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/regulations/" + regulationId + "/rename", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/regulations/{regulationId}/generate-rules")
    public Object generateRegulationRules(@PathVariable("regulationId") String regulationId)
    {
        return python.post("/api/v1/knowledge/regulations/" + regulationId + "/generate-rules");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/regulations/{regulationId}")
    public Object disableRegulation(@PathVariable("regulationId") String regulationId)
    {
        return python.delete("/api/v1/knowledge/regulations/" + regulationId);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @PostMapping("/knowledge/regulations/{regulationId}/restore")
    public Object restoreRegulation(@PathVariable("regulationId") String regulationId)
    {
        return python.post("/api/v1/knowledge/regulations/" + regulationId + "/restore");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:remove')")
    @DeleteMapping("/knowledge/regulations/{regulationId}/permanent")
    public Object deleteRegulation(@PathVariable("regulationId") String regulationId)
    {
        return python.delete("/api/v1/knowledge/regulations/" + regulationId + "/permanent");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/regulations/{regulationId}/file")
    public void regulationFile(@PathVariable("regulationId") String regulationId, HttpServletResponse response) throws IOException
    {
        copyDownload(python.download("/api/v1/knowledge/regulations/" + regulationId + "/file"), response);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/knowledge/rules")
    public Object regulationRules(@RequestParam(name = "regulationId", required = false) String regulationId,
            @RequestParam(name = "ruleStatus", required = false) String ruleStatus)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("regulation_id", regulationId);
        query.put("rule_status", ruleStatus);
        return python.get("/api/v1/knowledge/rules", query);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping(value = "/knowledge/rules/{ruleId}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object updateRegulationRule(@PathVariable("ruleId") String ruleId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/rules/" + ruleId, request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping(value = "/knowledge/rules/{ruleId}/test", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object testRegulationRule(@PathVariable("ruleId") String ruleId, @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/knowledge/rules/" + ruleId + "/test", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:import')")
    @PostMapping("/knowledge/rules/{ruleId}/publish")
    public Object publishRegulationRule(@PathVariable("ruleId") String ruleId)
    {
        return python.post("/api/v1/knowledge/rules/" + ruleId + "/publish");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/agent/config")
    public Object agentConfig()
    {
        return python.get("/api/v1/agent/config");
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @PostMapping(value = "/agent/config", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object saveAgentConfig(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/agent/config", request);
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/agent/sessions")
    public Object agentSessions(@RequestParam(name = "limit", defaultValue = "50") Integer limit)
    {
        return python.get("/api/v1/agent/sessions", Map.of("limit", limit), actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @PostMapping(value = "/agent/sessions", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object createAgentSession(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/agent/sessions", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @GetMapping("/agent/sessions/{sessionId}")
    public Object agentSession(@PathVariable("sessionId") String sessionId)
    {
        return python.get("/api/v1/agent/sessions/" + sessionId, null, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @PostMapping(value = "/agent/sessions/{sessionId}/rename", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object renameAgentSession(@PathVariable("sessionId") String sessionId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/agent/sessions/" + sessionId + "/rename", request, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @DeleteMapping("/agent/sessions/{sessionId}")
    public Object deleteAgentSession(@PathVariable("sessionId") String sessionId)
    {
        return python.delete("/api/v1/agent/sessions/" + sessionId, actorHeaders());
    }

    @PreAuthorize("@ss.hasPermi('rail:knowledge:list')")
    @PostMapping(value = "/agent/ask", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Object askAgent(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/agent/ask", request, actorHeaders());
    }

    private Map<String, String> actorHeaders()
    {
        Long userId = SecurityUtils.getUserId();
        String username = SecurityUtils.getUsername();
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("X-Actor-User-Id", userId == null ? "" : String.valueOf(userId));
        headers.put("X-Actor-Name", username == null ? "" : username);
        return headers;
    }

    private Map<String, String> optional(String name, String value)
    {
        Map<String, String> result = new LinkedHashMap<>();
        result.put(name, value);
        return result;
    }

    private Map<String, MultipartFile[]> optionalFiles(String name, MultipartFile[] value)
    {
        Map<String, MultipartFile[]> result = new LinkedHashMap<>();
        if (value != null && value.length > 0)
        {
            result.put(name, value);
        }
        return result;
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
