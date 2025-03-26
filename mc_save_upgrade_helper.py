#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import shutil
from collections import defaultdict

# 导入mc_save_analyzer模块
from mc_save_analyzer import MCRegionAnalyzer, analyze_multiple_mca_files

class MinecraftSaveUpgradeHelper:
    """
    Minecraft存档升级助手类
    帮助识别并分析可能在版本升级中存在问题的区块或实体
    """
    
    def __init__(self, save_dir, output_dir="upgrade_analysis"):
        """初始化升级助手"""
        self.save_dir = save_dir
        self.output_dir = output_dir
        self.region_dir = os.path.join(save_dir, "region")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 分析结果
        self.problematic_entity_types = []
        self.problematic_tile_entity_types = []
        self.entity_stats = defaultdict(int)
        self.tile_entity_stats = defaultdict(int)
        self.chunks_with_issues = []
    
    def set_problematic_entities(self, entity_list):
        """设置可能在升级中有问题的实体类型"""
        self.problematic_entity_types = entity_list
    
    def set_problematic_tile_entities(self, tile_entity_list):
        """设置可能在升级中有问题的方块实体类型"""
        self.problematic_tile_entity_types = tile_entity_list
    
    def analyze_save(self, max_files=None):
        """分析整个存档，查找可能有问题的区域"""
        if not os.path.exists(self.region_dir):
            print(f"找不到region目录: {self.region_dir}")
            return False
        
        # 获取所有mca文件
        mca_files = [f for f in os.listdir(self.region_dir) if f.endswith(".mca")]
        
        if not mca_files:
            print(f"在 {self.region_dir} 中找不到mca文件")
            return False
        
        # 限制分析文件数量（如果指定）
        if max_files and max_files > 0:
            mca_files = mca_files[:max_files]
        
        total_files = len(mca_files)
        print(f"找到 {total_files} 个区域文件，开始分析...")
        
        # 统计各种实体和方块实体
        for i, mca_file in enumerate(mca_files):
            mca_path = os.path.join(self.region_dir, mca_file)
            print(f"分析文件 {i+1}/{total_files}: {mca_file}")
            
            # 使用MCRegionAnalyzer分析区域文件
            analyzer = MCRegionAnalyzer(mca_path)
            success = analyzer.read_mca_file()
            
            if success:
                # 更新统计信息
                for entity_type, count in analyzer.entity_stats.items():
                    self.entity_stats[entity_type] += count
                
                for tile_type, count in analyzer.tile_entity_stats.items():
                    self.tile_entity_stats[tile_type] += count
                
                # 标记有问题的区块
                for chunk in analyzer.chunks_data:
                    chunk_has_issue = False
                    issues = []
                    
                    # 检查是否包含有问题的实体
                    for entity in chunk.get("entities", []):
                        if entity.get("id") in self.problematic_entity_types:
                            chunk_has_issue = True
                            issues.append(f"问题实体: {entity.get('id')}")
                    
                    # 检查是否包含有问题的方块实体
                    for tile_entity in chunk.get("tile_entities", []):
                        if tile_entity.get("id") in self.problematic_tile_entity_types:
                            chunk_has_issue = True
                            issues.append(f"问题方块实体: {tile_entity.get('id')}")
                    
                    if chunk_has_issue:
                        self.chunks_with_issues.append({
                            "file": mca_file,
                            "coords": chunk.get("coords"),
                            "issues": issues
                        })
        
        # 生成报告
        self.generate_report()
        
        return True
    
    def generate_report(self):
        """生成升级分析报告"""
        report_file = os.path.join(self.output_dir, "upgrade_analysis_report.txt")
        json_file = os.path.join(self.output_dir, "upgrade_analysis_report.json")
        
        # 准备报告数据
        report_data = {
            "save_directory": self.save_dir,
            "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "entity_stats": dict(self.entity_stats),
            "tile_entity_stats": dict(self.tile_entity_stats),
            "problematic_entity_types": self.problematic_entity_types,
            "problematic_tile_entity_types": self.problematic_tile_entity_types,
            "chunks_with_issues": self.chunks_with_issues
        }
        
        # 保存JSON报告
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # 保存文本报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Minecraft存档升级分析报告\n")
            f.write("======================\n\n")
            f.write(f"存档目录: {self.save_dir}\n")
            f.write(f"分析时间: {report_data['analysis_time']}\n\n")
            
            # 写入实体统计
            f.write("实体统计:\n")
            for entity_type, count in sorted(self.entity_stats.items(), key=lambda x: x[1], reverse=True):
                problematic = " (可能有问题)" if entity_type in self.problematic_entity_types else ""
                f.write(f"  {entity_type}: {count}{problematic}\n")
            f.write("\n")
            
            # 写入方块实体统计
            f.write("方块实体统计:\n")
            for tile_type, count in sorted(self.tile_entity_stats.items(), key=lambda x: x[1], reverse=True):
                problematic = " (可能有问题)" if tile_type in self.problematic_tile_entity_types else ""
                f.write(f"  {tile_type}: {count}{problematic}\n")
            f.write("\n")
            
            # 写入问题区块信息
            if self.chunks_with_issues:
                f.write(f"发现 {len(self.chunks_with_issues)} 个可能存在升级问题的区块:\n")
                for i, chunk in enumerate(self.chunks_with_issues[:100]):  # 限制显示100个
                    f.write(f"  {i+1}. 文件: {chunk['file']}, 坐标: {chunk['coords']}\n")
                    for issue in chunk['issues']:
                        f.write(f"     - {issue}\n")
                
                if len(self.chunks_with_issues) > 100:
                    f.write(f"  ... 还有 {len(self.chunks_with_issues) - 100} 个区块 (查看JSON文件获取完整列表)\n")
            else:
                f.write("未发现可能存在升级问题的区块\n")
        
        print(f"分析报告已保存到 {report_file} 和 {json_file}")
    
    def recommend_backup_strategy(self):
        """提供存档备份建议"""
        backup_file = os.path.join(self.output_dir, "backup_recommendations.txt")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("Minecraft存档升级备份建议\n")
            f.write("======================\n\n")
            
            f.write("1. 备份整个存档文件夹\n")
            f.write("   在升级之前，请先创建整个存档文件夹的完整备份。\n")
            f.write("   可以简单地复制整个文件夹，或使用压缩软件创建归档。\n\n")
            
            f.write("2. 问题区块处理建议\n")
            if self.chunks_with_issues:
                f.write(f"   发现 {len(self.chunks_with_issues)} 个可能有问题的区块。建议在升级前：\n")
                f.write("   - 访问这些区域并移除有问题的实体/方块\n")
                f.write("   - 或者使用MCEdit等工具删除这些区块，让游戏重新生成\n")
            else:
                f.write("   未发现明显问题区块，正常升级即可。\n\n")
            
            f.write("3. 升级步骤建议\n")
            f.write("   - 对于跨多个版本的大跨度升级，建议逐步升级而不是一次性升级到最终版本\n")
            f.write("   - 例如：1.7.10 → 1.12.2 → 1.16.5 → 1.20.x\n")
            f.write("   - 每一步升级后，先在游戏中加载并测试存档是否正常\n\n")
            
            f.write("4. 额外建议\n")
            f.write("   - 使用专业工具如Amulet或MCEdit检查和修复存档\n")
            f.write("   - 对于有大量模组方块的存档，升级可能导致模组方块消失或替换\n")
            f.write("   - 记录模组ID和方块ID的对应关系，以便在升级后恢复\n")
        
        print(f"备份建议已保存到 {backup_file}")


def main():
    """主函数"""
    # 定义存档目录
    save_dir = "save_world"
    output_dir = "upgrade_analysis"
    
    # 创建升级助手
    upgrade_helper = MinecraftSaveUpgradeHelper(save_dir, output_dir)
    
    # 设置可能在1.7.10升级到新版本时有问题的实体和方块实体
    problematic_entities = [
        "Minecart",  # 矿车可能会有变化
        "Boat",      # 船的机制有变化
        "ItemFrame", # 物品展示框的一些属性变化
        "Vehicle",   # 模组添加的交通工具
        "IC2.",      # IC2模组实体
        "BambooMod" # 模组实体
    ]
    
    problematic_tile_entities = [
        "RCHiddenTile",  # 铁路工艺模组的方块
        "CF-Wall",       # 模组方块
        "BambooMultiBlock", # 模组复杂方块
        "IC2NC",         # IC2模组方块
        "Tile",          # 许多模组方块前缀
        "TileArcaneLamp" # 神秘时代模组方块
    ]
    
    upgrade_helper.set_problematic_entities(problematic_entities)
    upgrade_helper.set_problematic_tile_entities(problematic_tile_entities)
    
    # 分析存档
    print("开始分析存档以准备升级...")
    upgrade_helper.analyze_save(max_files=5)  # 限制分析前5个区域文件，设为None则分析全部
    
    # 生成备份建议
    upgrade_helper.recommend_backup_strategy()
    
    print("\n分析完成！请查看upgrade_analysis目录中的报告。")


if __name__ == "__main__":
    main() 