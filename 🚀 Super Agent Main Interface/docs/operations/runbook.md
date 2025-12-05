# AI Stack Super Enhanced 运维手册

**版本**: v1.0  
**创建日期**: 2025-11-13  
**状态**: ✅ 生产就绪

---

## 📋 目录

1. [日常维护](#日常维护)
2. [应急预案](#应急预案)
3. [故障排查](#故障排查)
4. [运维检查清单](#运维检查清单)
5. [联系信息](#联系信息)

---

## 🔧 日常维护

### 1. 系统监控

#### 1.1 健康检查

**每日健康检查**:
```bash
# 运行日常健康检查脚本
cd "🚀 Super Agent Main Interface"
./scripts/daily_health_check.sh
```

**检查内容**:
- ✅ 系统依赖检查
- ✅ 磁盘空间检查
- ✅ 服务状态检查
- ✅ Docker容器状态检查

**检查频率**: 每日一次（建议在凌晨2:00执行）

**检查结果**:
- 日志文件: `logs/health/health_check_YYYYMMDD_HHMMSS.log`
- 报告文件: `logs/health/health_report_YYYYMMDD.txt`

#### 1.2 服务监控

**服务列表**:
| 服务名称 | 端口 | 健康检查URL | 状态 |
|---------|------|------------|------|
| Super Agent Main Interface | 8000 | http://localhost:8000/health | ✅ |
| RAG System | 8011 | http://localhost:8011/health | ✅ |
| ERP System | 8013 | http://localhost:8013/health | ✅ |
| Stock System | 8014 | http://localhost:8014/health | ✅ |
| Trend Analysis | 8015 | http://localhost:8015/health | ✅ |
| Content Creation | 8016 | http://localhost:8016/health | ✅ |
| Task Agent | 8017 | http://localhost:8017/health | ✅ |
| Resource Management | 8018 | http://localhost:8018/health | ✅ |
| Learning System | 8019 | http://localhost:8019/health | ✅ |
| OpenWebUI | 8020 | http://localhost:8020/health | ✅ |

**监控命令**:
```bash
# 检查所有服务状态
for port in 8000 8011 8013 8014 8015 8016 8017 8018 8019 8020; do
    echo "检查端口 $port..."
    curl -f http://localhost:$port/health || echo "服务 $port 不可用"
done
```

#### 1.3 性能监控

**关键指标**:
- API响应时间（目标: <30ms）
- 并发处理能力（目标: 2500+请求/秒）
- 缓存命中率（目标: 85%+）
- 系统可用性（目标: 99.9%+）

**监控端点**:
```bash
# 获取性能指标
curl http://localhost:8000/api/super-agent/performance/metrics

# 获取SLO报告
curl http://localhost:8000/api/super-agent/slo/report
```

**监控频率**: 实时监控（Prometheus + Grafana）

---

### 2. 日志管理

#### 2.1 日志位置

**日志目录结构**:
```
logs/
├── health/              # 健康检查日志
├── performance/        # 性能测试日志
├── demos/              # 演示日志
├── workflow/           # 工作流日志
└── application/        # 应用日志
```

#### 2.2 日志轮转

**日志轮转策略**:
- 按大小轮转: 单个日志文件最大100MB
- 按时间轮转: 每日轮转
- 保留期限: 30天

**日志轮转配置**:
```bash
# 使用logrotate进行日志轮转
# 配置文件: /etc/logrotate.d/ai-stack
/Users/ywc/ai-stack-super-enhanced/🚀\ Super\ Agent\ Main\ Interface/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

#### 2.3 日志分析

**常用日志分析命令**:
```bash
# 查看错误日志
grep -i error logs/**/*.log | tail -100

# 查看警告日志
grep -i warning logs/**/*.log | tail -100

# 统计错误数量
grep -i error logs/**/*.log | wc -l

# 查看最近的日志
tail -f logs/application/app.log
```

---

### 3. 备份策略

#### 3.1 数据备份

**备份内容**:
- 数据库数据
- 配置文件
- 日志文件
- 用户数据

**备份频率**:
- 数据库: 每日一次（凌晨3:00）
- 配置文件: 每周一次
- 日志文件: 每月一次

**备份命令**:
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U user dbname > backup_$(date +%Y%m%d).sql

# 配置文件备份
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# 日志文件备份
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

#### 3.2 备份验证

**验证步骤**:
1. 检查备份文件是否存在
2. 检查备份文件大小
3. 验证备份文件完整性
4. 测试备份恢复

**验证命令**:
```bash
# 检查备份文件
ls -lh backup_*.sql

# 验证SQL备份
head -20 backup_*.sql

# 测试恢复（在测试环境）
psql -U user testdb < backup_*.sql
```

---

### 4. 性能优化

#### 4.1 数据库优化

**优化措施**:
- 定期清理过期数据
- 优化慢查询
- 重建索引
- 更新统计信息

**优化命令**:
```bash
# 清理过期数据（保留30天）
psql -U user dbname -c "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';"

# 重建索引
psql -U user dbname -c "REINDEX DATABASE dbname;"

# 更新统计信息
psql -U user dbname -c "ANALYZE;"
```

#### 4.2 缓存优化

**缓存策略**:
- Redis缓存预热
- 缓存过期策略
- 缓存命中率监控

**优化命令**:
```bash
# 检查Redis状态
redis-cli ping

# 查看缓存统计
redis-cli INFO stats

# 清理缓存
redis-cli FLUSHDB
```

#### 4.3 系统资源优化

**资源监控**:
```bash
# CPU使用率
top -bn1 | grep "Cpu(s)" | awk '{print $2}'

# 内存使用率
free -h

# 磁盘使用率
df -h

# 网络流量
iftop
```

---

### 5. 安全维护

#### 5.1 安全扫描

**扫描内容**:
- 依赖安全检查
- 代码安全扫描
- 配置安全检查

**扫描命令**:
```bash
# 依赖安全检查
safety check

# 代码安全扫描
bandit -r .

# 合规检查
python3 scripts/compliance_check.py
```

#### 5.2 密钥管理

**密钥轮换**:
- API密钥: 每90天轮换一次
- 数据库密码: 每180天轮换一次
- SSL证书: 每年更新一次

**密钥检查**:
```bash
# 检查密钥过期时间
openssl x509 -in cert.pem -noout -dates
```

---

## 🚨 应急预案

### 1. 故障分类

#### 1.1 故障级别

**P0 - 严重故障**（立即响应）:
- 系统完全不可用
- 数据丢失或损坏
- 安全漏洞

**P1 - 高优先级故障**（1小时内响应）:
- 核心功能不可用
- 性能严重下降
- 部分服务中断

**P2 - 中优先级故障**（4小时内响应）:
- 非核心功能不可用
- 性能轻微下降
- 告警触发

**P3 - 低优先级故障**（24小时内响应）:
- 功能异常但不影响使用
- 性能优化建议
- 文档问题

#### 1.2 故障响应时间

| 故障级别 | 响应时间 | 解决时间 | 升级时间 |
|---------|---------|---------|---------|
| P0 | 15分钟 | 2小时 | 30分钟 |
| P1 | 1小时 | 8小时 | 2小时 |
| P2 | 4小时 | 24小时 | 8小时 |
| P3 | 24小时 | 72小时 | 24小时 |

---

### 2. 应急流程

#### 2.1 故障发现

**发现途径**:
- 监控告警
- 用户反馈
- 日志分析
- 健康检查

**发现后立即执行**:
1. 确认故障现象
2. 评估故障影响
3. 确定故障级别
4. 启动应急响应

#### 2.2 故障评估

**评估内容**:
- 影响范围
- 影响用户数
- 业务影响
- 数据影响

**评估工具**:
```bash
# 检查服务状态
./scripts/daily_health_check.sh

# 检查错误日志
grep -i error logs/**/*.log | tail -50

# 检查系统资源
top -bn1
df -h
free -h
```

#### 2.3 故障处理

**处理步骤**:
1. **隔离故障**
   - 停止受影响服务
   - 切换到备用服务
   - 限制访问

2. **诊断问题**
   - 查看日志
   - 检查监控指标
   - 分析错误信息

3. **修复问题**
   - 应用修复补丁
   - 重启服务
   - 恢复数据

4. **验证修复**
   - 功能验证
   - 性能验证
   - 监控验证

5. **事后总结**
   - 记录故障原因
   - 制定预防措施
   - 更新文档

---

### 3. 常见故障场景

#### 3.1 服务不可用

**症状**:
- 服务无法访问
- 健康检查失败
- 返回5xx错误

**处理步骤**:
```bash
# 1. 检查服务状态
systemctl status ai-stack-service
# 或
docker ps | grep ai-stack

# 2. 查看服务日志
journalctl -u ai-stack-service -n 100
# 或
docker logs ai-stack-container

# 3. 重启服务
systemctl restart ai-stack-service
# 或
docker restart ai-stack-container

# 4. 验证服务恢复
curl http://localhost:8000/health
```

#### 3.2 数据库连接失败

**症状**:
- 数据库查询失败
- 连接超时
- 连接池耗尽

**处理步骤**:
```bash
# 1. 检查数据库状态
docker ps | grep postgres
docker logs postgres-container

# 2. 检查数据库连接
psql -U user -h localhost -d dbname -c "SELECT 1;"

# 3. 检查连接数
psql -U user -h localhost -d dbname -c "SELECT count(*) FROM pg_stat_activity;"

# 4. 重启数据库（如需要）
docker restart postgres-container
```

#### 3.3 磁盘空间不足

**症状**:
- 磁盘使用率>90%
- 写入失败
- 日志轮转失败

**处理步骤**:
```bash
# 1. 检查磁盘使用率
df -h

# 2. 查找大文件
du -sh logs/* | sort -rh | head -10

# 3. 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete

# 4. 清理Docker镜像
docker system prune -a

# 5. 清理临时文件
rm -rf /tmp/*
```

#### 3.4 内存不足

**症状**:
- 内存使用率>90%
- OOM错误
- 服务响应变慢

**处理步骤**:
```bash
# 1. 检查内存使用
free -h
top -bn1 | head -20

# 2. 查找内存占用进程
ps aux --sort=-%mem | head -10

# 3. 重启高内存占用服务
systemctl restart high-memory-service

# 4. 增加swap空间（临时）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3.5 API响应超时

**症状**:
- API响应时间>2秒
- 超时错误
- 请求失败

**处理步骤**:
```bash
# 1. 检查API响应时间
curl -w "@-" -o /dev/null -s http://localhost:8000/api/health <<'EOF'
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
EOF

# 2. 检查慢查询
grep "slow" logs/**/*.log | tail -20

# 3. 检查数据库性能
psql -U user -d dbname -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 4. 重启服务
systemctl restart ai-stack-service
```

---

### 4. 恢复步骤

#### 4.1 服务恢复

**恢复流程**:
1. 停止故障服务
2. 清理故障状态
3. 重启服务
4. 验证服务正常
5. 监控服务状态

**恢复命令**:
```bash
# 停止服务
systemctl stop ai-stack-service
# 或
docker stop ai-stack-container

# 清理状态
rm -rf /tmp/ai-stack-*

# 重启服务
systemctl start ai-stack-service
# 或
docker start ai-stack-container

# 验证恢复
sleep 10
curl http://localhost:8000/health
```

#### 4.2 数据恢复

**恢复流程**:
1. 停止服务
2. 恢复备份数据
3. 验证数据完整性
4. 重启服务
5. 验证功能正常

**恢复命令**:
```bash
# 停止服务
systemctl stop ai-stack-service

# 恢复数据库
psql -U user dbname < backup_YYYYMMDD.sql

# 验证数据
psql -U user dbname -c "SELECT count(*) FROM table_name;"

# 重启服务
systemctl start ai-stack-service
```

#### 4.3 回滚操作

**回滚流程**:
1. 停止当前版本
2. 恢复上一版本
3. 重启服务
4. 验证功能

**回滚命令**:
```bash
# 停止当前版本
systemctl stop ai-stack-service

# 切换到上一版本
git checkout previous-version-tag

# 重新部署
./scripts/auto_deploy.sh

# 重启服务
systemctl start ai-stack-service
```

---

## 🔍 故障排查

### 1. 排查流程

#### 1.1 问题诊断

**诊断步骤**:
1. **收集信息**
   - 故障现象
   - 发生时间
   - 影响范围
   - 错误日志

2. **分析问题**
   - 查看日志
   - 检查监控指标
   - 分析错误信息
   - 对比历史数据

3. **定位根因**
   - 代码问题
   - 配置问题
   - 环境问题
   - 数据问题

4. **制定方案**
   - 临时方案（快速恢复）
   - 永久方案（彻底解决）

#### 1.2 排查工具

**常用工具**:
```bash
# 日志查看
tail -f logs/application/app.log
grep -i error logs/**/*.log

# 系统监控
top
htop
iotop
nethogs

# 网络诊断
ping
traceroute
netstat
ss

# 进程诊断
ps aux
pstree
lsof
strace
```

---

### 2. 常见问题排查

#### 2.1 服务启动失败

**排查步骤**:
```bash
# 1. 检查服务配置
cat /etc/systemd/system/ai-stack.service

# 2. 检查端口占用
netstat -tulpn | grep 8000
# 或
lsof -i :8000

# 3. 检查依赖服务
systemctl status postgresql
systemctl status redis

# 4. 查看启动日志
journalctl -u ai-stack-service -n 100

# 5. 手动启动测试
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**常见原因**:
- 端口被占用
- 依赖服务未启动
- 配置文件错误
- 权限问题

#### 2.2 API响应慢

**排查步骤**:
```bash
# 1. 检查API响应时间
time curl http://localhost:8000/api/health

# 2. 检查数据库查询
psql -U user -d dbname -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. 检查缓存命中率
redis-cli INFO stats | grep keyspace_hits

# 4. 检查系统资源
top -bn1
free -h
iostat -x 1 5

# 5. 检查网络延迟
ping localhost
traceroute api.example.com
```

**常见原因**:
- 数据库查询慢
- 缓存未命中
- 系统资源不足
- 网络延迟

#### 2.3 数据库连接问题

**排查步骤**:
```bash
# 1. 检查数据库状态
docker ps | grep postgres
docker logs postgres-container

# 2. 检查数据库连接
psql -U user -h localhost -d dbname -c "SELECT 1;"

# 3. 检查连接数
psql -U user -h localhost -d dbname -c "SELECT count(*) FROM pg_stat_activity;"

# 4. 检查连接池配置
grep -i "pool" config/*.yaml

# 5. 检查防火墙
iptables -L | grep 5432
```

**常见原因**:
- 数据库未启动
- 连接数超限
- 网络问题
- 认证失败

#### 2.4 缓存问题

**排查步骤**:
```bash
# 1. 检查Redis状态
redis-cli ping

# 2. 检查Redis内存
redis-cli INFO memory

# 3. 检查键数量
redis-cli DBSIZE

# 4. 检查连接数
redis-cli INFO clients

# 5. 检查慢查询
redis-cli SLOWLOG GET 10
```

**常见原因**:
- Redis未启动
- 内存不足
- 连接数超限
- 键过期策略问题

#### 2.5 日志问题

**排查步骤**:
```bash
# 1. 检查日志目录权限
ls -la logs/

# 2. 检查磁盘空间
df -h logs/

# 3. 检查日志轮转配置
cat /etc/logrotate.d/ai-stack

# 4. 检查日志文件大小
du -sh logs/**/*.log

# 5. 测试日志写入
echo "test" >> logs/test.log
```

**常见原因**:
- 磁盘空间不足
- 权限问题
- 日志轮转失败
- 日志配置错误

---

### 3. 性能问题排查

#### 3.1 CPU使用率高

**排查步骤**:
```bash
# 1. 查看CPU使用率
top -bn1 | grep "Cpu(s)"

# 2. 查找高CPU进程
ps aux --sort=-%cpu | head -10

# 3. 分析进程
strace -p <PID> -c

# 4. 检查系统负载
uptime

# 5. 检查中断
cat /proc/interrupts
```

**解决方案**:
- 优化代码性能
- 增加CPU资源
- 负载均衡
- 异步处理

#### 3.2 内存使用率高

**排查步骤**:
```bash
# 1. 查看内存使用
free -h

# 2. 查找高内存进程
ps aux --sort=-%mem | head -10

# 3. 检查内存泄漏
valgrind --leak-check=full python3 app.py

# 4. 检查swap使用
swapon --show

# 5. 检查OOM日志
dmesg | grep -i oom
```

**解决方案**:
- 优化内存使用
- 增加内存资源
- 修复内存泄漏
- 增加swap空间

#### 3.3 磁盘I/O高

**排查步骤**:
```bash
# 1. 查看磁盘I/O
iostat -x 1 5

# 2. 查找高I/O进程
iotop

# 3. 检查磁盘使用
df -h

# 4. 检查磁盘健康
smartctl -a /dev/sda

# 5. 检查文件系统
fsck -n /dev/sda1
```

**解决方案**:
- 优化I/O操作
- 使用SSD
- 增加缓存
- 优化数据库

---

### 4. 安全问题排查

#### 4.1 安全漏洞

**排查步骤**:
```bash
# 1. 依赖安全检查
safety check

# 2. 代码安全扫描
bandit -r .

# 3. 合规检查
python3 scripts/compliance_check.py

# 4. 检查开放端口
nmap localhost

# 5. 检查SSL证书
openssl s_client -connect localhost:443
```

**解决方案**:
- 更新依赖
- 修复漏洞
- 加强安全配置
- 定期安全扫描

#### 4.2 异常访问

**排查步骤**:
```bash
# 1. 检查访问日志
grep -i "unauthorized" logs/**/*.log

# 2. 检查失败登录
grep -i "failed" logs/**/*.log

# 3. 检查IP访问频率
awk '{print $1}' logs/access.log | sort | uniq -c | sort -rn | head -10

# 4. 检查异常请求
grep -i "error\|exception" logs/**/*.log | tail -50
```

**解决方案**:
- 加强访问控制
- 实施IP白名单
- 增加验证码
- 监控异常行为

---

## 📋 运维检查清单

### 每日检查

- [ ] 运行健康检查脚本
- [ ] 检查服务状态
- [ ] 检查错误日志
- [ ] 检查系统资源
- [ ] 检查磁盘空间
- [ ] 检查备份状态

### 每周检查

- [ ] 检查性能指标
- [ ] 检查安全扫描结果
- [ ] 检查日志轮转
- [ ] 检查依赖更新
- [ ] 检查配置备份
- [ ] 检查监控告警

### 每月检查

- [ ] 检查系统更新
- [ ] 检查安全补丁
- [ ] 检查性能优化
- [ ] 检查容量规划
- [ ] 检查文档更新
- [ ] 检查应急预案

---

## 📞 联系信息

### 应急联系人

**技术负责人**:
- 姓名: [待填写]
- 电话: [待填写]
- 邮箱: [待填写]
- 微信: [待填写]

**运维负责人**:
- 姓名: [待填写]
- 电话: [待填写]
- 邮箱: [待填写]
- 微信: [待填写]

**数据库DBA**:
- 姓名: [待填写]
- 电话: [待填写]
- 邮箱: [待填写]

**安全负责人**:
- 姓名: [待填写]
- 电话: [待填写]
- 邮箱: [待填写]

### 外部服务商

**云服务商**:
- 服务商: [待填写]
- 支持电话: [待填写]
- 工单系统: [待填写]

**监控服务**:
- 服务商: [待填写]
- 支持电话: [待填写]

---

## 📚 附录

### A. 常用命令速查

```bash
# 服务管理
systemctl status ai-stack-service
systemctl start ai-stack-service
systemctl stop ai-stack-service
systemctl restart ai-stack-service

# 日志查看
tail -f logs/application/app.log
journalctl -u ai-stack-service -f

# 健康检查
curl http://localhost:8000/health
./scripts/daily_health_check.sh

# 性能监控
curl http://localhost:8000/api/super-agent/performance/metrics
```

### B. 配置文件位置

```
config/
├── app.yaml              # 应用配置
├── database.yaml         # 数据库配置
├── redis.yaml            # Redis配置
└── logging.yaml          # 日志配置
```

### C. 日志文件位置

```
logs/
├── health/               # 健康检查日志
├── performance/         # 性能测试日志
├── demos/               # 演示日志
├── workflow/            # 工作流日志
└── application/         # 应用日志
```

### D. 备份文件位置

```
backups/
├── database/            # 数据库备份
├── config/             # 配置文件备份
└── logs/               # 日志文件备份
```

---

**文档版本**: v1.0  
**最后更新**: 2025-11-13  
**维护团队**: AI Stack运维团队

