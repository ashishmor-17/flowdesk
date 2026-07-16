import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { getPriorityColor, formatDate } from '../../utils/format';
import { 
  Plus, 
  Calendar, 
  ChevronRight, 
  AlertCircle,
  Clock,
  Filter,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import TaskDetailModal from './TaskDetailModal';

export default function TaskBoard({ initialOpenTaskId, onClearInitialOpenTaskId }) {
  const { activeOrg } = useAuth();
  const [projects, setProjects] = useState([]);
  const [selectedProjId, setSelectedProjId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [addTaskColumn, setAddTaskColumn] = useState('todo');
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskDueDate, setTaskDueDate] = useState('');

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const defaultColumns = [
    { id: 'todo', title: 'To Do', color: '#3b82f6' },
    { id: 'in_progress', title: 'In Progress', color: '#f59e0b' },
    { id: 'review', title: 'Review', color: '#a855f7' },
    { id: 'done', title: 'Done', color: '#10b981' }
  ];

  const [boardColumns, setBoardColumns] = useState(defaultColumns);
  const [orgMembers, setOrgMembers] = useState([]);

  const fetchProjects = async () => {
    try {
      const projs = await api.projects.list();
      const list = projs?.projects || [];
      setProjects(list);
      if (list.length > 0) {
        setSelectedProjId(list[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMembers = async () => {
    try {
      const data = await api.org.getMembers();
      setOrgMembers(data.members || data || []);
    } catch (err) {
      console.error('Failed to fetch org members:', err);
    }
  };

  const getAssigneeNames = (task) => {
    if (!task.assignees || task.assignees.length === 0) return 'Unassigned';
    return task.assignees.map(a => {
      const member = orgMembers.find(m => (m.user_id || m.id) === a.user_id);
      return member ? (member.full_name || member.email) : 'Unknown User';
    }).join(', ');
  };

  const getReporterName = (task) => {
    const member = orgMembers.find(m => (m.user_id || m.id) === task.created_by);
    return member ? (member.full_name || member.email) : 'Unknown User';
  };

  const fetchProjectStatuses = async () => {
    if (!selectedProjId) return;
    try {
      const data = await api.projects.getStatuses(selectedProjId);
      if (data && data.length > 0) {
        const sorted = [...data].sort((a, b) => a.position - b.position);
        setBoardColumns(sorted.map(st => ({
          id: st.name,
          title: st.name,
          color: st.color || '#6366f1'
        })));
      } else {
        setBoardColumns(defaultColumns);
      }
    } catch (err) {
      console.error(err);
      setBoardColumns(defaultColumns);
    }
  };

  const fetchTasks = async () => {
    if (!selectedProjId) return;
    setLoading(true);
    try {
      const taskList = await api.tasks.list(activeOrg.id, selectedProjId);
      setTasks(taskList?.tasks || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    fetchMembers();
  }, [activeOrg]);

  useEffect(() => {
    if (selectedProjId) {
      fetchTasks();
      fetchProjectStatuses();
    }
  }, [selectedProjId]);

  useEffect(() => {
    if (initialOpenTaskId) {
      const existingTask = tasks.find(t => t.id === initialOpenTaskId);
      if (existingTask) {
        setSelectedTask(existingTask);
        if (onClearInitialOpenTaskId) onClearInitialOpenTaskId();
      } else {
        api.tasks.get(initialOpenTaskId).then(t => {
          if (t) {
            // Check if project needs to be set
            if (t.project_id && t.project_id !== selectedProjId) {
              setSelectedProjId(t.project_id);
            }
            setSelectedTask(t);
          }
          if (onClearInitialOpenTaskId) onClearInitialOpenTaskId();
        }).catch(err => {
          console.error("Failed to fetch initialOpenTaskId:", err);
          if (onClearInitialOpenTaskId) onClearInitialOpenTaskId();
        });
      }
    }
  }, [initialOpenTaskId, tasks, selectedProjId]);

  const handleCreateTask = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.tasks.create(selectedProjId, taskTitle, taskDesc, taskPriority, taskDueDate || null);
      setShowAddTaskModal(false);
      setTaskTitle('');
      setTaskDesc('');
      setTaskPriority('medium');
      setTaskDueDate('');
      fetchTasks();
      setMessage('Task created successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to create task');
    }
  };

  const handleQuickStatusChange = async (taskId, newStatus) => {
    const taskObj = tasks.find(t => t.id === taskId);
    if (!taskObj) return;
    try {
      await api.tasks.updateStatus(taskId, newStatus, taskObj.version);
      fetchTasks();
      setMessage('Status updated!');
      setTimeout(() => setMessage(''), 2000);
    } catch (err) {
      setError(err.message || 'Failed to update status');
      setTimeout(() => setError(''), 3000);
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100vh', width: '100%', overflow: 'hidden' }} className="animate-fade-in">
      {/* Top bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '800' }}>Task Board</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="var(--text-secondary)" />
            <select
              className="input-field"
              style={{ width: '200px', padding: '6px 12px' }}
              value={selectedProjId}
              onChange={(e) => setSelectedProjId(e.target.value)}
            >
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {selectedProjId && (
          <button className="btn-primary" onClick={() => { setAddTaskColumn('todo'); setShowAddTaskModal(true); }}>
            <Plus size={16} /> Add Task
          </button>
        )}
      </div>

      {message && (
        <div className="glass-panel" style={{ padding: '10px 20px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <CheckCircle size={16} /> {message}
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: '10px 20px', background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Columns */}
      {!selectedProjId ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)', flexGrow: 1 }}>
          Create a project first in the Dashboard to begin mapping tasks!
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '40px', flexGrow: 1 }}>Loading task board...</div>
      ) : (
        <div className="glass-panel" style={{ overflow: 'hidden', flexGrow: 1, display: 'flex', flexDirection: 'column', padding: 0 }}>
          <div style={{ overflowY: 'auto', flexGrow: 1 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.02)' }}>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Task</th>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Priority</th>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Due Date</th>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Assignees</th>
                  <th style={{ padding: '16px', fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Reporter</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(task => {
                  const statusStr = task.status ? task.status.toUpperCase().replace('_', ' ') : 'TODO';
                  const priorityColor = getPriorityColor(task.priority);
                  return (
                    <tr 
                      key={task.id} 
                      className="task-row-hover"
                      style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.03)', 
                        cursor: 'pointer', 
                        transition: 'background 0.2s' 
                      }}
                      onClick={() => setSelectedTask(task)}
                    >
                      <td style={{ padding: '16px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>{task.title}</span>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Version {task.version}</span>
                        </div>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ 
                          fontSize: '11px', 
                          fontWeight: '700', 
                          background: 'rgba(99, 102, 241, 0.1)', 
                          color: '#818cf8', 
                          padding: '4px 10px', 
                          borderRadius: '12px',
                          border: '1px solid rgba(99, 102, 241, 0.2)',
                          letterSpacing: '0.03em'
                        }}>
                          {statusStr}
                        </span>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ 
                          fontSize: '11px', 
                          fontWeight: '700', 
                          color: priorityColor, 
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em'
                        }}>
                          {task.priority}
                        </span>
                      </td>
                      <td style={{ padding: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {task.due_date ? formatDate(task.due_date) : '-'}
                      </td>
                      <td style={{ padding: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {getAssigneeNames(task)}
                      </td>
                      <td style={{ padding: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {getReporterName(task)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {tasks.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                No tasks created in this project yet. Click "+ Add Task" to get started!
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Task Modal */}
      {showAddTaskModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
          <form onSubmit={handleCreateTask} className="glass-panel" style={{ padding: '28px', width: '450px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>Create New Task</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Task Title</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. Implement Oauth flow"
                value={taskTitle}
                onChange={(e) => setTaskTitle(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Description</label>
              <textarea
                className="input-field"
                rows={3}
                placeholder="Task description and requirements..."
                value={taskDesc}
                onChange={(e) => setTaskDesc(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Priority</label>
                <select
                  className="input-field"
                  value={taskPriority}
                  onChange={(e) => setTaskPriority(e.target.value)}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Due Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button type="button" className="btn-secondary" onClick={() => setShowAddTaskModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Create Task</button>
            </div>
          </form>
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <TaskDetailModal 
          task={selectedTask} 
          onClose={() => { setSelectedTask(null); fetchTasks(); }} 
        />
      )}
    </div>
  );
}
