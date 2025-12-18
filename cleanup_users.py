#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理用户数据脚本
只保留指定的两个用户，删除其他所有测试用户数据
"""

import json
import shutil
from pathlib import Path
import os

# 要保留的用户ID
KEEP_USERS = ['66_555', '22_11']

# 存储目录（使用绝对路径）
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / 'storage'
MOMENTS_DIR = STORAGE_DIR / 'moments'
USER_DATA_DIR = STORAGE_DIR / 'user_data'
NAMES_FILE = USER_DATA_DIR / 'names.json'

def cleanup_users():
    """清理用户数据"""
    print(f"🧹 开始清理用户数据，保留: {KEEP_USERS}")
    
    # 1. 读取 names.json
    if NAMES_FILE.exists():
        with open(NAMES_FILE, 'r', encoding='utf-8') as f:
            names_data = json.load(f)
        
        # 保留指定的用户
        new_names_data = {}
        for user_id in KEEP_USERS:
            if user_id in names_data:
                new_names_data[user_id] = names_data[user_id]
                print(f"✅ 保留用户: {user_id}")
        
        # 保存更新后的 names.json
        with open(NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_names_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已更新 names.json，保留 {len(new_names_data)} 个用户")
    else:
        print("⚠️ names.json 不存在")
    
    # 2. 删除其他用户的 moments 目录
    if MOMENTS_DIR.exists():
        deleted_count = 0
        for user_dir in MOMENTS_DIR.iterdir():
            if user_dir.is_dir() and user_dir.name not in KEEP_USERS:
                try:
                    shutil.rmtree(user_dir)
                    print(f"🗑️  已删除 moments 目录: {user_dir.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 删除失败 {user_dir.name}: {e}")
        print(f"✅ 已删除 {deleted_count} 个 moments 目录")
    else:
        print("⚠️ moments 目录不存在")
    
    # 3. 删除其他用户的 style.json 文件
    if USER_DATA_DIR.exists():
        deleted_count = 0
        for style_file in USER_DATA_DIR.glob('*_style.json'):
            user_id = style_file.stem.replace('_style', '')
            if user_id not in KEEP_USERS:
                try:
                    style_file.unlink()
                    print(f"🗑️  已删除 style 文件: {style_file.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 删除失败 {style_file.name}: {e}")
        print(f"✅ 已删除 {deleted_count} 个 style 文件")
    else:
        print("⚠️ user_data 目录不存在")
    
    print(f"\n✨ 清理完成！保留了 {len(KEEP_USERS)} 个用户: {', '.join(KEEP_USERS)}")

if __name__ == '__main__':
    cleanup_users()

