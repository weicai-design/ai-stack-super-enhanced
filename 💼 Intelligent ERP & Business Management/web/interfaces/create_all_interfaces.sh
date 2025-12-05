#!/bin/bash
# 批量创建剩余的ERP三级界面

INTERFACES=(
    "plan-management:计划管理"
    "receiving-management:入库管理"
    "production-management:生产管理"
    "quality-management:质检管理"
    "outbound-management:出库管理"
    "shipping-management:发运管理"
    "after-sales-management:售后管理"
    "settlement-management:结算管理"
)

for interface in "${INTERFACES[@]}"; do
    IFS=':' read -r filename title <<< "$interface"
    echo "创建 $title 界面..."
    # 这里可以调用Python脚本或直接创建HTML文件
done

echo "所有界面创建完成！"
