-- Agriculture Insights Platform Database Schema
-- Execute these queries in your Supabase SQL editor

-- Enable Row Level Security (RLS)
-- This will be enabled after creating tables

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(name) >= 2),
    email TEXT UNIQUE NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    role TEXT NOT NULL CHECK (role IN ('farmer', 'agronomist', 'researcher')),
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 2. Farmers table
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    location TEXT NOT NULL CHECK (length(location) >= 2),
    crops TEXT DEFAULT '[]', -- JSON string of crops array
    acres FLOAT NOT NULL CHECK (acres > 0),
    contact_number TEXT,
    soil_data JSONB DEFAULT '{}',
    water_level FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 3. Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    crop TEXT NOT NULL CHECK (length(crop) >= 2),
    prediction FLOAT NOT NULL CHECK (prediction >= 0),
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    input_data JSONB DEFAULT '{}',
    model_version TEXT DEFAULT '1.0',
    validated_by_agronomist BOOLEAN DEFAULT false,
    agronomist_comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 4. Research Data table
CREATE TABLE IF NOT EXISTS research_data (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) >= 5),
    description TEXT,
    aggregated_results JSONB DEFAULT '{}',
    ndvi_scores JSONB DEFAULT '{}',
    yield_predictions JSONB DEFAULT '{}',
    region TEXT,
    crop_type TEXT,
    season TEXT,
    data_source TEXT DEFAULT 'system_generated',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 5. Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL CHECK (alert_type IN ('irrigation', 'pest', 'weather', 'disease')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title TEXT NOT NULL CHECK (length(title) >= 5),
    message TEXT NOT NULL CHECK (length(message) >= 10),
    recommendations JSONB DEFAULT '[]',
    is_read BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_farmers_user_id ON farmers(user_id);
CREATE INDEX IF NOT EXISTS idx_farmers_location ON farmers(location);
CREATE INDEX IF NOT EXISTS idx_predictions_farmer_id ON predictions(farmer_id);
CREATE INDEX IF NOT EXISTS idx_predictions_crop ON predictions(crop);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_farmer_id ON alerts(farmer_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type_severity ON alerts(alert_type, severity);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read) WHERE is_read = false;
CREATE INDEX IF NOT EXISTS idx_research_data_region ON research_data(region);
CREATE INDEX IF NOT EXISTS idx_research_data_crop_type ON research_data(crop_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_farmers_updated_at BEFORE UPDATE ON farmers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_data_updated_at BEFORE UPDATE ON research_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE farmers ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Users: Users can only see their own profile
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Farmers: Farmers can only see their own data, agronomists and researchers can see all
CREATE POLICY "Farmers can view own data" ON farmers
    FOR SELECT USING (
        user_id = auth.uid()::integer OR
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::integer 
            AND role IN ('agronomist', 'researcher')
        )
    );

CREATE POLICY "Farmers can update own data" ON farmers
    FOR UPDATE USING (user_id = auth.uid()::integer);

CREATE POLICY "Farmers can insert own data" ON farmers
    FOR INSERT WITH CHECK (user_id = auth.uid()::integer);

-- Predictions: Farmers see own, agronomists and researchers see all
CREATE POLICY "View predictions policy" ON predictions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM farmers 
            WHERE id = predictions.farmer_id 
            AND user_id = auth.uid()::integer
        ) OR
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::integer 
            AND role IN ('agronomist', 'researcher')
        )
    );

CREATE POLICY "Insert predictions policy" ON predictions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM farmers 
            WHERE id = predictions.farmer_id 
            AND user_id = auth.uid()::integer
        )
    );

CREATE POLICY "Update predictions policy" ON predictions
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::integer 
            AND role = 'agronomist'
        )
    );

-- Alerts: Farmers see own, agronomists see all
CREATE POLICY "View alerts policy" ON alerts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM farmers 
            WHERE id = alerts.farmer_id 
            AND user_id = auth.uid()::integer
        ) OR
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::integer 
            AND role IN ('agronomist', 'researcher')
        )
    );

CREATE POLICY "Update alerts policy" ON alerts
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM farmers 
            WHERE id = alerts.farmer_id 
            AND user_id = auth.uid()::integer
        )
    );

-- Research Data: Only researchers can manage
CREATE POLICY "Research data policy" ON research_data
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid()::integer 
            AND role = 'researcher'
        )
    );

-- Insert some sample data for testing
INSERT INTO users (name, email, role, password_hash) VALUES
('John Farmer', 'john.farmer@example.com', 'farmer', 'hashed_password_1'),
('Jane Agronomist', 'jane.agronomist@example.com', 'agronomist', 'hashed_password_2'),
('Bob Researcher', 'bob.researcher@example.com', 'researcher', 'hashed_password_3')
ON CONFLICT (email) DO NOTHING;

-- Insert sample farmer data
INSERT INTO farmers (user_id, location, crops, acres, soil_data, water_level)
SELECT 
    u.id,
    'Sample Farm Location',
    '["corn", "wheat", "soybeans"]',
    25.5,
    '{"ph": 6.8, "nitrogen": 45, "phosphorus": 22, "potassium": 180}'::jsonb,
    65.0
FROM users u
WHERE u.email = 'john.farmer@example.com'
ON CONFLICT (user_id) DO NOTHING;