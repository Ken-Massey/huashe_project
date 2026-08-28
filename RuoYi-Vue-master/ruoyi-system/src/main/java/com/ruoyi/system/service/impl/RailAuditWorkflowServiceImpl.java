package com.ruoyi.system.service.impl;

import java.util.Date;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.domain.rail.RailAuditFlowLog;
import com.ruoyi.system.domain.rail.RailAuditFlowNode;
import com.ruoyi.system.domain.rail.RailAuditOpinionSnapshot;
import com.ruoyi.system.domain.rail.RailAuditTask;
import com.ruoyi.system.domain.rail.RailAuditWorkflow;
import com.ruoyi.system.domain.rail.RailAuditWorkflowAction;
import com.ruoyi.system.mapper.rail.RailAuditFlowLogMapper;
import com.ruoyi.system.mapper.rail.RailAuditFlowNodeMapper;
import com.ruoyi.system.mapper.rail.RailAuditOpinionSnapshotMapper;
import com.ruoyi.system.mapper.rail.RailAuditTaskMapper;
import com.ruoyi.system.mapper.rail.RailAuditWorkflowMapper;
import com.ruoyi.system.service.IRailAuditWorkflowService;

/** 案例审核多级流转 服务实现 */
@Service
public class RailAuditWorkflowServiceImpl implements IRailAuditWorkflowService
{
    private static final String FLOW_CODE = "BASEMENT_AUDIT";
    private static final String NODE_SUBMIT = "SUBMIT";
    private static final String NODE_REVIEW = "REVIEW";
    private static final String NODE_FINAL = "FINAL";
    private static final String STATUS_REVIEW = "REVIEW";
    private static final String STATUS_FINAL = "FINAL";
    private static final String STATUS_RETURNED = "RETURNED";
    private static final String STATUS_APPROVED = "APPROVED";
    private static final String STATUS_ARCHIVED = "ARCHIVED";
    private static final String TASK_TODO = "TODO";
    private static final String TASK_PASS = "PASS";
    private static final String TASK_RETURN = "RETURN";

    @Autowired
    private RailAuditWorkflowMapper workflowMapper;

    @Autowired
    private RailAuditTaskMapper taskMapper;

    @Autowired
    private RailAuditFlowLogMapper logMapper;

    @Autowired
    private RailAuditOpinionSnapshotMapper snapshotMapper;

    @Autowired
    private RailAuditFlowNodeMapper nodeMapper;

    @Override
    public RailAuditWorkflow selectWorkflowById(Long workflowId)
    {
        return workflowMapper.selectWorkflowById(workflowId);
    }

    @Override
    public List<RailAuditWorkflow> selectWorkflowList(RailAuditWorkflow workflow)
    {
        return workflowMapper.selectWorkflowList(workflow);
    }

    @Override
    public List<RailAuditWorkflow> selectTodoWorkflowList(RailAuditWorkflow workflow)
    {
        return workflowMapper.selectTodoWorkflowList(workflow);
    }

    @Override
    public List<RailAuditTask> selectTaskList(Long workflowId)
    {
        RailAuditTask query = new RailAuditTask();
        query.setWorkflowId(workflowId);
        return taskMapper.selectTaskList(query);
    }

    @Override
    public List<RailAuditFlowLog> selectLogList(Long workflowId)
    {
        return logMapper.selectLogList(workflowId);
    }

    @Override
    public List<RailAuditOpinionSnapshot> selectSnapshotList(Long workflowId)
    {
        RailAuditOpinionSnapshot query = new RailAuditOpinionSnapshot();
        query.setWorkflowId(workflowId);
        return snapshotMapper.selectSnapshotList(query);
    }

    @Override
    public List<RailAuditFlowNode> selectNodeList(RailAuditFlowNode node)
    {
        return nodeMapper.selectNodeList(node);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RailAuditWorkflow submit(RailAuditWorkflowAction action)
    {
        requireOperator(action);
        RailAuditWorkflow workflow = findOrCreateWorkflow(action);
        RailAuditFlowNode reviewNode = requireNode(NODE_REVIEW);

        taskMapper.cancelTodoTasks(workflow.getWorkflowId());
        applyLatestResult(workflow, action);
        workflow.setWorkflowStatus(STATUS_REVIEW);
        workflow.setCurrentNodeCode(reviewNode.getNodeCode());
        workflow.setCurrentNodeName(reviewNode.getNodeName());
        workflow.setCurrentAssigneeId(action.getAssigneeId());
        workflow.setCurrentAssignee(StringUtils.defaultString(action.getAssigneeName()));
        workflow.setSubmittedTime(new Date());
        workflow.setUpdateBy(action.getOperatorName());
        workflowMapper.updateWorkflow(workflow);

        RailAuditTask task = createTask(workflow, reviewNode, action.getAssigneeId(),
                StringUtils.defaultString(action.getAssigneeName()), action.getOperatorName());
        insertLog(workflow, null, "SUBMIT", "提交审核", NODE_SUBMIT, NODE_REVIEW, action);
        saveSnapshot(workflow, action, "SUMMARY", 0, "综合评价", workflow.getLatestSummary());
        return workflowMapper.selectWorkflowById(workflow.getWorkflowId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RailAuditWorkflow approve(RailAuditWorkflowAction action)
    {
        requireOperator(action);
        RailAuditWorkflow workflow = requireWorkflow(action.getWorkflowId());
        RailAuditTask currentTask = requireTodoTask(workflow.getWorkflowId());
        completeTask(currentTask, TASK_PASS, action);

        String fromNode = workflow.getCurrentNodeCode();
        if (NODE_REVIEW.equals(fromNode))
        {
            RailAuditFlowNode finalNode = requireNode(NODE_FINAL);
            workflow.setWorkflowStatus(STATUS_FINAL);
            workflow.setCurrentNodeCode(finalNode.getNodeCode());
            workflow.setCurrentNodeName(finalNode.getNodeName());
            workflow.setCurrentAssigneeId(action.getAssigneeId());
            workflow.setCurrentAssignee(StringUtils.defaultString(action.getAssigneeName()));
            workflow.setUpdateBy(action.getOperatorName());
            workflowMapper.updateWorkflow(workflow);
            createTask(workflow, finalNode, action.getAssigneeId(), StringUtils.defaultString(action.getAssigneeName()),
                    action.getOperatorName());
            insertLog(workflow, currentTask, "APPROVE", "审核通过", fromNode, NODE_FINAL, action);
        }
        else if (NODE_FINAL.equals(fromNode))
        {
            workflow.setWorkflowStatus(STATUS_APPROVED);
            workflow.setCurrentNodeCode(null);
            workflow.setCurrentNodeName(null);
            workflow.setCurrentAssigneeId(null);
            workflow.setCurrentAssignee("");
            workflow.setApprovedTime(new Date());
            workflow.setUpdateBy(action.getOperatorName());
            workflowMapper.updateWorkflow(workflow);
            insertLog(workflow, currentTask, "APPROVE", "终审通过", fromNode, null, action);
        }
        else
        {
            throw new ServiceException("当前节点不支持通过操作");
        }
        return workflowMapper.selectWorkflowById(workflow.getWorkflowId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RailAuditWorkflow returnBack(RailAuditWorkflowAction action)
    {
        requireOperator(action);
        RailAuditWorkflow workflow = requireWorkflow(action.getWorkflowId());
        RailAuditTask currentTask = requireTodoTask(workflow.getWorkflowId());
        completeTask(currentTask, TASK_RETURN, action);

        String fromNode = workflow.getCurrentNodeCode();
        workflow.setWorkflowStatus(STATUS_RETURNED);
        workflow.setCurrentNodeCode(NODE_SUBMIT);
        workflow.setCurrentNodeName("经办人提交");
        workflow.setCurrentAssigneeId(workflow.getInitiatorId());
        workflow.setCurrentAssignee(StringUtils.defaultString(workflow.getInitiatorName()));
        workflow.setUpdateBy(action.getOperatorName());
        workflowMapper.updateWorkflow(workflow);
        insertLog(workflow, currentTask, "RETURN", "退回修改", fromNode, NODE_SUBMIT, action);
        return workflowMapper.selectWorkflowById(workflow.getWorkflowId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RailAuditWorkflow archive(RailAuditWorkflowAction action)
    {
        requireOperator(action);
        RailAuditWorkflow workflow = requireWorkflow(action.getWorkflowId());
        RailAuditTask currentTask = taskMapper.selectTodoTaskByWorkflowId(workflow.getWorkflowId());
        if (currentTask != null)
        {
            completeTask(currentTask, TASK_PASS, action);
        }

        String fromNode = workflow.getCurrentNodeCode();
        workflow.setWorkflowStatus(STATUS_ARCHIVED);
        workflow.setCurrentNodeCode(null);
        workflow.setCurrentNodeName(null);
        workflow.setCurrentAssigneeId(null);
        workflow.setCurrentAssignee("");
        workflow.setApprovedTime(workflow.getApprovedTime() == null ? new Date() : workflow.getApprovedTime());
        workflow.setArchivedTime(new Date());
        workflow.setUpdateBy(action.getOperatorName());
        workflowMapper.updateWorkflow(workflow);
        insertLog(workflow, currentTask, "ARCHIVE", "终审归档", fromNode, null, action);
        return workflowMapper.selectWorkflowById(workflow.getWorkflowId());
    }

    private RailAuditWorkflow findOrCreateWorkflow(RailAuditWorkflowAction action)
    {
        RailAuditWorkflow workflow = null;
        if (action.getWorkflowId() != null)
        {
            workflow = workflowMapper.selectWorkflowById(action.getWorkflowId());
        }
        if (workflow == null)
        {
            RailAuditWorkflow query = new RailAuditWorkflow();
            query.setFlowCode(FLOW_CODE);
            query.setSessionId(action.getSessionId());
            query.setProjectId(action.getProjectId());
            query.setStageId(action.getStageId());
            workflow = workflowMapper.selectWorkflowByBusinessKey(query);
        }
        if (workflow != null)
        {
            return workflow;
        }

        workflow = new RailAuditWorkflow();
        workflow.setFlowCode(FLOW_CODE);
        workflow.setSessionId(action.getSessionId());
        workflow.setProjectId(action.getProjectId());
        workflow.setStageId(action.getStageId());
        workflow.setProjectName(StringUtils.defaultString(action.getProjectName()));
        workflow.setStageName(StringUtils.defaultString(action.getStageName()));
        workflow.setAuditVersion(action.getAuditVersion() == null ? 1 : action.getAuditVersion());
        workflow.setWorkflowStatus(STATUS_REVIEW);
        workflow.setInitiatorId(action.getOperatorId());
        workflow.setInitiatorName(action.getOperatorName());
        workflow.setCreateBy(action.getOperatorName());
        applyLatestResult(workflow, action);
        workflowMapper.insertWorkflow(workflow);
        return workflow;
    }

    private void applyLatestResult(RailAuditWorkflow workflow, RailAuditWorkflowAction action)
    {
        if (StringUtils.isNotBlank(action.getProjectName())) workflow.setProjectName(action.getProjectName());
        if (StringUtils.isNotBlank(action.getStageName())) workflow.setStageName(action.getStageName());
        if (action.getAuditVersion() != null) workflow.setAuditVersion(action.getAuditVersion());
        if (StringUtils.isNotBlank(action.getLatestSummary())) workflow.setLatestSummary(action.getLatestSummary());
        if (StringUtils.isNotBlank(action.getLatestRiskLevel())) workflow.setLatestRiskLevel(action.getLatestRiskLevel());
        if (StringUtils.isNotBlank(action.getLatestResultJson())) workflow.setLatestResultJson(action.getLatestResultJson());
    }

    private RailAuditTask createTask(RailAuditWorkflow workflow, RailAuditFlowNode node, Long assigneeId,
            String assigneeName, String operatorName)
    {
        RailAuditTask task = new RailAuditTask();
        task.setWorkflowId(workflow.getWorkflowId());
        task.setNodeCode(node.getNodeCode());
        task.setNodeName(node.getNodeName());
        task.setTaskStatus(TASK_TODO);
        task.setAssigneeId(assigneeId);
        task.setAssigneeName(assigneeName);
        task.setRoleKey(node.getRoleKey());
        task.setReceivedTime(new Date());
        task.setCreateBy(operatorName);
        taskMapper.insertTask(task);
        return task;
    }

    private void completeTask(RailAuditTask task, String status, RailAuditWorkflowAction action)
    {
        task.setTaskStatus(status);
        task.setHandledTime(new Date());
        task.setHandleOpinion(action.getOpinion());
        task.setUpdateBy(action.getOperatorName());
        taskMapper.updateTask(task);
    }

    private void insertLog(RailAuditWorkflow workflow, RailAuditTask task, String actionCode, String actionName,
            String fromNode, String toNode, RailAuditWorkflowAction action)
    {
        RailAuditFlowLog log = new RailAuditFlowLog();
        log.setWorkflowId(workflow.getWorkflowId());
        log.setTaskId(task == null ? null : task.getTaskId());
        log.setActionCode(actionCode);
        log.setActionName(actionName);
        log.setFromNodeCode(fromNode);
        log.setToNodeCode(toNode);
        log.setOperatorId(action.getOperatorId());
        log.setOperatorName(action.getOperatorName());
        log.setOpinion(action.getOpinion());
        log.setSnapshotJson(action.getSnapshotJson());
        log.setCreateBy(action.getOperatorName());
        logMapper.insertLog(log);
    }

    private void saveSnapshot(RailAuditWorkflow workflow, RailAuditWorkflowAction action, String type, int opinionNo,
            String title, String content)
    {
        if (StringUtils.isBlank(content) && StringUtils.isBlank(action.getLatestResultJson()))
        {
            return;
        }
        RailAuditOpinionSnapshot snapshot = new RailAuditOpinionSnapshot();
        snapshot.setWorkflowId(workflow.getWorkflowId());
        snapshot.setSessionId(workflow.getSessionId());
        snapshot.setAuditVersion(workflow.getAuditVersion());
        snapshot.setOpinionNo(opinionNo);
        snapshot.setOpinionType(type);
        snapshot.setTitle(title);
        snapshot.setRiskLevel(workflow.getLatestRiskLevel());
        snapshot.setOpinionContent(content);
        snapshot.setResultJson(action.getLatestResultJson());
        snapshot.setSourceFilesJson(action.getSourceFilesJson());
        snapshot.setCreateBy(action.getOperatorName());
        snapshotMapper.insertSnapshot(snapshot);
    }

    private RailAuditWorkflow requireWorkflow(Long workflowId)
    {
        if (workflowId == null)
        {
            throw new ServiceException("缺少流程实例ID");
        }
        RailAuditWorkflow workflow = workflowMapper.selectWorkflowById(workflowId);
        if (workflow == null)
        {
            throw new ServiceException("审核流程不存在");
        }
        return workflow;
    }

    private RailAuditTask requireTodoTask(Long workflowId)
    {
        RailAuditTask task = taskMapper.selectTodoTaskByWorkflowId(workflowId);
        if (task == null)
        {
            throw new ServiceException("当前流程没有待处理任务");
        }
        return task;
    }

    private RailAuditFlowNode requireNode(String nodeCode)
    {
        RailAuditFlowNode query = new RailAuditFlowNode();
        query.setFlowCode(FLOW_CODE);
        query.setNodeCode(nodeCode);
        RailAuditFlowNode node = nodeMapper.selectNodeByCode(query);
        if (node == null)
        {
            throw new ServiceException("流程节点未配置：" + nodeCode);
        }
        return node;
    }

    private void requireOperator(RailAuditWorkflowAction action)
    {
        if (action == null || action.getOperatorId() == null || StringUtils.isBlank(action.getOperatorName()))
        {
            throw new ServiceException("缺少当前登录用户信息");
        }
    }
}
