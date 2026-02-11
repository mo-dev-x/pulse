-- ============================================
-- PULSE DATABASE SCHEMA
-- ============================================
-- 
-- Privacy-First Campus Wellness Platform
-- Created: 2026-02-10
-- 
-- IMPORTANT PRIVACY NOTES:
-- 1. Anonymous posts store user_id but API never exposes it
-- 2. Aggregates require ≥10 posts before showing mood data
-- 3. No individual emotional tracking
-- 
-- ============================================

-- Create database (if running manually)
-- CREATE DATABASE IF NOT EXISTS pulse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE pulse_db;

-- ============================================
-- USERS & IDENTITY
-- ============================================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Public identity
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    profile_picture VARCHAR(500),
    
    -- Anonymous identity (persistent pseudonym)
    pseudonym VARCHAR(50) NOT NULL DEFAULT 'anonymous',
    pseudonym_last_changed TIMESTAMP NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Indexes for fast lookups
    INDEX idx_email (email),
    INDEX idx_username (username),
    
    -- Constraints
    CONSTRAINT chk_username_length CHECK (CHAR_LENGTH(username) >= 3),
    CONSTRAINT chk_pseudonym_length CHECK (CHAR_LENGTH(pseudonym) >= 3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- SOCIAL GRAPH
-- ============================================

CREATE TABLE followers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    follower_id INT NOT NULL,   -- User who clicks "follow"
    following_id INT NOT NULL,  -- User being followed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Constraints
    UNIQUE KEY unique_follow (follower_id, following_id),
    CHECK (follower_id != following_id),  -- Prevent self-follow
    
    -- Indexes for feed generation
    INDEX idx_follower (follower_id),
    INDEX idx_following (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- CONTENT
-- ============================================

CREATE TABLE campus_zones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    zone_type ENUM('academic', 'residence', 'social', 'sports', 'dining', 'other') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_zone_type (zone_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Author (ALWAYS stored, even for anonymous posts)
    -- This enables "My Anonymous Posts" view and deletion
    user_id INT NOT NULL,
    
    -- Location context
    zone_id INT NULL,
    
    -- Content
    content TEXT NOT NULL,
    
    -- Privacy mode
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- NLP analysis results
    sentiment_score DECIMAL(3,2),  -- -1.00 to 1.00
    sentiment_label ENUM('positive', 'neutral', 'negative'),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id) ON DELETE SET NULL,
    
    -- Indexes for common queries
    INDEX idx_user_posts (user_id, created_at DESC),
    INDEX idx_user_anonymous (user_id, is_anonymous),
    INDEX idx_zone_recent (zone_id, created_at DESC),
    INDEX idx_public_recent (is_anonymous, created_at DESC),
    INDEX idx_sentiment_date (sentiment_label, created_at),
    
    -- Constraints
    CONSTRAINT chk_content_length CHECK (CHAR_LENGTH(content) >= 10 AND CHAR_LENGTH(content) <= 500),
    CONSTRAINT chk_sentiment_range CHECK (sentiment_score >= -1.00 AND sentiment_score <= 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type ENUM('image', 'audio', 'video') NOT NULL,
    file_size INT NOT NULL,  -- bytes
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    INDEX idx_post_media (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- INTERACTIONS
-- ============================================

CREATE TABLE reactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    emoji VARCHAR(10) NOT NULL,  -- Unicode emoji
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- One reaction per user per post
    UNIQUE KEY unique_user_post_reaction (user_id, post_id),
    
    -- Indexes
    INDEX idx_post_reactions (post_id),
    INDEX idx_user_reactions (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- ANALYTICS (Privacy-Safe Aggregates)
-- ============================================

CREATE TABLE daily_aggregates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    zone_id INT NULL,  -- NULL = campus-wide aggregate
    
    -- Counts
    total_posts INT NOT NULL DEFAULT 0,
    positive_count INT NOT NULL DEFAULT 0,
    neutral_count INT NOT NULL DEFAULT 0,
    negative_count INT NOT NULL DEFAULT 0,
    
    -- Statistics
    avg_sentiment DECIMAL(3,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_daily_zone (date, zone_id),
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_date_zone (date, zone_id),
    INDEX idx_date (date),
    
    -- Validation
    CONSTRAINT chk_counts_non_negative CHECK (
        total_posts >= 0 AND 
        positive_count >= 0 AND 
        neutral_count >= 0 AND 
        negative_count >= 0
    ),
    CONSTRAINT chk_total_equals_sum CHECK (
        total_posts = positive_count + neutral_count + negative_count
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE weekly_aggregates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    zone_id INT NULL,
    
    total_posts INT NOT NULL DEFAULT 0,
    positive_count INT NOT NULL DEFAULT 0,
    neutral_count INT NOT NULL DEFAULT 0,
    negative_count INT NOT NULL DEFAULT 0,
    avg_sentiment DECIMAL(3,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_weekly_zone (week_start, zone_id),
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id) ON DELETE CASCADE,
    
    INDEX idx_week_zone (week_start, zone_id),
    
    CONSTRAINT chk_week_order CHECK (week_end >= week_start),
    CONSTRAINT chk_weekly_counts_non_negative CHECK (
        total_posts >= 0 AND 
        positive_count >= 0 AND 
        neutral_count >= 0 AND 
        negative_count >= 0
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    zone_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id) ON DELETE SET NULL,
    INDEX idx_event_date (event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================
-- SEED DATA (Campus Zones)
-- ============================================

INSERT INTO campus_zones (name, description, zone_type) VALUES
('Library', 'Main campus library and study spaces', 'academic'),
('Engineering Building', 'Engineering classrooms and labs', 'academic'),
('Student Center', 'Common area, cafeteria, student services', 'social'),
('Residence Hall A', 'Main residential building', 'residence'),
('Residence Hall B', 'Second residential building', 'residence'),
('Gym & Recreation Center', 'Fitness facilities and sports courts', 'sports'),
('Cafeteria', 'Main dining hall', 'dining'),
('Outdoor Commons', 'Lawn areas, benches, outdoor seating', 'social'),
('Computer Lab', 'Computer science and tech labs', 'academic'),
('Arts Building', 'Music, theater, visual arts spaces', 'academic');


-- ============================================
-- VIEWS (For Common Queries)
-- ============================================

-- View: Friends (mutual follows)
CREATE OR REPLACE VIEW friends_view AS
SELECT 
    f1.follower_id AS user_id,
    f1.following_id AS friend_id,
    u.username AS friend_username,
    u.display_name AS friend_display_name,
    u.profile_picture AS friend_profile_picture,
    f1.created_at AS friendship_date
FROM followers f1
INNER JOIN followers f2 
    ON f1.follower_id = f2.following_id 
    AND f1.following_id = f2.follower_id
INNER JOIN users u 
    ON f1.following_id = u.id;


-- ============================================
-- STORED PROCEDURES (Optional - For Future)
-- ============================================

-- Procedure to safely increment reaction count
DELIMITER //
CREATE PROCEDURE add_reaction(
    IN p_post_id INT,
    IN p_user_id INT,
    IN p_emoji VARCHAR(10)
)
BEGIN
    INSERT INTO reactions (post_id, user_id, emoji)
    VALUES (p_post_id, p_user_id, p_emoji)
    ON DUPLICATE KEY UPDATE 
        emoji = p_emoji,
        created_at = CURRENT_TIMESTAMP;
END //
DELIMITER ;


-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify schema is correct:

-- SELECT 'Tables created:' AS status;
-- SHOW TABLES;

-- SELECT 'Campus zones seeded:' AS status;
-- SELECT COUNT(*) AS zone_count FROM campus_zones;

-- SELECT 'Indexes created:' AS status;
-- SHOW INDEX FROM posts;

-- SELECT 'Foreign keys:' AS status;
-- SELECT 
--     TABLE_NAME,
--     CONSTRAINT_NAME,
--     REFERENCED_TABLE_NAME
-- FROM information_schema.KEY_COLUMN_USAGE
-- WHERE TABLE_SCHEMA = 'pulse_db'
-- AND REFERENCED_TABLE_NAME IS NOT NULL;
