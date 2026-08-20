package com.ruoyi.web.controller.rail;

import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.web.service.PythonAuditClient;

/** RuoYi-facing proxy for project archives, custom stages and their single audit records. */
@RestController
@RequestMapping("/rail/archives")
public class RailProjectArchiveController
{
    private final PythonAuditClient python;

    public RailProjectArchiveController(PythonAuditClient python)
    {
        this.python = python;
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:list,rail:audit:run')")
    @GetMapping("/projects")
    public Object projects(@RequestParam(name = "keyword", defaultValue = "") String keyword,
            @RequestParam(name = "includeArchived", defaultValue = "false") Boolean includeArchived)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("keyword", keyword);
        query.put("include_archived", includeArchived);
        return python.get("/api/v1/project-archives/projects", query);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:add,rail:audit:run')")
    @PostMapping("/projects")
    public Object createProject(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/project-archives/projects", request);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:add,rail:audit:run')")
    @PostMapping("/resolve")
    public Object resolveProjectStage(@RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/project-archives/resolve", request);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:list,rail:audit:run')")
    @GetMapping("/projects/nearby")
    public Object nearbyProjects(@RequestParam(name = "longitude") Double longitude,
            @RequestParam(name = "latitude") Double latitude,
            @RequestParam(name = "radius_m", defaultValue = "1000") Integer radiusM,
            @RequestParam(name = "exclude_project_id", defaultValue = "") String excludeProjectId,
            @RequestParam(name = "limit", defaultValue = "12") Integer limit)
    {
        Map<String, Object> query = new LinkedHashMap<>();
        query.put("longitude", longitude);
        query.put("latitude", latitude);
        query.put("radius_m", radiusM);
        query.put("exclude_project_id", excludeProjectId);
        query.put("limit", limit);
        return python.get("/api/v1/project-archives/projects/nearby", query);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:list,rail:audit:run')")
    @GetMapping("/projects/{projectId}")
    public Object project(@PathVariable("projectId") String projectId,
            @RequestParam(name = "includeArchivedStages", defaultValue = "false") Boolean includeArchivedStages)
    {
        return python.get(
                "/api/v1/project-archives/projects/" + projectId,
                Map.of("include_archived_stages", includeArchivedStages));
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:list,rail:audit:run')")
    @GetMapping("/projects/{projectId}/latest-audit-form")
    public Object latestAuditForm(@PathVariable("projectId") String projectId)
    {
        return python.get("/api/v1/project-archives/projects/" + projectId + "/latest-audit-form");
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:edit')")
    @PostMapping("/projects/{projectId}")
    public Object updateProject(@PathVariable("projectId") String projectId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/project-archives/projects/" + projectId, request);
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:remove')")
    @DeleteMapping("/projects/{projectId}")
    public Object deleteProject(@PathVariable("projectId") String projectId)
    {
        return python.delete("/api/v1/project-archives/projects/" + projectId);
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:remove')")
    @PostMapping("/projects/{projectId}/archive")
    public Object archiveProject(@PathVariable("projectId") String projectId)
    {
        return python.post("/api/v1/project-archives/projects/" + projectId + "/archive");
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:edit')")
    @PostMapping("/projects/{projectId}/restore")
    public Object restoreProject(@PathVariable("projectId") String projectId)
    {
        return python.post("/api/v1/project-archives/projects/" + projectId + "/restore");
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:add,rail:audit:run')")
    @PostMapping("/projects/{projectId}/stages")
    public Object createStage(@PathVariable("projectId") String projectId,
            @RequestBody Map<String, Object> request)
    {
        return python.post(
                "/api/v1/project-archives/projects/" + projectId + "/stages",
                request);
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:list,rail:audit:run')")
    @GetMapping("/stages/{stageId}")
    public Object stage(@PathVariable("stageId") String stageId)
    {
        return python.get("/api/v1/project-archives/stages/" + stageId);
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:edit')")
    @PostMapping("/stages/{stageId}")
    public Object updateStage(@PathVariable("stageId") String stageId,
            @RequestBody Map<String, Object> request)
    {
        return python.post("/api/v1/project-archives/stages/" + stageId, request);
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:remove')")
    @PostMapping("/stages/{stageId}/archive")
    public Object archiveStage(@PathVariable("stageId") String stageId)
    {
        return python.post("/api/v1/project-archives/stages/" + stageId + "/archive");
    }

    @PreAuthorize("@ss.hasPermi('rail:archive:edit')")
    @PostMapping("/stages/{stageId}/restore")
    public Object restoreStage(@PathVariable("stageId") String stageId)
    {
        return python.post("/api/v1/project-archives/stages/" + stageId + "/restore");
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:audit:list,rail:audit:run')")
    @GetMapping("/stages/{stageId}/audit")
    public Object stageAudit(@PathVariable("stageId") String stageId)
    {
        return python.get("/api/v1/project-archives/stages/" + stageId + "/audit");
    }

    @PreAuthorize("@ss.hasAnyPermi('rail:archive:audit:list,rail:audit:run')")
    @GetMapping("/stages/{stageId}/previous-audits")
    public Object previousAudits(@PathVariable("stageId") String stageId)
    {
        return python.get(
                "/api/v1/project-archives/stages/" + stageId + "/previous-audits");
    }
}
