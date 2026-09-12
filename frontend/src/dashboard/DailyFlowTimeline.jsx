import React, { useState } from 'react';
import {
  CheckCircle2, Circle, ChevronDown, ChevronUp, Calendar,
  Droplets, Bug, Sprout, Hammer, Clock, Sparkles, Check
} from 'lucide-react';
import '../styles/Dashboard/TodayDashboard.css';

const getCategoryIcon = (category) => {
  switch (category?.toLowerCase()) {
    case 'irrigation': return <Droplets size={15} />;
    case 'pest': return <Bug size={15} />;
    case 'fertilizer': return <Sprout size={15} />;
    case 'maintenance': return <Hammer size={15} />;
    case 'harvest': return <Sparkles size={15} />;
    default: return <Clock size={15} />;
  }
};

const DailyFlowTimeline = ({ stages = [], onToggleTask }) => {
  // Set the first active stage or stage 0 expanded by default
  const [expandedStages, setExpandedStages] = useState(() => {
    const activeIdx = stages.findIndex(s => s.status === 'active');
    return { [activeIdx >= 0 ? activeIdx : 0]: true };
  });

  const toggleStage = (idx) => {
    setExpandedStages(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  if (!stages || stages.length === 0) {
    return (
      <div className="empty-state" style={{ padding: '32px 20px', textAlign: 'center' }}>
        <Sprout size={36} style={{ opacity: 0.6, marginBottom: '12px' }} />
        <h4>No Season Timeline Available</h4>
        <p>Click 'Generate Season Flow' above to calculate the crop lifecycle stages and milestone tasks.</p>
      </div>
    );
  }

  return (
    <div className="daily-flow-timeline">
      <div className="timeline-intro-bar">
        <div className="timeline-legend">
          <span className="legend-item"><span className="legend-dot completed"></span> Completed</span>
          <span className="legend-item"><span className="legend-dot active"></span> Current Active Stage</span>
          <span className="legend-item"><span className="legend-dot upcoming"></span> Upcoming</span>
        </div>
      </div>

      <div className="stages-list">
        {stages.map((stage, idx) => {
          const isExpanded = !!expandedStages[idx];
          const isCompleted = stage.status === 'completed';
          const isActive = stage.status === 'active';
          const taskCount = stage.tasks?.length || 0;
          const completedTasksCount = stage.tasks?.filter(t => t.is_completed).length || 0;

          return (
            <div 
              key={stage.id || idx} 
              className={`stage-card ${stage.status} ${isExpanded ? 'expanded' : ''}`}
            >
              <div className="stage-card-header" onClick={() => toggleStage(idx)}>
                <div className="stage-header-left">
                  <div className={`stage-step-indicator ${stage.status}`}>
                    {isCompleted ? <Check size={14} /> : (idx + 1)}
                  </div>
                  <div>
                    <div className="stage-title-row">
                      <h4 className="stage-name">{stage.name}</h4>
                      <span className={`stage-status-badge ${stage.status}`}>
                        {isActive ? 'CURRENT STAGE' : stage.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="stage-meta-row">
                      <span className="stage-day-range">
                        <Calendar size={13} /> {stage.day_range}
                      </span>
                      <span className="stage-dates">
                        {new Date(stage.start_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} – {new Date(stage.end_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                      <span className="stage-task-pill">
                        {completedTasksCount}/{taskCount} tasks completed
                      </span>
                    </div>
                  </div>
                </div>

                <div className="stage-header-right">
                  <div className="stage-progress-mini">
                    <div className="progress-track">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${stage.progress_pct || (isCompleted ? 100 : 0)}%` }} 
                      />
                    </div>
                    <span className="progress-label">{stage.progress_pct || (isCompleted ? 100 : 0)}%</span>
                  </div>
                  <button className="stage-expand-btn" aria-label="Toggle stage">
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="stage-card-body">
                  <p className="stage-description">{stage.description}</p>

                  {taskCount === 0 ? (
                    <div className="stage-empty-tasks">
                      No specific tasks scheduled for this stage yet.
                    </div>
                  ) : (
                    <div className="stage-task-list">
                      {stage.tasks.map(task => (
                        <div 
                          key={task.id} 
                          className={`stage-task-row ${task.is_completed ? 'completed' : ''} priority-${task.priority?.toLowerCase()}`}
                          onClick={() => onToggleTask && onToggleTask(task.id, task.is_completed)}
                        >
                          <div className="task-checkbox-wrap">
                            {task.is_completed ? (
                              <CheckCircle2 className="checked" size={20} />
                            ) : (
                              <Circle className="unchecked" size={20} />
                            )}
                          </div>
                          
                          <div className="stage-task-main">
                            <div className="stage-task-title-line">
                              <span className="task-category-icon">
                                {getCategoryIcon(task.category)}
                              </span>
                              <span className="stage-task-title">{task.title}</span>
                              <span className={`stage-task-priority priority-${task.priority?.toLowerCase()}`}>
                                {task.priority?.toUpperCase()}
                              </span>
                            </div>
                            {task.description && (
                              <p className="stage-task-desc">{task.description}</p>
                            )}
                            <div className="stage-task-footer">
                              <span className="stage-task-date">
                                📅 Scheduled: {task.scheduled_date_str || new Date(task.scheduled_date).toLocaleDateString()}
                              </span>
                              <span className="stage-task-tag">
                                {task.category?.toUpperCase() || 'OPERATION'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DailyFlowTimeline;
