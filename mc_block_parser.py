#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Minecraft方块信息解析器 (Minecraft Block Information Parser)

该脚本用于解析Minecraft方块信息日志，提取方块ID、注册名称、未本地化名称和纹理信息，
并将其保存为结构化的JSON文件。

主要功能：
1. 支持多种编码（UTF-8, GBK, GB18030, GB2312）读取包含中文的日志文件
2. 提取方块基本信息：ID、注册名称、未本地化名称
3. 解析方块纹理类型，分为以下几类：
   - standard_block: 标准方块，所有面使用相同纹理
   - directional_block: 方向性方块，不同面使用不同纹理
   - custom_render: 自定义渲染方块，所有面均为null
4. 记录每个方块六个面(0-5)的纹理名称
5. 将所有数据以JSON格式保存，便于后续分析和处理

使用方法：
1. 确保blocks_info.log文件位于脚本同目录下
2. 运行脚本：python mc_block_parser.py
3. 生成的blocks_data.json文件包含所有解析出的方块信息

作者：神楽坂牧月
版本：1.0.0
日期：2025-03-27
许可证：MIT
"""

import re
import json
import os
from datetime import datetime

def parse_blocks_info_log(log_file_path):
    # 尝试不同的编码方式打开文件
    encodings = ['utf-8', 'gbk', 'gb18030', 'gb2312']
    
    for encoding in encodings:
        try:
            with open(log_file_path, 'r', encoding=encoding) as file:
                content = file.read()
                # 如果能成功读取，则跳出循环
                break
        except UnicodeDecodeError:
            continue
    else:
        # 如果所有编码都失败，抛出错误
        raise ValueError(f"无法用任何常见编码打开文件: {log_file_path}")

    # 存储所有方块信息的列表
    blocks_data = []
    
    # 用正则表达式匹配方块信息
    block_pattern = re.compile(r'\[[\d:]+\] 方块ID: (\d+), 注册名称: ([^,]+), 未本地化名称: ([^\n]+)\n(.*?)(?=\[[\d:]+\] 方块ID:|$)', re.DOTALL)
    
    # 纹理类型映射
    texture_type_mapping = {
        '方块使用相同纹理，标准方块': 'standard_block',
        '不同面使用不同纹理，定向方块': 'directional_block',
        '方块所有面均为null，可能使用完全自定义渲染': 'custom_render'
    }
    
    # 查找所有匹配项
    for match in block_pattern.finditer(content):
        block_id = int(match.group(1))
        registry_name = match.group(2)
        unlocalized_name = match.group(3)
        block_details = match.group(4)
        
        # 解析纹理信息
        textures = {}
        texture_pattern = re.compile(r'面 (\d+) 纹理: (.+)')
        texture_null_pattern = re.compile(r'面 (\d+) 纹理为null')
        
        for line in block_details.split('\n'):
            # 查找标准纹理
            texture_match = texture_pattern.search(line)
            if texture_match:
                face_id = int(texture_match.group(1))
                texture_name = texture_match.group(2).strip()
                textures[f'face_{face_id}'] = texture_name
                continue
            
            # 查找null纹理
            null_match = texture_null_pattern.search(line)
            if null_match:
                face_id = int(null_match.group(1))
                textures[f'face_{face_id}'] = None
        
        # 解析纹理类型
        texture_type = "unknown"
        
        # 检查是否所有面都为null
        all_null = all(textures.get(f'face_{i}') is None for i in range(6))
        if all_null:
            texture_type = "custom_render"
        else:
            # 检查是否所有面都使用相同纹理
            face_textures = [textures.get(f'face_{i}') for i in range(6) if textures.get(f'face_{i}') is not None]
            if face_textures and all(texture == face_textures[0] for texture in face_textures):
                texture_type = "standard_block"
            else:
                texture_type = "directional_block"
        
        # 尝试从日志中获取更详细的纹理类型描述
        texture_type_description = None
        for line in block_details.split('\n'):
            if '结论:' in line:
                texture_type_description = line.split('结论:')[1].strip()
                break
        
        # 创建方块数据字典
        block_data = {
            'block_id': block_id,
            'registry_name': registry_name,
            'unlocalized_name': unlocalized_name,
            'texture_type': texture_type,
            'texture_type_description': texture_type_description,
            'textures': textures
        }
        
        blocks_data.append(block_data)
    
    return blocks_data

def save_to_json(blocks_data, output_file):
    # 创建包含元数据的输出字典
    output_data = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_blocks': len(blocks_data)
        },
        'blocks': blocks_data
    }
    
    # 确保输出目录存在（只有当输出文件路径包含目录时才创建）
    output_dir = os.path.dirname(output_file)
    if output_dir:  # 只有当路径不为空时才创建目录
        os.makedirs(output_dir, exist_ok=True)
    
    # 写入JSON文件，确保中文字符正确显示
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

def main():
    input_file = 'blocks_info.log'
    output_file = 'blocks_data.json'
    
    print(f"开始解析Minecraft方块信息...")
    try:
        blocks_data = parse_blocks_info_log(input_file)
        save_to_json(blocks_data, output_file)
        print(f"解析完成! 共处理了 {len(blocks_data)} 个方块，数据已保存到 {output_file}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    main() 