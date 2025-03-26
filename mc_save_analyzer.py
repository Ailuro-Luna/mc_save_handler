#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import struct
import gzip
import zlib
import time
import amulet_nbt as nbt
from io import BytesIO
from collections import defaultdict

class MCRegionAnalyzer:
    """
    使用amulet-nbt库分析Minecraft区域文件（.mca）的工具类
    支持旧版本的Minecraft存档（1.7.10及以上）
    """
    
    def __init__(self, mca_file_path):
        """初始化分析器"""
        self.mca_file_path = mca_file_path
        self.file_name = os.path.basename(mca_file_path)
        try:
            parts = self.file_name.replace('r.', '').replace('.mca', '').split('.')
            self.region_x = int(parts[0])
            self.region_z = int(parts[1])
        except:
            self.region_x = 0
            self.region_z = 0
        
        # 分析结果
        self.analyzed_chunks = 0
        self.chunks_data = []
        self.error_count = 0
        self.block_stats = defaultdict(int)
        self.entity_stats = defaultdict(int)
        self.tile_entity_stats = defaultdict(int)
    
    def read_mca_file(self):
        """读取MCA文件并分析其内容"""
        try:
            with open(self.mca_file_path, 'rb') as mca_file:
                # 读取头部
                header_data = mca_file.read(8192)  # 4096字节的位置信息 + 4096字节的时间戳信息
                
                # 分析区块位置和大小
                chunks_to_analyze = []
                for chunk_index in range(1024):  # 32x32区块
                    loc_offset = chunk_index * 4
                    sectors_data = header_data[loc_offset:loc_offset+3]
                    sectors_count = header_data[loc_offset+3]
                    
                    if sectors_count > 0:  # 区块存在
                        offset = struct.unpack('>I', b'\x00' + sectors_data)[0] * 4096  # 转换为字节偏移
                        size_in_sectors = sectors_count
                        
                        # 计算区块坐标
                        chunk_x = (self.region_x * 32) + (chunk_index % 32)
                        chunk_z = (self.region_z * 32) + (chunk_index // 32)
                        
                        chunks_to_analyze.append((chunk_index, chunk_x, chunk_z, offset, size_in_sectors))
                
                # 遍历并分析发现的区块
                for i, (chunk_index, chunk_x, chunk_z, offset, size_in_sectors) in enumerate(chunks_to_analyze):
                    try:
                        # 跳转到区块位置
                        mca_file.seek(offset)
                        
                        # 读取区块数据长度
                        length = struct.unpack('>I', mca_file.read(4))[0]
                        
                        if length > 0:
                            # 读取压缩类型
                            compression_type = struct.unpack('B', mca_file.read(1))[0]
                            
                            # 读取压缩数据
                            compressed_data = mca_file.read(length - 1)
                            
                            # 分析这个区块
                            self.analyze_chunk(chunk_x, chunk_z, compression_type, compressed_data)
                    except Exception as e:
                        self.error_count += 1
                        print(f"处理区块 ({chunk_x}, {chunk_z}) 时出错: {str(e)}")
            
            return True
        except Exception as e:
            print(f"读取MCA文件时出错: {str(e)}")
            return False
    
    def analyze_chunk(self, chunk_x, chunk_z, compression_type, compressed_data):
        """分析单个区块的数据"""
        try:
            # 解压区块数据
            if compression_type == 1:  # Gzip压缩
                data = gzip.decompress(compressed_data)
            elif compression_type == 2:  # Zlib压缩
                data = zlib.decompress(compressed_data)
            else:
                print(f"未知的压缩类型 {compression_type} (区块: {chunk_x}, {chunk_z})")
                return
            
            # 解析NBT数据
            nbt_data = nbt.load(BytesIO(data))
            
            # 提取区块信息
            chunk_info = {
                "coords": [chunk_x, chunk_z],
                "entities": [],
                "tile_entities": []
            }
            
            # 处理实体
            try:
                if "Entities" in nbt_data.tag["Level"]:
                    entities = nbt_data.tag["Level"]["Entities"]
                    for entity in entities:
                        if "id" in entity:
                            entity_id = str(entity["id"])
                            self.entity_stats[entity_id] += 1
                            
                            entity_info = {
                                "id": entity_id
                            }
                            
                            # 获取实体位置
                            if "Pos" in entity:
                                pos = entity["Pos"]
                                if len(pos) >= 3:
                                    entity_info["position"] = [
                                        float(pos[0]),
                                        float(pos[1]),
                                        float(pos[2])
                                    ]
                            
                            chunk_info["entities"].append(entity_info)
            except Exception as e:
                print(f"处理实体数据时出错 (区块: {chunk_x}, {chunk_z}): {str(e)}")
            
            # 处理方块实体
            try:
                if "TileEntities" in nbt_data.tag["Level"]:
                    tile_entities = nbt_data.tag["Level"]["TileEntities"]
                    for tile_entity in tile_entities:
                        if "id" in tile_entity:
                            tile_id = str(tile_entity["id"])
                            self.tile_entity_stats[tile_id] += 1
                            
                            tile_info = {
                                "id": tile_id
                            }
                            
                            # 获取方块位置
                            if all(k in tile_entity for k in ["x", "y", "z"]):
                                tile_info["position"] = [
                                    int(tile_entity["x"]),
                                    int(tile_entity["y"]),
                                    int(tile_entity["z"])
                                ]
                            
                            chunk_info["tile_entities"].append(tile_info)
            except Exception as e:
                print(f"处理方块实体数据时出错 (区块: {chunk_x}, {chunk_z}): {str(e)}")
            
            # 统计区块中的方块数据（基本信息）
            try:
                if "Sections" in nbt_data.tag["Level"]:
                    sections = nbt_data.tag["Level"]["Sections"]
                    for section in sections:
                        if "Blocks" in section:
                            blocks = section["Blocks"]
                            # 我们可以在这里统计方块类型，但这需要处理方块ID和数据值的映射
                            # 这对于1.7.10来说比较复杂
                            chunk_info["has_blocks"] = True
            except Exception as e:
                print(f"处理方块数据时出错 (区块: {chunk_x}, {chunk_z}): {str(e)}")
            
            # 保存区块信息
            self.chunks_data.append(chunk_info)
            self.analyzed_chunks += 1
            
        except Exception as e:
            self.error_count += 1
            print(f"分析区块 ({chunk_x}, {chunk_z}) 时出错: {str(e)}")
    
    def get_results(self):
        """获取分析结果"""
        return {
            "file_name": self.file_name,
            "region_coords": [self.region_x, self.region_z],
            "analyzed_chunks": self.analyzed_chunks,
            "error_count": self.error_count,
            "entity_stats": dict(self.entity_stats),
            "tile_entity_stats": dict(self.tile_entity_stats),
            "chunks": self.chunks_data
        }
    
    def save_analysis(self, output_txt=None, output_json=None):
        """保存分析结果到文件"""
        if output_txt is None:
            output_txt = f"{self.file_name}_analysis.txt"
        
        if output_json is None:
            output_json = f"{self.file_name}_analysis.json"
        
        # 获取结果
        results = self.get_results()
        
        # 保存文本报告
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(f"Minecraft区域文件分析报告\n")
            f.write(f"========================\n\n")
            f.write(f"文件: {self.file_name}\n")
            f.write(f"区域坐标: {self.region_x}, {self.region_z}\n")
            f.write(f"分析区块数: {self.analyzed_chunks}\n")
            f.write(f"错误次数: {self.error_count}\n\n")
            
            if self.entity_stats:
                f.write("实体统计:\n")
                for entity_id, count in sorted(self.entity_stats.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {entity_id}: {count}\n")
                f.write("\n")
            
            if self.tile_entity_stats:
                f.write("方块实体统计:\n")
                for tile_id, count in sorted(self.tile_entity_stats.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {tile_id}: {count}\n")
                f.write("\n")
            
            if self.chunks_data:
                f.write(f"区块详情 (显示前10个):\n")
                for i, chunk in enumerate(self.chunks_data[:10]):
                    f.write(f"区块 {i+1}: 坐标 {chunk['coords']}\n")
                    if chunk.get("entities"):
                        f.write(f"  实体数量: {len(chunk['entities'])}\n")
                    if chunk.get("tile_entities"):
                        f.write(f"  方块实体数量: {len(chunk['tile_entities'])}\n")
                    f.write("\n")
        
        # 保存JSON报告
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"分析完成，结果保存至 {output_txt} 和 {output_json}")
        return output_txt, output_json


def analyze_multiple_mca_files(save_dir, output_dir=None, max_files=3):
    """分析多个MCA文件并生成报告"""
    if output_dir is None:
        output_dir = "analysis_results"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取region目录
    region_dir = os.path.join(save_dir, "region")
    if not os.path.exists(region_dir):
        print(f"找不到region目录: {region_dir}")
        return
    
    # 获取所有mca文件
    mca_files = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
    
    if not mca_files:
        print(f"在 {region_dir} 中找不到mca文件")
        return
    
    print(f"找到 {len(mca_files)} 个mca文件，将分析前 {min(max_files, len(mca_files))} 个")
    
    # 分析选定的文件
    for i, mca_file in enumerate(mca_files[:max_files]):
        mca_path = os.path.join(region_dir, mca_file)
        print(f"分析文件 {i+1}/{min(max_files, len(mca_files))}: {mca_file}")
        
        start_time = time.time()
        analyzer = MCRegionAnalyzer(mca_path)
        success = analyzer.read_mca_file()
        
        if success:
            # 保存结果到输出目录
            txt_file = os.path.join(output_dir, f"{mca_file}_analysis.txt")
            json_file = os.path.join(output_dir, f"{mca_file}_analysis.json")
            analyzer.save_analysis(txt_file, json_file)
            
            elapsed_time = time.time() - start_time
            print(f"  完成，耗时: {elapsed_time:.2f}秒")
        else:
            print(f"  分析失败")


def main():
    """主函数"""
    # 定义存档目录
    save_dir = "save_world"
    
    # 创建输出目录
    output_dir = "analysis_results"
    
    # 分析多个文件
    analyze_multiple_mca_files(save_dir, output_dir, max_files=3)
    
    print("\n所有分析任务完成！")


if __name__ == "__main__":
    main() 