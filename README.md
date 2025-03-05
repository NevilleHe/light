# Light Analyzer

封闭容器中的灯泡温度分析器，用于分析和可视化不同情况下容器内的温度分布。
（最终目的用于爬虫箱/Reptile Terrarium内温度环境构建，目前为测试版）

## 功能特性

- 3D容器显示和温度分布可视化
- 支持多种材料的容器壁
- 可配置开孔和灯罩
- 实时温度分析和数据显示
- 完整的参数配置界面

## 系统要求

- Windows 10 或更高版本
- Python 3.8 或更高版本（仅开发时需要）
- 显示器分辨率建议 1920x1080 或更高

## 快速开始

### 运行已编译程序

1. 下载发布包中的 LightAnalyzer.exe
2. 双击运行即可

## 开发指南

### 项目结构
```
light_analyzer/
├── assets/           # 资源文件
├── __init__.py
├── main.py          # 主程序
├── temperature_model.py  # 温度计算模型
├── visualization.py  # 可视化模块
└── ui_windows.py    # 界面窗口
```

### 构建说明

1. 终端运行 `pyinstaller LightAnalyzer.spec`命令从源码构建
3. 编译后的文件位于 `dist/` 目录下

## 故障排除

如果遇到问题：
1. 运行 `check_env.py` 检查环境
2. 检查 log 文件中的详细错误信息
3. 确保运行环境中的 Python 版本正确
4. 尝试重新安装依赖包

## 使用协议

本软件仅供学习和研究使用。

## 技术支持

如有问题或建议，请提交 issue 或联系开发团队。
