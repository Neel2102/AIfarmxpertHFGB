import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Sprout, 
  MapPin, 
  Ruler, 
  Mountain, 
  Wheat, 
  Droplets, 
  Waves, 
  Cpu, 
  Target, 
  Leaf, 
  Bug, 
  Truck, 
  Users, 
  ChevronRight, 
  ChevronLeft,
  Check,
  Home,
  TreePine,
  Flower,
  Carrot,
  Apple,
  Package,
  Sun,
  Cloud,
  Wind,
  Factory,
  Heart,
  Shield,
  Zap
} from 'lucide-react';
import styles from './FarmOnboarding.module.css';

const FarmOnboarding = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { completeOnboarding, user } = useAuth();
  const [formData, setFormData] = useState({
    farmName: '',
    state: '',
    district: '',
    farmSize: '',
    soilType: '',
    mainCropCategory: '',
    specificCrop: '',
    irrigationMethod: '',
    waterSourceQuality: '',
    iotSetup: '',
    primaryGoal: '',
    fertilizerPreference: '',
    pestManagement: '',
    machinery: [],
    laborSetup: ''
  });

  const [otherInputs, setOtherInputs] = useState({
    soilType: '',
    mainCropCategory: '',
    specificCrop: '',
    irrigationMethod: '',
    waterSourceQuality: '',
    iotSetup: '',
    primaryGoal: '',
    fertilizerPreference: '',
    pestManagement: '',
    machinery: '',
    laborSetup: ''
  });

  const states = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa',
    'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland',
    'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
    'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Mumbai', 'Kolkata'
  ];

  const soilTypes = [
    { id: 'clay', label: 'Clay', icon: Mountain },
    { id: 'sandy', label: 'Sandy', icon: Sun },
    { id: 'loamy', label: 'Loamy', icon: Sprout },
    { id: 'silt', label: 'Silt', icon: Waves },
    { id: 'peaty', label: 'Peaty', icon: TreePine },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const cropCategories = [
    { id: 'cereals', label: 'Cereals', icon: Wheat },
    { id: 'pulses', label: 'Pulses', icon: Package },
    { id: 'cash', label: 'Cash Crops', icon: Factory },
    { id: 'fruits', label: 'Fruits', icon: Apple },
    { id: 'vegetables', label: 'Vegetables', icon: Carrot },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const irrigationMethods = [
    { id: 'drip', label: 'Drip', icon: Droplets },
    { id: 'sprinkler', label: 'Sprinkler', icon: Wind },
    { id: 'rainfed', label: 'Rainfed', icon: Cloud },
    { id: 'canal', label: 'Canal/Flood', icon: Waves },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const waterSources = [
    { id: 'fresh', label: 'Fresh/Sweet', icon: Droplets },
    { id: 'saline', label: 'Saline', icon: Waves },
    { id: 'brackish', label: 'Brackish', icon: Zap },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const iotSetups = [
    { id: 'none', label: 'None', icon: Shield },
    { id: 'basic', label: 'Basic Sensors', icon: Cpu },
    { id: 'advanced', label: 'Advanced/Automated', icon: Zap },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const goals = [
    { id: 'yield', label: 'Maximize Yield', icon: Target },
    { id: 'costs', label: 'Reduce Costs', icon: Heart },
    { id: 'organic', label: 'Transition to Organic', icon: Leaf },
    { id: 'climate', label: 'Climate Resilience', icon: Shield },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const fertilizerPreferences = [
    { id: 'chemical', label: '100% Chemical', icon: Factory },
    { id: 'organic', label: '100% Organic', icon: Leaf },
    { id: 'integrated', label: 'Integrated/Mixed', icon: Sprout },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const pestManagement = [
    { id: 'preventive', label: 'Preventive', icon: Shield },
    { id: 'reactive', label: 'Reactive', icon: Bug },
    { id: 'biological', label: 'Biological/IPM', icon: Leaf },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const machineryOptions = [
    { id: 'tractor', label: 'Tractor', icon: Truck },
    { id: 'harvester', label: 'Harvester', icon: Wheat },
    { id: 'drone', label: 'Drone', icon: Wind },
    { id: 'none', label: 'None', icon: Shield }
  ];

  const laborSetups = [
    { id: 'family', label: 'Family only', icon: Users },
    { id: 'hired', label: 'Hired help', icon: Users },
    { id: 'mechanized', label: 'Fully mechanized', icon: Truck },
    { id: 'other', label: 'Other', icon: ChevronRight }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleCardSelect = (field, value) => {
    if (value === 'other') {
      setFormData(prev => ({ ...prev, [field]: '' }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
      setOtherInputs(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleMachineryToggle = (value) => {
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.includes(value)
        ? prev.machinery.filter(item => item !== value)
        : [...prev.machinery, value]
    }));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && canProceed()) {
      e.preventDefault();
      if (currentStep < 14) {
        nextStep();
      } else if (currentStep === 14) {
        handleSubmit();
      }
    }
  };

  const nextStep = () => {
    if (currentStep < 14) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return formData.farmName.trim() !== '';
      case 1: return formData.state !== '' && formData.district.trim() !== '';
      case 2: return formData.farmSize !== '';
      case 3: return formData.soilType !== '';
      case 4: return formData.mainCropCategory !== '';
      case 5: return formData.specificCrop.trim() !== '';
      case 6: return formData.irrigationMethod !== '';
      case 7: return formData.waterSourceQuality !== '';
      case 8: return formData.iotSetup !== '';
      case 9: return formData.primaryGoal !== '';
      case 10: return formData.fertilizerPreference !== '';
      case 11: return formData.pestManagement !== '';
      case 12: return true; // Machinery is optional
      case 13: return formData.laborSetup !== '';
      case 14: return true; // Review step
      default: return false;
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const result = await completeOnboarding(formData);
      
      if (result.success) {
        if ((user?.role || '').toLowerCase() === 'admin') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
      } else {
        setError(result.error || 'Failed to complete onboarding');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <motion.div
            key="step0"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <div className={styles.welcomeSection}>
              <Home className={styles.welcomeIcon} />
              <h2>Welcome to FarmXpert!</h2>
              <p>Let's set up your farm profile to get personalized AI assistance</p>
            </div>
            <div className={styles.formGroup}>
              <label>Farm Name</label>
              <input
                type="text"
                value={formData.farmName}
                onChange={(e) => handleInputChange('farmName', e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter your farm name"
                className={styles.textInput}
              />
            </div>
          </motion.div>
        );

      case 1:
        return (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <MapPin className={styles.stepIcon} />
            <h2>Farm Location</h2>
            <div className={styles.formGroup}>
              <label>State</label>
              <select
                value={formData.state}
                onChange={(e) => handleInputChange('state', e.target.value)}
                onKeyDown={handleKeyDown}
                className={styles.selectInput}
              >
                <option value="">Select your state</option>
                {states.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>
            <div className={styles.formGroup}>
              <label>District</label>
              <input
                type="text"
                value={formData.district}
                onChange={(e) => handleInputChange('district', e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter your district"
                className={styles.textInput}
              />
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Ruler className={styles.stepIcon} />
            <h2>Farm Size</h2>
            <div className={styles.formGroup}>
              <label>Farm Size (in Acres)</label>
              <input
                type="number"
                value={formData.farmSize}
                onChange={(e) => handleInputChange('farmSize', e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter farm size in acres"
                className={styles.textInput}
                min="0.1"
                step="0.1"
              />
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Mountain className={styles.stepIcon} />
            <h2>Primary Soil Type</h2>
            <div className={styles.cardGrid}>
              {soilTypes.map(type => {
                const Icon = type.icon;
                return (
                  <div
                    key={type.id}
                    className={`${styles.card} ${formData.soilType === type.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('soilType', type.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('soilType', type.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{type.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.soilType === 'other' && (
              <input
                type="text"
                value={otherInputs.soilType}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, soilType: e.target.value }));
                  handleInputChange('soilType', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your soil type"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Wheat className={styles.stepIcon} />
            <h2>Main Crop Category</h2>
            <div className={styles.cardGrid}>
              {cropCategories.map(category => {
                const Icon = category.icon;
                return (
                  <div
                    key={category.id}
                    className={`${styles.card} ${formData.mainCropCategory === category.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('mainCropCategory', category.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('mainCropCategory', category.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{category.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.mainCropCategory === 'other' && (
              <input
                type="text"
                value={otherInputs.mainCropCategory}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, mainCropCategory: e.target.value }));
                  handleInputChange('mainCropCategory', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your crop category"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 5:
        return (
          <motion.div
            key="step5"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Flower className={styles.stepIcon} />
            <h2>Specific Crop/Variety</h2>
            <div className={styles.formGroup}>
              <label>What specific crop or variety do you grow?</label>
              <input
                type="text"
                value={formData.specificCrop}
                onChange={(e) => handleInputChange('specificCrop', e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g., Basmati Rice, Tomatoes, Cotton"
                className={styles.textInput}
              />
            </div>
          </motion.div>
        );

      case 6:
        return (
          <motion.div
            key="step6"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Droplets className={styles.stepIcon} />
            <h2>Irrigation Method</h2>
            <div className={styles.cardGrid}>
              {irrigationMethods.map(method => {
                const Icon = method.icon;
                return (
                  <div
                    key={method.id}
                    className={`${styles.card} ${formData.irrigationMethod === method.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('irrigationMethod', method.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('irrigationMethod', method.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{method.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.irrigationMethod === 'other' && (
              <input
                type="text"
                value={otherInputs.irrigationMethod}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, irrigationMethod: e.target.value }));
                  handleInputChange('irrigationMethod', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your irrigation method"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 7:
        return (
          <motion.div
            key="step7"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Waves className={styles.stepIcon} />
            <h2>Water Source Quality</h2>
            <div className={styles.cardGrid}>
              {waterSources.map(source => {
                const Icon = source.icon;
                return (
                  <div
                    key={source.id}
                    className={`${styles.card} ${formData.waterSourceQuality === source.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('waterSourceQuality', source.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('waterSourceQuality', source.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{source.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.waterSourceQuality === 'other' && (
              <input
                type="text"
                value={otherInputs.waterSourceQuality}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, waterSourceQuality: e.target.value }));
                  handleInputChange('waterSourceQuality', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your water source quality"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 8:
        return (
          <motion.div
            key="step8"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Cpu className={styles.stepIcon} />
            <h2>Current IoT/Hardware Setup</h2>
            <div className={styles.cardGrid}>
              {iotSetups.map(setup => {
                const Icon = setup.icon;
                return (
                  <div
                    key={setup.id}
                    className={`${styles.card} ${formData.iotSetup === setup.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('iotSetup', setup.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('iotSetup', setup.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{setup.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.iotSetup === 'other' && (
              <input
                type="text"
                value={otherInputs.iotSetup}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, iotSetup: e.target.value }));
                  handleInputChange('iotSetup', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please describe your IoT setup"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 9:
        return (
          <motion.div
            key="step9"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Target className={styles.stepIcon} />
            <h2>Primary Farming Goal</h2>
            <div className={styles.cardGrid}>
              {goals.map(goal => {
                const Icon = goal.icon;
                return (
                  <div
                    key={goal.id}
                    className={`${styles.card} ${formData.primaryGoal === goal.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('primaryGoal', goal.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('primaryGoal', goal.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{goal.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.primaryGoal === 'other' && (
              <input
                type="text"
                value={otherInputs.primaryGoal}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, primaryGoal: e.target.value }));
                  handleInputChange('primaryGoal', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your farming goal"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 10:
        return (
          <motion.div
            key="step10"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Leaf className={styles.stepIcon} />
            <h2>Fertilizer Preference</h2>
            <div className={styles.cardGrid}>
              {fertilizerPreferences.map(pref => {
                const Icon = pref.icon;
                return (
                  <div
                    key={pref.id}
                    className={`${styles.card} ${formData.fertilizerPreference === pref.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('fertilizerPreference', pref.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('fertilizerPreference', pref.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{pref.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.fertilizerPreference === 'other' && (
              <input
                type="text"
                value={otherInputs.fertilizerPreference}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, fertilizerPreference: e.target.value }));
                  handleInputChange('fertilizerPreference', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your fertilizer preference"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 11:
        return (
          <motion.div
            key="step11"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Bug className={styles.stepIcon} />
            <h2>Pest Management Approach</h2>
            <div className={styles.cardGrid}>
              {pestManagement.map(approach => {
                const Icon = approach.icon;
                return (
                  <div
                    key={approach.id}
                    className={`${styles.card} ${formData.pestManagement === approach.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('pestManagement', approach.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('pestManagement', approach.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{approach.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.pestManagement === 'other' && (
              <input
                type="text"
                value={otherInputs.pestManagement}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, pestManagement: e.target.value }));
                  handleInputChange('pestManagement', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your pest management approach"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 12:
        return (
          <motion.div
            key="step12"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Truck className={styles.stepIcon} />
            <h2>Available Machinery</h2>
            <div className={styles.chipGrid}>
              {machineryOptions.map(option => {
                const Icon = option.icon;
                return (
                  <div
                    key={option.id}
                    className={`${styles.chip} ${formData.machinery.includes(option.id) ? styles.selected : ''}`}
                    onClick={() => handleMachineryToggle(option.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleMachineryToggle(option.id);
                    }}
                  >
                    <Icon className={styles.chipIcon} />
                    <span>{option.label}</span>
                    {formData.machinery.includes(option.id) && <Check className={styles.checkIcon} />}
                  </div>
                );
              })}
            </div>
          </motion.div>
        );

      case 13:
        return (
          <motion.div
            key="step13"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Users className={styles.stepIcon} />
            <h2>Labor Setup</h2>
            <div className={styles.cardGrid}>
              {laborSetups.map(setup => {
                const Icon = setup.icon;
                return (
                  <div
                    key={setup.id}
                    className={`${styles.card} ${formData.laborSetup === setup.id ? styles.selected : ''}`}
                    onClick={() => handleCardSelect('laborSetup', setup.id)}
                    tabIndex="0"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCardSelect('laborSetup', setup.id);
                    }}
                  >
                    <Icon className={styles.cardIcon} />
                    <span>{setup.label}</span>
                  </div>
                );
              })}
            </div>
            {formData.laborSetup === 'other' && (
              <input
                type="text"
                value={otherInputs.laborSetup}
                onChange={(e) => {
                  setOtherInputs(prev => ({ ...prev, laborSetup: e.target.value }));
                  handleInputChange('laborSetup', e.target.value);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please specify your labor setup"
                className={styles.textInput}
              />
            )}
          </motion.div>
        );

      case 14:
        return (
          <motion.div
            key="step14"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -300 }}
            className={styles.stepContent}
          >
            <Check className={styles.stepIcon} />
            <h2>Review & Submit</h2>
            <div className={styles.reviewSection}>
              <h3>Farm Profile Summary</h3>
              <div className={styles.reviewGrid}>
                <div className={styles.reviewItem}>
                  <strong>Farm Name:</strong> {formData.farmName}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Location:</strong> {formData.state}, {formData.district}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Farm Size:</strong> {formData.farmSize} acres
                </div>
                <div className={styles.reviewItem}>
                  <strong>Soil Type:</strong> {formData.soilType}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Main Crop:</strong> {formData.mainCropCategory}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Specific Crop:</strong> {formData.specificCrop}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Irrigation:</strong> {formData.irrigationMethod}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Water Quality:</strong> {formData.waterSourceQuality}
                </div>
                <div className={styles.reviewItem}>
                  <strong>IoT Setup:</strong> {formData.iotSetup}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Primary Goal:</strong> {formData.primaryGoal}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Fertilizer:</strong> {formData.fertilizerPreference}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Pest Management:</strong> {formData.pestManagement}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Machinery:</strong> {formData.machinery.join(', ') || 'None'}
                </div>
                <div className={styles.reviewItem}>
                  <strong>Labor Setup:</strong> {formData.laborSetup}
                </div>
              </div>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={styles.onboardingContainer}>
      <div className={styles.progressSection}>
        <div className={styles.progressBar}>
          <div 
            className={styles.progressFill}
            style={{ width: `${((currentStep + 1) / 15) * 100}%` }}
          />
        </div>
        <div className={styles.progressText}>
          Step {currentStep + 1} of 15
        </div>
      </div>

      <div className={styles.contentWrapper}>
        {error && (
          <div className={styles.errorMessage}>
            <span>{error}</span>
          </div>
        )}
        <AnimatePresence mode="wait">
          {renderStep()}
        </AnimatePresence>
      </div>

      <div className={styles.navigationButtons}>
        <button
          onClick={prevStep}
          disabled={currentStep === 0}
          className={`${styles.navButton} ${styles.backButton} ${currentStep === 0 ? styles.disabled : ''}`}
        >
          <ChevronLeft className={styles.buttonIcon} />
          Back
        </button>

        {currentStep < 14 ? (
          <button
            onClick={nextStep}
            disabled={!canProceed()}
            className={`${styles.navButton} ${styles.nextButton} ${!canProceed() ? styles.disabled : ''}`}
          >
            Next
            <ChevronRight className={styles.buttonIcon} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`${styles.navButton} ${styles.submitButton} ${loading ? styles.loading : ''}`}
          >
            {loading ? 'Submitting...' : 'Complete Setup'}
            <Check className={styles.buttonIcon} />
          </button>
        )}
      </div>
    </div>
  );
};

export default FarmOnboarding;
