package com.ruoyi.system.mapper.rail;

import java.util.List;
import java.util.Map;

/** 会议协调管理 数据层 */
public interface RailMeetingMapper
{
    public List<Map<String, Object>> selectMeetingList(Map<String, Object> params);

    public Map<String, Object> selectMeetingById(Long meetingId);

    public int insertMeeting(Map<String, Object> meeting);

    public int updateMeeting(Map<String, Object> meeting);

    public int deleteMeetingByIds(Long[] meetingIds);

    public int updateMeetingStatus(Map<String, Object> params);

    public List<Map<String, Object>> selectParticipantList(Long meetingId);

    public int insertParticipant(Map<String, Object> participant);

    public int updateParticipant(Map<String, Object> participant);

    public int deleteParticipantByIds(Long[] participantIds);

    public List<Map<String, Object>> selectFileList(Long meetingId);

    public Map<String, Object> selectFileById(Long fileId);

    public int insertFile(Map<String, Object> file);

    public int deleteFileByIds(Long[] fileIds);

    public Map<String, Object> selectMinutesByMeetingId(Long meetingId);

    public int insertMinutes(Map<String, Object> minutes);

    public int updateMinutes(Map<String, Object> minutes);

    public int confirmMinutes(Map<String, Object> minutes);

    public List<Map<String, Object>> selectIssueList(Long meetingId);

    public int insertIssue(Map<String, Object> issue);

    public int updateIssue(Map<String, Object> issue);

    public int deleteIssueByIds(Long[] issueIds);

    public List<Map<String, Object>> selectDecisionList(Long meetingId);

    public int insertDecision(Map<String, Object> decision);

    public int updateDecision(Map<String, Object> decision);

    public int deleteDecisionByIds(Long[] decisionIds);

    public List<Map<String, Object>> selectTodoList(Map<String, Object> params);

    public int insertTodo(Map<String, Object> todo);

    public int updateTodo(Map<String, Object> todo);

    public int deleteTodoByIds(Long[] todoIds);

    public int insertLog(Map<String, Object> log);

    public List<Map<String, Object>> selectLogList(Long meetingId);
}
