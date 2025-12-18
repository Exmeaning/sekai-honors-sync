-- Sekai Honors Database Schema
-- 支持多服务器: cn, jp, en, tw, kr

-- 普通徽章表
CREATE TABLE IF NOT EXISTS honors (
    id SERIAL PRIMARY KEY,
    server VARCHAR(10) NOT NULL,           -- cn, jp, en, tw, kr
    honor_id INT NOT NULL,                 -- 游戏内徽章ID
    seq INT,                               -- 排序序号
    group_id INT,                          -- 徽章组ID
    group_name VARCHAR(255),               -- 徽章组名称 (from honorGroups)
    honor_rarity VARCHAR(20),              -- low, middle, high, highest
    name VARCHAR(255),                     -- 徽章名称
    asset_bundle_name VARCHAR(255),        -- 资源包名称
    levels JSONB DEFAULT '[]',             -- 徽章等级信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(server, honor_id)
);

-- 羁绊徽章表
CREATE TABLE IF NOT EXISTS bonds_honors (
    id SERIAL PRIMARY KEY,
    server VARCHAR(10) NOT NULL,
    bonds_honor_id INT NOT NULL,
    seq INT,
    bonds_group_id INT,
    game_character_unit_id1 INT,
    game_character_unit_id2 INT,
    honor_rarity VARCHAR(20),
    name VARCHAR(255),
    description TEXT,
    levels JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(server, bonds_honor_id)
);

-- 徽章分组表
CREATE TABLE IF NOT EXISTS honor_groups (
    id SERIAL PRIMARY KEY,
    server VARCHAR(10) NOT NULL,
    group_id INT NOT NULL,
    name VARCHAR(255),
    honor_type VARCHAR(50),
    background_asset_bundle_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(server, group_id)
);

-- 同步日志表（可选）
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    server VARCHAR(10) NOT NULL,
    sync_type VARCHAR(50) NOT NULL,        -- honors, bonds_honors, honor_groups
    record_count INT DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_honors_server ON honors(server);
CREATE INDEX IF NOT EXISTS idx_honors_group_id ON honors(server, group_id);
CREATE INDEX IF NOT EXISTS idx_honors_rarity ON honors(server, honor_rarity);

CREATE INDEX IF NOT EXISTS idx_bonds_honors_server ON bonds_honors(server);
CREATE INDEX IF NOT EXISTS idx_bonds_honors_characters ON bonds_honors(server, game_character_unit_id1, game_character_unit_id2);

CREATE INDEX IF NOT EXISTS idx_honor_groups_server ON honor_groups(server);

CREATE INDEX IF NOT EXISTS idx_sync_logs_server ON sync_logs(server, synced_at DESC);

-- 用于查询的视图
CREATE OR REPLACE VIEW v_honors_with_group AS
SELECT 
    h.*,
    hg.name as group_name,
    hg.honor_type,
    hg.background_asset_bundle_name
FROM honors h
LEFT JOIN honor_groups hg ON h.server = hg.server AND h.group_id = hg.group_id;

-- 注释
COMMENT ON TABLE honors IS '游戏徽章数据，支持多服务器';
COMMENT ON TABLE bonds_honors IS '羁绊徽章数据，支持多服务器';
COMMENT ON TABLE honor_groups IS '徽章分组数据，支持多服务器';
COMMENT ON COLUMN honors.server IS '服务器标识: cn=国服, jp=日服, en=国际服, tw=台服, kr=韩服';