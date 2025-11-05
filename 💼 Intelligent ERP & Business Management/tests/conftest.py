"""
Pytest Configuration
Pytest配置

为所有测试提供公共fixtures和配置
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加父目录到路径
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import Base


@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine):
    """创建测试数据库会话"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

