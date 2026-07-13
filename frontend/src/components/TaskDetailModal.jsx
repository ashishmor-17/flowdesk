import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  User, 
  Calendar, 
  MessageSquare, 
  ChevronDown, 
  Send,
  Plus,
  Trash2,
  AlertTriangle
} from 'lucide-react';

export default function TaskDetailModal({ task, onClose }) {
  const { activeOrg } = useAuth();
  const [currentTask, setCurrentTask] = useState(task);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [priority, setPriority] = useState(task.priority);
  const [dueDate, setDueDate] = useState(task.due_date ? task.due_date.split('T')[0] : '');
  const [statusVal, setStatusVal] = useState(task.status);
  
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [commentCursor, setCommentCursor] = useState(null);
  const [hasMoreComments, setHasMoreComments] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  const [orgMembers, setOrgMembers] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [mentionStartIndex, setMentionStartIndex] = useState(-1);
  const commentInputRef = useRef(null);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [commentError, setCommentError] = useState('');

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
      setOrgMembers(data.members);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchComments();
    fetchMembers();
  }, [currentTask.id]);

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
      if (!/\s/.test(filterText)) {
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

  const handleAddComment = async (e) => {
    e.preventDefault();
    setCommentError('');
    if (!newComment.trim()) return;

    try {
      await api.comments.create(currentTask.id, newComment);
      setNewComment('');
      fetchComments();
    } catch (err) {
      setCommentError(err.message || 'Failed to post comment');
    }
  };

  const filteredMembers = orgMembers.filter(m => 
    m.full_name.toLowerCase().includes(mentionFilter) || 
    m.email.toLowerCase().includes(mentionFilter)
  );

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)' }}>
      <div className="glass-panel" style={{ width: '850px', height: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', flexShrink: 0 }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Task Details</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ID: {currentTask.id}</span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <X size={20} />
          </button>
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
                  <option value="backlog">Backlog</option>
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="review">Review</option>
                  <option value="done">Done</option>
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

          {/* Right panel - Comments */}
          <div style={{ width: '380px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
            <h4 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={16} /> Comments
            </h4>
            
            <form onSubmit={handleAddComment} style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative' }}>
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
                  <div className="glass-panel" style={{ position: 'absolute', bottom: '100%', left: 0, right: 0, zIndex: 100, maxHeight: '150px', overflowY: 'auto', padding: '6px', marginBottom: '4px', background: 'rgba(10, 11, 16, 0.95)' }}>
                    {filteredMembers.map(member => (
                      <button
                        key={member.user_id}
                        type="button"
                        onClick={() => handleSelectMention(member)}
                        style={{ width: '100%', padding: '8px', background: 'transparent', border: 'none', color: 'var(--text-primary)', textAlign: 'left', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', display: 'block' }}
                        onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                        onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <div style={{ fontWeight: '600' }}>{member.full_name}</div>
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

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1, overflowY: 'auto', marginTop: '8px' }}>
              {comments.map(c => (
                <div key={c.id} className="glass-card" style={{ padding: '12px', background: 'rgba(255,255,255,0.015)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', fontWeight: '600' }}>{c.author ? `${c.author.first_name} ${c.author.last_name || ''}` : 'System'}</span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4', wordBreak: 'break-word' }}>{c.content}</p>
                </div>
              ))}

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

        </div>

      </div>
    </div>
  );
}
