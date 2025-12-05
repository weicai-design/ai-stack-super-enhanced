# Evidence目录说明

此目录用于存储CI测试产生的所有证据文件，包括日志、报告、截图等。

## 目录结构

```
evidence/
├── performance/          # 性能测试证据
│   ├── *.json           # 性能测试报告
│   ├── *.log            # 性能测试日志
│   └── *.txt            # 性能测试摘要
├── chaos/               # Chaos工程测试证据
│   ├── *.json           # Chaos测试报告
│   ├── *.log            # Chaos测试日志
│   └── *.txt            # Chaos测试摘要
├── screenshots/         # 截图证据（如果适用）
│   └── *.png            # 测试截图
└── ci_summary/         # CI汇总证据
    └── summary.txt      # CI测试汇总
```

## 文件命名规范

- 性能测试: `performance_test_YYYYMMDD_HHMMSS.*`
- Chaos测试: `chaos_test_<scenario_name>_YYYYMMDD_HHMMSS.*`
- 截图: `screenshot_<test_name>_YYYYMMDD_HHMMSS.png`

## 保留策略

- 性能测试证据: 保留30天
- Chaos测试证据: 保留30天
- CI汇总证据: 保留90天

## 注意事项

- 此目录中的文件由CI自动生成
- 请勿手动修改此目录中的文件
- 定期清理旧文件以节省存储空间

