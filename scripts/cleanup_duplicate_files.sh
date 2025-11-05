#!/bin/bash
# AI Stack Super Enhanced - 清理重复的连字符命名文件
# 当下划线版本已存在时，删除连字符版本

set -euo pipefail

BASE_DIR="📚 Enhanced RAG & Knowledge Graph"
cd "$(dirname "$0")/.."

echo "🧹 清理重复的连字符命名文件..."

# 定义文件对：如果下划线版本存在，删除连字符版本
declare -a file_pairs=(
    "processors/text_processors/entity-relationship-extractor.py:processors/text_processors/entity_relationship_extractor.py"
    "processors/text_processors/semantic-cleaner.py:processors/text_processors/semantic_cleaner.py"
    "processors/text_processors/quality-validator.py:processors/text_processors/quality_validator.py"
    "processors/text_processors/intelligent-chunker.py:processors/text_processors/intelligent_chunker.py"
    "processors/media_processors/image-semantic-analyzer.py:processors/media_processors/image_semantic_analyzer.py"
    "processors/media_processors/video-content-analyzer.py:processors/media_processors/video_content_analyzer.py"
    "processors/media_processors/audio-content-extractor.py:processors/media_processors/audio_content_extractor.py"
    "web/api/rag-api.py:web/api/rag_api.py"
    "web/api/kg-api.py:web/api/kg_api.py"
    "web/api/file-api.py:web/api/file_api.py"
)

deleted_count=0
for file_pair in "${file_pairs[@]}"; do
    hyphen_file="${file_pair%%:*}"
    underscore_file="${file_pair##*:}"
    hyphen_path="$BASE_DIR/$hyphen_file"
    underscore_path="$BASE_DIR/$underscore_file"
    
    if [ -f "$hyphen_path" ] && [ -f "$underscore_path" ]; then
        # 对比文件内容
        if diff -q "$hyphen_path" "$underscore_path" > /dev/null 2>&1; then
            echo "  删除重复文件（内容相同）: $hyphen_file"
            rm "$hyphen_path"
            ((deleted_count++)) || true
        else
            echo "  ⚠️  文件内容不同，需要手动检查: $hyphen_file vs $underscore_file"
        fi
    elif [ -f "$hyphen_path" ] && [ ! -f "$underscore_path" ]; then
        echo "  ⚠️  只有连字符版本存在: $hyphen_file"
    fi
done

echo ""
echo "✅ 清理完成，共删除 $deleted_count 个重复文件"

# 检查备份文件
echo ""
echo "🗑️  检查备份文件..."
backup_files=$(find "$BASE_DIR" -name "*.backup" -o -name "*.bak" -o -name "*~" 2>/dev/null | wc -l)
if [ "$backup_files" -gt 0 ]; then
    echo "  发现 $backup_files 个备份文件:"
    find "$BASE_DIR" -name "*.backup" -o -name "*.bak" -o -name "*~" 2>/dev/null | while read -r file; do
        echo "    $file"
    done
    echo ""
    read -p "是否删除这些备份文件？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find "$BASE_DIR" -name "*.backup" -o -name "*.bak" -o -name "*~" 2>/dev/null | while read -r file; do
            echo "  删除: $file"
            rm "$file"
        done
    fi
else
    echo "  ✅ 未发现备份文件"
fi

echo ""
echo "🎉 清理完成！"

