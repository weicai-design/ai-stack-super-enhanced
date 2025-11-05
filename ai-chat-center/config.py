# AI Stack API配置
RAG_API = "http://localhost:8011"
ERP_API = "http://localhost:8013"
STOCK_API = "http://localhost:8014"
CONTENT_API = "http://localhost:8015"
LEARNING_API = "http://localhost:8012"

# Ollama配置
OLLAMA_API = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"  # 修复：使用实际安装的模型名称

# 支持的模型列表（需求8）- 使用实际已安装的模型
SUPPORTED_MODELS = [
    {"id": "qwen2.5:7b", "name": "Qwen 2.5 (推荐)", "size": "7B", "type": "通用"},
    {"id": "qwen2.5:1.5b", "name": "Qwen 2.5 轻量版", "size": "1.5B", "type": "通用"},
    {"id": "llama3.2:1b", "name": "Llama 3.2", "size": "1B", "type": "通用"},
    {"id": "mistral:7b", "name": "Mistral", "size": "7B", "type": "通用"},
    {"id": "llama2:7b", "name": "Llama 2", "size": "7B", "type": "通用"},
    {"id": "qwen:7b", "name": "Qwen 1.0", "size": "7B", "type": "通用"},
]

