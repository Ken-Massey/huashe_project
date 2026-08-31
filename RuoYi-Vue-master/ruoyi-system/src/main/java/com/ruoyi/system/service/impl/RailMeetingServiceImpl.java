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
import com.ruoyi.system.mapper.rail.RailMeetingMapper;
import com.ruoyi.system.service.IRailMeetingService;

/** 会议协调管理 服务实现 */
@Service
public class RailMeetingServiceImpl implements IRailMeetingService
{
    @Autowired
    private RailMeetingMapper meetingMapper;

    @Override
    public List<Map<String, Object>> selectMeetingList(Map<String, Object> params)
    {
        return meetingMapper.selectMeetingList(params);
    }

    @Override
    public Map<String, Object> selectMeetingDetail(Long meetingId)
    {
        Map<String, Object> meeting = meetingMapper.selectMeetingById(meetingId);
        if (meeting == null)
        {
            throw new ServiceException("会议不存在");
        }
        meeting.put("participants", meetingMapper.selectParticipantList(meetingId));
        meeting.put("files", meetingMapper.selectFileList(meetingId));
        meeting.put("minutes", meetingMapper.selectMinutesByMeetingId(meetingId));
        meeting.put("issues", meetingMapper.selectIssueList(meetingId));
        meeting.put("decisions", meetingMapper.selectDecisionList(meetingId));
        Map<String, Object> todoQuery = new LinkedHashMap<>();
        todoQuery.put("meetingId", meetingId);
        meeting.put("todos", meetingMapper.selectTodoList(todoQuery));
        meeting.put("logs", meetingMapper.selectLogList(meetingId));
        return meeting;
    }

    @Override
    @Transactional
    public int insertMeeting(Map<String, Object> meeting, Long userId, String username)
    {
        if (StringUtils.isEmpty((String) meeting.get("meetingName")))
        {
            throw new ServiceException("会议名称不能为空");
        }
        meeting.putIfAbsent("meetingCode", buildMeetingCode());
        meeting.putIfAbsent("status", "draft");
        meeting.put("createBy", username);
        int rows = meetingMapper.insertMeeting(meeting);
        Long meetingId = toLong(meeting.get("meetingId"));
        addLog(meetingId, "meeting", meetingId, "create", "创建会议", "", "draft", userId, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateMeeting(Map<String, Object> meeting, String username)
    {
        Long meetingId = toLong(meeting.get("meetingId"));
        if (meetingId == null)
        {
            throw new ServiceException("会议ID不能为空");
        }
        meeting.put("updateBy", username);
        int rows = meetingMapper.updateMeeting(meeting);
        addLog(meetingId, "meeting", meetingId, "update", "修改会议", "", "", null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int deleteMeetingByIds(Long[] meetingIds, String username)
    {
        int rows = meetingMapper.deleteMeetingByIds(meetingIds);
        if (meetingIds != null)
        {
            for (Long meetingId : meetingIds)
            {
                addLog(meetingId, "meeting", meetingId, "delete", "删除会议", "", "deleted", null, username, "");
            }
        }
        return rows;
    }

    @Override
    @Transactional
    public int notifyMeeting(Long meetingId, Map<String, Object> request, String username)
    {
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("meetingId", meetingId);
        params.put("status", "notified");
        params.put("noticeContent", request.get("noticeContent"));
        params.put("updateBy", username);
        int rows = meetingMapper.updateMeetingStatus(params);
        addLog(meetingId, "meeting", meetingId, "notify", "发送会议通知", "", "notified", null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int markMeetingHeld(Long meetingId, String username)
    {
        Map<String, Object> meeting = meetingMapper.selectMeetingById(meetingId);
        if (meeting == null)
        {
            throw new ServiceException("会议不存在");
        }
        if ("archived".equals(meeting.get("status")))
        {
            throw new ServiceException("已归档会议不能修改状态");
        }
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("meetingId", meetingId);
        params.put("status", "held");
        params.put("updateBy", username);
        int rows = meetingMapper.updateMeetingStatus(params);
        addLog(meetingId, "meeting", meetingId, "held", "标记会议已召开", String.valueOf(meeting.get("status")), "held", null, username, "");
        return rows;
    }

    @Override
    public List<Map<String, Object>> selectParticipantList(Long meetingId)
    {
        return meetingMapper.selectParticipantList(meetingId);
    }

    @Override
    @Transactional
    public int insertParticipant(Long meetingId, Map<String, Object> participant, String username)
    {
        participant.put("meetingId", meetingId);
        participant.put("createBy", username);
        int rows = meetingMapper.insertParticipant(participant);
        addLog(meetingId, "participant", toLong(participant.get("participantId")), "participant_add", "登记参会人员", "", "", null, username, "");
        return rows;
    }

    @Override
    public int updateParticipant(Map<String, Object> participant, String username)
    {
        participant.put("updateBy", username);
        return meetingMapper.updateParticipant(participant);
    }

    @Override
    public int deleteParticipantByIds(Long[] participantIds)
    {
        return meetingMapper.deleteParticipantByIds(participantIds);
    }

    @Override
    public List<Map<String, Object>> selectFileList(Long meetingId)
    {
        return meetingMapper.selectFileList(meetingId);
    }

    @Override
    public Map<String, Object> selectFileById(Long fileId)
    {
        return meetingMapper.selectFileById(fileId);
    }

    @Override
    @Transactional
    public int insertFile(Long meetingId, Map<String, Object> file, String username)
    {
        file.put("meetingId", meetingId);
        file.put("createBy", username);
        int rows = meetingMapper.insertFile(file);
        addLog(meetingId, "file", toLong(file.get("fileId")), "file_upload", "上传会议材料", "", "", null, username, "");
        return rows;
    }

    @Override
    public int deleteFileByIds(Long[] fileIds)
    {
        return meetingMapper.deleteFileByIds(fileIds);
    }

    @Override
    @Transactional
    public Map<String, Object> saveMinutes(Long meetingId, Map<String, Object> minutes, Long userId, String username)
    {
        minutes.put("meetingId", meetingId);
        minutes.put("compileUserId", userId);
        minutes.put("compileBy", username);
        minutes.put("updateBy", username);
        Map<String, Object> existing = meetingMapper.selectMinutesByMeetingId(meetingId);
        if (existing == null)
        {
            minutes.put("createBy", username);
            meetingMapper.insertMinutes(minutes);
            addLog(meetingId, "minutes", toLong(minutes.get("minutesId")), "minutes_create", "编制会议纪要", "", "draft", userId, username, "");
        }
        else
        {
            minutes.put("minutesId", existing.get("minutesId"));
            meetingMapper.updateMinutes(minutes);
            addLog(meetingId, "minutes", toLong(existing.get("minutesId")), "minutes_update", "修改会议纪要", "", "", userId, username, "");
        }
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("meetingId", meetingId);
        params.put("status", "minuting");
        params.put("updateBy", username);
        meetingMapper.updateMeetingStatus(params);
        return meetingMapper.selectMinutesByMeetingId(meetingId);
    }

    @Override
    @Transactional
    public int confirmMinutes(Long meetingId, Map<String, Object> minutes, Long userId, String username)
    {
        minutes.put("meetingId", meetingId);
        minutes.put("confirmUserId", userId);
        minutes.put("confirmBy", username);
        minutes.put("updateBy", username);
        minutes.putIfAbsent("confirmStatus", "2");
        int rows = meetingMapper.confirmMinutes(minutes);
        addLog(meetingId, "minutes", toLong(minutes.get("minutesId")), "minutes_confirm", "确认会议纪要", "", String.valueOf(minutes.get("confirmStatus")), userId, username, String.valueOf(minutes.getOrDefault("confirmOpinion", "")));
        refreshMeetingProgress(meetingId, username);
        return rows;
    }

    @Override
    @Transactional
    public int archiveMeeting(Long meetingId, String username)
    {
        validateReadyToArchive(meetingId);
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("meetingId", meetingId);
        params.put("status", "archived");
        params.put("archiveStatus", "1");
        params.put("updateBy", username);
        int rows = meetingMapper.updateMeetingStatus(params);
        addLog(meetingId, "archive", meetingId, "archive", "会议归档", "", "archived", null, username, "");
        return rows;
    }

    @Override
    public List<Map<String, Object>> selectIssueList(Long meetingId)
    {
        return meetingMapper.selectIssueList(meetingId);
    }

    @Override
    public int insertIssue(Long meetingId, Map<String, Object> issue, String username)
    {
        issue.put("meetingId", meetingId);
        issue.putIfAbsent("status", "open");
        issue.put("createBy", username);
        int rows = meetingMapper.insertIssue(issue);
        refreshMeetingProgress(meetingId, username);
        addLog(meetingId, "issue", toLong(issue.get("issueId")), "issue_add", "记录问题", "", String.valueOf(issue.get("status")), null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateIssue(Map<String, Object> issue, String username)
    {
        applyCloseFields(issue, username);
        issue.put("updateBy", username);
        int rows = meetingMapper.updateIssue(issue);
        Long meetingId = toLong(issue.get("meetingId"));
        if (meetingId != null)
        {
            refreshMeetingProgress(meetingId, username);
            addLog(meetingId, "issue", toLong(issue.get("issueId")), "issue_update", "更新问题", "", String.valueOf(issue.get("status")), null, username, String.valueOf(issue.getOrDefault("closeRemark", "")));
        }
        return rows;
    }

    @Override
    public int deleteIssueByIds(Long[] issueIds)
    {
        return meetingMapper.deleteIssueByIds(issueIds);
    }

    @Override
    public List<Map<String, Object>> selectDecisionList(Long meetingId)
    {
        return meetingMapper.selectDecisionList(meetingId);
    }

    @Override
    public int insertDecision(Long meetingId, Map<String, Object> decision, String username)
    {
        decision.put("meetingId", meetingId);
        decision.putIfAbsent("status", "open");
        decision.put("createBy", username);
        int rows = meetingMapper.insertDecision(decision);
        refreshMeetingProgress(meetingId, username);
        addLog(meetingId, "decision", toLong(decision.get("decisionId")), "decision_add", "记录决议", "", String.valueOf(decision.get("status")), null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateDecision(Map<String, Object> decision, String username)
    {
        applyCloseFields(decision, username);
        decision.put("updateBy", username);
        int rows = meetingMapper.updateDecision(decision);
        Long meetingId = toLong(decision.get("meetingId"));
        if (meetingId != null)
        {
            refreshMeetingProgress(meetingId, username);
            addLog(meetingId, "decision", toLong(decision.get("decisionId")), "decision_update", "更新决议", "", String.valueOf(decision.get("status")), null, username, String.valueOf(decision.getOrDefault("closeRemark", "")));
        }
        return rows;
    }

    @Override
    public int deleteDecisionByIds(Long[] decisionIds)
    {
        return meetingMapper.deleteDecisionByIds(decisionIds);
    }

    @Override
    public List<Map<String, Object>> selectTodoList(Map<String, Object> params)
    {
        return meetingMapper.selectTodoList(params);
    }

    @Override
    public int insertTodo(Long meetingId, Map<String, Object> todo, String username)
    {
        todo.put("meetingId", meetingId);
        todo.putIfAbsent("status", "pending");
        todo.put("createBy", username);
        int rows = meetingMapper.insertTodo(todo);
        refreshMeetingProgress(meetingId, username);
        addLog(meetingId, "todo", toLong(todo.get("todoId")), "todo_add", "创建待办", "", String.valueOf(todo.get("status")), null, username, "");
        return rows;
    }

    @Override
    @Transactional
    public int updateTodo(Map<String, Object> todo, String username)
    {
        applyCloseFields(todo, username);
        if (isClosedStatus(todo.get("status")))
        {
            todo.putIfAbsent("closeBy", username);
        }
        todo.put("updateBy", username);
        int rows = meetingMapper.updateTodo(todo);
        Long meetingId = toLong(todo.get("meetingId"));
        if (meetingId != null)
        {
            refreshMeetingProgress(meetingId, username);
            addLog(meetingId, "todo", toLong(todo.get("todoId")), "todo_update", "更新待办", "", String.valueOf(todo.get("status")), null, username, String.valueOf(todo.getOrDefault("closeRemark", "")));
        }
        return rows;
    }

    @Override
    public int deleteTodoByIds(Long[] todoIds)
    {
        return meetingMapper.deleteTodoByIds(todoIds);
    }

    private String buildMeetingCode()
    {
        return "MT" + new SimpleDateFormat("yyyyMMddHHmmssSSS").format(new Date());
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

    private void applyCloseFields(Map<String, Object> item, String username)
    {
        if (isClosedStatus(item.get("status")))
        {
            item.putIfAbsent("closeTime", new Date());
            item.putIfAbsent("closeRemark", "已闭环");
            item.putIfAbsent("finishTime", new Date());
            item.putIfAbsent("finishContent", "已完成");
            item.putIfAbsent("closeBy", username);
        }
    }

    private void refreshMeetingProgress(Long meetingId, String username)
    {
        Map<String, Object> meeting = meetingMapper.selectMeetingById(meetingId);
        if (meeting == null || "archived".equals(meeting.get("status")) || "cancelled".equals(meeting.get("status")))
        {
            return;
        }

        String nextStatus = hasOpenTrackingItems(meetingId) ? "tracking" : "held";
        Map<String, Object> params = new LinkedHashMap<>();
        params.put("meetingId", meetingId);
        params.put("status", nextStatus);
        params.put("updateBy", username);
        meetingMapper.updateMeetingStatus(params);
    }

    private void validateReadyToArchive(Long meetingId)
    {
        Map<String, Object> minutes = meetingMapper.selectMinutesByMeetingId(meetingId);
        if (minutes == null)
        {
            throw new ServiceException("会议纪要尚未编制，不能归档");
        }
        if (!"2".equals(String.valueOf(minutes.get("confirmStatus"))))
        {
            throw new ServiceException("会议纪要尚未确认，不能归档");
        }
        if (hasOpenTrackingItems(meetingId))
        {
            throw new ServiceException("会议仍有问题、决议或待办未闭环，不能归档");
        }
    }

    private boolean hasOpenTrackingItems(Long meetingId)
    {
        for (Map<String, Object> item : meetingMapper.selectIssueList(meetingId))
        {
            if (!isClosedStatus(item.get("status")))
            {
                return true;
            }
        }
        for (Map<String, Object> item : meetingMapper.selectDecisionList(meetingId))
        {
            if (!isClosedStatus(item.get("status")))
            {
                return true;
            }
        }
        Map<String, Object> todoQuery = new LinkedHashMap<>();
        todoQuery.put("meetingId", meetingId);
        for (Map<String, Object> item : meetingMapper.selectTodoList(todoQuery))
        {
            if (!isClosedStatus(item.get("status")))
            {
                return true;
            }
        }
        return false;
    }

    private boolean isClosedStatus(Object status)
    {
        String value = String.valueOf(status);
        return "closed".equals(value) || "completed".equals(value)
                || "resolved".equals(value) || "done".equals(value);
    }

    private void addLog(Long meetingId, String targetType, Long targetId, String actionCode,
            String actionName, String fromStatus, String toStatus, Long operatorId,
            String operatorName, String opinion)
    {
        if (meetingId == null)
        {
            return;
        }
        Map<String, Object> log = new LinkedHashMap<>();
        log.put("meetingId", meetingId);
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
        meetingMapper.insertLog(log);
    }
}
