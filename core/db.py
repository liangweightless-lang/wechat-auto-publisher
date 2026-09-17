# -*- coding: utf-8 -*-
"""
轻量级 SQLite 数据持久化模块
职责：
1. 存储与归档生成的历史文章（包括微信图文、抖音解说脚本、小红书笔记等矩阵资产）；
2. 爬虫热点资讯去重池，避免重复推送；
3. 单文件数据库 storage/publisher.db，零依赖零配置。
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from config.settings import logger

DB_PATH = Path("storage/publisher.db")


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db_connection()
    try:
        with conn:
            # 1. 文章与矩阵发布历史表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_hash TEXT UNIQUE,
                    title TEXT NOT NULL,
                    category TEXT,
                    theme TEXT DEFAULT 'think_tank',
                    author TEXT DEFAULT '局势洞见研判组',
                    lead TEXT,
                    markdown_content TEXT,
                    wechat_html TEXT,
                    douyin_script TEXT,
                    xiaohongshu_note TEXT,
                    cover_image_path TEXT,
                    illustration_path TEXT,
                    illustration_prompt TEXT,
                    wechat_media_id TEXT,
                    publish_status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. 热点资讯去重池
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_pool (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE,
                    title TEXT NOT NULL,
                    category TEXT,
                    source TEXT,
                    url TEXT,
                    pub_time TEXT,
                    summary TEXT,
                    is_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. 索引优化
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_category ON news_pool(category);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_hash ON news_pool(url_hash);")

        logger.info(f"SQLite 数据库初始化完成: {DB_PATH}")
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
    finally:
        conn.close()


# 立即在模块加载时验证/初始化
init_db()


class DatabaseManager:
    """数据库操作管理器"""

    @staticmethod
    def save_article(
        title: str,
        category: str = "",
        theme: str = "think_tank",
        author: str = "局势洞见研判组",
        lead: str = "",
        markdown_content: str = "",
        wechat_html: str = "",
        douyin_script: str = "",
        xiaohongshu_note: str = "",
        cover_image_path: str = "",
        illustration_path: str = "",
        illustration_prompt: str = "",
        wechat_media_id: str = "",
        publish_status: str = "draft"
    ) -> int:
        """保存或更新已生成的矩阵文章"""
        conn = get_db_connection()
        article_hash = hashlib.md5(f"{title}_{datetime.now().strftime('%Y%m%d%H')}".encode("utf-8")).hexdigest()
        try:
            with conn:
                cursor = conn.execute("""
                    INSERT INTO articles (
                        article_hash, title, category, theme, author, lead,
                        markdown_content, wechat_html, douyin_script, xiaohongshu_note,
                        cover_image_path, illustration_path, illustration_prompt,
                        wechat_media_id, publish_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(article_hash) DO UPDATE SET
                        theme = excluded.theme,
                        wechat_html = excluded.wechat_html,
                        douyin_script = excluded.douyin_script,
                        xiaohongshu_note = excluded.xiaohongshu_note,
                        wechat_media_id = COALESCE(excluded.wechat_media_id, articles.wechat_media_id),
                        publish_status = excluded.publish_status,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    article_hash, title, category, theme, author, lead,
                    markdown_content, wechat_html, douyin_script, xiaohongshu_note,
                    cover_image_path, illustration_path, illustration_prompt,
                    wechat_media_id, publish_status
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"保存文章到数据库失败: {e}")
            return 0
        finally:
            conn.close()

    @staticmethod
    def update_article_publish_status(article_id: int, wechat_media_id: str, status: str = "published"):
        """更新微信发布状态与 media_id"""
        conn = get_db_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE articles 
                    SET wechat_media_id = ?, publish_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (wechat_media_id, status, article_id))
        except Exception as e:
            logger.error(f"更新文章发布状态失败: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_recent_articles(limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近生成的历史文章列表"""
        conn = get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT id, article_hash, title, category, theme, author, lead,
                       cover_image_path, wechat_media_id, publish_status, created_at,
                       markdown_content, douyin_script, xiaohongshu_note, illustration_prompt
                FROM articles
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取历史文章失败: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取完整文章详情"""
        conn = get_db_connection()
        try:
            cursor = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"查询文章详情失败: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def record_news_items(items: List[Dict[str, Any]]):
        """批量录入资讯并去重"""
        conn = get_db_connection()
        try:
            with conn:
                for item in items:
                    url = item.get("url", "")
                    title = item.get("title", "")
                    if not url and not title:
                        continue
                    url_hash = hashlib.md5(f"{title}_{url}".encode("utf-8")).hexdigest()
                    conn.execute("""
                        INSERT OR IGNORE INTO news_pool (url_hash, title, category, source, url, pub_time, summary)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        url_hash,
                        title,
                        item.get("category", ""),
                        item.get("source", ""),
                        url,
                        item.get("pub_time", ""),
                        item.get("summary", "")
                    ))
        except Exception as e:
            logger.error(f"批量记录资讯失败: {e}")
        finally:
            conn.close()

    @staticmethod
    def mark_news_used(title: str):
        """标记资讯已被选题使用"""
        conn = get_db_connection()
        try:
            with conn:
                conn.execute("UPDATE news_pool SET is_used = 1 WHERE title LIKE ?", (f"%{title[:12]}%",))
        except Exception as e:
            logger.error(f"标记资讯状态失败: {e}")
        finally:
            conn.close()
