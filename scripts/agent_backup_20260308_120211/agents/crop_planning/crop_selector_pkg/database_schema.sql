-- Database Schema for Crop Selector Agent
-- PostgreSQL schema for storing crop recommendations and agent outputs

-- Farmers table
CREATE TABLE farmers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20),
    state VARCHAR(50),
    district VARCHAR(50),
    village VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crop recommendations table
CREATE TABLE crop_recommendations (
    id VARCHAR(50) PRIMARY KEY,
    farmer_id VARCHAR(50) REFERENCES farmers(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    season VARCHAR(20),
    land_size_acre DECIMAL(10,2),
    risk_preference VARCHAR(20),
    
    -- Agent outputs (JSON)
    weather_output JSONB,
    soil_output JSONB,
    water_output JSONB,
    pest_output JSONB,
    market_output JSONB,
    government_output JSONB,
    
    -- Results (JSON)
    recommendations JSONB,
    risk_assessment JSONB,
    reasoning JSONB,
    
    -- Metadata
    processing_time_ms DECIMAL(10,2),
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent performance metrics
CREATE TABLE agent_performance (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms DECIMAL(10,2),
    success BOOLEAN,
    error_message TEXT,
    input_hash VARCHAR(64)
);

-- Crop outcomes tracking (for learning)
CREATE TABLE crop_outcomes (
    id SERIAL PRIMARY KEY,
    recommendation_id VARCHAR(50) REFERENCES crop_recommendations(id),
    farmer_id VARCHAR(50) REFERENCES farmers(id),
    actual_crop_planted VARCHAR(100),
    yield_tonnes DECIMAL(10,2),
    revenue_inr DECIMAL(10,2),
    success_rating INTEGER CHECK (success_rating >= 1 AND success_rating <= 5),
    challenges TEXT,
    feedback TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_recommendations_farmer_id ON crop_recommendations(farmer_id);
CREATE INDEX idx_recommendations_timestamp ON crop_recommendations(timestamp);
CREATE INDEX idx_recommendations_season ON crop_recommendations(season);
CREATE INDEX idx_recommendations_state ON crop_recommendations(farmer_id) WHERE farmers.state IS NOT NULL;

CREATE INDEX idx_outcomes_recommendation_id ON crop_outcomes(recommendation_id);
CREATE INDEX idx_outcomes_farmer_id ON crop_outcomes(farmer_id);

-- Sample queries for analytics

-- Get recommendations by state and season
SELECT 
    f.state,
    cr.season,
    COUNT(*) as total_recommendations,
    AVG(cr.confidence_score) as avg_confidence
FROM crop_recommendations cr
JOIN farmers f ON cr.farmer_id = f.id
GROUP BY f.state, cr.season
ORDER BY total_recommendations DESC;

-- Get most recommended crops
SELECT 
    jsonb_array_elements(recommendations->'safest')->>'crop' as crop,
    COUNT(*) as frequency
FROM crop_recommendations
WHERE recommendations->'safested' IS NOT NULL
GROUP BY crop
ORDER BY frequency DESC;

-- Agent performance metrics
SELECT 
    agent_name,
    AVG(processing_time_ms) as avg_processing_time,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE success = true) as successful_calls
FROM agent_performance
GROUP BY agent_name
ORDER BY avg_processing_time;
