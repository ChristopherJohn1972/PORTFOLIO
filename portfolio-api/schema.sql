-- ============================================
-- PORTFOLIO BACKEND — DATABASE SCHEMA
-- PostgreSQL
-- ============================================
-- Run this manually or let Django migrations
-- create the tables automatically.
-- ============================================

-- Contact form submissions
CREATE TABLE IF NOT EXISTS contact_requests (
    id              SERIAL PRIMARY KEY,
    request_id      VARCHAR(36) UNIQUE NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    company         VARCHAR(255) NOT NULL,
    email           VARCHAR(254) NOT NULL,
    opportunity_type VARCHAR(50) NOT NULL,
    position        VARCHAR(255),
    message         TEXT NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    ip_address      INET,
    user_agent      TEXT,
    honeypot_hit    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- CV request submissions
CREATE TABLE IF NOT EXISTS cv_requests (
    id              SERIAL PRIMARY KEY,
    request_id      VARCHAR(36) UNIQUE NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    company         VARCHAR(255) NOT NULL,
    email           VARCHAR(254) NOT NULL,
    position        VARCHAR(255) NOT NULL,
    message         TEXT,
    status          VARCHAR(20) DEFAULT 'pending',
    ip_address      INET,
    user_agent      TEXT,
    honeypot_hit    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Project link request submissions
CREATE TABLE IF NOT EXISTS project_link_requests (
    id              SERIAL PRIMARY KEY,
    request_id      VARCHAR(36) UNIQUE NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    company         VARCHAR(255) NOT NULL,
    email           VARCHAR(254) NOT NULL,
    projects        TEXT[] NOT NULL,
    message         TEXT,
    status          VARCHAR(20) DEFAULT 'pending',
    ip_address      INET,
    user_agent      TEXT,
    honeypot_hit    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Security and audit log
CREATE TABLE IF NOT EXISTS security_logs (
    id              SERIAL PRIMARY KEY,
    event_id        VARCHAR(36) UNIQUE NOT NULL,
    event_type      VARCHAR(50) NOT NULL,
    endpoint        VARCHAR(500) NOT NULL,
    http_method     VARCHAR(10) NOT NULL,
    http_status     SMALLINT,
    result          VARCHAR(20) NOT NULL DEFAULT 'allowed',
    ip_address      INET,
    user_agent      TEXT,
    detail          TEXT,
    request_id      VARCHAR(36),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contact_requests_created ON contact_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_contact_requests_status ON contact_requests(status);
CREATE INDEX IF NOT EXISTS idx_cv_requests_created ON cv_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_cv_requests_status ON cv_requests(status);
CREATE INDEX IF NOT EXISTS idx_project_link_requests_created ON project_link_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_project_link_requests_status ON project_link_requests(status);
CREATE INDEX IF NOT EXISTS idx_security_logs_created ON security_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_result ON security_logs(result);
CREATE INDEX IF NOT EXISTS idx_security_logs_ip ON security_logs(ip_address);

-- Admin users table (handled by Django auth, shown for reference)
-- Django creates: auth_user, django_content_type, django_session, etc.

-- Admin tokens for API authentication
CREATE TABLE IF NOT EXISTS admin_tokens (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    token           VARCHAR(64) UNIQUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- RETENTION POLICY (run periodically)
-- ============================================
-- Normal logs older than 30 days:
-- DELETE FROM security_logs
-- WHERE created_at < NOW() - INTERVAL '30 days'
--   AND result = 'allowed'
--   AND event_type NOT IN ('rate_limit_exceeded', 'honeypot_triggered');
--
-- Suspicious events retained for 90 days:
-- DELETE FROM security_logs
-- WHERE created_at < NOW() - INTERVAL '90 days'
--   AND event_type IN ('rate_limit_exceeded', 'honeypot_triggered', 'suspicious_request');
--
-- Old requests retained for 180 days:
-- DELETE FROM contact_requests WHERE created_at < NOW() - INTERVAL '180 days';
-- DELETE FROM cv_requests WHERE created_at < NOW() - INTERVAL '180 days';
-- DELETE FROM project_link_requests WHERE created_at < NOW() - INTERVAL '180 days';
