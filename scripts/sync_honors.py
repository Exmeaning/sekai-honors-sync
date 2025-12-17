#!/usr/bin/env python3
"""
Sekai Honors Sync Script
从各服务器的 masterdata 同步徽章数据到 PostgreSQL
"""

import os
import sys
import json
import logging
from typing import Optional
from datetime import datetime

import requests
import psycopg2
from psycopg2.extras import execute_values, Json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 服务器对应的 masterdata 仓库
SERVERS = {
    'cn': 'haruki-sekai-sc-master',
    'jp': 'haruki-sekai-master',
    'en': 'haruki-sekai-en-master',
    'tw': 'haruki-sekai-tc-master',
    'kr': 'haruki-sekai-kr-master',
}

# 服务器显示名称
SERVER_NAMES = {
    'cn': '简体中文',
    'jp': '日本語',
    'en': 'English',
    'tw': '繁體中文',
    'kr': '한국어',
}

# GitHub Raw 文件 URL 模板
RAW_URL_TEMPLATE = 'https://raw.githubusercontent.com/Team-Haruki/{repo}/main/master/{file}'

# jsDelivr CDN URL 模板（备用）
CDN_URL_TEMPLATE = 'https://cdn.jsdelivr.net/gh/Team-Haruki/{repo}@main/master/{file}'


class HonorsSyncer:
    def __init__(self, database_url: str, server: str):
        self.server = server
        self.repo = SERVERS.get(server)
        if not self.repo:
            raise ValueError(f"Unknown server: {server}")
        
        self.conn = psycopg2.connect(database_url, sslmode='require')
        self.conn.autocommit = False
        logger.info(f"Connected to database for server: {server} ({SERVER_NAMES.get(server)})")
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def fetch_json(self, filename: str) -> Optional[list]:
        """从 GitHub 获取 JSON 数据"""
        urls = [
            RAW_URL_TEMPLATE.format(repo=self.repo, file=filename),
            CDN_URL_TEMPLATE.format(repo=self.repo, file=filename),
        ]
        
        for url in urls:
            try:
                logger.info(f"Fetching {filename} from {url}")
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"Fetched {len(data)} records from {filename}")
                return data
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {url}: {e}")
                continue
        
        logger.error(f"All sources failed for {filename}")
        return None
    
    def sync_honors(self) -> int:
        """同步普通徽章"""
        data = self.fetch_json('honors.json')
        if not data:
            return 0
        
        records = []
        for item in data:
            records.append((
                self.server,
                item.get('id'),
                item.get('seq'),
                item.get('groupId'),
                item.get('honorRarity'),
                item.get('name'),
                item.get('assetbundleName'),
                Json(item.get('levels', [])),
            ))
        
        sql = """
            INSERT INTO honors (
                server, honor_id, seq, group_id, honor_rarity, 
                name, asset_bundle_name, levels, updated_at
            ) VALUES %s
            ON CONFLICT (server, honor_id) DO UPDATE SET
                seq = EXCLUDED.seq,
                group_id = EXCLUDED.group_id,
                honor_rarity = EXCLUDED.honor_rarity,
                name = EXCLUDED.name,
                asset_bundle_name = EXCLUDED.asset_bundle_name,
                levels = EXCLUDED.levels,
                updated_at = CURRENT_TIMESTAMP
        """
        
        with self.conn.cursor() as cur:
            execute_values(
                cur, sql, records,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)"
            )
        
        logger.info(f"Synced {len(records)} honors for {self.server}")
        return len(records)
    
    def sync_bonds_honors(self) -> int:
        """同步羁绊徽章"""
        data = self.fetch_json('bondsHonors.json')
        if not data:
            return 0
        
        records = []
        for item in data:
            records.append((
                self.server,
                item.get('id'),
                item.get('seq'),
                item.get('bondsGroupId'),
                item.get('gameCharacterUnitId1'),
                item.get('gameCharacterUnitId2'),
                item.get('honorRarity'),
                item.get('name'),
                item.get('description'),
                Json(item.get('levels', [])),
            ))
        
        sql = """
            INSERT INTO bonds_honors (
                server, bonds_honor_id, seq, bonds_group_id,
                game_character_unit_id1, game_character_unit_id2,
                honor_rarity, name, description, levels, updated_at
            ) VALUES %s
            ON CONFLICT (server, bonds_honor_id) DO UPDATE SET
                seq = EXCLUDED.seq,
                bonds_group_id = EXCLUDED.bonds_group_id,
                game_character_unit_id1 = EXCLUDED.game_character_unit_id1,
                game_character_unit_id2 = EXCLUDED.game_character_unit_id2,
                honor_rarity = EXCLUDED.honor_rarity,
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                levels = EXCLUDED.levels,
                updated_at = CURRENT_TIMESTAMP
        """
        
        with self.conn.cursor() as cur:
            execute_values(
                cur, sql, records,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)"
            )
        
        logger.info(f"Synced {len(records)} bonds honors for {self.server}")
        return len(records)
    
    def sync_honor_groups(self) -> int:
        """同步徽章分组"""
        data = self.fetch_json('honorGroups.json')
        if not data:
            return 0
        
        records = []
        for item in data:
            records.append((
                self.server,
                item.get('id'),
                item.get('name'),
                item.get('honorType'),
                item.get('backgroundAssetbundleName'),
            ))
        
        sql = """
            INSERT INTO honor_groups (
                server, group_id, name, honor_type,
                background_asset_bundle_name, updated_at
            ) VALUES %s
            ON CONFLICT (server, group_id) DO UPDATE SET
                name = EXCLUDED.name,
                honor_type = EXCLUDED.honor_type,
                background_asset_bundle_name = EXCLUDED.background_asset_bundle_name,
                updated_at = CURRENT_TIMESTAMP
        """
        
        with self.conn.cursor() as cur:
            execute_values(
                cur, sql, records,
                template="(%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)"
            )
        
        logger.info(f"Synced {len(records)} honor groups for {self.server}")
        return len(records)
    
    def run(self) -> dict:
        """执行完整同步"""
        results = {
            'server': self.server,
            'server_name': SERVER_NAMES.get(self.server),
            'honors': 0,
            'bonds_honors': 0,
            'honor_groups': 0,
            'success': False,
            'error': None,
        }
        
        try:
            results['honors'] = self.sync_honors()
            results['bonds_honors'] = self.sync_bonds_honors()
            results['honor_groups'] = self.sync_honor_groups()
            
            self.conn.commit()
            results['success'] = True
            logger.info(f"Sync completed for {self.server}: "
                       f"{results['honors']} honors, "
                       f"{results['bonds_honors']} bonds honors, "
                       f"{results['honor_groups']} honor groups")
        
        except Exception as e:
            self.conn.rollback()
            results['error'] = str(e)
            logger.error(f"Sync failed for {self.server}: {e}")
        
        return results


def main():
    # 从环境变量获取配置
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)
    
    server = os.environ.get('SERVER', 'cn')
    if server not in SERVERS:
        logger.error(f"Invalid server: {server}. Valid options: {list(SERVERS.keys())}")
        sys.exit(1)
    
    logger.info(f"Starting honors sync for server: {server}")
    
    syncer = HonorsSyncer(database_url, server)
    try:
        results = syncer.run()
        
        if results['success']:
            logger.info("=" * 50)
            logger.info("SYNC SUCCESSFUL")
            logger.info(f"Server: {results['server']} ({results['server_name']})")
            logger.info(f"Honors: {results['honors']}")
            logger.info(f"Bonds Honors: {results['bonds_honors']}")
            logger.info(f"Honor Groups: {results['honor_groups']}")
            logger.info("=" * 50)
        else:
            logger.error(f"Sync failed: {results['error']}")
            sys.exit(1)
    
    finally:
        syncer.close()


if __name__ == '__main__':
    main()