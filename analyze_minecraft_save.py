#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import traceback
from anvil.region import Region
from anvil.errors import ChunkNotFound

def analyze_mca_file(mca_file_path, output_file_path=None, max_chunks=50):
    """
    分析指定的.mca文件，提取方块信息
    
    Args:
        mca_file_path: MCA文件的路径
        output_file_path: 输出文件路径，如果为None则自动生成
        max_chunks: 最大处理区块数量，防止处理过大的文件
    
    Returns:
        保存的输出文件路径
    """
    if output_file_path is None:
        base_name = os.path.basename(mca_file_path)
        output_file_path = f"{base_name}_analysis.txt"
    
    try:
        # 打开区域文件
        region = Region(mca_file_path)
        
        # 提取文件名和区域坐标
        file_name = os.path.basename(mca_file_path)
        try:
            region_coords = list(map(int, file_name.replace('r.', '').replace('.mca', '').split('.')))
        except:
            region_coords = [0, 0]  # 默认值，以防解析失败
        
        # 准备区域信息字典
        region_data = {
            "file_name": file_name,
            "region_coords": region_coords,
            "chunks": []
        }
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"分析文件: {mca_file_path}\n")
            f.write(f"区域坐标: {region_coords}\n\n")
            
            # 计算区域基础坐标
            region_x, region_z = region_coords
            base_x = region_x * 32
            base_z = region_z * 32
            
            # 尝试读取每个可能的区块位置
            chunks_found = 0
            for cx in range(32):
                for cz in range(32):
                    # 计算绝对区块坐标
                    abs_cx = base_x + cx
                    abs_cz = base_z + cz
                    
                    # 尝试获取区块
                    try:
                        chunk = region.get_chunk(abs_cx, abs_cz)
                        
                        # 区块存在，增加计数
                        chunks_found += 1
                        
                        # 输出区块信息
                        f.write(f"区块 ({abs_cx}, {abs_cz}) 存在\n")
                        
                        # 准备区块数据
                        chunk_data = {
                            "coords": [abs_cx, abs_cz]
                        }
                        
                        # 处理实体数据
                        try:
                            if hasattr(chunk, 'entities') and chunk.entities:
                                entity_count = len(chunk.entities)
                                f.write(f"  实体数量: {entity_count}\n")
                                chunk_data["entity_count"] = entity_count
                        except:
                            pass
                        
                        # 处理方块实体数据
                        try:
                            if hasattr(chunk, 'tile_entities') and chunk.tile_entities:
                                tile_entity_count = len(chunk.tile_entities)
                                f.write(f"  方块实体数量: {tile_entity_count}\n")
                                chunk_data["tile_entity_count"] = tile_entity_count
                                
                                # 统计方块实体类型
                                entity_types = {}
                                for entity in chunk.tile_entities:
                                    if 'id' in entity:
                                        entity_id = str(entity['id'].value)
                                        entity_types[entity_id] = entity_types.get(entity_id, 0) + 1
                                
                                if entity_types:
                                    f.write("  方块实体类型:\n")
                                    for entity_type, count in entity_types.items():
                                        f.write(f"    {entity_type}: {count}\n")
                                    chunk_data["entity_types"] = entity_types
                        except:
                            pass
                        
                        # 将区块数据添加到结果
                        region_data["chunks"].append(chunk_data)
                        
                        # 达到最大区块数后停止
                        if chunks_found >= max_chunks:
                            f.write(f"\n达到最大区块处理数 {max_chunks}，停止分析\n")
                            break
                    
                    except ChunkNotFound:
                        # 区块不存在，跳过
                        pass
                    except Exception as e:
                        # 其他错误
                        error_str = str(e)
                        if len(error_str) > 100:
                            error_str = error_str[:100] + "..."
                        f.write(f"  读取区块 ({abs_cx}, {abs_cz}) 时出错: {error_str}\n")
                
                # 达到最大区块数后停止外层循环
                if chunks_found >= max_chunks:
                    break
            
            # 写入区域摘要
            f.write(f"\n区域摘要:\n")
            f.write(f"找到的区块数量: {len(region_data['chunks'])}\n")
        
        # 同时保存JSON格式的分析结果
        json_output_path = output_file_path.replace('.txt', '.json')
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(region_data, f, ensure_ascii=False, indent=2)
        
        print(f"分析完成，结果保存至 {output_file_path} 和 {json_output_path}")
        return output_file_path
        
    except Exception as e:
        error_message = f"分析 {mca_file_path} 时出错: {str(e)}"
        print(error_message)
        traceback.print_exc()
        
        # 记录错误到文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(error_message)
        
        return output_file_path

if __name__ == "__main__":
    # 选择一个区域文件进行分析
    mca_file = os.path.join("save_world", "region", "r.-1.5.mca")
    output_file = "r.-1.5.mca_analysis.txt"
    
    # 限制最大区块数量，以防文件过大
    analyze_mca_file(mca_file, output_file, max_chunks=50) 