# Minecraft存档分析与升级助手

这个工具用于分析Minecraft Java版存档文件（尤其是老版本的1.7.10存档），并帮助进行存档升级。

## 功能特点

1. **区域文件分析**：解析Minecraft的.mca区域文件，提取区块、实体和方块实体信息
2. **升级风险评估**：识别在版本升级过程中可能出现问题的实体和方块实体
3. **升级建议生成**：提供针对特定存档的备份策略和升级路径建议
4. **兼容性**：专为支持1.7.10到1.20+版本范围设计

## 安装依赖

```bash
pip install amulet-nbt
```

## 使用方法

### 基本用法

1. 将您要分析的Minecraft存档文件夹放在`save_world`目录下
2. 运行区域文件分析脚本：
   ```
   python mc_save_analyzer.py
   ```
3. 运行升级助手脚本：
   ```
   python mc_save_upgrade_helper.py
   ```
4. 查看生成的报告文件：
   - `analysis_results/` - 包含区域文件分析结果
   - `upgrade_analysis/` - 包含升级建议和问题区块报告

### 自定义分析

您可以修改`mc_save_upgrade_helper.py`中的`problematic_entities`和`problematic_tile_entities`列表，以适应特定模组或版本升级的需求。

## 脚本说明

- `analyze_minecraft_save.py`: 使用anvil-parser库的基础分析脚本
- `mc_save_analyzer.py`: 使用amulet-nbt库的高级分析脚本，支持更多细节提取
- `mc_save_upgrade_helper.py`: 升级助手主脚本，用于生成升级建议和问题区块报告

## 输出文件说明

- `.txt`文件：人类可读的分析报告
- `.json`文件：结构化的分析数据，可用于进一步处理

## 升级建议

对于1.7.10存档升级到新版本，建议分阶段进行：

1. 1.7.10 → 1.12.2
2. 1.12.2 → 1.16.5
3. 1.16.5 → 1.20.x

每个阶段后，先在游戏中测试存档是否正常加载。

## 注意事项

- 该工具主要用于分析原版和常见模组的方块/实体，对于复杂模组可能需要额外检查
- 在升级前务必进行完整备份
- 对于模组存档，如果不再使用相同的模组，可能会丢失所有模组添加的方块和物品 