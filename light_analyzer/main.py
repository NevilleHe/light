#!/usr/bin/env python3
"""
Light Analyzer主程序

该模块支持以下两种运行方式：
1. 作为独立程序直接运行
2. 作为包的一部分被其他模块导入

当直接运行时，会自动添加父目录到Python路径以支持模块导入。
"""

import os
import sys
import atexit

# 如果是直接运行此文件，添加父目录到Python路径
if __name__ == "__main__":
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# 基础库导入
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

# matplotlib配置（必须在导入pyplot之前设置）
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# 导入自定义模块
from .temperature_model import WALL_THICKNESS, MATERIAL_PROPERTIES, calculate_slice_temperature
from .visualization import draw_container, draw_temperature_plot
from .ui_windows import ContainerSettingsWindow, LightSettingsWindow, ValueAdjuster

def cleanup():
    """清理资源并确保程序完全退出"""
    try:
        plt.close('all')
        os._exit(0)
    except:
        pass

class ContainerAnalyzer(tk.Tk):
    """封闭容器中灯泡温度分析器的主界面类
    
    处理容器显示、温度计算和用户界面交互。
    温度显示会自动限制在合理范围内（环境温度±50°C）。
    """
    def __init__(self):
        super().__init__()

        self.title("封闭容器中的灯泡温度分析器")
        self.geometry("1400x900")

        # 配置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 初始化参数
        self.init_parameters()
        
        # 创建界面
        self.create_interface()
        
        # 初始化网格和绘图
        self.initialize_grid()
        self.update_plot()

    def init_parameters(self):
        """初始化所有参数"""
        # 容器参数
        self.container_size = (0.6, 0.4, 0.4)  # 长宽高(m)
        self.wall_thickness = WALL_THICKNESS  # 容器壁厚(m)
        # 初始化所有面为PP塑料
        self.face_materials = {
            "front": "PP", "back": "PP", "left": "PP",
            "right": "PP", "top": "PP", "bottom": "PP"
        }
        self.hole_params = None
        
        # 灯具参数
        self.has_shade = False
        self.shade_params = None
        self.bulb_pos = None  # 将在initialize_grid中设置
        
        # 温度相关参数
        self.power_var = tk.DoubleVar(value=15)
        self.temp_var = tk.DoubleVar(value=20)
        
        # 剖切面参数
        self.plane_var = tk.StringVar(value="XY")
        self.x_slice_var = tk.DoubleVar(value=30)
        self.y_slice_var = tk.DoubleVar(value=20)
        self.z_slice_var = tk.DoubleVar(value=20)

    def create_interface(self):
        """创建用户界面"""
        # 创建菜单栏
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="参数设置", menu=settings_menu)
        settings_menu.add_command(label="容器参数", command=self.show_container_settings)
        settings_menu.add_command(label="灯具参数", command=self.show_light_settings)
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建控制面板和图形区域
        self.create_control_panel(main_frame)
        self.create_plot_area(main_frame)

    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 功率控制
        power_frame = ttk.LabelFrame(control_frame, text="功率设置")
        power_frame.pack(fill=tk.X, padx=5, pady=5)
        power_adjuster = ValueAdjuster(power_frame, 
                                     "功率 (W):", 
                                     self.power_var, 1, 100, 1,
                                     decimal_places=0)
        power_adjuster.pack(fill=tk.X, padx=5, pady=2)

        # 环境温度控制
        temp_frame = ttk.LabelFrame(control_frame, text="环境温度")
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        temp_adjuster = ValueAdjuster(temp_frame, 
                                    "温度 (°C):", 
                                    self.temp_var, 10, 30, 1,
                                    decimal_places=0)
        temp_adjuster.pack(fill=tk.X, padx=5, pady=2)

        # 剖切面控制
        self.create_slice_controls(control_frame)

        # 信息显示区域
        self.info_label = ttk.Label(control_frame, text="", wraplength=800)
        self.info_label.pack(fill=tk.X, padx=5, pady=5)

        return control_frame

    def create_slice_controls(self, parent):
        """创建剖切面控制"""
        slice_frame = ttk.LabelFrame(parent, text="剖切面控制")
        slice_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 剖切位置控制
        controls = [
            ("X轴位置 (cm):", self.x_slice_var, 0, 60, 1),
            ("Y轴位置 (cm):", self.y_slice_var, 0, 40, 1),
            ("Z轴位置 (cm):", self.z_slice_var, 0, 40, 1)
        ]
        
        for text, var, min_val, max_val, increment in controls:
            adjuster = ValueAdjuster(slice_frame, text, var, 
                                   min_val, max_val, increment,
                                   decimal_places=1)
            adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        # 剖切面选择
        plane_frame = ttk.Frame(slice_frame)
        plane_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(plane_frame, text="剖切面:").pack(side=tk.LEFT)
        for plane in ["XY", "YZ", "XZ"]:
            ttk.Radiobutton(plane_frame, text=plane,
                          variable=self.plane_var,
                          value=plane).pack(side=tk.LEFT, padx=10)

    def create_plot_area(self, parent):
        """创建图形显示区域"""
        self.fig = plt.figure(figsize=(12, 6))
        self.fig.set_size_inches(12, 6, forward=True)
        
        # 固定子图位置和大小
        container_pos = [0.05, 0.15, 0.42, 0.7]  # left, bottom, width, height
        self.temp_pos = [0.55, 0.15, 0.35, 0.7]
        
        self.container_ax = self.fig.add_axes(container_pos, projection='3d')
        self.temp_ax = self.fig.add_axes(self.temp_pos)
        
        # 将matplotlib图形嵌入tkinter窗口
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()
        
        # 绑定更新事件
        for var in [self.power_var, self.temp_var, 
                   self.x_slice_var, self.y_slice_var, self.z_slice_var]:
            var.trace_add("write", self.update_plot)
        self.plane_var.trace_add("write", self.update_plot)

    def initialize_grid(self):
        """初始化计算网格"""
        # 灯泡位置（顶部中心）
        self.bulb_pos = np.array([
            self.container_size[0]/2,
            self.container_size[1]/2,
            self.container_size[2]
        ])

    def update_plot(self, *args):
        """更新图形显示
        
        根据当前设置更新容器显示和温度分布。
        温度显示会自动限制在环境温度±50°C的范围内。
        """
        try:
            # 准备剖切面位置
            slice_pos = np.array([
                self.x_slice_var.get() / 100,
                self.y_slice_var.get() / 100,
                self.z_slice_var.get() / 100
            ])
            
            # 更新3D容器视图
            draw_container(
                self.container_ax,
                self.container_size,
                self.face_materials['front'],
                self.face_materials['back'],
                self.face_materials['left'],
                self.face_materials['right'],
                self.face_materials['top'],
                self.face_materials['bottom'],
                self.hole_params,
                self.bulb_pos,
                self.has_shade,
                self.shade_params,
                self.plane_var.get(),
                slice_pos
            )
            
            # 移除旧的colorbar
            for cbar in self.fig.get_axes():
                if cbar.get_label() == 'colorbar':
                    self.fig.delaxes(cbar)
            
            # 计算温度分布
            coords, temps = calculate_slice_temperature(
                plane=self.plane_var.get(),
                pos=slice_pos,
                container_size=self.container_size,
                power=self.power_var.get(),
                t_amb=self.temp_var.get(),
                bulb_pos=self.bulb_pos,
                wall_thickness=self.wall_thickness,
                front_material=self.face_materials['front'],
                back_material=self.face_materials['back'],
                left_material=self.face_materials['left'],
                right_material=self.face_materials['right'],
                top_material=self.face_materials['top'],
                bottom_material=self.face_materials['bottom'],
                has_hole=bool(self.hole_params),
                hole_face=self.hole_params['face'] if self.hole_params else None,
                hole_type=self.hole_params['type'] if self.hole_params else None,
                hole_x=float(self.hole_params['x']) if self.hole_params else 0.0,
                hole_y=float(self.hole_params['y']) if self.hole_params else 0.0,
                hole_diameter=float(self.hole_params['diameter']) if self.hole_params and self.hole_params['type'] == 'circle' else 0.0,
                hole_width=float(self.hole_params['width']) if self.hole_params and self.hole_params['type'] == 'rectangle' else 0.0,
                hole_height=float(self.hole_params['height']) if self.hole_params and self.hole_params['type'] == 'rectangle' else 0.0,
                has_shade=self.has_shade,
                shade_height=float(self.shade_params['height']) if self.has_shade and self.shade_params else 0.0,
                shade_angle_h=float(self.shade_params['angle_h']) if self.has_shade and self.shade_params else 0.0,
                shade_angle_v=float(self.shade_params['angle_v']) if self.has_shade and self.shade_params else 0.0,
                shade_top_radius=float(self.shade_params['top_radius']) if self.has_shade and self.shade_params else 0.0,
                shade_bottom_radius=float(self.shade_params['bottom_radius']) if self.has_shade and self.shade_params else 0.0
            )
            
            # 设置坐标轴范围
            if self.plane_var.get() == "XY":
                xlims = (0, self.container_size[0])
                ylims = (0, self.container_size[1])
            elif self.plane_var.get() == "YZ":
                xlims = (0, self.container_size[1])
                ylims = (0, self.container_size[2])
            else:  # XZ
                xlims = (0, self.container_size[0])
                ylims = (0, self.container_size[2])
            
            # 限制温度显示范围
            temps = np.clip(temps,
                          self.temp_var.get() - 10,  # 最低显示到环境温度-10°C
                          self.temp_var.get() + 50)  # 最高显示到环境温度+50°C
            
            # 绘制温度分布图
            im = draw_temperature_plot(
                self.temp_ax,
                coords,
                temps,
                self.temp_var.get(),
                self.plane_var.get(),
                xlims,
                ylims
            )
            
            # 添加颜色条
            cax = self.fig.add_axes([0.92, 0.15, 0.02, 0.7])
            cbar = self.fig.colorbar(im, cax=cax)
            cbar.set_label('温度 (°C)')
            cbar.ax.set_label('colorbar')
            
            # 重置温度图的位置和大小
            self.temp_ax.set_position(self.temp_pos)
            
            # 更新canvas
            self.canvas.draw_idle()
            
            # 计算并显示温度统计信息
            wall_mask = self.get_wall_mask(temps.shape)
            wall_temps = temps[wall_mask]
            inner_temps = temps[~wall_mask]
            
            self.update_temperature_info(wall_temps, inner_temps)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"更新图形时出错: {str(e)}")
            self.info_label.config(text="更新图形时出错，请检查参数设置")
    
    def get_wall_mask(self, shape):
        """获取壁面温度点的掩码"""
        wall_mask = np.zeros(shape, dtype=bool)
        
        if self.plane_var.get() == "XY":
            wall_mask[0,:] = True  # 前壁
            wall_mask[-1,:] = True  # 后壁
            wall_mask[:,0] = True  # 左壁
            wall_mask[:,-1] = True  # 右壁
        elif self.plane_var.get() == "YZ":
            wall_mask[:,0] = True  # 底面
            wall_mask[:,-1] = True  # 顶面
            wall_mask[0,:] = True  # 前壁
            wall_mask[-1,:] = True  # 后壁
        else:  # XZ
            wall_mask[:,0] = True  # 底面
            wall_mask[:,-1] = True  # 顶面
            wall_mask[0,:] = True  # 左壁
            wall_mask[-1,:] = True  # 右壁
        
        return wall_mask
    
    def update_temperature_info(self, wall_temps, inner_temps):
        """更新温度信息显示"""
        wall_max = np.max(wall_temps)
        wall_min = np.min(wall_temps)
        inner_max = np.max(inner_temps)
        inner_min = np.min(inner_temps)
        
        # 精简信息显示格式
        self.info_label.config(
            text=(
                f"当前参数:\n"
                f"• 功率: {self.power_var.get():.0f} W\n"
                f"• 环境温度: {self.temp_var.get():.0f} °C\n\n"
                f"温度分析:\n"
                f"• 容器壁: {wall_min:.1f} ~ {wall_max:.1f} °C\n"
                f"• 容器内: {inner_min:.1f} ~ {inner_max:.1f} °C"
            )
        )

    def show_container_settings(self):
        """显示容器参数设置窗口"""
        ContainerSettingsWindow(self)
    
    def show_light_settings(self):
        """显示灯具参数设置窗口"""
        LightSettingsWindow(self)

def main():
    """启动主程序"""
    app = ContainerAnalyzer()
    app.protocol("WM_DELETE_WINDOW", cleanup)
    try:
        app.mainloop()
    finally:
        cleanup()

if __name__ == "__main__":
    main()
