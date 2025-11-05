# ❓ 常见问题解答 (FAQ)

**版本**: v2.0.0  
**更新时间**: 2025-11-03  

---

## 🚀 安装和部署

### Q1: 如何快速启动系统？

**A**: 使用一键部署脚本：
```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/quick_deploy.sh
```
脚本会自动：
- 检查依赖
- 配置环境
- 启动服务
- 打开浏览器

---

### Q2: 启动时提示"端口被占用"怎么办？

**A**: 释放被占用的端口：
```bash
# 查看占用进程
lsof -i :8013

# 释放端口
lsof -ti :8013 | xargs kill -9

# 或使用部署脚本自动处理
./scripts/quick_deploy.sh  # 会询问是否释放端口
```

---

### Q3: Python依赖安装失败？

**A**: 使用虚拟环境：
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

---

### Q4: npm install 失败？

**A**: 尝试以下方法：
```bash
# 方法1：清除缓存
npm cache clean --force
npm install

# 方法2：使用淘宝镜像
npm install --registry=https://registry.npmmirror.com

# 方法3：更新npm
npm install -g npm@latest
```

---

## 💻 使用问题

### Q5: 网页打不开或显示空白？

**A**: 按顺序尝试：
1. **硬刷新**: `Cmd/Ctrl + Shift + R`
2. **清除缓存**: 浏览器设置 → 清除缓存
3. **无痕模式**: 打开无痕窗口访问
4. **检查服务**: 
   ```bash
   lsof -i :8012  # ERP前端
   lsof -i :8013  # ERP后端
   ```
5. **查看日志**: 
   ```bash
   tail -f logs/*.log
   ```

---

### Q6: API调用返回404？

**A**: 检查以下几点：
1. **确认服务运行**:
   ```bash
   curl http://localhost:8013/health
   ```
2. **检查API路径**: 访问 http://localhost:8013/docs 查看正确路径
3. **确认路由注册**: 检查 `api/main.py` 中是否注册了对应router

---

### Q7: 数据不显示或为空？

**A**: 添加测试数据：
```bash
cd "💼 Intelligent ERP & Business Management"

# 添加财务数据
python3 scripts/add_test_data.py

# 添加业务数据
python3 scripts/add_business_test_data.py

# 添加流程数据
python3 scripts/add_process_data.py
```

---

### Q8: 命令面板命令无响应？

**A**: 检查命令网关状态：
```bash
# 检查服务
curl http://localhost:8020/health

# 重启命令网关
cd "💬 Intelligent OpenWebUI Interaction Center"
python3 command_gateway.py
```

---

## 🔧 功能问题

### Q9: 如何添加新的ERP模块？

**A**: 参考现有模块结构：
```bash
1. 创建数据模型: core/new_module_models.py
2. 创建API: api/new_module_api.py
3. 注册路由: 在 api/main.py 中添加
4. 创建前端页面: web/frontend/src/views/
5. 更新路由: web/frontend/src/router/index.js
```

---

### Q10: 如何自定义专家模型？

**A**: 创建自定义modelfile：
```bash
# 1. 创建配置文件
cat > custom_expert.modelfile << EOF
FROM qwen2.5:7b
PARAMETER temperature 0.7
SYSTEM """你是一位...专家"""
EOF

# 2. 创建模型
ollama create my-expert -f custom_expert.modelfile

# 3. 使用模型
curl http://localhost:11434/api/generate \
  -d '{"model":"my-expert","prompt":"问题"}'
```

---

### Q11: 如何集成第三方API？

**A**: 参考 `integrations/api_examples.py`：
```python
# 1. 安装必要的库
pip install requests

# 2. 使用示例代码
from integrations.api_examples import StockAPIIntegration

stock_api = StockAPIIntegration(api_key="your_key")
price = stock_api.get_stock_price("AAPL")

# 3. 在.env中配置密钥
ALPHA_VANTAGE_API_KEY=your_key
```

---

### Q12: 如何备份数据？

**A**: 备份SQLite数据库：
```bash
# 备份ERP数据
cp "💼 Intelligent ERP & Business Management/erp.db" \
   "backups/erp_$(date +%Y%m%d).db"

# 自动备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
backup_dir="backups/$(date +%Y%m%d)"
mkdir -p "$backup_dir"
find . -name "*.db" -exec cp {} "$backup_dir/" \;
echo "备份完成: $backup_dir"
EOF

chmod +x backup.sh
```

---

## 🐛 错误处理

### Q13: 出现"ModuleNotFoundError"错误？

**A**: 安装缺失的模块：
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装单个模块
pip install module_name

# 或重新安装所有依赖
pip install -r requirements.txt
```

---

### Q14: 数据库错误"table not found"？

**A**: 重新初始化数据库：
```bash
cd "💼 Intelligent ERP & Business Management"

# 删除旧数据库（注意备份）
rm erp.db

# 重启服务，自动创建表
python3 api/main.py

# 添加测试数据
python3 scripts/add_test_data.py
```

---

### Q15: CORS错误？

**A**: 检查CORS配置：
```python
# 在 api/main.py 中确认
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8012"],  # 添加前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Q16: 内存不足或系统变慢？

**A**: 优化资源使用：
```bash
# 1. 关闭不用的服务
kill -9 <PID>

# 2. 减少并发worker
# 在启动命令中添加
uvicorn main:app --workers 1

# 3. 清理缓存
# 删除 __pycache__ 目录
find . -type d -name "__pycache__" -exec rm -rf {} +

# 4. 使用轻量级模型
ollama pull qwen2.5:1.5b  # 更小的模型
```

---

## 🔒 安全问题

### Q17: 如何保护API密钥？

**A**: 使用环境变量：
```bash
# 1. 创建.env文件
cat > .env << EOF
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key
OPENAI_API_KEY=sk-your_key
EOF

# 2. 添加到.gitignore
echo ".env" >> .gitignore

# 3. 在代码中使用
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
```

---

### Q18: 生产环境如何部署？

**A**: 生产部署清单：
```bash
# 1. 使用生产级服务器
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# 2. 配置Nginx反向代理
# 3. 启用HTTPS
# 4. 设置防火墙
# 5. 定期备份数据
# 6. 配置监控告警
# 7. 使用PostgreSQL替代SQLite
```

---

## 📊 性能优化

### Q19: 如何提升系统性能？

**A**: 多方面优化：
```bash
# 1. 使用生产级数据库
DATABASE_URL=postgresql://user:pass@localhost/db

# 2. 启用缓存
pip install redis
# 在代码中添加Redis缓存

# 3. 优化查询
# 添加数据库索引
# 使用分页查询

# 4. 前端优化
npm run build  # 生产构建
# 启用gzip压缩
# 使用CDN

# 5. 使用负载均衡
# Nginx配置多个upstream
```

---

### Q20: API响应太慢？

**A**: 性能分析和优化：
```python
# 1. 添加性能监控
import time

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 2. 使用异步查询
# 3. 添加缓存
# 4. 优化数据库查询
# 5. 减少数据传输量
```

---

## 🎨 自定义和扩展

### Q21: 如何修改前端样式？

**A**: 编辑Vue组件：
```bash
# 1. 找到对应组件
cd "💼 Intelligent ERP & Business Management/web/frontend/src"

# 2. 编辑样式
# 在.vue文件的<style>标签中修改

# 3. 实时预览
npm run dev

# 4. 构建生产版本
npm run build
```

---

### Q22: 如何添加新的API接口？

**A**: 在对应模块添加：
```python
# 在 api/xxx_api.py 中添加
@router.get("/new-endpoint")
async def new_function():
    return {"message": "新接口"}

# 访问 http://localhost:8013/docs 查看
```

---

### Q23: 如何修改数据库表结构？

**A**: 修改模型并重建：
```python
# 1. 修改 core/*_models.py
class NewField(Base):
    new_column = Column(String(100))

# 2. 开发环境：删除数据库重建
rm erp.db
python3 api/main.py  # 自动创建新表

# 3. 生产环境：使用数据库迁移工具
pip install alembic
alembic init alembic
# 配置并执行迁移
```

---

## 🤝 社区和支持

### Q24: 在哪里获取帮助？

**A**: 多个渠道：
1. **查看文档**: 
   - README.md
   - 🎯终极使用指南.md
   - 各模块README

2. **API文档**: http://localhost:8013/docs

3. **日志分析**: 
   ```bash
   tail -f logs/*.log
   ```

4. **技术资源**:
   - FastAPI官网: https://fastapi.tiangolo.com/
   - Vue.js文档: https://vuejs.org/
   - Ollama文档: https://ollama.ai/

---

### Q25: 如何贡献代码或反馈问题？

**A**: 参与项目：
1. **Fork项目** (如果是开源)
2. **创建分支**: `git checkout -b feature/new-feature`
3. **提交代码**: `git commit -m "Add feature"`
4. **推送分支**: `git push origin feature/new-feature`
5. **创建Pull Request**

反馈问题：
- 提供详细的错误信息
- 说明复现步骤
- 附上日志文件
- 说明系统环境

---

## 💡 最佳实践

### Q26: 开发时的最佳实践？

**A**: 遵循规范：
```bash
# 1. 使用虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 遵循代码规范
pip install black flake8
black .
flake8 .

# 3. 编写测试
pytest tests/

# 4. 使用Git版本控制
git add .
git commit -m "描述性提交信息"

# 5. 及时更新文档
```

---

### Q27: 生产环境注意事项？

**A**: 安全检查清单：
- [ ] 更换默认密钥
- [ ] 启用HTTPS
- [ ] 配置防火墙
- [ ] 设置速率限制
- [ ] 启用日志记录
- [ ] 定期备份数据
- [ ] 监控系统资源
- [ ] 准备应急方案

---

## 🎉 成功案例

### Q28: 有实际使用案例吗？

**A**: 系统已完整实现：
- ✅ 完整的ERP系统（13模块）
- ✅ 175+个API接口
- ✅ 7个专家模型
- ✅ 一键部署工具
- ✅ 完整的文档体系

**可立即用于**:
- 企业管理
- 生产制造
- 库存管理
- 财务分析
- AI辅助决策

---

**最后更新**: 2025-11-03  
**版本**: v2.0.0  
**状态**: 完整版  

**💬 还有其他问题？查看详细文档或联系支持！**

