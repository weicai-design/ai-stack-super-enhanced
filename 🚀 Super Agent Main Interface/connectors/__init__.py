#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接器模块
提供各种外部API连接器
"""

from .tonghuashun import (
    TonghuashunConnector,
    get_tonghuashun_connector,
    fetch_quote,
    place_order,
)

from .douyin import (
    DouyinConnector,
    get_douyin_connector,
    generate_auth_url,
    handle_callback,
)

__all__ = [
    "TonghuashunConnector",
    "get_tonghuashun_connector",
    "fetch_quote",
    "place_order",
    "DouyinConnector",
    "get_douyin_connector",
    "generate_auth_url",
    "handle_callback",
]

