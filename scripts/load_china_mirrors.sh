#!/usr/bin/env bash
# 加载国内镜像配置

if [ -f ".config/china_mirrors.env" ]; then
    source .config/china_mirrors.env
    echo "✅ 国内镜像配置已加载"
else
    echo "⚠️  配置文件不存在，运行 'bash scripts/setup_china_mirrors.sh' 生成"
fi
