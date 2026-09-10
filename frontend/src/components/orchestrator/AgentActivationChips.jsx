import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FlaskConical,
  CloudSun,
  TrendingUp,
  Sprout,
  Wheat,
  Pill,
  Droplets,
  Bug,
  BarChart3,
  DollarSign,
  Calendar,
  Tractor,
  MapPin,
  Package,
  ShieldAlert,
  Users,
  ClipboardCheck,
  MessageSquare,
  Bot
} from 'lucide-react';

const ChipsContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
`;

const AgentChip = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  ${props => {
    switch (props.status) {
      case 'running':
        return `
          background: linear-gradient(135deg, #3b82f6, #1d4ed8);
          color: white;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        `;
      case 'completed':
        return `
          background: linear-gradient(135deg, #10b981, #059669);
          color: white;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        `;
      case 'failed':
        return `
          background: linear-gradient(135deg, #ef4444, #dc2626);
          color: white;
          box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        `;
      case 'pending':
        return `
          background: linear-gradient(135deg, #f59e0b, #d97706);
          color: white;
          box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
        `;
      default:
        return `
          background: #f3f4f6;
          color: #6b7280;
          border: 1px solid #e5e7eb;
        `;
    }
  }}
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  }
`;

const AgentIcon = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
`;

const AgentName = styled.span`
  white-space: nowrap;
`;

const StatusIndicator = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'running': return '#60a5fa';
      case 'completed': return '#34d399';
      case 'failed': return '#f87171';
      case 'pending': return '#fbbf24';
      default: return '#9ca3af';
    }
  }};
  animation: ${props => props.status === 'running' ? 'pulse 1.5s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const AgentActivationChips = ({ 
  agents = [], 
  onAgentClick = null,
  showStatus = true,
  className = '' 
}) => {
  const getAgentIcon = (agentName) => {
    const iconMap = {
      'soil_health_agent': <FlaskConical size={14} />,
      'weather_watcher_agent': <CloudSun size={14} />,
      'market_intelligence_agent': <TrendingUp size={14} />,
      'crop_selector_agent': <Sprout size={14} />,
      'seed_selection_agent': <Wheat size={14} />,
      'fertilizer_advisor_agent': <Pill size={14} />,
      'irrigation_planner_agent': <Droplets size={14} />,
      'pest_disease_diagnostic_agent': <Bug size={14} />,
      'yield_predictor_agent': <BarChart3 size={14} />,
      'profit_optimization_agent': <DollarSign size={14} />,
      'task_scheduler_agent': <Calendar size={14} />,
      'machinery_equipment_agent': <Tractor size={14} />,
      'farm_layout_mapping_agent': <MapPin size={14} />,
      'logistics_storage_agent': <Package size={14} />,
      'crop_insurance_risk_agent': <ShieldAlert size={14} />,
      'farmer_coach_agent': <Users size={14} />,
      'compliance_certification_agent': <ClipboardCheck size={14} />,
      'community_engagement_agent': <MessageSquare size={14} />
    };
    
    return iconMap[agentName] || <Bot size={14} />;
  };

  const getAgentDisplayName = (agentName) => {
    const nameMap = {
      'soil_health_agent': 'Soil Health',
      'weather_watcher_agent': 'Weather Watcher',
      'market_intelligence_agent': 'Market Intelligence',
      'crop_selector_agent': 'Crop Selector',
      'seed_selection_agent': 'Seed Selection',
      'fertilizer_advisor_agent': 'Fertilizer Advisor',
      'irrigation_planner_agent': 'Irrigation Planner',
      'pest_disease_diagnostic_agent': 'Pest Diagnostic',
      'yield_predictor_agent': 'Yield Predictor',
      'profit_optimization_agent': 'Profit Optimization',
      'task_scheduler_agent': 'Task Scheduler',
      'machinery_equipment_agent': 'Machinery',
      'farm_layout_mapping_agent': 'Farm Layout',
      'logistics_storage_agent': 'Logistics',
      'crop_insurance_risk_agent': 'Risk Management',
      'farmer_coach_agent': 'Farmer Coach',
      'compliance_certification_agent': 'Compliance',
      'community_engagement_agent': 'Community'
    };
    
    return nameMap[agentName] || agentName.replace('_agent', '').replace(/_/g, ' ');
  };

  const handleAgentClick = (agent) => {
    if (onAgentClick) {
      onAgentClick(agent);
    }
  };

  if (!agents || agents.length === 0) {
    return (
      <ChipsContainer className={className}>
        <div style={{ color: '#6b7280', fontStyle: 'italic' }}>
          No agents active
        </div>
      </ChipsContainer>
    );
  }

  return (
    <ChipsContainer className={className}>
      <AnimatePresence>
        {agents.map((agent, index) => (
          <AgentChip
            key={agent.id || agent.name || index}
            status={agent.status || 'pending'}
            onClick={() => handleAgentClick(agent)}
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -20 }}
            transition={{ 
              duration: 0.3, 
              delay: index * 0.1,
              type: "spring",
              stiffness: 200
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {showStatus && <StatusIndicator status={agent.status || 'pending'} />}
            <AgentIcon>{getAgentIcon(agent.name)}</AgentIcon>
            <AgentName>{getAgentDisplayName(agent.name)}</AgentName>
          </AgentChip>
        ))}
      </AnimatePresence>
    </ChipsContainer>
  );
};

export default AgentActivationChips;
