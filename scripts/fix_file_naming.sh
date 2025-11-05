#!/bin/bash
# AI Stack Super Enhanced - 文件命名统一脚本
# 将连字符命名的文件重命名为下划线命名（Python标准）
# 并删除符号链接

set -euo pipefail

BASE_DIR="📚 Enhanced RAG & Knowledge Graph"
cd "$(dirname "$0")/.."

echo "🔧 开始统一文件命名..."

# 定义需要重命名的文件对（源文件 -> 目标文件）
declare -a files_to_rename=(
    # knowledge_graph 模块
    "knowledge_graph/dynamic-graph-updater.py:knowledge_graph/dynamic_graph_updater.py"
    "knowledge_graph/graph-construction-engine.py:knowledge_graph/graph_construction_engine.py"
    "knowledge_graph/graph-query-optimizer.py:knowledge_graph/graph_query_optimizer.py"
    "knowledge_graph/knowledge-inference-engine.py:knowledge_graph/knowledge_inference_engine.py"
    "knowledge_graph/node-relationship-miner.py:knowledge_graph/node_relationship_miner.py"
    
    # file_processors 模块
    "processors/file_processors/audio-transcriber.py:processors/file_processors/audio_transcriber.py"
    "processors/file_processors/code-analyzer.py:processors/file_processors/code_analyzer.py"
    "processors/file_processors/database-file-handler.py:processors/file_processors/database_file_handler.py"
    "processors/file_processors/ebook-extractor.py:processors/file_processors/ebook_extractor.py"
    "processors/file_processors/image-ocr-processor.py:processors/file_processors/image_ocr_processor.py"
    "processors/file_processors/mindmap-parser.py:processors/file_processors/mindmap_parser.py"
    "processors/file_processors/office-document-handler.py:processors/file_processors/office_document_handler.py"
    "processors/file_processors/universal-file-parser.py:processors/file_processors/universal_file_parser.py"
    "processors/file_processors/video-frame-extractor.py:processors/file_processors/video_frame_extractor.py"
    
    # pipelines 模块
    "pipelines/knowledge-fusion-engine.py:pipelines/knowledge_fusion_engine.py"
    "pipelines/multi-stage-preprocessor.py:pipelines/multi_stage_preprocessor.py"
    "pipelines/adaptive-grouping-pipeline.py:pipelines/adaptive_grouping_pipeline.py"
    "pipelines/truth-verification-pipeline.py:pipelines/truth_verification_pipeline.py"
    
    # text_processors 模块
    "processors/text_processors/entity-relationship-extractor.py:processors/text_processors/entity_relationship_extractor.py"
    "processors/text_processors/semantic-cleaner.py:processors/text_processors/semantic_cleaner.py"
    "processors/text_processors/quality-validator.py:processors/text_processors/quality_validator.py"
    "processors/text_processors/intelligent-chunker.py:processors/text_processors/intelligent_chunker.py"
    
    # media_processors 模块
    "processors/media_processors/image-semantic-analyzer.py:processors/media_processors/image_semantic_analyzer.py"
    "processors/media_processors/video-content-analyzer.py:processors/media_processors/video_content_analyzer.py"
    "processors/media_processors/audio-content-extractor.py:processors/media_processors/audio_content_extractor.py"
    
    # web/api 模块
    "web/api/rag-api.py:web/api/rag_api.py"
    "web/api/kg-api.py:web/api/kg_api.py"
    "web/api/file-api.py:web/api/file_api.py"
)

# 定义需要删除的符号链接
declare -a symlinks_to_remove=(
    "knowledge_graph/dynamic_graph_updater.py"
    "knowledge_graph/graph_construction_engine.py"
    "knowledge_graph/graph_query_optimizer.py"
    "knowledge_graph/knowledge_inference_engine.py"
    "knowledge_graph/node_relationship_miner.py"
    "processors/file_processors/audio_transcriber.py"
    "processors/file_processors/code_analyzer.py"
    "processors/file_processors/database_file_handler.py"
    "processors/file_processors/ebook_extractor.py"
    "processors/file_processors/image_ocr_processor.py"
    "processors/file_processors/mindmap_parser.py"
    "processors/file_processors/office_document_handler.py"
    "processors/file_processors/universal_file_parser.py"
    "processors/file_processors/video_frame_extractor.py"
    # pipelines 符号链接
    "pipelines/adaptive_grouping_pipeline.py"
    "pipelines/knowledge_fusion_engine.py"
    "pipelines/multi_stage_preprocessor.py"
    "pipelines/truth_verification_pipeline.py"
)

# 检查pipelines目录中是否有类似文件
echo "📋 检查 pipelines 目录..."
if [ -d "$BASE_DIR/pipelines" ]; then
    find "$BASE_DIR/pipelines" -name "*-*.py" -type f | while read -r file; do
        echo "  发现: $file"
    done
fi

# 检查preprocessors目录
echo "📋 检查 preprocessors 目录..."
if [ -d "$BASE_DIR/preprocessors" ]; then
    find "$BASE_DIR/preprocessors" -name "*-*.py" -type f | while read -r file; do
        echo "  发现: $file"
    done
fi

# 创建备份
echo ""
echo "💾 创建备份..."
BACKUP_DIR="backup-file-naming-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/file-naming-backup.tar.gz" "$BASE_DIR" 2>/dev/null || true
echo "✅ 备份已创建: $BACKUP_DIR/file-naming-backup.tar.gz"

# 步骤1: 删除所有符号链接
echo ""
echo "🗑️  删除符号链接..."
for symlink in "${symlinks_to_remove[@]}"; do
    full_path="$BASE_DIR/$symlink"
    if [ -L "$full_path" ]; then
        echo "  删除符号链接: $symlink"
        rm "$full_path"
    fi
done

# 步骤2: 重命名文件
echo ""
echo "📝 重命名文件（连字符 -> 下划线）..."
renamed_count=0
for file_pair in "${files_to_rename[@]}"; do
    src="${file_pair%%:*}"
    dst="${file_pair##*:}"
    src_path="$BASE_DIR/$src"
    dst_path="$BASE_DIR/$dst"
    
    if [ -f "$src_path" ] && [ ! -f "$dst_path" ]; then
        echo "  重命名: $src -> $dst"
        mv "$src_path" "$dst_path"
        ((renamed_count++)) || true
    elif [ -f "$dst_path" ]; then
        echo "  ⚠️  目标文件已存在，跳过: $dst"
    elif [ ! -f "$src_path" ]; then
        echo "  ⚠️  源文件不存在，跳过: $src"
    fi
done

echo ""
echo "✅ 文件重命名完成，共处理 $renamed_count 个文件"

# 步骤3: 检查是否还有遗留文件
echo ""
echo "🔍 检查遗留文件..."
remaining=$(find "$BASE_DIR" -name "*-*.py" -type f | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo "  ⚠️  发现 $remaining 个连字符命名的文件:"
    find "$BASE_DIR" -name "*-*.py" -type f | while read -r file; do
        echo "    $file"
    done
else
    echo "  ✅ 所有文件已统一为下划线命名"
fi

echo ""
echo "🎉 文件命名统一完成！"
echo ""
echo "📝 下一步："
echo "   1. 检查并更新所有导入语句"
echo "   2. 运行测试确保导入正常"
echo "   3. 提交更改"

