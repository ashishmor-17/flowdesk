import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
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

export default function KanbanBoard() {
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

  const columns = [
    { id: 'backlog', title: 'Backlog', color: '#6b7280' },
    { id: 'todo', title: 'To Do', color: '#3b82f6' },
    { id: 'in_progress', title: 'In Progress', color: '#f59e0b' },
    { id: 'review', title: 'Review', color: '#a855f7' },
    { id: 'done', title: 'Done', color: '#10b981' }
  ];

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
  }, [activeOrg]);

  useEffect(() => {
    fetchTasks();
  }, [selectedProjId]);

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

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return 'var(--text-secondary)';
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
        <div className="kanban-container" style={{ display: 'flex', gap: '16px', overflowX: 'auto', flexGrow: 1 }}>
          {columns.map(col => {
            const colTasks = tasks.filter(t => t.status === col.id);
            return (
              <div key={col.id} className="kanban-column" style={{ flex: '1 0 280px', display: 'flex', flexDirection: 'column', background: 'rgba(255,255,255,0.015)', border: '1px solid var(--border-glass)', borderRadius: '12px', padding: '16px', maxHeight: '100%', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexShrink: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: col.color }} />
                    <h3 style={{ fontSize: '15px', fontWeight: '700' }}>{col.title}</h3>
                  </div>
                  <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', padding: '2px 8px', borderRadius: '12px' }}>
                    {colTasks.length}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', flexGrow: 1, paddingRight: '4px' }}>
                  {colTasks.map(task => (
                    <div 
                      key={task.id} 
                      className="glass-card" 
                      style={{ padding: '14px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px' }}
                      onClick={() => setSelectedTask(task)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontSize: '10px', textTransform: 'uppercase', color: getPriorityColor(task.priority), fontWeight: '700', letterSpacing: '0.05em' }}>
                          {task.priority}
                        </span>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                          v{task.version}
                        </span>
                      </div>

                      <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', lineHeight: '1.4' }}>{task.title}</h4>
                      
                      {task.due_date && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                          <Clock size={12} />
                          <span>{new Date(task.due_date).toLocaleDateString()}</span>
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '8px', gap: '4px' }} onClick={e => e.stopPropagation()}>
                        <select
                          className="input-field"
                          style={{ width: '100%', fontSize: '11px', padding: '4px 8px', background: 'rgba(255,255,255,0.02)' }}
                          value={task.status}
                          onChange={(e) => handleQuickStatusChange(task.id, e.target.value)}
                        >
                          {columns.map(c => (
                            <option key={c.id} value={c.id}>{c.title}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
                  
                  {col.id === 'todo' && (
                    <button 
                      onClick={() => { setAddTaskColumn('todo'); setShowAddTaskModal(true); }}
                      style={{ background: 'transparent', border: '1px dashed var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', width: '100%', transition: 'all 0.2s' }}
                      onMouseOver={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'}
                      onMouseOut={e => e.currentTarget.style.borderColor = 'var(--border-glass)'}
                    >
                      <Plus size={14} /> Add Task
                    </button>
                  )}
                </div>
              </div>
            );
          })}
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
