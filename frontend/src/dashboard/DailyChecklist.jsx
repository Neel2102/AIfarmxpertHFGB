import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Clock, AlertCircle, Droplets, Bug, Sprout, Hammer, Check } from 'lucide-react';
import apiService from '../services/api';
import '../styles/Dashboard/DailyChecklist.css';

const DailyChecklist = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/api/tasks/today');
      setTasks(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
      setTasks([]);
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleGenerateTasks = async () => {
    try {
      setGenerating(true);
      const response = await apiService.post('/api/tasks/generate');
      setTasks(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to generate tasks:', err);
      setError('Could not generate new tasks. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const toggleTask = async (taskId, currentStatus) => {
    // Optimistic update
    setTasks(tasks.map(task => 
      task.id === taskId ? { ...task, is_completed: !currentStatus } : task
    ));

    try {
      await apiService.patch(`/api/tasks/${taskId}/complete`, {
        is_completed: !currentStatus
      });
    } catch (err) {
      // Revert on error
      console.error('Failed to update task:', err);
      setTasks(tasks.map(task => 
        task.id === taskId ? { ...task, is_completed: currentStatus } : task
      ));
    }
  };

  const getCategoryIcon = (category) => {
    switch (category?.toLowerCase()) {
      case 'irrigation': return <Droplets size={16} />;
      case 'pest': return <Bug size={16} />;
      case 'fertilizer': return <Sprout size={16} />;
      case 'maintenance': return <Hammer size={16} />;
      default: return <Clock size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="daily-checklist skeleton">
        <div className="skeleton-header"></div>
        <div className="skeleton-item"></div>
        <div className="skeleton-item"></div>
        <div className="skeleton-item"></div>
      </div>
    );
  }

  return (
    <div className="daily-checklist">
      <div className="checklist-header">
        <div>
          <h3>Daily Checklist</h3>
          <p className="subtitle">AI-recommended tasks based on your farm data</p>
        </div>
        
        {tasks.length > 0 && (
          <div className="progress-indicator">
            {tasks.filter(t => t.is_completed).length} / {tasks.length} Completed
          </div>
        )}
      </div>

      {error && (
        <div className="checklist-error">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon-wrap">
            <Check size={32} />
          </div>
          <h4>You're all caught up!</h4>
          <p>Generate today's personalized tasks based on your crop stage and weather.</p>
          <button 
            className="generate-btn" 
            onClick={handleGenerateTasks}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate Today\'s Tasks'}
          </button>
        </div>
      ) : (
        <div className="task-list">
          {tasks.map((task) => (
            <div 
              key={task.id} 
              className={`task-item ${task.is_completed ? 'completed' : ''} priority-${task.priority.toLowerCase()}`}
              onClick={() => toggleTask(task.id, task.is_completed)}
            >
              <div className="task-checkbox">
                {task.is_completed ? (
                  <CheckCircle2 className="checked" size={24} />
                ) : (
                  <Circle className="unchecked" size={24} />
                )}
              </div>
              
              <div className="task-content">
                <div className="task-title-row">
                  <h4 className="task-title">{task.title}</h4>
                  <span className={`task-badge ${task.priority.toLowerCase()}`}>
                    {task.priority.toUpperCase()}
                  </span>
                </div>
                
                <p className="task-desc">{task.description}</p>
                
                <div className="task-meta">
                  <span className="task-category">
                    {getCategoryIcon(task.category)}
                    {task.category.charAt(0).toUpperCase() + task.category.slice(1)}
                  </span>
                </div>
              </div>
            </div>
          ))}
          
          <div className="checklist-footer">
            <button 
              className="generate-more-btn" 
              onClick={handleGenerateTasks}
              disabled={generating}
            >
              {generating ? 'Regenerating...' : 'Regenerate Tasks'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyChecklist;
