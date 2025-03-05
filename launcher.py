#!/usr/bin/env python3
"""
Light Analyzer启动器脚本
用于正确设置环境并启动应用程序
"""

import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox

def setup_environment():
    """设置运行环境"""
    try:
        # 获取执行文件所在目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            app_dir = os.path.dirname(sys.executable)
        else:
            # 如果是源码运行
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 确保在正确的工作目录
        os.chdir(app_dir)
        
        # 添加到Python路径
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        
        return True
    except Exception as e:
        error_msg = f"设置环境时出错:\n{str(e)}\n\n{traceback.format_exc()}"
        try:
            # 尝试使用GUI显示错误
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except:
            # 如果GUI失败，使用控制台输出
            print(error_msg)
        return False

def main():
    """主函数"""
    if not setup_environment():
        sys.exit(1)
    
    try:
        from light_analyzer.main import main as app_main
        app_main()
    except ImportError as e:
        error_msg = f"导入错误:\n{str(e)}\n可能是依赖库未正确安装。"
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except:
            print(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"启动失败:\n{str(e)}\n\n{traceback.format_exc()}"
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("运行错误", error_msg)
            root.destroy()
        except:
            print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
