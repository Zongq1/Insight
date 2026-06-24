"""测试数据脚本

用于插入测试数据。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def seed_data() -> None:
    """插入测试数据"""
    print("Seeding test data...")

    # TODO: 实现测试数据插入逻辑
    # 1. 插入测试主题
    # 2. 插入测试洞见

    print("Test data seeded!")


if __name__ == "__main__":
    asyncio.run(seed_data())
