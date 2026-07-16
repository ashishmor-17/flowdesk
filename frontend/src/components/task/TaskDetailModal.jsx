import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { formatTime } from '../../utils/format';
import { 
  X, 
  User, 
  Calendar, 
  MessageSquare, 
  ChevronDown, 
  Send,
  Plus,
  Trash2,
  AlertTriangle,
  Paperclip,
  CheckCircle,
  Clock,
  Download,
  FileText,
  UserCheck,
  Check,
  AlertCircle,
  Eye,
  EyeOff,
  Link,
  History
} from 'lucide-react';

export default function TaskDetailModal({ task, onClose }) {
  const { user: currentUser, activeOrg } = useAuth();
  const [currentTask, setCurrentTask] = useState(task);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [priority, setPriority] = useState(task.priority);
  const [dueDate, setDueDate] = useState(task.due_date ? task.due_date.split('T')[0] : '');
  const [statusVal, setStatusVal] = useState(task.status);
  
  // Tab control for right panel
  const [rightPanelTab, setRightPanelTab] = useState('comments');

  // Comments state
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [commentCursor, setCommentCursor] = useState(null);
  const [hasMoreComments, setHasMoreComments] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  // General members state (for mentions and assignees/approvers)
  const [orgMembers, setOrgMembers] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [mentionStartIndex, setMentionStartIndex] = useState(-1);
  const commentInputRef = useRef(null);

  // Approval mentions state
  const [showApprovalMentions, setShowApprovalMentions] = useState(false);
  const [approvalMentionFilter, setApprovalMentionFilter] = useState('');
  const [approvalMentionStartIndex, setApprovalMentionStartIndex] = useState(-1);
  const approvalCommentInputRef = useRef(null);

  // Attachments state
  const [attachments, setAttachments] = useState([]);
  const [uploadingAttachment, setUploadingAttachment] = useState(false);

  // Approvals state
  const [approvals, setApprovals] = useState([]);
  const [selectedApprover, setSelectedApprover] = useState('');
  const [approvalComment, setApprovalComment] = useState('');

  // Time entries state
  const [timeEntries, setTimeEntries] = useState([]);
  const [logMinutes, setLogMinutes] = useState('');
  const [logDescription, setLogDescription] = useState('');

  // Watcher state
  const [isWatching, setIsWatching] = useState(() => {
    try {
      const watched = JSON.parse(localStorage.getItem(`watched_tasks_${currentUser?.id}`) || '[]');
      return watched.includes(task.id);
    } catch {
      return false;
    }
  });

  // Activities state
  const [activities, setActivities] = useState([]);
  const [loadingActivities, setLoadingActivities] = useState(false);

  // Link state
  const [projectTasks, setProjectTasks] = useState([]);
  const [selectedLinkTarget, setSelectedLinkTarget] = useState('');
  const [selectedLinkType, setSelectedLinkType] = useState('blocks');

  const [projectStatuses, setProjectStatuses] = useState([]);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [commentError, setCommentError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const fetchProjectStatuses = async () => {
    try {
      const data = await api.projects.getStatuses(currentTask.project_id);
      setProjectStatuses(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchTaskDetails = async () => {
    try {
      const taskList = await api.tasks.list(activeOrg.id);
      const latest = (taskList?.tasks || []).find(t => t.id === currentTask.id);
      if (latest) {
        setCurrentTask(latest);
        setTitle(latest.title);
        setDescription(latest.description || '');
        setPriority(latest.priority);
        setDueDate(latest.due_date ? latest.due_date.split('T')[0] : '');
        setStatusVal(latest.status);
      }
    } catch (err) {
      console.error('Failed to reload task:', err);
    }
  };

  const fetchComments = async (cursorVal = null) => {
    setLoadingComments(true);
    try {
      const data = await api.comments.list(currentTask.id, 5, cursorVal);
      if (cursorVal) {
        setComments(prev => [...prev, ...data.comments]);
      } else {
        setComments(data.comments);
      }
      setCommentCursor(data.next_cursor);
      setHasMoreComments(!!data.next_cursor);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingComments(false);
    }
  };

  const fetchMembers = async () => {
    try {
      const data = await api.org.getMembers();
      setOrgMembers(data.members || data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAttachments = async () => {
    try {
      const data = await api.tasks.listAttachments(currentTask.id);
      setAttachments(data);
    } catch (err) {
      console.error('Failed to fetch attachments:', err);
    }
  };

  const fetchApprovals = async () => {
    try {
      const data = await api.tasks.listApprovals(currentTask.id);
      setApprovals(data);
    } catch (err) {
      console.error('Failed to fetch approvals:', err);
    }
  };

  const fetchTimeEntries = async () => {
    try {
      const data = await api.tasks.listTimeEntries(currentTask.id);
      setTimeEntries(data);
    } catch (err) {
      console.error('Failed to fetch time entries:', err);
    }
  };

  const fetchActivities = async () => {
    setLoadingActivities(true);
    try {
      const data = await api.tasks.getActivity(currentTask.id);
      setActivities(data);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
    } finally {
      setLoadingActivities(false);
    }
  };

  const fetchProjectTasks = async () => {
    try {
      const data = await api.tasks.list(activeOrg.id, currentTask.project_id);
      setProjectTasks((data?.tasks || []).filter(t => t.id !== currentTask.id));
    } catch (err) {
      console.error('Failed to fetch project tasks:', err);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, []);

  useEffect(() => {
    fetchTaskDetails();
    fetchProjectStatuses();
  }, [currentTask.id]);

  useEffect(() => {
    if (rightPanelTab === 'comments') {
      fetchComments();
    } else if (rightPanelTab === 'attachments') {
      fetchAttachments();
    } else if (rightPanelTab === 'approvals') {
      fetchApprovals();
    } else if (rightPanelTab === 'time') {
      fetchTimeEntries();
    } else if (rightPanelTab === 'activity') {
      fetchActivities();
    } else if (rightPanelTab === 'links') {
      fetchProjectTasks();
    }
  }, [rightPanelTab, currentTask.id]);

  const handleUpdateTask = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      let currentVersion = currentTask.version;
      if (statusVal !== currentTask.status) {
        const statusUpdatedTask = await api.tasks.updateStatus(currentTask.id, statusVal, currentVersion);
        currentVersion = statusUpdatedTask.version;
      }

      const updated = await api.tasks.update(currentTask.id, {
        title,
        description,
        priority,
        due_date: dueDate || null,
        version: currentVersion
      });

      setCurrentTask(updated);
      setMessage('Task updated successfully!');
      setError('');
    } catch (err) {
      if (err.message && (err.message.includes('version') || err.message.includes('lock') || err.message.includes('conflict') || err.message.includes('mismatch'))) {
        setError('Version mismatch! This task was modified by another request. Please close this modal, refresh, and try again.');
      } else {
        setError(err.message || 'Failed to update task');
      }
    }
  };

  const handleDeleteTask = async () => {
    setError('');
    try {
      await api.tasks.delete(currentTask.id);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to delete task');
    }
  };

  const handleCommentChange = (e) => {
    const val = e.target.value;
    setNewComment(val);

    const cursorPosition = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursorPosition);
    const lastAtIdx = textBeforeCursor.lastIndexOf('@');

    if (lastAtIdx !== -1 && (lastAtIdx === 0 || /\s/.test(textBeforeCursor[lastAtIdx - 1]))) {
      const filterText = textBeforeCursor.slice(lastAtIdx + 1);
      if (filterText.length <= 30 && !/\n/.test(filterText) && (filterText.split(' ').length <= 3)) {
        setShowMentions(true);
        setMentionFilter(filterText.toLowerCase());
        setMentionStartIndex(lastAtIdx);
        return;
      }
    }
    setShowMentions(false);
  };

  const handleSelectMention = (member) => {
    const textBeforeMention = newComment.slice(0, mentionStartIndex);
    const textAfterMention = newComment.slice(commentInputRef.current.selectionStart);
    const mentionTag = `@${member.email}`;
    const updatedText = `${textBeforeMention}${mentionTag} ${textAfterMention}`;
    
    setNewComment(updatedText);
    setShowMentions(false);
    
    setTimeout(() => {
      commentInputRef.current.focus();
      const newCursorPos = textBeforeMention.length + mentionTag.length + 1;
      commentInputRef.current.setSelectionRange(newCursorPos, newCursorPos);
    }, 50);
  };

  const handleApprovalCommentChange = (e) => {
    const val = e.target.value;
    setApprovalComment(val);

    const cursorPosition = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursorPosition);
    const lastAtIdx = textBeforeCursor.lastIndexOf('@');

    if (lastAtIdx !== -1 && (lastAtIdx === 0 || /\s/.test(textBeforeCursor[lastAtIdx - 1]))) {
      const filterText = textBeforeCursor.slice(lastAtIdx + 1);
      if (filterText.length <= 30 && !/\n/.test(filterText) && (filterText.split(' ').length <= 3)) {
        setShowApprovalMentions(true);
        setApprovalMentionFilter(filterText.toLowerCase());
        setApprovalMentionStartIndex(lastAtIdx);
        return;
      }
    }
    setShowApprovalMentions(false);
  };

  const handleSelectApprovalMention = (member) => {
    const textBeforeMention = approvalComment.slice(0, approvalMentionStartIndex);
    const textAfterMention = approvalComment.slice(approvalCommentInputRef.current.selectionStart);
    const mentionTag = `@${member.email}`;
    const updatedText = `${textBeforeMention}${mentionTag} ${textAfterMention}`;
    
    setApprovalComment(updatedText);
    setShowApprovalMentions(false);
    
    setTimeout(() => {
      approvalCommentInputRef.current.focus();
      const newCursorPos = textBeforeMention.length + mentionTag.length + 1;
      approvalCommentInputRef.current.setSelectionRange(newCursorPos, newCursorPos);
    }, 50);
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    setCommentError('');
    if (!newComment.trim()) return;

    try {
      const added = await api.comments.create(currentTask.id, newComment);
      setNewComment('');
      setComments(prev => [added, ...prev]);
    } catch (err) {
      setCommentError(err.message || 'Failed to post comment');
    }
  };

  // Attachments Handlers
  const handleUploadFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingAttachment(true);
    setUploadProgress(0);
    try {
      const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB chunk size
      if (file.size > CHUNK_SIZE) {
        // Initiate multi-part session
        const session = await api.tasks.initiateUpload(currentTask.id, {
          filename: file.name,
          file_size: file.size
        });
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        
        for (let i = 0; i < totalChunks; i++) {
          const start = i * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          const chunk = file.slice(start, end);
          
          // Create file object from blob
          const chunkFile = new File([chunk], file.name, { type: file.type });
          
          // Upload part
          await api.tasks.uploadPart(currentTask.id, session.id, i + 1, chunkFile);
          
          const progressPercent = Math.round(((i + 1) / totalChunks) * 100);
          setUploadProgress(progressPercent);
        }
        
        // Finalize
        await api.tasks.completeUpload(currentTask.id, session.id);
      } else {
        // Single file upload
        await api.tasks.uploadAttachment(currentTask.id, file);
      }
      
      await fetchAttachments();
      fetchTaskDetails();
    } catch (err) {
      alert(err.message || 'Failed to upload attachment');
    } finally {
      setUploadingAttachment(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    try {
      await api.tasks.deleteAttachment(currentTask.id, attachmentId);
      await fetchAttachments();
      fetchTaskDetails();
    } catch (err) {
      alert(err.message || 'Failed to delete attachment');
    }
  };

  // Watcher Handler
  const handleToggleWatch = async () => {
    try {
      if (isWatching) {
        await api.tasks.unwatch(currentTask.id, currentUser.id);
        const watched = JSON.parse(localStorage.getItem(`watched_tasks_${currentUser?.id}`) || '[]');
        const updated = watched.filter(id => id !== currentTask.id);
        localStorage.setItem(`watched_tasks_${currentUser?.id}`, JSON.stringify(updated));
        setIsWatching(false);
      } else {
        await api.tasks.watch(currentTask.id);
        const watched = JSON.parse(localStorage.getItem(`watched_tasks_${currentUser?.id}`) || '[]');
        if (!watched.includes(currentTask.id)) {
          watched.push(currentTask.id);
        }
        localStorage.setItem(`watched_tasks_${currentUser?.id}`, JSON.stringify(watched));
        setIsWatching(true);
      }
    } catch (err) {
      alert(err.message || 'Failed to toggle watch state');
    }
  };

  // Link Handlers
  const handleCreateLink = async (e) => {
    e.preventDefault();
    if (!selectedLinkTarget) return;
    try {
      await api.tasks.createLink(currentTask.id, {
        target_task_id: selectedLinkTarget,
        link_type: selectedLinkType
      });
      setSelectedLinkTarget('');
      await fetchTaskDetails();
    } catch (err) {
      alert(err.message || 'Failed to create link');
    }
  };

  const handleDeleteLink = async (linkId) => {
    if (!confirm('Are you sure you want to delete this link?')) return;
    try {
      await api.tasks.deleteLink(currentTask.id, linkId);
      await fetchTaskDetails();
    } catch (err) {
      alert(err.message || 'Failed to delete link');
    }
  };

  // Approvals Handlers
  const handleCreateApproval = async (e) => {
    e.preventDefault();
    if (!selectedApprover) return;
    try {
      await api.tasks.createApproval(currentTask.id, selectedApprover);
      setSelectedApprover('');
      await fetchApprovals();
    } catch (err) {
      alert(err.message || 'Failed to send approval request');
    }
  };

  const handleDecideApproval = async (approvalId, statusChoice) => {
    try {
      await api.tasks.updateApproval(currentTask.id, approvalId, statusChoice, approvalComment || null);
      setApprovalComment('');
      await fetchApprovals();
    } catch (err) {
      alert(err.message || 'Failed to submit approval decision');
    }
  };

  // Time Entries Handlers
  const handleLogTime = async (e) => {
    e.preventDefault();
    const minutes = parseInt(logMinutes);
    if (!minutes || minutes <= 0) return;
    try {
      await api.tasks.createTimeEntry(currentTask.id, minutes, logDescription || null);
      setLogMinutes('');
      setLogDescription('');
      await fetchTimeEntries();
      fetchTaskDetails();
    } catch (err) {
      alert(err.message || 'Failed to log time');
    }
  };

  const filteredMembers = orgMembers.filter(m => 
    (m.full_name || '').toLowerCase().includes(mentionFilter) || 
    (m.email || '').toLowerCase().includes(mentionFilter)
  );

  const filteredApprovalMembers = orgMembers.filter(m => 
    (m.full_name || '').toLowerCase().includes(approvalMentionFilter) || 
    (m.email || '').toLowerCase().includes(approvalMentionFilter)
  );

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)' }}>
      <div className="glass-panel" style={{ width: '920px', height: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', flexShrink: 0 }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Task Details</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ID: {currentTask.id}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button 
              type="button" 
              onClick={handleToggleWatch} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                background: isWatching ? 'rgba(99, 102, 241, 0.15)' : 'transparent', 
                border: '1px solid rgba(255, 255, 255, 0.1)', 
                borderRadius: '6px', 
                padding: '6px 12px', 
                color: isWatching ? 'var(--primary)' : 'var(--text-secondary)', 
                cursor: 'pointer', 
                fontSize: '12px', 
                fontWeight: '600',
                transition: 'all 0.2s' 
              }}
            >
              {isWatching ? <EyeOff size={14} /> : <Eye size={14} />}
              {isWatching ? 'Stop Watching' : 'Watch Task'}
            </button>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '4px' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          
          {/* Left panel - Edit form */}
          <form onSubmit={handleUpdateTask} style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', borderRight: '1px solid var(--border-glass)' }}>
            {message && <div style={{ color: 'var(--success)', fontSize: '13px' }}>{message}</div>}
            {error && <div style={{ color: 'var(--danger)', fontSize: '13px', lineHeight: '1.4' }}>{error}</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Title</label>
              <input
                type="text"
                required
                className="input-field"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Description</label>
              <textarea
                className="input-field"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Status</label>
                <select
                  className="input-field"
                  value={statusVal}
                  onChange={(e) => setStatusVal(e.target.value)}
                >
                  {projectStatuses && projectStatuses.length > 0 ? (
                    [...projectStatuses].sort((a, b) => a.position - b.position).map(st => (
                      <option key={st.id} value={st.name}>{st.name}</option>
                    ))
                  ) : (
                    <>
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="review">Review</option>
                      <option value="done">Done</option>
                    </>
                  )}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Priority</label>
                <select
                  className="input-field"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Due Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Task Version</label>
                <input
                  type="text"
                  disabled
                  className="input-field"
                  value={`v${currentTask.version}`}
                  style={{ opacity: 0.7 }}
                />
              </div>
            </div>

            {/* SLA Status Widget */}
            {currentTask.sla_status && (
              <div 
                className="glass-card" 
                style={{ 
                  padding: '12px', 
                  background: currentTask.sla_status === 'breached' ? 'rgba(239, 68, 68, 0.05)' : 'rgba(16, 185, 129, 0.05)',
                  border: currentTask.sla_status === 'breached' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                {currentTask.sla_status === 'breached' ? <AlertCircle size={18} color="#f87171" /> : <Clock size={18} color="#34d399" />}
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: currentTask.sla_status === 'breached' ? '#f87171' : '#34d399' }}>
                    SLA Status: {currentTask.sla_status}
                  </div>
                  {currentTask.sla_deadline && (
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      Deadline: {new Date(currentTask.sla_deadline).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Time Tracker Total Display */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="glass-card" style={{ padding: '12px', background: 'rgba(255,255,255,0.02)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Time Logged</div>
                <div style={{ fontSize: '18px', fontWeight: '800', color: 'var(--primary)', marginTop: '4px' }}>
                  {currentTask.total_minutes_logged || 0} mins
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '20px' }}>
              <button type="button" className="btn-danger" onClick={handleDeleteTask}>
                <Trash2 size={16} /> Delete Task
              </button>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" className="btn-secondary" onClick={fetchTaskDetails}>Reload</button>
                <button type="submit" className="btn-primary">Save Changes</button>
              </div>
            </div>
          </form>

          {/* Right panel - Tabs (Comments, Attachments, Approvals, Time Tracking) */}
          <div style={{ width: '420px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            
            {/* Tabs Row */}
            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-glass)', flexShrink: 0, overflowX: 'auto', scrollbarWidth: 'none' }} className="hide-scrollbar">
              <button 
                type="button" 
                onClick={() => setRightPanelTab('comments')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'comments' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'comments' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'comments' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <MessageSquare size={14} /> Comments
              </button>
              
              <button 
                type="button" 
                onClick={() => setRightPanelTab('attachments')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'attachments' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'attachments' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'attachments' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <Paperclip size={14} /> Files
              </button>

              <button 
                type="button" 
                onClick={() => setRightPanelTab('approvals')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'approvals' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'approvals' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'approvals' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <CheckCircle size={14} /> Approvals
              </button>

              <button 
                type="button" 
                onClick={() => setRightPanelTab('time')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'time' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'time' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'time' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <Clock size={14} /> Time Logs
              </button>

              <button 
                type="button" 
                onClick={() => setRightPanelTab('links')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'links' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'links' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'links' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <Link size={14} /> Links
              </button>

              <button 
                type="button" 
                onClick={() => setRightPanelTab('activity')} 
                style={{ flex: '1 0 auto', padding: '12px 16px', background: rightPanelTab === 'activity' ? 'rgba(255,255,255,0.05)' : 'transparent', border: 'none', borderBottom: rightPanelTab === 'activity' ? '2px solid var(--primary)' : 'none', color: rightPanelTab === 'activity' ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12.5px' }}
              >
                <History size={14} /> Activity
              </button>
            </div>

            {/* Tab Body */}
            <div style={{ flexGrow: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
              
              {/* COMMENTS TAB */}
              {rightPanelTab === 'comments' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <form onSubmit={handleAddComment} style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative', flexShrink: 0 }}>
                    {commentError && <div style={{ color: 'var(--danger)', fontSize: '11px' }}>{commentError}</div>}
                    <div style={{ position: 'relative' }}>
                      <textarea
                        ref={commentInputRef}
                        className="input-field"
                        rows={2}
                        style={{ resize: 'none', paddingRight: '40px' }}
                        placeholder="Type a comment... use @ to mention"
                        value={newComment}
                        onChange={handleCommentChange}
                      />
                      {showMentions && filteredMembers.length > 0 && (
                        <div className="glass-panel" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100, maxHeight: '150px', overflowY: 'auto', padding: '6px', marginTop: '4px', background: '#0e0e1a', border: '1px solid rgba(255, 255, 255, 0.15)' }}>
                          {filteredMembers.map(member => (
                            <button
                              key={member.user_id || member.id}
                              type="button"
                              onClick={() => handleSelectMention(member)}
                              style={{ width: '100%', padding: '8px', background: 'transparent', border: 'none', color: 'var(--text-primary)', textAlign: 'left', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', display: 'block' }}
                              onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                              onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                            >
                              <div style={{ fontWeight: '600' }}>{member.full_name || member.email}</div>
                              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{member.email}</div>
                            </button>
                          ))}
                        </div>
                      )}
                      <button 
                        type="submit" 
                        style={{ position: 'absolute', right: '10px', bottom: '12px', background: 'transparent', border: 'none', color: 'var(--primary)', cursor: 'pointer' }}
                      >
                        <Send size={18} />
                      </button>
                    </div>
                  </form>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1, overflowY: 'auto' }}>
                    {comments.map(c => {
                      const authorObj = orgMembers.find(m => (m.user_id || m.id) === c.author_id);
                      const authorName = authorObj ? (authorObj.full_name || authorObj.email) : 'System/Unknown';
                      return (
                        <div key={c.id} className="glass-card" style={{ padding: '12px', background: 'rgba(255,255,255,0.015)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <span style={{ fontSize: '12px', fontWeight: '600' }}>{authorName}</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{formatTime(c.created_at)}</span>
                          </div>
                          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4', wordBreak: 'break-word' }}>{c.content}</p>
                        </div>
                      );
                    })}
                    {hasMoreComments && (
                      <button 
                        onClick={() => fetchComments(commentCursor)}
                        className="btn-secondary" 
                        style={{ width: '100%', fontSize: '12px', padding: '6px' }}
                        disabled={loadingComments}
                      >
                        {loadingComments ? 'Loading...' : 'Load Older Comments'}
                      </button>
                    )}
                    {!loadingComments && comments.length === 0 && (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>
                        No comments posted yet.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ATTACHMENTS TAB */}
              {rightPanelTab === 'attachments' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <div style={{ border: '2px dashed var(--border-glass)', padding: '16px', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', position: 'relative' }}>
                    <input 
                      type="file" 
                      onChange={handleUploadFile} 
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }} 
                      disabled={uploadingAttachment}
                    />
                    <Paperclip size={24} style={{ margin: '0 auto 8px', color: 'var(--text-secondary)' }} />
                    <div style={{ fontSize: '13px', fontWeight: '600' }}>
                      {uploadingAttachment ? (
                        <div>
                          Uploading file... {uploadProgress > 0 ? `${uploadProgress}%` : ''}
                          {uploadProgress > 0 && (
                            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginTop: '8px', overflow: 'hidden' }}>
                              <div style={{ width: `${uploadProgress}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.2s' }} />
                            </div>
                          )}
                        </div>
                      ) : 'Click or Drag file to upload'}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1, overflowY: 'auto' }}>
                    {attachments.map(att => (
                      <div key={att.id} className="glass-card" style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.01)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                          <FileText size={16} color="var(--primary)" />
                          <div style={{ overflow: 'hidden' }}>
                            <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{att.filename}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{(att.size / 1024).toFixed(1)} KB</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <a 
                            href={api.tasks.getDownloadUrl(currentTask.id, att.id)} 
                            target="_blank" 
                            rel="noreferrer"
                            className="btn-secondary" 
                            style={{ padding: '6px', display: 'flex', alignItems: 'center', justifyItems: 'center' }}
                            title="Download"
                          >
                            <Download size={14} />
                          </a>
                          <button 
                            type="button"
                            onClick={() => handleDeleteAttachment(att.id)}
                            style={{ background: 'transparent', border: '1px solid rgba(239,68,68,0.2)', padding: '6px', color: '#f87171', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                    {attachments.length === 0 && (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>
                        No attachments uploaded yet.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* APPROVALS TAB */}
              {rightPanelTab === 'approvals' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <form onSubmit={handleCreateApproval} style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                    <select
                      value={selectedApprover}
                      onChange={e => setSelectedApprover(e.target.value)}
                      className="input-field"
                      style={{ background: 'var(--bg-dark)', flexGrow: 1 }}
                    >
                      <option value="">Select Approver...</option>
                      {orgMembers.map(m => (
                        <option key={m.user_id || m.id} value={m.user_id || m.id}>
                          {m.full_name || m.email} ({m.role})
                        </option>
                      ))}
                    </select>
                    <button type="submit" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '4px' }} disabled={!selectedApprover}>
                      <UserCheck size={14} /> Request
                    </button>
                  </form>

                  {/* Comment box for decider */}
                  {approvals.some(app => app.approver_id === currentUser.id && app.status === 'pending') && (
                    <div className="glass-panel" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative' }}>
                      <div style={{ fontSize: '12px', fontWeight: '700' }}>Approval Decision Comment:</div>
                      <div style={{ position: 'relative' }}>
                        <input 
                          ref={approvalCommentInputRef}
                          type="text" 
                          className="input-field" 
                          value={approvalComment} 
                          onChange={handleApprovalCommentChange} 
                          placeholder="Optional comment e.g. Looks good! Use @ to mention"
                        />
                        {showApprovalMentions && filteredApprovalMembers.length > 0 && (
                          <div className="glass-panel" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100, maxHeight: '150px', overflowY: 'auto', padding: '6px', marginTop: '4px', background: '#0e0e1a', border: '1px solid rgba(255, 255, 255, 0.15)' }}>
                            {filteredApprovalMembers.map(member => (
                              <button
                                key={member.user_id || member.id}
                                type="button"
                                onClick={() => handleSelectApprovalMention(member)}
                                style={{ width: '100%', padding: '8px', background: 'transparent', border: 'none', color: 'var(--text-primary)', textAlign: 'left', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', display: 'block' }}
                                onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                                onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                              >
                                <div style={{ fontWeight: '600' }}>{member.full_name || member.email}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{member.email}</div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flexGrow: 1, overflowY: 'auto' }}>
                    {approvals.map(app => {
                      const approverObj = orgMembers.find(m => (m.user_id || m.id) === app.approver_id);
                      const requestorObj = orgMembers.find(m => (m.user_id || m.id) === app.requestor_id);
                      return (
                        <div key={app.id} className="glass-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <div style={{ fontSize: '12.5px', fontWeight: '600' }}>
                                Approver: {approverObj?.full_name || approverObj?.email || 'Unknown'}
                              </div>
                              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                Requested by: {requestorObj?.full_name || requestorObj?.email || 'Unknown'}
                              </div>
                            </div>
                            <span style={{ 
                              padding: '3px 8px', 
                              borderRadius: '4px', 
                              fontSize: '10px', 
                              fontWeight: '750', 
                              textTransform: 'uppercase',
                              background: app.status === 'approved' ? 'rgba(16, 185, 129, 0.15)' : app.status === 'rejected' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                              color: app.status === 'approved' ? '#34d399' : app.status === 'rejected' ? '#f87171' : '#fbbf24'
                            }}>
                              {app.status}
                            </span>
                          </div>

                          {app.comment && (
                            <div style={{ fontSize: '12px', fontStyle: 'italic', background: 'rgba(255,255,255,0.02)', padding: '6px', borderRadius: '4px', borderLeft: '2px solid var(--border-glass)' }}>
                              "{app.comment}"
                            </div>
                          )}

                          {app.status === 'pending' && app.approver_id === currentUser.id && (
                            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                              <button 
                                onClick={() => handleDecideApproval(app.id, 'approved')} 
                                className="btn-primary" 
                                style={{ flex: 1, padding: '6px', fontSize: '11.5px', background: 'var(--success)' }}
                              >
                                Approve
                              </button>
                              <button 
                                onClick={() => handleDecideApproval(app.id, 'rejected')} 
                                className="btn-danger" 
                                style={{ flex: 1, padding: '6px', fontSize: '11.5px' }}
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {approvals.length === 0 && (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>
                        No approval requests sent yet.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TIME LOGS TAB */}
              {rightPanelTab === 'time' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <form onSubmit={handleLogTime} style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexShrink: 0 }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input 
                        type="number" 
                        required 
                        min="1" 
                        className="input-field" 
                        placeholder="Minutes spent" 
                        value={logMinutes} 
                        onChange={e => setLogMinutes(e.target.value)}
                        style={{ width: '130px' }}
                      />
                      <input 
                        type="text" 
                        className="input-field" 
                        placeholder="What did you do?" 
                        value={logDescription} 
                        onChange={e => setLogDescription(e.target.value)}
                        style={{ flexGrow: 1 }}
                      />
                    </div>
                    <button type="submit" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyItems: 'center', alignSelf: 'flex-start' }} disabled={!logMinutes}>
                      <Clock size={14} /> Log Work
                    </button>
                  </form>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1, overflowY: 'auto' }}>
                    {timeEntries.map(entry => {
                      const userObj = orgMembers.find(m => (m.user_id || m.id) === entry.user_id);
                      return (
                        <div key={entry.id} className="glass-card" style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.01)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--primary)' }}>{entry.minutes} mins</span>
                            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                              {new Date(entry.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {entry.description && (
                            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>{entry.description}</p>
                          )}
                          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'right' }}>
                            by {userObj?.full_name || userObj?.email || 'Unknown'}
                          </div>
                        </div>
                      );
                    })}
                    {timeEntries.length === 0 && (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>
                        No time entries logged yet.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* LINKS TAB */}
              {rightPanelTab === 'links' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <form onSubmit={handleCreateLink} style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexShrink: 0 }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select
                        className="input-field"
                        value={selectedLinkTarget}
                        onChange={e => setSelectedLinkTarget(e.target.value)}
                        style={{ flexGrow: 1 }}
                      >
                        <option value="">Select Task to Link...</option>
                        {projectTasks.map(t => (
                          <option key={t.id} value={t.id}>{t.title}</option>
                        ))}
                      </select>
                      <select
                        className="input-field"
                        value={selectedLinkType}
                        onChange={e => setSelectedLinkType(e.target.value)}
                        style={{ width: '130px' }}
                      >
                        <option value="blocks">Blocks</option>
                        <option value="blocked_by">Blocked By</option>
                        <option value="relates_to">Relates To</option>
                      </select>
                    </div>
                    <button type="submit" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyItems: 'center', alignSelf: 'flex-start' }} disabled={!selectedLinkTarget}>
                      <Plus size={14} /> Link Task
                    </button>
                  </form>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1, overflowY: 'auto' }}>
                    {(currentTask.links || []).map(link => {
                      const otherTaskId = link.source_task_id === currentTask.id ? link.target_task_id : link.source_task_id;
                      const otherTask = projectTasks.find(t => t.id === otherTaskId) || { title: otherTaskId };
                      return (
                        <div key={link.id} className="glass-card" style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.01)' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '10px', textTransform: 'uppercase', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)', padding: '2px 6px', borderRadius: '4px', fontWeight: '700' }}>
                                {link.link_type.replace('_', ' ')}
                              </span>
                            </div>
                            <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {otherTask.title}
                            </div>
                          </div>
                          <button 
                            type="button"
                            onClick={() => handleDeleteLink(link.id)}
                            style={{ background: 'transparent', border: '1px solid rgba(239,68,68,0.2)', padding: '6px', color: '#f87171', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                            title="Remove Link"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      );
                    })}
                    {(!currentTask.links || currentTask.links.length === 0) && (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>
                        No linked tasks.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ACTIVITY TAB */}
              {rightPanelTab === 'activity' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1, overflowY: 'auto' }}>
                    {loadingActivities ? (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>Loading activities...</div>
                    ) : activities.length === 0 ? (
                      <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)', padding: '20px' }}>No activities logged.</div>
                    ) : (
                      activities.map(act => {
                        const actorObj = orgMembers.find(m => (m.user_id || m.id) === act.actor_id);
                        const actorName = actorObj ? (actorObj.full_name || actorObj.email) : 'System/Automation';
                        return (
                          <div key={act.id} className="glass-card" style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.01)', borderLeft: '3px solid var(--primary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span style={{ fontSize: '12px', fontWeight: '600' }}>{actorName}</span>
                              <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                                {new Date(act.created_at).toLocaleString()}
                              </span>
                            </div>
                            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                              <strong style={{ color: 'var(--text-primary)' }}>{act.action.replace('_', ' ').toUpperCase()}</strong>
                            </div>
                            {act.metadata && Object.keys(act.metadata).length > 0 && (
                              <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '4px', background: 'rgba(0,0,0,0.1)', padding: '6px', borderRadius: '4px' }}>
                                {Object.entries(act.metadata).map(([key, val]) => (
                                  <div key={key}>
                                    <strong>{key}:</strong> {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}

            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
