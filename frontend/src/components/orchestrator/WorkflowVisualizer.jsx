import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FlaskConical, CloudSun, TrendingUp, Sprout, Wheat, Pill, Droplets,
  Bug, BarChart3, DollarSign, Calendar, Truck, Map, Package, Shield,
  User, ClipboardList, Users, Bot, RefreshCw, Zap, Check, X
} from 'lucide-react';

const WorkflowContainer = styled.div`
  margin: 2rem 0;
  padding: 1.5rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
`;

const WorkflowHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f3f4f6;
`;

const HeaderTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const ProgressIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
`;

const ProgressBar = styled.div`
  width: 200px;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
`;

const ProgressFill = styled(motion.div)`
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  position: absolute;
  top: 0;
  left: 0;
`;

const StepsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const StepItem = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 12px;
  border: 2px solid ${props => {
    switch (props.status) {
      case 'completed': return '#10b981';
      case 'running': return '#3b82f6';
      case 'failed': return '#ef4444';
      case 'pending': return '#e5e7eb';
      default: return '#e5e7eb';
    }
  }};
  background: ${props => {
    switch (props.status) {
      case 'completed': return '#f0fdf4';
      case 'running': return '#eff6ff';
      case 'failed': return '#fef2f2';
      case 'pending': return '#f9fafb';
      default: return '#f9fafb';
    }
  }};
  transition: all 0.3s ease;
  
  ${props => props.status === 'running' && `
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    animation: pulse 2s infinite;
    
    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
      50% { box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.2); }
    }
  `}
`;

const StepNumber = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  background: ${props => {
    switch (props.status) {
      case 'completed': return '#10b981';
      case 'running': return '#3b82f6';
      case 'failed': return '#ef4444';
      case 'pending': return '#9ca3af';
      default: return '#9ca3af';
    }
  }};
  position: relative;
  
  ${props => props.status === 'running' && `
    animation: spin 1s linear infinite;
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `}
`;

const StepContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const StepTitle = styled.div`
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const StepDescription = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`;

const StepStatus = styled.div`
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${props => {
    switch (props.status) {
      case 'completed': return '#10b981';
      case 'running': return '#3b82f6';
      case 'failed': return '#ef4444';
      case 'pending': return '#9ca3af';
      default: return '#9ca3af';
    }
  }};
`;

const StepIcon = styled.span`
  font-size: 1.25rem;
`;

const StepTime = styled.div`
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
`;

const ErrorMessage = styled.div`
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 0.875rem;
`;

const WorkflowVisualizer = ({ 
  workflow = null,
  isActive = false,
  onStepClick = null,
  className = '' 
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (workflow && workflow.tasks) {
      const completedTasks = workflow.tasks.filter(task => task.status === 'completed').length;
      const totalTasks = workflow.tasks.length;
      const newProgress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
      setProgress(newProgress);
      
      // Find current running step
      const runningIndex = workflow.tasks.findIndex(task => task.status === 'running');
      setCurrentStep(runningIndex >= 0 ? runningIndex : completedTasks);
    }
  }, [workflow]);

  const getStepIcon = (agentName) => {
    const iconMap = {
      'soil_health_agent': <FlaskConical size={18} />,
      'weather_watcher_agent': <CloudSun size={18} />,
      'market_intelligence_agent': <TrendingUp size={18} />,
      'crop_selector_agent': <Sprout size={18} />,
      'seed_selection_agent': <Wheat size={18} />,
      'fertilizer_advisor_agent': <Pill size={18} />,
      'irrigation_planner_agent': <Droplets size={18} />,
      'pest_disease_diagnostic_agent': <Bug size={18} />,
      'yield_predictor_agent': <BarChart3 size={18} />,
      'profit_optimization_agent': <DollarSign size={18} />,
      'task_scheduler_agent': <Calendar size={18} />,
      'machinery_equipment_agent': <Truck size={18} />,
      'farm_layout_mapping_agent': <Map size={18} />,
      'logistics_storage_agent': <Package size={18} />,
      'crop_insurance_risk_agent': <Shield size={18} />,
      'farmer_coach_agent': <User size={18} />,
      'compliance_certification_agent': <ClipboardList size={18} />,
      'community_engagement_agent': <Users size={18} />
    };
    
    return iconMap[agentName] || <Bot size={18} />;
  };

  const getStepTitle = (agentName) => {
    const titleMap = {
      'soil_health_agent': 'Analyzing Soil Health',
      'weather_watcher_agent': 'Checking Weather Conditions',
      'market_intelligence_agent': 'Gathering Market Data',
      'crop_selector_agent': 'Selecting Best Crops',
      'seed_selection_agent': 'Recommending Seeds',
      'fertilizer_advisor_agent': 'Planning Fertilizer Application',
      'irrigation_planner_agent': 'Planning Irrigation',
      'pest_disease_diagnostic_agent': 'Diagnosing Plant Issues',
      'yield_predictor_agent': 'Predicting Yield',
      'profit_optimization_agent': 'Optimizing Profit',
      'task_scheduler_agent': 'Scheduling Farm Tasks',
      'machinery_equipment_agent': 'Planning Equipment',
      'farm_layout_mapping_agent': 'Mapping Farm Layout',
      'logistics_storage_agent': 'Planning Storage',
      'crop_insurance_risk_agent': 'Assessing Risks',
      'farmer_coach_agent': 'Providing Guidance',
      'compliance_certification_agent': 'Checking Compliance',
      'community_engagement_agent': 'Community Support'
    };
    
    return titleMap[agentName] || agentName.replace('_agent', '').replace(/_/g, ' ');
  };

  const getStepDescription = (agentName) => {
    const descMap = {
      'soil_health_agent': 'Analyzing soil composition, pH levels, and nutrient content',
      'weather_watcher_agent': 'Checking current weather and forecasting conditions',
      'market_intelligence_agent': 'Gathering market prices and demand trends',
      'crop_selector_agent': 'Selecting optimal crops based on conditions',
      'seed_selection_agent': 'Recommending best seed varieties',
      'fertilizer_advisor_agent': 'Planning fertilizer application schedule',
      'irrigation_planner_agent': 'Creating irrigation schedule',
      'pest_disease_diagnostic_agent': 'Identifying plant health issues',
      'yield_predictor_agent': 'Predicting crop yield based on conditions',
      'profit_optimization_agent': 'Optimizing for maximum profit',
      'task_scheduler_agent': 'Creating farm task schedule',
      'machinery_equipment_agent': 'Planning machinery and equipment needs',
      'farm_layout_mapping_agent': 'Mapping farm layout and zones',
      'logistics_storage_agent': 'Planning storage and logistics',
      'crop_insurance_risk_agent': 'Assessing crop risks and insurance',
      'farmer_coach_agent': 'Providing farming guidance and tips',
      'compliance_certification_agent': 'Checking regulatory compliance',
      'community_engagement_agent': 'Connecting with farming community'
    };
    
    return descMap[agentName] || 'Processing request...';
  };

  const handleStepClick = (step, index) => {
    if (onStepClick) {
      onStepClick(step, index);
    }
  };

  if (!workflow || !workflow.tasks) {
    return (
      <WorkflowContainer className={className}>
        <div style={{ color: '#6b7280', fontStyle: 'italic', textAlign: 'center', padding: '2rem' }}>
          No workflow data available
        </div>
      </WorkflowContainer>
    );
  }

  const totalSteps = workflow.tasks.length;
  const completedSteps = workflow.tasks.filter(task => task.status === 'completed').length;
  const runningSteps = workflow.tasks.filter(task => task.status === 'running').length;

  return (
    <WorkflowContainer className={className}>
      <WorkflowHeader>
        <HeaderTitle>
          <RefreshCw size={18} style={{ display: 'inline', marginRight: '8px' }} />
          Workflow Progress
          {isActive && <Zap size={16} style={{ display: 'inline', marginLeft: '6px', color: '#f59e0b' }} />}
        </HeaderTitle>
        
        <ProgressIndicator>
          <span>{completedSteps}/{totalSteps} completed</span>
          <ProgressBar>
            <ProgressFill
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </ProgressBar>
          <span>{Math.round(progress)}%</span>
        </ProgressIndicator>
      </WorkflowHeader>

      <StepsContainer>
        <AnimatePresence>
          {workflow.tasks.map((task, index) => (
            <StepItem
              key={task.id || index}
              status={task.status || 'pending'}
              onClick={() => handleStepClick(task, index)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{ cursor: onStepClick ? 'pointer' : 'default' }}
            >
              <StepNumber status={task.status || 'pending'}>
                {task.status === 'completed' ? <Check size={14} /> : 
                 task.status === 'running' ? <RefreshCw size={14} className="animate-spin" /> : 
                 task.status === 'failed' ? <X size={14} /> : 
                 index + 1}
              </StepNumber>
              
              <StepContent>
                <StepTitle>
                  <StepIcon>{getStepIcon(task.agent_name)}</StepIcon>
                  {getStepTitle(task.agent_name)}
                </StepTitle>
                
                <StepDescription>
                  {getStepDescription(task.agent_name)}
                </StepDescription>
                
                {task.error_message && (
                  <ErrorMessage>
                    Error: {task.error_message}
                  </ErrorMessage>
                )}
              </StepContent>
              
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                <StepStatus status={task.status || 'pending'}>
                  {task.status || 'pending'}
                </StepStatus>
                
                {task.execution_time && (
                  <StepTime>
                    {task.execution_time.toFixed(2)}s
                  </StepTime>
                )}
              </div>
            </StepItem>
          ))}
        </AnimatePresence>
      </StepsContainer>
    </WorkflowContainer>
  );
};

export default WorkflowVisualizer;
