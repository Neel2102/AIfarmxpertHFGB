-- ============================================================
-- FarmXpert — Agent Seed Data
-- ============================================================
-- Seeds 5 agent categories and 22 agents with capabilities
-- and orchestrator routing keywords.
-- Run AFTER schema.sql has been applied.
-- ============================================================

BEGIN;

-- ============================================================
-- AGENT CATEGORIES
-- ============================================================

INSERT INTO agent_categories (category_name, description) VALUES
    ('Crop Planning & Growth',          'Agents for crop selection, seed recommendation, growth monitoring, and yield prediction'),
    ('Farm Operations & Automation',    'Agents for fertilizer, irrigation, weather, pest detection, and equipment management'),
    ('Analytics & Optimization',        'Agents for soil analysis, crop health vision, water optimization, farm analytics, and carbon tracking'),
    ('Supply Chain & Market Access',    'Agents for market intelligence, supply chain, mandi prices, and cold storage advisory'),
    ('Farmer Support & Education',      'Agents for farm coaching, voice assistance, government schemes, and loan/insurance advisory');

-- ============================================================
-- AGENT REGISTRY — 22 Agents
-- ============================================================
-- agent_type:  analysis | vision | api | monitoring
-- Flags:       requires_image, requires_sensor_data, requires_external_api, uses_memory

-- ──────────────────────────────────────
-- Category 1: Crop Planning & Growth
-- ──────────────────────────────────────

INSERT INTO agent_registry (category_id, agent_name, agent_type, requires_image, requires_sensor_data, requires_external_api, uses_memory) VALUES
    ((SELECT id FROM agent_categories WHERE category_name = 'Crop Planning & Growth'),
        'Crop Selector',            'analysis',     FALSE, TRUE,  TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Crop Planning & Growth'),
        'Seed Recommender',         'analysis',     FALSE, FALSE, FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Crop Planning & Growth'),
        'Growth Stage Monitor',     'monitoring',   TRUE,  TRUE,  TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Crop Planning & Growth'),
        'Yield Predictor',          'analysis',     FALSE, TRUE,  TRUE,  TRUE);

-- ──────────────────────────────────────
-- Category 2: Farm Operations & Automation
-- ──────────────────────────────────────

INSERT INTO agent_registry (category_id, agent_name, agent_type, requires_image, requires_sensor_data, requires_external_api, uses_memory) VALUES
    ((SELECT id FROM agent_categories WHERE category_name = 'Farm Operations & Automation'),
        'Fertilizer Advisor',       'analysis',     FALSE, TRUE,  FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farm Operations & Automation'),
        'Irrigation Scheduler',     'monitoring',   FALSE, TRUE,  TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farm Operations & Automation'),
        'Weather Watcher',          'api',          FALSE, FALSE, TRUE,  FALSE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farm Operations & Automation'),
        'Pest & Disease Detector',  'vision',       TRUE,  FALSE, FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farm Operations & Automation'),
        'Farm Equipment Manager',   'monitoring',   FALSE, FALSE, FALSE, TRUE);

-- ──────────────────────────────────────
-- Category 3: Analytics & Optimization
-- ──────────────────────────────────────

INSERT INTO agent_registry (category_id, agent_name, agent_type, requires_image, requires_sensor_data, requires_external_api, uses_memory) VALUES
    ((SELECT id FROM agent_categories WHERE category_name = 'Analytics & Optimization'),
        'Soil Health Analyzer',     'analysis',     FALSE, TRUE,  FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Analytics & Optimization'),
        'Crop Health Vision',       'vision',       TRUE,  FALSE, FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Analytics & Optimization'),
        'Water Resource Optimizer', 'analysis',     FALSE, TRUE,  TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Analytics & Optimization'),
        'Farm Analytics Dashboard', 'analysis',     FALSE, TRUE,  FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Analytics & Optimization'),
        'Carbon Footprint Tracker', 'analysis',     FALSE, TRUE,  FALSE, FALSE);

-- ──────────────────────────────────────
-- Category 4: Supply Chain & Market Access
-- ──────────────────────────────────────

INSERT INTO agent_registry (category_id, agent_name, agent_type, requires_image, requires_sensor_data, requires_external_api, uses_memory) VALUES
    ((SELECT id FROM agent_categories WHERE category_name = 'Supply Chain & Market Access'),
        'Market Intelligence',      'api',          FALSE, FALSE, TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Supply Chain & Market Access'),
        'Supply Chain Optimizer',   'analysis',     FALSE, FALSE, TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Supply Chain & Market Access'),
        'Mandi Price Predictor',    'api',          FALSE, FALSE, TRUE,  FALSE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Supply Chain & Market Access'),
        'Cold Storage Advisor',     'analysis',     FALSE, FALSE, FALSE, TRUE);

-- ──────────────────────────────────────
-- Category 5: Farmer Support & Education
-- ──────────────────────────────────────

INSERT INTO agent_registry (category_id, agent_name, agent_type, requires_image, requires_sensor_data, requires_external_api, uses_memory) VALUES
    ((SELECT id FROM agent_categories WHERE category_name = 'Farmer Support & Education'),
        'Farm Coach',               'analysis',     FALSE, FALSE, FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farmer Support & Education'),
        'Voice Assistant',          'analysis',     FALSE, FALSE, FALSE, TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farmer Support & Education'),
        'Government Scheme Advisor','api',          FALSE, FALSE, TRUE,  TRUE),
    ((SELECT id FROM agent_categories WHERE category_name = 'Farmer Support & Education'),
        'Loan & Insurance Advisor', 'analysis',     FALSE, FALSE, TRUE,  TRUE);

-- ============================================================
-- AGENT CAPABILITIES
-- ============================================================

-- Crop Selector
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'),
        'Multi-Factor Crop Recommendation', 'Analyzes soil, weather, water, market data to recommend optimal crops'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'),
        'Risk Assessment', 'Provides risk-stratified crop portfolios (safest, balanced, aggressive)');

-- Seed Recommender
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'),
        'Variety Selection', 'Recommends best seed varieties based on region, season, and soil'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'),
        'Seed Cost Optimization', 'Compares seed costs and expected yields for budget planning');

-- Growth Stage Monitor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'),
        'Growth Stage Detection', 'Identifies current crop growth stage from images and sensor data'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'),
        'Growth Anomaly Alert', 'Detects growth anomalies and suggests corrective actions');

-- Yield Predictor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'),
        'Yield Forecasting', 'Predicts expected yield using historical data and current conditions'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'),
        'Revenue Estimation', 'Estimates expected revenue based on predicted yield and market prices');

-- Fertilizer Advisor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'),
        'NPK Recommendation', 'Calculates optimal NPK ratios from soil sensor data'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'),
        'Application Schedule', 'Creates fertilizer application timeline per growth stage');

-- Irrigation Scheduler
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'),
        'Water Scheduling', 'Generates irrigation schedules from soil moisture and weather forecasts'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'),
        'Deficit Alerts', 'Alerts when soil moisture drops below critical thresholds');

-- Weather Watcher
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'),
        'Weather Forecasting', 'Fetches and interprets weather forecasts for farm locations'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'),
        'Extreme Weather Alerts', 'Sends alerts for storms, frost, heatwaves, and heavy rain');

-- Pest & Disease Detector
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'),
        'Disease Identification', 'Identifies crop diseases from leaf/stem/fruit images'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'),
        'Treatment Recommendation', 'Suggests organic and chemical treatment options');

-- Farm Equipment Manager
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'),
        'Maintenance Scheduling', 'Tracks equipment maintenance schedules and reminders'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'),
        'Usage Optimization', 'Recommends optimal equipment usage patterns');

-- Soil Health Analyzer
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'),
        'Soil Profile Analysis', 'Comprehensive soil health report from sensor and test data'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'),
        'Amendment Recommendations', 'Suggests soil amendments to improve health metrics');

-- Crop Health Vision
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'),
        'Visual Health Assessment', 'Assesses crop health from images using computer vision'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'),
        'Deficiency Detection', 'Detects nutrient deficiencies from leaf color and texture patterns');

-- Water Resource Optimizer
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'),
        'Water Budget Planning', 'Plans water usage across the season based on crop needs and availability'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'),
        'Efficiency Analysis', 'Analyzes irrigation efficiency and suggests improvements');

-- Farm Analytics Dashboard
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'),
        'KPI Tracking', 'Tracks key farm performance indicators over time'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'),
        'Comparative Analytics', 'Compares farm performance against regional benchmarks');

-- Carbon Footprint Tracker
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'),
        'Emission Estimation', 'Estimates carbon emissions from farm operations'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'),
        'Sustainability Score', 'Computes and tracks a farm sustainability score');

-- Market Intelligence
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'),
        'Price Trend Analysis', 'Analyzes historical and current market price trends'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'),
        'Demand Forecasting', 'Forecasts crop demand for upcoming seasons');

-- Supply Chain Optimizer
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'),
        'Logistics Planning', 'Optimizes transport routes and timing for produce delivery'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'),
        'Buyer Matching', 'Matches farmers with optimal buyers based on crop type and location');

-- Mandi Price Predictor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'),
        'Price Prediction', 'Predicts mandi prices for next 7-30 days using ML models'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'),
        'Best Sell Window', 'Recommends optimal time to sell for maximum profit');

-- Cold Storage Advisor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'),
        'Storage Recommendations', 'Recommends cold storage options based on crop type and volume'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'),
        'Cost-Benefit Analysis', 'Analyzes storage costs vs. expected price appreciation');

-- Farm Coach
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'),
        'Personalized Guidance', 'Provides personalized farming advice based on conversation history'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'),
        'Best Practice Education', 'Teaches modern farming best practices in local context');

-- Voice Assistant
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'),
        'Voice Interaction', 'Handles voice input/output for farmers with limited literacy'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'),
        'Multilingual Support', 'Supports conversations in multiple regional languages');

-- Government Scheme Advisor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'),
        'Scheme Discovery', 'Finds applicable government schemes based on farmer profile'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'),
        'Application Assistance', 'Guides farmers through scheme application processes');

-- Loan & Insurance Advisor
INSERT INTO agent_capabilities (agent_id, capability_name, description) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'),
        'Loan Comparison', 'Compares agricultural loan options from various banks'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'),
        'Insurance Advisory', 'Recommends crop insurance plans based on risk profile');

-- ============================================================
-- ORCHESTRATOR ROUTING KEYWORDS
-- ============================================================

-- Crop Selector
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'crop'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'which crop'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'what to grow'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'crop selection'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'best crop'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Selector'), 'recommend crop');

-- Seed Recommender
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'), 'seed'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'), 'variety'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'), 'seed type'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'), 'best seed'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Seed Recommender'), 'seed recommendation');

-- Growth Stage Monitor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'), 'growth'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'), 'growth stage'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'), 'plant stage'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'), 'crop stage'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Growth Stage Monitor'), 'maturity');

-- Yield Predictor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'), 'yield'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'), 'harvest prediction'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'), 'expected yield'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Yield Predictor'), 'production estimate');

-- Fertilizer Advisor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'), 'fertilizer'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'), 'npk'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'), 'urea'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'), 'nutrient'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Fertilizer Advisor'), 'manure');

-- Irrigation Scheduler
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'), 'irrigation'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'), 'water schedule'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'), 'watering'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'), 'drip'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Irrigation Scheduler'), 'sprinkler');

-- Weather Watcher
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'), 'weather'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'), 'rain'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'), 'forecast'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'), 'temperature'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Weather Watcher'), 'storm');

-- Pest & Disease Detector
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'pest'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'disease'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'insect'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'leaf spot'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'blight'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Pest & Disease Detector'), 'fungus');

-- Farm Equipment Manager
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'), 'equipment'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'), 'tractor'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'), 'machinery'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Equipment Manager'), 'maintenance');

-- Soil Health Analyzer
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'), 'soil'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'), 'soil health'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'), 'soil test'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'), 'ph level'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Soil Health Analyzer'), 'organic matter');

-- Crop Health Vision
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'), 'crop health'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'), 'leaf image'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'), 'plant health'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Crop Health Vision'), 'scan crop');

-- Water Resource Optimizer
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'), 'water resource'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'), 'water management'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'), 'water efficiency'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Water Resource Optimizer'), 'water budget');

-- Farm Analytics Dashboard
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'), 'analytics'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'), 'dashboard'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'), 'performance'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'), 'report'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Analytics Dashboard'), 'statistics');

-- Carbon Footprint Tracker
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'), 'carbon'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'), 'emission'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'), 'sustainability'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Carbon Footprint Tracker'), 'green farming');

-- Market Intelligence
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'), 'market'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'), 'price trend'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'), 'demand'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Market Intelligence'), 'market analysis');

-- Supply Chain Optimizer
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'), 'supply chain'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'), 'logistics'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'), 'transport'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Supply Chain Optimizer'), 'buyer');

-- Mandi Price Predictor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'), 'mandi'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'), 'mandi price'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'), 'sell price'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Mandi Price Predictor'), 'when to sell');

-- Cold Storage Advisor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'), 'cold storage'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'), 'storage'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'), 'preserve'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Cold Storage Advisor'), 'refrigeration');

-- Farm Coach
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'), 'advice'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'), 'guide'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'), 'help'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'), 'best practice'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Farm Coach'), 'farming tips');

-- Voice Assistant
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'), 'voice'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'), 'speak'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'), 'talk'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Voice Assistant'), 'audio');

-- Government Scheme Advisor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'), 'scheme'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'), 'subsidy'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'), 'government'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'), 'pm kisan'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Government Scheme Advisor'), 'yojana');

-- Loan & Insurance Advisor
INSERT INTO agent_keywords (agent_id, keyword) VALUES
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'), 'loan'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'), 'insurance'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'), 'credit'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'), 'kcc'),
    ((SELECT id FROM agent_registry WHERE agent_name = 'Loan & Insurance Advisor'), 'crop insurance');

COMMIT;
