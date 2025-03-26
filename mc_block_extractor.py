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

class MCBlockExtractor:
    """
    从Minecraft区域文件(.mca)中提取所有方块信息的工具类
    支持1.7.10及以上版本的Minecraft存档
    """
    
    def __init__(self, mca_file_path):
        """初始化提取器"""
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
        self.total_blocks = 0
    
    def read_mca_file(self):
        """读取MCA文件并提取其内容"""
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
                            
                            # 提取这个区块的方块数据
                            self.extract_chunk_blocks(chunk_x, chunk_z, compression_type, compressed_data)
                    except Exception as e:
                        self.error_count += 1
                        print(f"处理区块 ({chunk_x}, {chunk_z}) 时出错: {str(e)}")
            
            return True
        except Exception as e:
            print(f"读取MCA文件时出错: {str(e)}")
            return False
    
    def extract_chunk_blocks(self, chunk_x, chunk_z, compression_type, compressed_data):
        """提取单个区块中的所有方块数据"""
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
            
            # 初始化区块信息
            chunk_info = {
                "coords": [chunk_x, chunk_z],
                "blocks": []
            }
            
            # 提取区块中的方块数据
            if "Level" in nbt_data.tag:
                level_tag = nbt_data.tag["Level"]
                
                # 提取区块中的所有区段（Sections）数据
                if "Sections" in level_tag:
                    sections = level_tag["Sections"]
                    
                    for section in sections:
                        # 每个区段的Y坐标（表示区段在Y轴上的位置，乘以16得到方块坐标）
                        section_y = int(section["Y"])
                        
                        # 处理不同版本的方块数据存储格式
                        if "Blocks" in section:
                            # 1.7.10 - 1.12.2格式（旧格式）
                            blocks = section["Blocks"]
                            data = section.get("Data", None)  # 方块附加数据
                            
                            # 遍历该区段中的所有方块
                            for y in range(16):
                                for z in range(16):
                                    for x in range(16):
                                        index = y * 256 + z * 16 + x
                                        if index < len(blocks):
                                            block_id = blocks[index]
                                            
                                            # 获取附加数据（Minecraft使用半字节存储Data值）
                                            block_data = 0
                                            if data is not None and index // 2 < len(data):
                                                if index % 2 == 0:
                                                    block_data = data[index // 2] & 0x0F
                                                else:
                                                    block_data = (data[index // 2] >> 4) & 0x0F
                                            
                                            # 跳过空气方块以减少数据量
                                            if block_id != 0:  # 0 = 空气
                                                # 计算绝对坐标
                                                abs_x = chunk_x * 16 + x
                                                abs_y = section_y * 16 + y
                                                abs_z = chunk_z * 16 + z
                                                
                                                # 转换为字符串ID
                                                block_key = f"{block_id}:{block_data}"
                                                
                                                # 添加到区块的方块列表
                                                block_info = {
                                                    "position": [abs_x, abs_y, abs_z],
                                                    "id": block_key
                                                }
                                                chunk_info["blocks"].append(block_info)
                                                
                                                # 更新统计信息
                                                self.block_stats[block_key] += 1
                                                self.total_blocks += 1
                        
                        elif "BlockStates" in section and "Palette" in section:
                            # 1.13+格式（新格式 - 使用调色板）
                            # 这是一个更复杂的数据格式，需要特殊处理
                            # 目前只是记录有这样的区段，实际解析需要更多代码
                            chunk_info["has_modern_format"] = True
                            print(f"区块 ({chunk_x}, {chunk_z}) 使用现代区块格式（1.13+），暂不支持提取详细方块数据")
            
            # 将区块信息添加到结果中
            if chunk_info.get("blocks") or chunk_info.get("has_modern_format"):
                self.chunks_data.append(chunk_info)
                self.analyzed_chunks += 1
            
        except Exception as e:
            self.error_count += 1
            print(f"提取区块 ({chunk_x}, {chunk_z}) 的方块时出错: {str(e)}")
    
    def get_results(self):
        """获取分析结果"""
        return {
            "file_name": self.file_name,
            "region_coords": [self.region_x, self.region_z],
            "analyzed_chunks": self.analyzed_chunks,
            "error_count": self.error_count,
            "total_blocks": self.total_blocks,
            "block_stats": dict(self.block_stats),
            "chunks": self.chunks_data
        }
    
    def save_results(self, output_json=None, output_summary=None):
        """保存提取结果到文件"""
        if output_json is None:
            output_json = f"{self.file_name}_blocks.json"
        
        if output_summary is None:
            output_summary = f"{self.file_name}_summary.txt"
        
        # 获取结果
        results = self.get_results()
        
        # 保存JSON数据
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存摘要文本
        with open(output_summary, 'w', encoding='utf-8') as f:
            f.write(f"Minecraft区域文件方块提取报告\n")
            f.write(f"========================\n\n")
            f.write(f"文件: {self.file_name}\n")
            f.write(f"区域坐标: {self.region_x}, {self.region_z}\n")
            f.write(f"分析区块数: {self.analyzed_chunks}\n")
            f.write(f"错误次数: {self.error_count}\n")
            f.write(f"总方块数: {self.total_blocks}\n\n")
            
            if self.block_stats:
                f.write("方块统计 (按数量排序):\n")
                for block_id, count in sorted(self.block_stats.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {block_id}: {count}\n")
            
        print(f"提取完成，结果保存至 {output_json} 和 {output_summary}")
        return output_json, output_summary


def extract_blocks_from_region_files(save_dir, output_dir=None):
    """从多个区域文件中提取方块信息"""
    if output_dir is None:
        output_dir = "block_data"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取region目录
    region_dir = os.path.join(save_dir, "region")
    if not os.path.exists(region_dir):
        print(f"找不到region目录: {region_dir}")
        return False
    
    # 获取所有mca文件
    mca_files = [f for f in os.listdir(region_dir) if f.endswith(".mca")]
    
    if not mca_files:
        print(f"在 {region_dir} 中找不到mca文件")
        return False
    
    print(f"找到 {len(mca_files)} 个区域文件，开始提取方块信息...")
    
    # 处理每个区域文件
    for i, mca_file in enumerate(mca_files):
        mca_path = os.path.join(region_dir, mca_file)
        print(f"处理文件 {i+1}/{len(mca_files)}: {mca_file}")
        
        start_time = time.time()
        extractor = MCBlockExtractor(mca_path)
        success = extractor.read_mca_file()
        
        if success:
            # 保存结果到输出目录
            json_file = os.path.join(output_dir, f"{mca_file}_blocks.json")
            summary_file = os.path.join(output_dir, f"{mca_file}_summary.txt")
            extractor.save_results(json_file, summary_file)
            
            elapsed_time = time.time() - start_time
            print(f"  完成，提取了 {extractor.total_blocks} 个方块，耗时: {elapsed_time:.2f}秒")
        else:
            print(f"  提取失败")
    
    print(f"\n所有区域文件处理完成，结果保存在 {output_dir} 目录")
    return True


def main():
    """主函数"""
    # 指定存档目录 - 这里使用题目要求的路径
    save_dir = "save_world/test"
    
    # 创建输出目录
    output_dir = "extracted_blocks"
    
    # 提取方块数据
    success = extract_blocks_from_region_files(save_dir, output_dir)
    
    if success:
        print("\n方块数据提取任务完成！")
    else:
        print("\n方块数据提取任务失败！")


if __name__ == "__main__":
    main() 