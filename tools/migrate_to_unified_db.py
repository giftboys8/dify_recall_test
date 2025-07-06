#!/usr/bin/env python3
"""
数据库迁移脚本
将多个独立的SQLite数据库迁移到统一的数据库中
"""

import sys
import os
from pathlib import Path
import shutil
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.unified_database_manager import UnifiedDatabaseManager
from src.utils.logger import setup_logger


def main():
    """主函数"""
    setup_logger()
    logger = logging.getLogger(__name__)
    
    # 配置路径
    old_db_dir = "data/databases"
    new_db_path = "data/unified_documents.db"
    backup_dir = "data/databases_backup"
    
    logger.info("开始数据库迁移...")
    
    # 检查旧数据库目录是否存在
    if not Path(old_db_dir).exists():
        logger.info("未找到旧数据库目录，无需迁移")
        return
    
    # 创建统一数据库管理器
    unified_db = UnifiedDatabaseManager(new_db_path)
    
    # 备份旧数据库
    logger.info("备份旧数据库...")
    if Path(old_db_dir).exists():
        if Path(backup_dir).exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(old_db_dir, backup_dir)
        logger.info(f"旧数据库已备份到: {backup_dir}")
    
    # 执行迁移
    logger.info("开始迁移数据...")
    success = unified_db.migrate_from_old_databases(old_db_dir)
    
    if success:
        logger.info("数据迁移成功！")
        
        # 询问是否删除旧数据库
        response = input("是否删除旧的数据库文件？(y/N): ").strip().lower()
        if response == 'y':
            shutil.rmtree(old_db_dir)
            logger.info(f"已删除旧数据库目录: {old_db_dir}")
            logger.info(f"备份仍保留在: {backup_dir}")
        else:
            logger.info("保留了旧数据库文件")
        
        logger.info(f"新的统一数据库位于: {new_db_path}")
        
    else:
        logger.error("数据迁移失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()