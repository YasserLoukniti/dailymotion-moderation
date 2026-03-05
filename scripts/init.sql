-- Database schema for moderation system

CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id BIGINT NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    assigned_moderator VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_status CHECK (status IN ('pending', 'spam', 'not spam'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_assigned_moderator ON videos(assigned_moderator);
CREATE INDEX idx_videos_created_at ON videos(created_at);
CREATE INDEX idx_videos_pending_queue ON videos(status, assigned_moderator, created_at);

CREATE TABLE IF NOT EXISTS moderation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    moderator VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_video FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_moderation_logs_video_id ON moderation_logs(video_id);
CREATE INDEX idx_moderation_logs_created_at ON moderation_logs(created_at);
