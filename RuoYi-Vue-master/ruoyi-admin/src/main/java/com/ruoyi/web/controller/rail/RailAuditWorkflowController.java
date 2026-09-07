package com.ruoyi.web.controller.rail;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.system.domain.rail.RailAuditFlowNode;
import com.ruoyi.system.domain.rail.RailAuditFlowLog;
import com.ruoyi.system.domain.rail.RailAuditOpinionSnapshot;
import com.ruoyi.system.domain.rail.RailAuditTask;
import com.ruoyi.system.domain.rail.RailAuditWorkflow;
import com.ruoyi.system.domain.rail.RailAuditWorkflowAction;
import com.ruoyi.system.service.IRailAuditWorkflowService;
import com.ruoyi.web.service.PythonAuditClient;

/** 案例审核多级流转控制器 */
@RestController
@RequestMapping("/rail/audit/workflow")
public class RailAuditWorkflowController extends BaseController
{
    @Autowired
    private IRailAuditWorkflowService workflowService;

    @Autowired
    private PythonAuditClient python;

    /** 查询审核流程列表 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/list")
    public TableDataInfo list(RailAuditWorkflow workflow)
    {
        startPage();
        List<RailAuditWorkflow> list = workflowService.selectWorkflowList(workflow);
        return getDataTable(list);
    }

    /** 查询当前用户待办 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/todo")
    public TableDataInfo todo(RailAuditWorkflow workflow)
    {
        workflow.setCurrentUserId(getUserId());
        startPage();
        List<RailAuditWorkflow> list = workflowService.selectTodoWorkflowList(workflow);
        return getDataTable(list);
    }

    /** 获取流程详情，包含任务、日志和审核意见快照 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/{workflowId}")
    public AjaxResult getInfo(@PathVariable Long workflowId)
    {
        AjaxResult result = success(workflowService.selectWorkflowById(workflowId));
        result.put("tasks", workflowService.selectTaskList(workflowId));
        result.put("logs", workflowService.selectLogList(workflowId));
        result.put("snapshots", workflowService.selectSnapshotList(workflowId));
        return result;
    }

    /** 获取流转日志 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/{workflowId}/logs")
    public AjaxResult logs(@PathVariable Long workflowId)
    {
        List<RailAuditFlowLog> list = workflowService.selectLogList(workflowId);
        return success(list);
    }

    /** 获取审核意见快照 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/{workflowId}/snapshots")
    public AjaxResult snapshots(@PathVariable Long workflowId)
    {
        List<RailAuditOpinionSnapshot> list = workflowService.selectSnapshotList(workflowId);
        return success(list);
    }

    /** 获取流程节点配置 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:config')")
    @GetMapping("/nodes")
    public AjaxResult nodes(RailAuditFlowNode node)
    {
        return success(workflowService.selectNodeList(node));
    }

    /** 提交审核 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:submit')")
    @Log(title = "案例审核流转", businessType = BusinessType.INSERT)
    @PostMapping("/submit")
    public AjaxResult submit(@RequestBody RailAuditWorkflowAction action)
    {
        fillOperator(action);
        return success(workflowService.submit(action));
    }

    /** 审核通过 */
    @PreAuthorize("@ss.hasAnyPermi('rail:audit:workflow:approve,rail:audit:workflow:submitFinal,rail:audit:workflow:final')")
    @Log(title = "案例审核流转", businessType = BusinessType.UPDATE)
    @PostMapping("/approve")
    public AjaxResult approve(@RequestBody RailAuditWorkflowAction action)
    {
        fillOperator(action);
        RailAuditWorkflow workflow = workflowService.approve(action);
        AjaxResult result = success(workflow);
        if ("APPROVED".equals(workflow.getWorkflowStatus()))
        {
            try
            {
                result.put("patrolTask", python.post("/api/v1/patrol/workflow-tasks", patrolTaskPayload(workflow, action)));
            }
            catch (ServiceException exception)
            {
                // Workflow approval is already persisted. Return a visible warning instead of incorrectly reporting a failed approval.
                result.put("patrolTaskSyncWarning", "终审已通过，但现场巡查任务创建失败：" + exception.getMessage());
            }
        }
        return result;
    }

    /** 退回修改 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:return')")
    @Log(title = "案例审核流转", businessType = BusinessType.UPDATE)
    @PostMapping("/return")
    public AjaxResult returnBack(@RequestBody RailAuditWorkflowAction action)
    {
        fillOperator(action);
        return success(workflowService.returnBack(action));
    }

    /** 终审归档 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:archive')")
    @Log(title = "案例审核流转", businessType = BusinessType.UPDATE)
    @PostMapping("/archive")
    public AjaxResult archive(@RequestBody RailAuditWorkflowAction action)
    {
        fillOperator(action);
        return success(workflowService.archive(action));
    }

    /** 获取任务列表 */
    @PreAuthorize("@ss.hasPermi('rail:audit:workflow:list')")
    @GetMapping("/{workflowId}/tasks")
    public AjaxResult tasks(@PathVariable Long workflowId)
    {
        List<RailAuditTask> list = workflowService.selectTaskList(workflowId);
        return success(list);
    }

    private void fillOperator(RailAuditWorkflowAction action)
    {
        if (action == null)
        {
            throw new ServiceException("请求参数不能为空");
        }
        action.setOperatorId(getUserId());
        action.setOperatorName(getUsername());
    }

    private Map<String, Object> patrolTaskPayload(RailAuditWorkflow workflow, RailAuditWorkflowAction action)
    {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("workflow_id", String.valueOf(workflow.getWorkflowId()));
        payload.put("project_name", workflow.getProjectName());
        payload.put("initiator_id", workflow.getInitiatorId());
        payload.put("initiator_name", workflow.getInitiatorName());
        payload.put("latest_summary", workflow.getLatestSummary());
        payload.put("latest_result_json", workflow.getLatestResultJson());
        payload.put("final_approval_opinion", action.getOpinion());
        return payload;
    }
}
