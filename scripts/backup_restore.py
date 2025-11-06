#!/usr/bin/env python3
"""
数据备份和恢复工具
支持数据库、配置文件、向量数据的备份和恢复
"""
import os
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
import json


class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.workspace = Path('/Users/ywc/ai-stack-super-enhanced')
        self.backup_dir = self.workspace / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # 需要备份的目录和文件
        self.backup_targets = {
            'databases': [
                'rag/vector_store.db',
                '💼 Intelligent ERP & Business Management/data/erp.db',
                '📈 Intelligent Stock Trading/data/trading.db',
                '🧠 Self Learning System/data/learning.db'
            ],
            'configs': [
                'config.json',
                '.env',
                'ai-chat-center/config.json'
            ],
            'vectors': [
                'rag/chroma_db',
                'rag/faiss_index'
            ],
            'logs': [
                'logs'
            ]
        }
    
    def create_backup(self, backup_type: str = 'full') -> str:
        """
        创建备份
        
        Args:
            backup_type: 备份类型 (full/databases/configs)
        
        Returns:
            备份文件路径
        """
        print(f"\n🗜️  开始创建{backup_type}备份...")
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"ai_stack_backup_{backup_type}_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        # 创建临时目录
        temp_dir = self.backup_dir / f"temp_{timestamp}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 复制文件到临时目录
            files_copied = 0
            
            if backup_type in ['full', 'databases']:
                print("\n📦 备份数据库文件...")
                for db_path in self.backup_targets['databases']:
                    source = self.workspace / db_path
                    if source.exists():
                        dest = temp_dir / 'databases' / source.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        print(f"  ✓ {source.name}")
                        files_copied += 1
            
            if backup_type in ['full', 'configs']:
                print("\n📋 备份配置文件...")
                for config_path in self.backup_targets['configs']:
                    source = self.workspace / config_path
                    if source.exists():
                        dest = temp_dir / 'configs' / source.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        print(f"  ✓ {source.name}")
                        files_copied += 1
            
            if backup_type == 'full':
                print("\n🧲 备份向量数据...")
                for vector_path in self.backup_targets['vectors']:
                    source = self.workspace / vector_path
                    if source.exists():
                        dest = temp_dir / 'vectors' / source.name
                        if source.is_dir():
                            shutil.copytree(source, dest)
                        else:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source, dest)
                        print(f"  ✓ {source.name}")
                        files_copied += 1
            
            # 创建备份元数据
            metadata = {
                'backup_type': backup_type,
                'timestamp': timestamp,
                'files_count': files_copied,
                'created_at': datetime.now().isoformat()
            }
            
            with open(temp_dir / 'backup_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 压缩备份
            print(f"\n🗜️  压缩备份文件...")
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(temp_dir, arcname=os.path.basename(temp_dir))
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 获取备份文件大小
            backup_size = backup_path.stat().st_size / 1024 / 1024  # MB
            
            print(f"\n✅ 备份创建成功！")
            print(f"   文件: {backup_name}")
            print(f"   大小: {backup_size:.2f} MB")
            print(f"   位置: {backup_path}")
            
            return str(backup_path)
        
        except Exception as e:
            print(f"\n❌ 备份失败: {str(e)}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def restore_backup(self, backup_file: str) -> bool:
        """
        恢复备份
        
        Args:
            backup_file: 备份文件路径
        
        Returns:
            是否成功
        """
        print(f"\n📂 开始恢复备份...")
        print(f"   文件: {backup_file}")
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_file}")
            return False
        
        # 创建临时目录
        temp_dir = self.backup_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 解压备份
            print("\n📦 解压备份文件...")
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # 读取元数据
            extracted_dir = next(temp_dir.iterdir())
            metadata_file = extracted_dir / 'backup_metadata.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                print(f"\n备份信息:")
                print(f"  类型: {metadata['backup_type']}")
                print(f"  创建时间: {metadata['created_at']}")
                print(f"  文件数量: {metadata['files_count']}")
            
            # 恢复文件
            files_restored = 0
            
            # 恢复数据库
            db_dir = extracted_dir / 'databases'
            if db_dir.exists():
                print("\n📦 恢复数据库...")
                for db_file in db_dir.iterdir():
                    # 找到对应的目标路径
                    for target in self.backup_targets['databases']:
                        if Path(target).name == db_file.name:
                            dest = self.workspace / target
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(db_file, dest)
                            print(f"  ✓ {db_file.name}")
                            files_restored += 1
                            break
            
            # 恢复配置
            config_dir = extracted_dir / 'configs'
            if config_dir.exists():
                print("\n📋 恢复配置文件...")
                for config_file in config_dir.iterdir():
                    for target in self.backup_targets['configs']:
                        if Path(target).name == config_file.name:
                            dest = self.workspace / target
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(config_file, dest)
                            print(f"  ✓ {config_file.name}")
                            files_restored += 1
                            break
            
            # 恢复向量数据
            vector_dir = extracted_dir / 'vectors'
            if vector_dir.exists():
                print("\n🧲 恢复向量数据...")
                for vector_item in vector_dir.iterdir():
                    for target in self.backup_targets['vectors']:
                        if Path(target).name == vector_item.name:
                            dest = self.workspace / target
                            if vector_item.is_dir():
                                if dest.exists():
                                    shutil.rmtree(dest)
                                shutil.copytree(vector_item, dest)
                            else:
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(vector_item, dest)
                            print(f"  ✓ {vector_item.name}")
                            files_restored += 1
                            break
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            print(f"\n✅ 恢复完成！")
            print(f"   恢复文件数: {files_restored}")
            
            return True
        
        except Exception as e:
            print(f"\n❌ 恢复失败: {str(e)}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
    
    def list_backups(self):
        """列出所有备份"""
        print("\n📋 备份文件列表:\n")
        
        backups = sorted(self.backup_dir.glob('ai_stack_backup_*.tar.gz'), 
                        key=os.path.getmtime, reverse=True)
        
        if not backups:
            print("  暂无备份文件")
            return
        
        for i, backup in enumerate(backups, 1):
            size = backup.stat().st_size / 1024 / 1024  # MB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name}")
            print(f"   大小: {size:.2f} MB")
            print(f"   时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def main():
    """主函数"""
    manager = BackupManager()
    
    print("\n" + "=" * 60)
    print("💾 AI Stack 数据备份和恢复工具")
    print("=" * 60)
    
    print("\n请选择操作:")
    print("1. 创建完整备份")
    print("2. 仅备份数据库")
    print("3. 仅备份配置")
    print("4. 恢复备份")
    print("5. 查看备份列表")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice == '1':
        manager.create_backup('full')
    elif choice == '2':
        manager.create_backup('databases')
    elif choice == '3':
        manager.create_backup('configs')
    elif choice == '4':
        manager.list_backups()
        backup_file = input("\n请输入备份文件名（或完整路径）: ").strip()
        if not backup_file.startswith('/'):
            backup_file = str(manager.backup_dir / backup_file)
        manager.restore_backup(backup_file)
    elif choice == '5':
        manager.list_backups()
    else:
        print("无效选项")


if __name__ == "__main__":
    main()







