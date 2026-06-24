"""数据库初始化脚本

用于创建数据库表结构和初始数据。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def setup_database() -> None:
    """初始化数据库"""
    print(f"Setting up database at: {settings.DATABASE_URL}")

    # TODO: 实现数据库初始化逻辑
    # 1. 创建数据库（如果不存在）
    # 2. 运行 Alembic 迁移
    # 3. 插入初始数据

    print("Database setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_database())
