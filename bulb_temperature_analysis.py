import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import ttk
import os
from io import BytesIO
import atexit
import sys

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False     # 解决负号显示问题

# 物理参数设置
POWER = 15  # 灯泡功率 (W)
RADIUS = 0.025  # 灯泡半径 (m)
AIR_CONDUCTIVITY = 0.026  # 空气导热系数 (W/m·K)
SURFACE_HEAT_TRANSFER = 5  # 表面换热系数 (W/m²·K)

def cleanup():
    """清理资源并确保程序完全退出"""
    try:
        # 关闭所有matplotlib图形
        plt.close('all')
        
        # 强制退出程序
        os._exit(0)
    except:
        pass

# 注册退出处理程序
atexit.register(cleanup)

def find_31_degree_point(distance_grid, ambient_temp_grid, temp_grid):
    """找到温度最接近31度的点"""
    if len(temp_grid.shape) == 2:
        # 3D模式
        diff = np.abs(temp_grid - 31)
        i, j = np.unravel_index(diff.argmin(), diff.shape)
        return distance_grid[i,j], ambient_temp_grid[i,j], temp_grid[i,j]
    else:
        # 2D模式
        diff = np.abs(temp_grid - 31)
        idx = diff.argmin()
        return distance_grid[idx], None, temp_grid[idx]

def get_31_degree_contour(distance_grid, temp_grid, ambient_temps):
    """获取31度等温线上的点"""
    points = []
    for i, temp_row in enumerate(temp_grid):
        for j in range(len(temp_row)-1):
            if (temp_row[j] - 31) * (temp_row[j+1] - 31) <= 0:
                # 找到一个穿过31度的点
                t = (31 - temp_row[j]) / (temp_row[j+1] - temp_row[j])
                d = distance_grid[i,j] + t * (distance_grid[i,j+1] - distance_grid[i,j])
                points.append((d, ambient_temps[i], 31))
    return np.array(points) if points else np.array([])

def calculate_temperature(fixed_ambient_temp=None):
    """计算空气温度分布"""
    # 生成网格数据
    distances = np.linspace(0.05, 0.5, 50)  # 距离范围 5-50cm (转换为米)
    ambient_temps = np.linspace(10, 30, 50)  # 环境温度范围
    
    if fixed_ambient_temp is None:
        # 3D模式
        D, T_env = np.meshgrid(distances, ambient_temps)
        T = np.array([[calculate_single_point(d, t) for d in distances] for t in ambient_temps])
        return D*100, T_env, T, ambient_temps
    else:
        # 2D模式
        D = distances
        T = np.array([calculate_single_point(d, fixed_ambient_temp) for d in distances])
        return D*100, fixed_ambient_temp, T, None

def calculate_single_point(d, T_amb):
    """计算单点温度"""
    # 1. 计算灯泡表面温度
    surface_area = 4 * np.pi * RADIUS**2
    # 灯泡表面温度随功率线性增加
    Ts = T_amb + (POWER * 3) / (SURFACE_HEAT_TRANSFER * surface_area)
    
    # 2. 计算空气温升
    power_factor = (POWER / 15.0)  # 线性功率影响
    distance_factor = (RADIUS / d) ** 1.5  # 距离衰减
    
    # 温升计算（考虑功率和距离的综合影响）
    delta_T = (Ts - T_amb) * distance_factor * power_factor
    
    # 3. 应用距离衰减并确保温度在合理范围内
    T = T_amb + delta_T * np.exp(-d/(2*RADIUS))
    return min(max(T, T_amb), Ts)

class BulbAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("白炽灯泡温度分析器")
        self.geometry("1200x800")

        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 功率滑块
        power_frame = ttk.Frame(control_frame)
        power_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(power_frame, text="灯泡功率 (W):").pack(side=tk.LEFT)
        self.power_var = tk.DoubleVar(value=15)
        power_slider = ttk.Scale(power_frame, from_=5, to=100, 
                               variable=self.power_var, orient=tk.HORIZONTAL)
        power_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        power_label = ttk.Label(power_frame, textvariable=self.power_var)
        power_label.pack(side=tk.LEFT, padx=5)

        # 信息显示区域
        info_frame = ttk.Frame(control_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.info_label = ttk.Label(info_frame, text="", wraplength=800)
        self.info_label.pack(fill=tk.X)

        # 环境温度控制
        temp_frame = ttk.Frame(control_frame)
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        self.fixed_temp_var = tk.BooleanVar(value=False)
        temp_check = ttk.Checkbutton(temp_frame, text="固定环境温度",
                                   variable=self.fixed_temp_var,
                                   command=self.toggle_temp_input)
        temp_check.pack(side=tk.LEFT)
        ttk.Label(temp_frame, text="温度值 (°C):").pack(side=tk.LEFT, padx=(10,0))
        self.temp_var = tk.DoubleVar(value=20)
        self.temp_entry = ttk.Entry(temp_frame, textvariable=self.temp_var, width=10)
        self.temp_entry.pack(side=tk.LEFT, padx=5)
        self.temp_entry.config(state='disabled')

        # 设置初始状态
        self.is_3d = True

        # 创建图形区域
        self.fig = plt.figure(figsize=(10, 6))
        self.create_subplot()
        
        # 将matplotlib图形嵌入tkinter窗口
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar = NavigationToolbar2Tk(self.canvas, main_frame)
        toolbar.update()
        
        # 绑定事件
        power_slider.bind("<B1-Motion>", self.update_plot)
        power_slider.bind("<ButtonRelease-1>", self.update_plot)
        self.temp_var.trace_add("write", self.on_temp_change)

        # 初始绘图
        self.update_plot(None)

    def toggle_temp_input(self):
        """切换固定环境温度设置"""
        # 更新状态
        self.is_3d = not self.fixed_temp_var.get()
        
        # 更新输入框状态
        if self.fixed_temp_var.get():
            self.temp_entry.config(state='normal')
        else:
            self.temp_entry.config(state='disabled')
        
        # 重新创建图形
        self.create_subplot()
        self.update_plot(None)

    def create_subplot(self):
        """创建子图"""
        self.fig.clear()
        if self.is_3d:
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax = self.fig.add_subplot(111)

    def on_temp_change(self, *args):
        """处理温度变化"""
        try:
            float(self.temp_var.get())
            self.update_plot(None)
        except:
            pass

    def update_plot(self, event):
        """更新图形显示"""
        global POWER
        POWER = self.power_var.get()
        
        # 计算新的温度分布
        fixed_temp = self.temp_var.get() if self.fixed_temp_var.get() else None
        distance_grid, ambient_temp_grid, temp_grid, ambient_temps = calculate_temperature(fixed_temp)
        
        # 找到31度点
        d31, t31_amb, t31 = find_31_degree_point(distance_grid, ambient_temp_grid, temp_grid)
        
        # 清除并重新创建图形
        self.create_subplot()
        
        if self.is_3d:
            # 绘制3D曲面
            surf = self.ax.plot_surface(distance_grid, ambient_temp_grid, temp_grid, 
                                      cmap='coolwarm',
                                      rstride=1, cstride=1,
                                      linewidth=0, antialiased=True)
            
            # 绘制31度等温线
            contour_points = get_31_degree_contour(distance_grid, temp_grid, ambient_temps)
            if len(contour_points) > 0:
                self.ax.plot(contour_points[:,0], contour_points[:,1], contour_points[:,2], 
                           'r-', linewidth=2, label='31°C等温线')
            
            # 标注31度点
            if t31_amb is not None:
                self.ax.scatter([d31], [t31_amb], [t31], color='red', s=100, label='31°C点')
            
            self.ax.set_xlabel('距离 (cm)')
            self.ax.set_ylabel('环境温度 (°C)')
            self.ax.set_zlabel('空气温度 (°C)')
            self.ax.set_title(f'{POWER}W 白炽灯泡周围空气温度分布')
            
            # 添加颜色条
            self.fig.colorbar(surf, ax=self.ax, shrink=0.5, aspect=5, label='温度 (°C)')
            self.ax.legend()

            # 更新信息显示
            if len(contour_points) > 0:
                contour_eq = f"31°C等温线方程：T(d,t) = 31°C"
                point_info = f"31°C点坐标：(d={d31:.1f}cm, t={t31_amb:.1f}°C, T=31°C)"
                self.info_label.config(text=f"{contour_eq}\n{point_info}")
            
        else:
            # 绘制2D曲线
            self.ax.plot(distance_grid, temp_grid, 'b-', linewidth=2)
            
            # 标注31度点
            if t31 is not None:
                self.ax.plot([d31], [t31], 'ro', markersize=10, label='31°C点')
            
            self.ax.set_xlabel('距离 (cm)')
            self.ax.set_ylabel('温度 (°C)')
            self.ax.set_title(f'{POWER}W 白炽灯泡温度-距离关系\n(环境温度: {self.temp_var.get()}°C)')
            self.ax.grid(True)
            self.ax.legend()

            # 更新信息显示
            point_info = f"31°C点坐标：(d={d31:.1f}cm, T=31°C)"
            self.info_label.config(text=point_info)
        
        # 调整图形布局并更新
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    app = BulbAnalyzer()
    # 添加窗口关闭事件处理
    app.protocol("WM_DELETE_WINDOW", cleanup)
    try:
        app.mainloop()
    finally:
        cleanup()
