-- Create farm_profiles table for storing onboarding data
-- Migration: Add farm profiles table

CREATE TABLE IF NOT EXISTS farm_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic Farm Information
    farm_name VARCHAR(255),
    farm_size VARCHAR(100),
    farm_size_unit VARCHAR(20),
    location VARCHAR(255),
    state VARCHAR(100),
    district VARCHAR(100),
    village VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Soil Information
    soil_type VARCHAR(100),
    soil_ph VARCHAR(20),
    soil_organic_matter VARCHAR(50),
    soil_texture VARCHAR(100),
    soil_drainage VARCHAR(100),
    
    -- Water Source
    water_source VARCHAR(100),
    irrigation_method VARCHAR(100),
    water_availability VARCHAR(100),
    
    -- Crop Information
    primary_crops JSONB,
    crop_rotation VARCHAR(100),
    cropping_season VARCHAR(100),
    specific_crop VARCHAR(255),
    
    -- Farming Practices
    farming_experience VARCHAR(100),
    labor_setup VARCHAR(100),
    machinery JSONB,
    
    -- Sustainability Practices
    sustainability_focus JSONB,
    pest_management VARCHAR(100),
    fertilizer_approach VARCHAR(100),
    
    -- Technology & Goals
    tech_comfort VARCHAR(100),
    farm_goals JSONB,
    challenges VARCHAR(500),
    
    -- Additional Information
    additional_info TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_farm_profiles_user_id ON farm_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_farm_profiles_state ON farm_profiles(state);
CREATE INDEX IF NOT EXISTS idx_farm_profiles_created_at ON farm_profiles(created_at);

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_farm_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER farm_profiles_updated_at_trigger
    BEFORE UPDATE ON farm_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_farm_profiles_updated_at();

-- Add comment
COMMENT ON TABLE farm_profiles IS 'Stores comprehensive farm profile data from user onboarding';
