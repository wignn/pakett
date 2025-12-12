-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Packages table (raw ingest from devices)
CREATE TABLE IF NOT EXISTS packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id VARCHAR(50) UNIQUE NOT NULL,
    device_id VARCHAR(50),
    operator_id VARCHAR(50),
    ocr_text TEXT,
    ocr_confidence FLOAT,
    image_path TEXT,
    priority VARCHAR(20) DEFAULT 'standard',
    status VARCHAR(30) DEFAULT 'pending',
    gps_lat DOUBLE PRECISION,
    gps_lon DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Addresses table (normalized & geocoded)
CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id UUID REFERENCES packages(id) ON DELETE CASCADE,
    raw_text TEXT NOT NULL,
    street VARCHAR(255),
    house_number VARCHAR(30),
    rt VARCHAR(10),
    rw VARCHAR(10),
    neighborhood VARCHAR(100),  -- Kelurahan
    subdistrict VARCHAR(100),   -- Kecamatan
    city VARCHAR(100),          -- Kota/Kabupaten
    province VARCHAR(100),
    postal_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'Indonesia',
    location GEOGRAPHY(POINT, 4326),
    geocode_confidence FLOAT,
    geocode_source VARCHAR(50),
    requires_verification BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    verified_by VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) DEFAULT 'motorcycle',
    capacity INT DEFAULT 50,
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    start_lat DOUBLE PRECISION,
    start_lon DOUBLE PRECISION,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Routes table (VRP solutions)
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID REFERENCES vehicles(id),
    planned_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'planned',
    total_distance_km FLOAT,
    total_time_minutes INT,
    total_stops INT,
    optimization_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Route stops (ordered sequence of deliveries)
CREATE TABLE IF NOT EXISTS route_stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    package_id UUID REFERENCES packages(id),
    address_id UUID REFERENCES addresses(id),
    sequence_order INT NOT NULL,
    estimated_arrival TIMESTAMPTZ,
    actual_arrival TIMESTAMPTZ,
    estimated_service_time_minutes INT DEFAULT 5,
    actual_service_time_minutes INT,
    status VARCHAR(30) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Geocode cache table
CREATE TABLE IF NOT EXISTS geocode_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_hash VARCHAR(64) UNIQUE NOT NULL,
    normalized_address TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    place_id VARCHAR(100),
    confidence FLOAT,
    source VARCHAR(50),
    response_json JSONB,
    hit_count INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW()
);

-- Telemetry table (for ML training data)
CREATE TABLE IF NOT EXISTS delivery_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_stop_id UUID REFERENCES route_stops(id),
    event_type VARCHAR(30) NOT NULL,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    metadata JSONB
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_packages_status ON packages(status);
CREATE INDEX IF NOT EXISTS idx_packages_created_at ON packages(created_at);
CREATE INDEX IF NOT EXISTS idx_packages_package_id ON packages(package_id);

CREATE INDEX IF NOT EXISTS idx_addresses_location ON addresses USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_addresses_package_id ON addresses(package_id);
CREATE INDEX IF NOT EXISTS idx_addresses_postal_code ON addresses(postal_code);
CREATE INDEX IF NOT EXISTS idx_addresses_city ON addresses(city);

CREATE INDEX IF NOT EXISTS idx_routes_planned_date ON routes(planned_date);
CREATE INDEX IF NOT EXISTS idx_routes_vehicle_id ON routes(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(status);

CREATE INDEX IF NOT EXISTS idx_route_stops_route_id ON route_stops(route_id);
CREATE INDEX IF NOT EXISTS idx_route_stops_sequence ON route_stops(route_id, sequence_order);

CREATE INDEX IF NOT EXISTS idx_geocode_cache_hash ON geocode_cache(address_hash);
CREATE INDEX IF NOT EXISTS idx_geocode_cache_last_used ON geocode_cache(last_used_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_packages_updated_at BEFORE UPDATE ON packages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addresses_updated_at BEFORE UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_route_stops_updated_at BEFORE UPDATE ON route_stops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample vehicle for testing
INSERT INTO vehicles (vehicle_id, vehicle_type, capacity, driver_name, start_lat, start_lon)
VALUES 
    ('V001', 'motorcycle', 30, 'Driver A', -6.2088, 106.8456),
    ('V002', 'motorcycle', 30, 'Driver B', -6.2088, 106.8456),
    ('V003', 'van', 100, 'Driver C', -6.2088, 106.8456)
ON CONFLICT (vehicle_id) DO NOTHING;
