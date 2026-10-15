-- 执行范围：仅独立毕设库 brand_geo_rag_agent；不是原GEO主库或国家库。
-- 仅创建结构；管理员和业务数据由独立程序写入，不属于数据库迁移。
CREATE DATABASE IF NOT EXISTS `brand_geo_rag_agent` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
USE `brand_geo_rag_agent`;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL COMMENT '登录账号',
    password_hash VARCHAR(200) NOT NULL COMMENT '带盐的scrypt密码哈希',
    role VARCHAR(20) NOT NULL DEFAULT 'superadmin' COMMENT '角色，当前仅支持超级管理员',
    enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uq_users_username (username),
    CHECK (role = 'superadmin'),
    CHECK (enabled IN (0,1))
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    aliases MEDIUMTEXT NOT NULL,
    competitors MEDIUMTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS questions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    text VARCHAR(500) NOT NULL,
    normalized VARCHAR(500) NOT NULL,
    enabled TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uq_questions_normalized (project_id,normalized),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    CHECK (enabled IN (0,1))
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS batches (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    source VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    total INT UNSIGNED NOT NULL,
    completed INT UNSIGNED NOT NULL DEFAULT 0,
    error TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY ix_batches_project (project_id,id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS answers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    batch_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NOT NULL,
    question VARCHAR(500) NOT NULL,
    answer MEDIUMTEXT NOT NULL,
    model VARCHAR(100) NOT NULL,
    source VARCHAR(20) NOT NULL,
    collected_date DATE NULL,
    extraction MEDIUMTEXT NOT NULL,
    extractor_version VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY ix_answers_project_source (project_id,source,id),
    KEY ix_answers_batch (batch_id,id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (batch_id) REFERENCES batches(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(200) NOT NULL,
    source VARCHAR(500) NOT NULL,
    content MEDIUMTEXT NOT NULL,
    chunk_count INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY ix_documents_project (project_id,id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS chunks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,
    ordinal INT UNSIGNED NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uq_chunks_ordinal (document_id,ordinal),
    FOREIGN KEY (document_id) REFERENCES documents(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS optimizations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    query VARCHAR(500) NOT NULL,
    mode VARCHAR(100) NOT NULL,
    diagnosis TEXT NOT NULL,
    suggestions MEDIUMTEXT NOT NULL,
    citations MEDIUMTEXT NOT NULL,
    trace MEDIUMTEXT NOT NULL,
    draft MEDIUMTEXT NOT NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    review_note TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY ix_optimizations_project (project_id,id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS reviews (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    optimization_id BIGINT UNSIGNED NOT NULL,
    status VARCHAR(20) NOT NULL,
    note TEXT NOT NULL,
    draft MEDIUMTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    KEY ix_reviews_optimization (optimization_id,id),
    FOREIGN KEY (optimization_id) REFERENCES optimizations(id)
) ENGINE=InnoDB;
