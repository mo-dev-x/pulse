-- ============================================
-- PULSE DATABASE SCHEMA
-- ============================================
-- 
-- Privacy-First Campus Wellness Platform
-- Created: 2026-02-10
-- 
-- IMPORTANT PRIVACY NOTES:
-- 1. Anonymous posts store user_id but API never exposes it
-- 2. Aggregates require â‰¥10 posts before showing mood data
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
    password_hash VARCHAR(255) NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token VARCHAR(255) NULL,
    verification_expires TIMESTAMP NULL,
    reset_token VARCHAR(255) NULL,
    reset_expires TIMESTAMP NULL,
    cas_username VARCHAR(50) UNIQUE NULL,
    account_type ENUM('student', 'staff', 'faculty', 'alumni') NOT NULL DEFAULT 'student',
    
    -- Public identity
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    profile_picture VARCHAR(500),
    header_image VARCHAR(500),
    website VARCHAR(255),
    location VARCHAR(100),

    -- Privacy settings
    profile_visibility ENUM('public', 'followers', 'private') NOT NULL DEFAULT 'public',
    show_email BOOLEAN NOT NULL DEFAULT FALSE,

    -- Preferences
    theme ENUM('light', 'dark', 'auto') NOT NULL DEFAULT 'auto',
    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    push_notifications BOOLEAN NOT NULL DEFAULT TRUE,

    -- 2FA
    totp_secret VARCHAR(32) NULL,
    totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    backup_codes JSON NULL,

    -- Account lifecycle
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_deactivated BOOLEAN NOT NULL DEFAULT FALSE,
    deactivated_at TIMESTAMP NULL,
    pinned_post_id INT NULL,
    
    -- Language preference (UniversitÃ© Laval bilingual community)
    preferred_language ENUM('en', 'fr') DEFAULT 'fr' NOT NULL,
    
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
    INDEX idx_verification_token (verification_token),
    INDEX idx_reset_token (reset_token),
    
    -- Constraints
    CONSTRAINT chk_username_length CHECK (CHAR_LENGTH(username) >= 3),
    CONSTRAINT chk_pseudonym_length CHECK (CHAR_LENGTH(pseudonym) >= 3),
    CONSTRAINT chk_email_domain CHECK (email LIKE '%@ulaval.ca')
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
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    
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
    
    -- NLP analysis results (bilingual support)
    sentiment_score DECIMAL(3,2),  -- -1.00 to 1.00
    sentiment_label ENUM('positive', 'neutral', 'negative'),
    emotion_label VARCHAR(20) NULL,
    emotion_display VARCHAR(30) NULL,
    detected_language ENUM('en', 'fr') DEFAULT 'fr',  -- Auto-detected language
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    flagged_at TIMESTAMP NULL,
    hidden_by_mod BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (zone_id) REFERENCES campus_zones(id) ON DELETE SET NULL,
    
    -- Indexes for common queries
    INDEX idx_user_posts (user_id, created_at DESC),
    INDEX idx_user_anonymous (user_id, is_anonymous),
    INDEX idx_zone_recent (zone_id, created_at DESC),
    INDEX idx_feed_query (zone_id, is_anonymous, created_at DESC)
    INDEX idx_sentiment_date (sentiment_label, created_at),
    INDEX idx_language (detected_language),
    
    -- Constraints
    CONSTRAINT chk_content_length CHECK (CHAR_LENGTH(content) >= 10 AND CHAR_LENGTH(content) <= 500),
    CONSTRAINT chk_sentiment_range CHECK (sentiment_score >= -1.00 AND sentiment_score <= 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    parent_id INT NULL,
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,

    INDEX idx_post_comments (post_id, created_at DESC),
    INDEX idx_parent_comments (parent_id),
    INDEX idx_comment_user (user_id),

    CONSTRAINT chk_comment_length CHECK (CHAR_LENGTH(content) >= 1 AND CHAR_LENGTH(content) <= 500)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('new_follower', 'new_comment', 'comment_reply', 'post_reaction', 'mention', 'system') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_type ENUM('post', 'comment', 'user') NULL,
    related_id INT NULL,
    actor_id INT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_notification_user_created (user_id, created_at DESC),
    INDEX idx_notification_unread (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_jti VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(512) NULL,
    device_type ENUM('web', 'mobile', 'desktop', 'unknown') NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_user_active (user_id, is_active),
    INDEX idx_session_jti (token_jti)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE security_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    event_type ENUM(
        'login_success',
        'login_failed',
        'logout',
        'password_change',
        'password_reset',
        '2fa_enabled',
        '2fa_disabled',
        '2fa_verify_failed',
        'account_deactivated',
        'account_reactivated',
        'session_revoked',
        'report_submitted',
        'report_reviewed',
        'content_hidden_by_admin',
        'user_warned',
        'user_deactivated_by_admin',
        'post_deleted_by_admin'
    ) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(512) NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_security_log_user_created (user_id, created_at DESC),
    INDEX idx_security_log_event (event_type, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE bookmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    post_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_bookmark (user_id, post_id),
    INDEX idx_bookmark_user_created (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    target_type ENUM('post', 'comment', 'user') NOT NULL,
    target_id INT NOT NULL,
    reason ENUM('spam', 'harassment', 'self_harm', 'misinformation', 'inappropriate', 'other') NOT NULL,
    details TEXT NULL,
    status ENUM('pending', 'reviewed', 'actioned', 'dismissed') NOT NULL DEFAULT 'pending',
    reviewed_by INT NULL,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_reporter_target (reporter_id, target_type, target_id),
    INDEX idx_reports_status (status),
    INDEX idx_reports_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_a INT NOT NULL,
    participant_b INT NOT NULL,
    last_message_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (participant_a) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_b) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_conversation (participant_a, participant_b),
    INDEX idx_conv_last_msg (last_message_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_msg_conv_time (conversation_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE push_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    platform ENUM('web', 'ios', 'android') NOT NULL,
    token TEXT NOT NULL,
    device_label VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_push_user (user_id),
    INDEX idx_push_active (is_active)
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
    emoji VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,  -- Binary collation for exact emoji matching
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
('Pavillon Alphonse-Desjardins', 'Administration, sciences sociales (ADJ)', 'academic'),
('Pavillon Charles-De Koninck', 'Philosophie (DKN)', 'academic'),
('Pavillon Félix-Antoine-Savard', 'Lettres et sciences humaines (FAS)', 'academic'),
('Pavillon Jean-Charles-Bonenfant', 'Bibliothèque des sciences humaines et sociales (BNF)', 'academic'),
('Pavillon Louis-Jacques-Casault', 'Sciences de l''éducation (CSL)', 'academic'),
('Pavillon Jeanne-Lapointe', 'Littérature, langues (JLA)', 'academic'),
('Pavillon Adrien-Pouliot', 'Génie (PLT)', 'academic'),
('Pavillon Alexandre-Vachon', 'Sciences et génie, mathématiques (VCH)', 'academic'),
('Pavillon Abitibi-Price', 'Foresterie, géographie (ABP)', 'academic'),
('Pavillon Gene-H. Kruger', 'Sciences forestières (GHK)', 'academic'),
('Pavillon Paul-Comtois', 'Sciences de l''agriculture et de l''alimentation (CMT)', 'academic'),
('Pavillon de l''Envirotron', 'Sciences de l''environnement (EVT)', 'academic'),
('Pavillon Charles-Eugène-Marchand', 'Chimie (CHM)', 'academic'),
('Pavillon d''Optique-photonique', 'Optique, photonique, physique (COP)', 'academic'),
('Pavillon Ferdinand-Vandry', 'Sciences de la santé, médecine (VND)', 'academic'),
('Pavillon de la Médecine dentaire', 'Dentisterie (MDE)', 'academic'),
('Pavillon Maurice-Pollack', 'Pharmacie (POL)', 'academic'),
('Pavillon Agathe-Lacerte', 'Nutrition, sciences infirmières (LCT)', 'academic'),
('Pavillon Palasis-Prince', 'Sciences de l''administration (PAP)', 'academic'),
('Pavillon des Services', 'Services aux étudiants, registrariat (PSA)', 'social'),
('Place de l''Université', 'Cœur du campus, espaces de rencontre', 'social'),
('Pavillon Alphonse-Marie-Parent', 'Services aux étudiants (PRN)', 'social'),
('PEPS - Zone sociale', 'Cafétéria, espaces communs PEPS', 'social'),
('PEPS - Pavillon principal', 'Centre sportif principal (PEPS)', 'sports'),
('PEPS - Arénas', 'Patinoires et sports sur glace', 'sports'),
('PEPS - Gymnases', 'Salles d''entraînement et sports collectifs', 'sports'),
('PEPS - Piscine', 'Centre aquatique', 'sports'),
('Stade TELUS-Université Laval', 'Stade de football (SSI)', 'sports'),
('Terrain extérieur PEPS', 'Terrains sportifs extérieurs', 'sports'),
('Café de la Terrasse', 'Café étudiant, espace détente', 'dining'),
('Café Desjardins', 'Cafétéria Pavillon Alphonse-Desjardins', 'dining'),
('Café PEPS', 'Restauration au complexe sportif', 'dining'),
('Café Pollack', 'Cafétéria Pavillon Maurice-Pollack', 'dining'),
('Résidences universitaires - Zone Nord', 'Résidences étudiantes secteur nord', 'residence'),
('Résidences universitaires - Zone Sud', 'Résidences étudiantes secteur sud', 'residence'),
('Pavillon Ernest-Lemieux', 'Résidence (LEM)', 'residence'),
('Jardin Roger-Van den Hende', 'Jardin botanique, espaces verts', 'other'),
('Boulevard Hochelaga', 'Artère principale du campus', 'other'),
('Avenue de la Médecine', 'Secteur sciences de la santé', 'other'),
('Rue de l''Université', 'Axe central du campus', 'other'),
('Stationnements campus', 'Aires de stationnement', 'other'),
('Pavillon de l''Est', 'Installations diverses (PVE)', 'other');


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
