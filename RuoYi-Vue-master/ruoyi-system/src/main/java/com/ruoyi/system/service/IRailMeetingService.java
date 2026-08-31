package com.ruoyi.system.service;

import java.util.List;
import java.util.Map;

/** 会议协调管理 服务层 */
public interface IRailMeetingService
{
    public List<Map<String, Object>> selectMeetingList(Map<String, Object> params);

    public Map<String, Object> selectMeetingDetail(Long meetingId);

    public int insertMeeting(Map<String, Object> meeting, Long userId, String username);

    public int updateMeeting(Map<String, Object> meeting, String username);

    public int deleteMeetingByIds(Long[] meetingIds, String username);

    public int notifyMeeting(Long meetingId, Map<String, Object> request, String username);

    public int markMeetingHeld(Long meetingId, String username);

    public List<Map<String, Object>> selectParticipantList(Long meetingId);

    public int insertParticipant(Long meetingId, Map<String, Object> participant, String username);

    public int updateParticipant(Map<String, Object> participant, String username);

    public int deleteParticipantByIds(Long[] participantIds);

    public List<Map<String, Object>> selectFileList(Long meetingId);

    public Map<String, Object> selectFileById(Long fileId);

    public int insertFile(Long meetingId, Map<String, Object> file, String username);

    public int deleteFileByIds(Long[] fileIds);

    public Map<String, Object> saveMinutes(Long meetingId, Map<String, Object> minutes, Long userId, String username);

    public int confirmMinutes(Long meetingId, Map<String, Object> minutes, Long userId, String username);

    public int archiveMeeting(Long meetingId, String username);

    public List<Map<String, Object>> selectIssueList(Long meetingId);

    public int insertIssue(Long meetingId, Map<String, Object> issue, String username);

    public int updateIssue(Map<String, Object> issue, String username);

    public int deleteIssueByIds(Long[] issueIds);

    public List<Map<String, Object>> selectDecisionList(Long meetingId);

    public int insertDecision(Long meetingId, Map<String, Object> decision, String username);

    public int updateDecision(Map<String, Object> decision, String username);

    public int deleteDecisionByIds(Long[] decisionIds);

    public List<Map<String, Object>> selectTodoList(Map<String, Object> params);

    public int insertTodo(Long meetingId, Map<String, Object> todo, String username);

    public int updateTodo(Map<String, Object> todo, String username);

    public int deleteTodoByIds(Long[] todoIds);
}
