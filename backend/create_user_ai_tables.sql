-- Migration script for User AI-extracted information and scanned documents tables
-- Execute this script to add the new tables to your PostgreSQL database

-- Create user_ai_extracted_info table
CREATE TABLE user_ai_extracted_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Extracted personal information
    extracted_first_name VARCHAR(100),
    extracted_last_name VARCHAR(100),
    extracted_cnp VARCHAR(13),
    extracted_address TEXT,
    extracted_phone VARCHAR(20),
    extracted_birth_date DATE,
    extracted_birth_place VARCHAR(255),
    extracted_nationality VARCHAR(100),
    extracted_id_series VARCHAR(10),
    extracted_id_number VARCHAR(20),
    extracted_issued_by VARCHAR(255),
    extracted_issue_date DATE,
    extracted_expiry_date DATE,
    
    -- Source document information
    source_document_type VARCHAR(50), -- "carte_identitate", "pasaport", "certificat_nastere", etc.
    source_document_path TEXT,
    extraction_confidence DECIMAL(5,4), -- 0.0 - 1.0
    
    -- AI processing metadata
    extracted_data_raw JSONB, -- Raw AI response
    processing_notes TEXT,
    ai_model_used VARCHAR(50) DEFAULT 'gemini-2.0-flash',
    
    -- Status tracking
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    verification_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_scanned_documents table
CREATE TABLE user_scanned_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Document information
    original_filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50), -- Category detected by AI
    title VARCHAR(255), -- AI-generated title
    description TEXT, -- AI-generated description
    
    -- File storage
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    
    -- OCR results
    transcribed_text TEXT, -- Full OCR text
    metadata_json JSONB, -- Structured metadata from AI
    confidence_score DECIMAL(5,4), -- Overall OCR confidence
    
    -- AI processing
    ai_model_used VARCHAR(50) DEFAULT 'gemini-2.0-flash',
    processing_time DECIMAL(8,3), -- Seconds
    
    -- Status
    processing_status VARCHAR(20) DEFAULT 'completed', -- processing, completed, failed
    error_message TEXT,
    
    -- Privacy and access
    is_private BOOLEAN DEFAULT TRUE, -- User-specific by default
    shared_with_officials BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_user_ai_extracted_info_user_id ON user_ai_extracted_info(user_id);
CREATE INDEX idx_user_ai_extracted_info_created_at ON user_ai_extracted_info(created_at);
CREATE INDEX idx_user_ai_extracted_info_verification ON user_ai_extracted_info(verification_status);
CREATE INDEX idx_user_ai_extracted_info_document_type ON user_ai_extracted_info(source_document_type);

CREATE INDEX idx_user_scanned_documents_user_id ON user_scanned_documents(user_id);
CREATE INDEX idx_user_scanned_documents_created_at ON user_scanned_documents(created_at);
CREATE INDEX idx_user_scanned_documents_type ON user_scanned_documents(document_type);
CREATE INDEX idx_user_scanned_documents_status ON user_scanned_documents(processing_status);

-- Add constraints
ALTER TABLE user_ai_extracted_info 
ADD CONSTRAINT chk_verification_status 
CHECK (verification_status IN ('pending', 'approved', 'rejected'));

ALTER TABLE user_ai_extracted_info 
ADD CONSTRAINT chk_extraction_confidence 
CHECK (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0);

ALTER TABLE user_scanned_documents 
ADD CONSTRAINT chk_processing_status 
CHECK (processing_status IN ('processing', 'completed', 'failed'));

ALTER TABLE user_scanned_documents 
ADD CONSTRAINT chk_confidence_score 
CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0);

-- Update existing users table if needed (add missing columns)
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cnp VARCHAR(13);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_ai_extracted_info_updated_at 
    BEFORE UPDATE ON user_ai_extracted_info 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_scanned_documents_updated_at 
    BEFORE UPDATE ON user_scanned_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some example document types for reference
INSERT INTO document_categories (name, description, icon, color) VALUES
('Carte de Identitate', 'Documente de identitate românești', 'id-card', '#3B82F6'),
('Pașaport', 'Pașapoarte românești și străine', 'passport', '#10B981'),
('Certificat Naștere', 'Certificate de naștere', 'certificate', '#F59E0B'),
('Permis Conducere', 'Permise de conducere', 'car', '#EF4444'),
('Document Personal', 'Alte documente personale', 'document', '#8B5CF6')
ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_ai_extracted_info TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_scanned_documents TO your_app_user;

COMMENT ON TABLE user_ai_extracted_info IS 'AI-extracted personal information from scanned documents';
COMMENT ON TABLE user_scanned_documents IS 'User-uploaded and scanned documents with OCR processing results';
COMMENT ON COLUMN user_ai_extracted_info.extraction_confidence IS 'AI confidence score for extraction accuracy (0.0-1.0)';
COMMENT ON COLUMN user_scanned_documents.confidence_score IS 'Overall OCR confidence score (0.0-1.0)';
COMMENT ON COLUMN user_ai_extracted_info.extracted_data_raw IS 'Raw JSON response from AI processing';
COMMENT ON COLUMN user_scanned_documents.metadata_json IS 'Structured metadata extracted by AI'; 