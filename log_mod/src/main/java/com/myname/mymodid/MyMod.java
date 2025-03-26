package com.myname.mymodid;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.Date;

import net.minecraft.block.Block;
import net.minecraft.util.IIcon;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import cpw.mods.fml.common.Mod;
import cpw.mods.fml.common.SidedProxy;
import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPostInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;
import cpw.mods.fml.common.event.FMLServerStartingEvent;
import cpw.mods.fml.common.registry.FMLControlledNamespacedRegistry;
import cpw.mods.fml.common.registry.GameData;

@Mod(modid = MyMod.MODID, version = Tags.VERSION, name = "MyMod", acceptedMinecraftVersions = "[1.7.10]")
public class MyMod {

    public static final String MODID = "mymodid";
    public static final Logger LOG = LogManager.getLogger(MODID);
    private static final String LOG_FILE_NAME = "blocks_info.log";
    private PrintWriter fileLogger;
    private File logFile;

    @SidedProxy(clientSide = "com.myname.mymodid.ClientProxy", serverSide = "com.myname.mymodid.CommonProxy")
    public static CommonProxy proxy;

    @Mod.EventHandler
    // preInit "Run before anything else. Read your config, create blocks, items, etc, and register them with the
    // GameRegistry." (Remove if not needed)
    public void preInit(FMLPreInitializationEvent event) {
        // 设置自定义日志文件
        setupCustomLogger(
            event.getModConfigurationDirectory()
                .getParentFile());

        logInfo("初始化日志系统完成，日志文件将保存在: " + logFile.getAbsolutePath());
        proxy.preInit(event);
    }

    /**
     * 设置自定义日志文件
     * 
     * @param minecraftDir Minecraft根目录
     */
    private void setupCustomLogger(File minecraftDir) {
        try {
            // 创建日志文件路径
            File logDir = new File(minecraftDir, "logs");
            if (!logDir.exists()) {
                logDir.mkdirs();
            }
            logFile = new File(logDir, LOG_FILE_NAME);

            // 创建文件写入器
            fileLogger = new PrintWriter(new FileWriter(logFile));

            // 写入日志头部
            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            fileLogger.println("========================================");
            fileLogger.println("方块信息日志 - 生成时间: " + dateFormat.format(new Date()));
            fileLogger.println("Minecraft版本: 1.7.10");
            fileLogger.println("========================================");
            fileLogger.flush();

            LOG.info("自定义日志文件已设置: " + logFile.getAbsolutePath());
        } catch (IOException e) {
            LOG.error("创建自定义日志文件失败", e);
            // 如果创建失败，将fileLogger设为null
            fileLogger = null;
        }
    }

    /**
     * 记录信息到自定义日志文件和Minecraft日志
     */
    private void logInfo(String message) {
        // 记录到Minecraft日志
        LOG.info(message);

        // 记录到自定义文件
        if (fileLogger != null) {
            SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss");
            fileLogger.println("[" + timeFormat.format(new Date()) + "] " + message);
            fileLogger.flush(); // 立即刷新，确保数据写入文件
        }
    }

    /**
     * 记录错误到自定义日志文件和Minecraft日志
     */
    private void logError(String message, Throwable error) {
        // 记录到Minecraft日志
        LOG.error(message, error);

        // 记录到自定义文件
        if (fileLogger != null) {
            SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss");
            fileLogger.println("[" + timeFormat.format(new Date()) + "] [ERROR] " + message);
            if (error != null) {
                fileLogger.println("异常信息: " + error.getMessage());
            }
            fileLogger.flush();
        }
    }

    /**
     * 关闭日志文件
     */
    private void closeLogger() {
        if (fileLogger != null) {
            fileLogger.println("========================================");
            fileLogger.println("日志记录完成 - " + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
            fileLogger.println("========================================");
            fileLogger.flush();
            fileLogger.close();
        }
    }

    @Mod.EventHandler
    // load "Do your mod setup. Build whatever data structures you care about. Register recipes." (Remove if not needed)
    public void init(FMLInitializationEvent event) {
        proxy.init(event);
    }

    @Mod.EventHandler
    // postInit "Handle interaction with other mods, complete your setup based on this." (Remove if not needed)
    public void postInit(FMLPostInitializationEvent event) {
        proxy.postInit(event);

        // 在所有mod加载完成后记录方块信息
        logInfo("===== 开始记录所有已加载的方块 =====");
        logAllBlocks();
        logInfo("===== 方块记录完成 =====");

        // 关闭日志文件
        closeLogger();
    }

    @Mod.EventHandler
    // register server commands in this event handler (Remove if not needed)
    public void serverStarting(FMLServerStartingEvent event) {
        proxy.serverStarting(event);
    }

    /**
     * 记录所有已注册的方块及其纹理信息，并按照类型分类
     */
    private void logAllBlocks() {
        try {
            // 获取方块注册表
            FMLControlledNamespacedRegistry<Block> blockRegistry = GameData.getBlockRegistry();

            // 创建分类计数器
            int totalBlocks = 0;
            int standardBlocks = 0; // 所有面使用相同纹理
            int directionalBlocks = 0; // 不同面使用不同纹理
            int customRenderBlocks = 0; // 至少一个面返回null
            int errorBlocks = 0; // 获取纹理时抛出异常
            int unknownBlocks = 0; // 无法确定类型

            logInfo("===== 按类型统计方块 =====");

            // 准备分类日志
            logInfo("方块分类将记录在日志末尾的汇总部分");

            // 用于存储每种类型的方块
            StringBuilder standardBlocksList = new StringBuilder();
            StringBuilder directionalBlocksList = new StringBuilder();
            StringBuilder customRenderBlocksList = new StringBuilder();
            StringBuilder errorBlocksList = new StringBuilder();
            StringBuilder unknownBlocksList = new StringBuilder();

            // 遍历所有已注册的方块
            for (Object obj : blockRegistry) {
                if (obj instanceof Block) {
                    Block block = (Block) obj;
                    totalBlocks++;

                    // 获取方块ID、名称和解除本地化名称
                    int id = blockRegistry.getId(block);
                    String registryName = blockRegistry.getNameForObject(block);
                    String unlocalizedName = block.getUnlocalizedName();
                    String blockClass = block.getClass()
                        .getSimpleName();

                    // 记录基本信息
                    logInfo("方块ID: " + id + ", 注册名称: " + registryName + ", 未本地化名称: " + unlocalizedName);

                    // 检查方块类型
                    BlockTextureType textureType = analyzeBlockTextureType(block, registryName);

                    // 更新计数器并添加到相应分类列表
                    switch (textureType) {
                        case STANDARD:
                            standardBlocks++;
                            standardBlocksList.append("  ")
                                .append(registryName)
                                .append(" (")
                                .append(blockClass)
                                .append(")\n");
                            break;
                        case DIRECTIONAL:
                            directionalBlocks++;
                            directionalBlocksList.append("  ")
                                .append(registryName)
                                .append(" (")
                                .append(blockClass)
                                .append(")\n");
                            break;
                        case CUSTOM_RENDER:
                            customRenderBlocks++;
                            customRenderBlocksList.append("  ")
                                .append(registryName)
                                .append(" (")
                                .append(blockClass)
                                .append(")\n");
                            break;
                        case ERROR:
                            errorBlocks++;
                            errorBlocksList.append("  ")
                                .append(registryName)
                                .append(" (")
                                .append(blockClass)
                                .append(")\n");
                            break;
                        case UNKNOWN:
                        default:
                            unknownBlocks++;
                            unknownBlocksList.append("  ")
                                .append(registryName)
                                .append(" (")
                                .append(blockClass)
                                .append(")\n");
                            break;
                    }
                }
            }

            // 记录统计信息
            logInfo("\n===== 方块分类统计 =====");
            logInfo("总方块数: " + totalBlocks);
            logInfo("标准方块 (所有面相同纹理): " + standardBlocks + " (" + percentage(standardBlocks, totalBlocks) + "%)");
            logInfo("方向性方块 (不同面不同纹理): " + directionalBlocks + " (" + percentage(directionalBlocks, totalBlocks) + "%)");
            logInfo(
                "自定义渲染方块 (至少一个面无纹理): " + customRenderBlocks
                    + " ("
                    + percentage(customRenderBlocks, totalBlocks)
                    + "%)");
            logInfo("错误方块 (获取纹理发生异常): " + errorBlocks + " (" + percentage(errorBlocks, totalBlocks) + "%)");
            logInfo("未知类型方块: " + unknownBlocks + " (" + percentage(unknownBlocks, totalBlocks) + "%)");

            // 记录每种类型的方块列表
            logInfo("\n===== 标准方块列表 =====\n" + standardBlocksList.toString());
            logInfo("\n===== 方向性方块列表 =====\n" + directionalBlocksList.toString());
            logInfo("\n===== 自定义渲染方块列表 =====\n" + customRenderBlocksList.toString());
            logInfo("\n===== 错误方块列表 =====\n" + errorBlocksList.toString());
            if (unknownBlocks > 0) {
                logInfo("\n===== 未知类型方块列表 =====\n" + unknownBlocksList.toString());
            }

        } catch (Exception e) {
            logError("记录方块信息时发生错误", e);
        }
    }

    /**
     * 方块纹理类型枚举
     */
    private enum BlockTextureType {
        STANDARD, // 所有面使用相同纹理
        DIRECTIONAL, // 不同面使用不同纹理
        CUSTOM_RENDER, // 至少一个面返回null
        ERROR, // 获取纹理时抛出异常
        UNKNOWN // 无法确定类型
    }

    /**
     * 分析方块的纹理类型
     */
    private BlockTextureType analyzeBlockTextureType(Block block, String registryName) {
        logInfo("  分析方块纹理类型:");

        try {
            // 检查各个面的纹理
            IIcon[] faceIcons = new IIcon[6];
            boolean hasNullTexture = false;
            boolean allSame = true;

            // 先获取所有面的纹理图标
            for (int i = 0; i < 6; i++) {
                try {
                    faceIcons[i] = block.getIcon(i, 0);
                    if (faceIcons[i] == null) {
                        hasNullTexture = true;
                        logInfo("  面 " + i + " 纹理为null");
                    } else {
                        logInfo("  面 " + i + " 纹理: " + faceIcons[i].getIconName());
                    }
                } catch (Exception e) {
                    logInfo(
                        "  获取面 " + i
                            + " 纹理时出错: "
                            + e.getClass()
                                .getName()
                            + ": "
                            + e.getMessage());
                    return BlockTextureType.ERROR;
                }
            }

            // 比较所有非空纹理是否相同
            IIcon firstNonNull = null;
            for (int i = 0; i < 6; i++) {
                if (faceIcons[i] != null) {
                    if (firstNonNull == null) {
                        firstNonNull = faceIcons[i];
                    } else if (faceIcons[i] != firstNonNull) {
                        // 找到了不同的非空纹理
                        allSame = false;
                        break;
                    }
                }
            }

            // 确定类型
            if (hasNullTexture) {
                // 检查是否所有面都为null
                boolean allNull = true;
                for (IIcon icon : faceIcons) {
                    if (icon != null) {
                        allNull = false;
                        break;
                    }
                }

                if (allNull) {
                    logInfo("  结果: 所有面纹理均为null，可能使用完全自定义渲染");
                    return BlockTextureType.CUSTOM_RENDER;
                } else {
                    // 部分面为null，看剩余面是否相同
                    if (allSame) {
                        logInfo("  结果: 部分面无纹理，其余面纹理相同，可能是部分自定义渲染");
                    } else {
                        logInfo("  结果: 部分面无纹理，其余面纹理不同，混合渲染类型");
                    }
                    return BlockTextureType.CUSTOM_RENDER;
                }
            } else {
                // 所有面都有纹理
                if (allSame) {
                    logInfo("  结果: 所有面使用相同纹理，标准方块");
                    return BlockTextureType.STANDARD;
                } else {
                    logInfo("  结果: 不同面使用不同纹理，方向性方块");
                    return BlockTextureType.DIRECTIONAL;
                }
            }

        } catch (Exception e) {
            logInfo(
                "  分析纹理类型时发生错误: " + e.getClass()
                    .getName() + ": " + e.getMessage());
            return BlockTextureType.UNKNOWN;
        }
    }

    /**
     * 尝试获取并记录方块的纹理信息
     */
    private void tryLogBlockTextureInfo(Block block, String registryName) {
        try {
            // 记录方块类名
            String blockClassName = block.getClass()
                .getName();
            logInfo("  方块类型: " + blockClassName);

            // 检查所有面的纹理情况
            for (int i = 0; i < 6; i++) {
                try {
                    IIcon icon = block.getIcon(i, 0);
                    if (icon != null) {
                        try {
                            String iconName = icon.getIconName();
                            logInfo("  面 " + i + " 纹理名称: " + iconName);

                            // 安全地解析纹理路径
                            try {
                                if (iconName.contains(":")) {
                                    String modId = iconName.split(":")[0];
                                    String textureName = iconName.split(":")[1];
                                    String texturePath = modId + ":textures/blocks/" + textureName + ".png";
                                    logInfo("    可能的纹理文件路径: " + texturePath);
                                } else if (registryName.contains(":")) {
                                    String modId = registryName.split(":")[0];
                                    String texturePath = modId + ":textures/blocks/" + iconName + ".png";
                                    logInfo("    可能的纹理文件路径: " + texturePath);
                                }
                            } catch (Exception e) {
                                logInfo("    解析纹理路径时出错: " + e.getMessage());
                            }
                        } catch (Exception e) {
                            logInfo("    获取图标名称时出错: " + e.getMessage());
                        }
                    } else {
                        logInfo("  面 " + i + " 纹理为null，可能使用自定义渲染");
                    }
                } catch (Exception e) {
                    logInfo("  获取面 " + i + " 图标时出错: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            logInfo("  无法获取纹理信息: " + e.getMessage());
        }
    }

    /**
     * 计算百分比
     */
    private double percentage(int part, int total) {
        if (total == 0) return 0;
        return Math.round((double) part / total * 1000) / 10.0;
    }

}
