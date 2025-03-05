import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from .temperature_model import MATERIAL_PROPERTIES

class ValueAdjuster(ttk.Frame):
    """数值调节控件，组合了Spinbox和Scale"""
    def __init__(self, parent, text, variable, from_, to, increment=0.1, decimal_places=1, **kwargs):
        super().__init__(parent)
        
        self.variable = variable
        self.decimal_places = decimal_places
        ttk.Label(self, text=text).pack(side=tk.LEFT)
        
        # 创建输入框
        self.entry = ttk.Entry(
            self,
            width=8,
            justify='right'
        )
        self.entry.pack(side=tk.LEFT, padx=2)
        self.entry.insert(0, f"{variable.get():.{decimal_places}f}")
        
        # 创建Scale
        self.scale = ttk.Scale(
            self,
            from_=from_,
            to=to,
            orient=tk.HORIZONTAL,
            variable=variable,
            command=self._on_scale_change
        )
        self.scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 绑定输入框验证和更新事件
        self.entry.bind('<Return>', self._on_entry_change)
        self.entry.bind('<FocusOut>', self._on_entry_change)
        
        # 设置不同参数类型的小数位数
        if "功率" in text or "温度" in text:
            self.decimal_places = 0  # 整数
        elif "角度" in text:
            self.decimal_places = 0  # 整数
        elif "长度" in text or "宽度" in text or "高度" in text:
            self.decimal_places = 1  # 一位小数
        elif "半径" in text or "位置" in text:
            self.decimal_places = 1  # 一位小数
        elif "壁厚" in text:
            self.decimal_places = 2  # 两位小数
        
        # 更新显示的值
        self.entry.delete(0, tk.END)
        self.entry.insert(0, f"{self.variable.get():.{self.decimal_places}f}")
    
    def _on_scale_change(self, value):
        """处理Scale值变化"""
        value = float(self.scale.get())
        self.variable.set(value)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, f"{value:.{self.decimal_places}f}")
    
    def _on_entry_change(self, event=None):
        """处理输入框值变化"""
        try:
            value = float(self.entry.get())
            if self.scale['from'] <= value <= self.scale['to']:
                self.variable.set(value)
                self.entry.delete(0, tk.END)
                self.entry.insert(0, f"{value:.{self.decimal_places}f}")
            else:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, f"{self.variable.get():.{self.decimal_places}f}")
        except ValueError:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f"{self.variable.get():.{self.decimal_places}f}")

class ContainerSettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("容器参数设置")
        self.geometry("500x600")
        
        # 尺寸调整frame
        size_frame = ttk.LabelFrame(self, text="容器尺寸")
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 从父窗口获取当前值
        self.length_var = tk.DoubleVar(value=parent.container_size[0] * 100)  # 米转厘米
        self.width_var = tk.DoubleVar(value=parent.container_size[1] * 100)
        self.height_var = tk.DoubleVar(value=parent.container_size[2] * 100)
        self.thickness_var = tk.DoubleVar(value=parent.wall_thickness * 1000)  # 米转毫米
        
        # 尺寸控件
        dims = [
            ("长度 (cm):", self.length_var),
            ("宽度 (cm):", self.width_var),
            ("高度 (cm):", self.height_var),
            ("壁厚 (mm):", self.thickness_var)
        ]
        
        for text, var in dims:
            # 创建数值调节控件
            if text == "长度 (cm):":
                adjuster = ValueAdjuster(size_frame, text, var, 10, 100, 1)
            elif text == "宽度 (cm):" or text == "高度 (cm):":
                adjuster = ValueAdjuster(size_frame, text, var, 10, 60, 1)
            else:  # 壁厚
                adjuster = ValueAdjuster(size_frame, text, var, 0.1, 5, 0.1)
            adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        # 导热面选择frame
        heat_frame = ttk.LabelFrame(self, text="导热面选择")
        heat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 导热面变量
        self.face_mapping = {
            "前面": "front", "后面": "back", "左面": "left",
            "右面": "right", "顶面": "top", "底面": "bottom"
        }

        # 从父窗口获取当前材料状态
        self.face_materials = {}
        for name, eng_name in self.face_mapping.items():
            material = parent.face_materials.get(eng_name, 'PP')
            self.face_materials[name] = tk.StringVar(value=material)

        # 创建材料选择框
        for face, var in self.face_materials.items():
            frame = ttk.Frame(heat_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(frame, text=f"{face}:").pack(side=tk.LEFT)
            material_combo = ttk.Combobox(frame, textvariable=var,
                                        values=list(MATERIAL_PROPERTIES.keys()),
                                        width=15, state="readonly")
            material_combo.pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=MATERIAL_PROPERTIES[var.get()]['name']).pack(side=tk.LEFT)
            # 绑定更新事件
            var.trace_add("write", lambda *args, f=face, l=frame.winfo_children()[-1]:
                         l.config(text=MATERIAL_PROPERTIES[self.face_materials[f].get()]['name']))
        
        # 开孔设置frame
        hole_frame = ttk.LabelFrame(self, text="开孔设置")
        hole_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 从父窗口获取当前开孔设置
        if parent.hole_params is None:
            self.hole_type_var = tk.StringVar(value="none")
            self.hole_diameter_var = tk.DoubleVar(value=10)
            self.hole_width_var = tk.DoubleVar(value=10)
            self.hole_height_var = tk.DoubleVar(value=10)
            self.hole_x_var = tk.DoubleVar(value=30)
            self.hole_y_var = tk.DoubleVar(value=20)
            self.hole_face_var = tk.StringVar(value="前面")
        else:
            self.hole_type_var = tk.StringVar(value=parent.hole_params['type'])
            self.hole_x_var = tk.DoubleVar(value=parent.hole_params['x'])
            self.hole_y_var = tk.DoubleVar(value=parent.hole_params['y'])
            
            # 找到对应的中文面名称
            face_name = next(cn for cn, en in self.face_mapping.items() 
                           if en == parent.hole_params['face'])
            self.hole_face_var = tk.StringVar(value=face_name)
            
            if parent.hole_params['type'] == 'circle':
                self.hole_diameter_var = tk.DoubleVar(value=parent.hole_params['diameter'])
                self.hole_width_var = tk.DoubleVar(value=10)
                self.hole_height_var = tk.DoubleVar(value=10)
            else:  # rectangle
                self.hole_diameter_var = tk.DoubleVar(value=10)
                self.hole_width_var = tk.DoubleVar(value=parent.hole_params['width'])
                self.hole_height_var = tk.DoubleVar(value=parent.hole_params['height'])
        
        # 开孔类型选择
        ttk.Radiobutton(hole_frame, text="无开孔", 
                       variable=self.hole_type_var, 
                       value="none").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(hole_frame, text="圆形", 
                       variable=self.hole_type_var, 
                       value="circle").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(hole_frame, text="矩形", 
                       variable=self.hole_type_var, 
                       value="rectangle").pack(anchor=tk.W, padx=5)
        
        # 开孔参数frame
        hole_size_frame = ttk.Frame(hole_frame)
        hole_size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 圆形开孔尺寸控件
        self.circle_frame = ttk.Frame(hole_size_frame)
        circle_adjuster = ValueAdjuster(self.circle_frame, 
                                      "直径 (cm):", 
                                      self.hole_diameter_var, 
                                      1, 30, 0.5)
        circle_adjuster.pack(fill=tk.X)
                 
        # 矩形开孔尺寸控件
        self.rect_frame = ttk.Frame(hole_size_frame)
        rect_w_adjuster = ValueAdjuster(self.rect_frame, 
                                      "宽度 (cm):", 
                                      self.hole_width_var, 
                                      1, 30, 0.5)
        rect_w_adjuster.pack(fill=tk.X, pady=2)
        rect_h_adjuster = ValueAdjuster(self.rect_frame, 
                                      "高度 (cm):", 
                                      self.hole_height_var, 
                                      1, 30, 0.5)
        rect_h_adjuster.pack(fill=tk.X)
        
        # 开孔位置frame
        hole_pos_frame = ttk.Frame(hole_frame)
        hole_pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 面选择下拉框
        face_frame = ttk.Frame(hole_pos_frame)
        face_frame.pack(fill=tk.X, pady=2)
        ttk.Label(face_frame, text="位于:").pack(side=tk.LEFT)
        faces = list(self.face_mapping.keys())
        face_combo = ttk.Combobox(face_frame, textvariable=self.hole_face_var, 
                                values=faces, width=10, state="readonly")
        face_combo.pack(side=tk.LEFT, padx=5)
        
        # 位置调节控件
        x_adjuster = ValueAdjuster(hole_pos_frame, 
                                 "X (cm):", 
                                 self.hole_x_var, 
                                 0, 60, 0.5)
        x_adjuster.pack(fill=tk.X, pady=2)
        
        y_adjuster = ValueAdjuster(hole_pos_frame, 
                                 "Y (cm):", 
                                 self.hole_y_var, 
                                 0, 40, 0.5)
        y_adjuster.pack(fill=tk.X)
        
        # 应用按钮
        ttk.Button(self, text="应用更改", 
                  command=self.apply_changes).pack(pady=10)
        
        # 绑定事件
        self.hole_type_var.trace_add("write", self.update_hole_ui)
        self.update_hole_ui()
        
    def update_hole_ui(self, *args):
        """根据开孔类型更新UI"""
        hole_type = self.hole_type_var.get()
        
        # 移除现有frame
        self.circle_frame.pack_forget()
        self.rect_frame.pack_forget()
        
        # 显示相应的frame
        if hole_type == "circle":
            self.circle_frame.pack(fill=tk.X)
        elif hole_type == "rectangle":
            self.rect_frame.pack(fill=tk.X)
    
    def apply_changes(self):
        """应用更改到主窗口"""
        # 更新容器尺寸
        self.parent.container_size = (
            self.length_var.get() / 100,  # 转换为米
            self.width_var.get() / 100,
            self.height_var.get() / 100
        )
        self.parent.wall_thickness = self.thickness_var.get() / 1000  # 转换为米
        
        # 更新导热面设置
        self.parent.face_materials = {
            self.face_mapping[face]: var.get()
            for face, var in self.face_materials.items()
        }
        
        # 更新开孔设置
        hole_type = self.hole_type_var.get()
        if hole_type == "none":
            self.parent.hole_params = None
        else:
            self.parent.hole_params = {
                'type': hole_type,
                'x': self.hole_x_var.get(),
                'y': self.hole_y_var.get(),
                'face': self.face_mapping[self.hole_face_var.get()]
            }
            if hole_type == "circle":
                self.parent.hole_params['diameter'] = self.hole_diameter_var.get()
            else:  # rectangle
                self.parent.hole_params['width'] = self.hole_width_var.get()
                self.parent.hole_params['height'] = self.hole_height_var.get()
        
        # 更新主窗口
        self.parent.initialize_grid()
        self.parent.update_plot()
        self.destroy()

class LightSettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("灯具参数设置")
        self.geometry("800x600")

        # 创建左右分栏
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建预览图
        preview_frame = ttk.LabelFrame(right_frame, text="预览")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图形
        self.fig = plt.figure(figsize=(7, 7))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # 调整子图位置以充分利用空间
        self.fig.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95)
        self.canvas = FigureCanvasTkAgg(self.fig, master=preview_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 从父窗口获取当前值
        self.x_pos_var = tk.DoubleVar(value=parent.bulb_pos[0] * 100)  # 米转厘米
        self.y_pos_var = tk.DoubleVar(value=parent.bulb_pos[1] * 100)  # 米转厘米
        self.power_var = tk.DoubleVar(value=parent.power_var.get())

        # 灯泡基本参数设置
        bulb_frame = ttk.LabelFrame(left_frame, text="灯泡参数")
        bulb_frame.pack(fill=tk.X, padx=5, pady=5)

        # 功率设置使用数值调节控件
        power_adjuster = ValueAdjuster(bulb_frame, "功率 (W):", 
                                     self.power_var, 1, 100, 1)
        power_adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        # 位置调整frame
        pos_frame = ttk.LabelFrame(left_frame, text="灯具位置")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 位置控件使用ValueAdjuster
        x_adjuster = ValueAdjuster(pos_frame, "X位置 (cm):", 
                                 self.x_pos_var, 0, 60, 1)
        x_adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        y_adjuster = ValueAdjuster(pos_frame, "Y位置 (cm):", 
                                 self.y_pos_var, 0, 40, 1)
        y_adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        # 灯罩设置frame
        shade_frame = ttk.LabelFrame(left_frame, text="灯罩设置")
        shade_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 从父窗口获取当前灯罩设置
        self.has_shade_var = tk.BooleanVar(value=parent.has_shade)
        if parent.shade_params:
            self.top_radius_var = tk.DoubleVar(value=parent.shade_params['top_radius'] * 100)
            self.bottom_radius_var = tk.DoubleVar(value=parent.shade_params['bottom_radius'] * 100)
            self.height_var = tk.DoubleVar(value=parent.shade_params['height'] * 100)
            self.angle_h_var = tk.DoubleVar(value=parent.shade_params.get('angle_h', 0))
            self.angle_v_var = tk.DoubleVar(value=parent.shade_params.get('angle_v', 0))
        else:
            self.top_radius_var = tk.DoubleVar(value=3)
            self.bottom_radius_var = tk.DoubleVar(value=6)
            self.height_var = tk.DoubleVar(value=8)
            self.angle_h_var = tk.DoubleVar(value=0)
            self.angle_v_var = tk.DoubleVar(value=0)
        
        # 灯罩启用开关
        ttk.Checkbutton(shade_frame, text="启用灯罩", 
                       variable=self.has_shade_var).pack(anchor=tk.W, padx=5)
        
        # 灯罩参数frame
        self.shade_params_frame = ttk.Frame(shade_frame)
        self.shade_params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 灯罩参数控件
        shade_params = [
            ("顶面半径 (cm):", self.top_radius_var),
            ("底面半径 (cm):", self.bottom_radius_var),
            ("高度 (cm):", self.height_var),
            ("水平旋转角 (度):", self.angle_h_var),
            ("垂直倾斜角 (度):", self.angle_v_var)
        ]
        
        for text, var in shade_params:
            if "半径" in text:
                adjuster = ValueAdjuster(self.shade_params_frame, text, var, 0.1, 20, 0.1)
            elif "高度" in text:
                adjuster = ValueAdjuster(self.shade_params_frame, text, var, 1, 30, 0.5)
            elif "水平旋转角" in text:
                adjuster = ValueAdjuster(self.shade_params_frame, text, var, -360, 360, 5)
            else:  # 垂直倾斜角
                adjuster = ValueAdjuster(self.shade_params_frame, text, var, -90, 90, 5)
            adjuster.pack(fill=tk.X, padx=5, pady=2)
        
        # 应用按钮
        ttk.Button(left_frame, text="应用更改", 
                  command=self.apply_changes).pack(pady=10)
        
        # 绑定事件
        for var in [self.x_pos_var, self.y_pos_var,
                   self.power_var, self.top_radius_var, 
                   self.bottom_radius_var, self.height_var, 
                   self.angle_h_var, self.angle_v_var,
                   self.has_shade_var]:
            var.trace_add("write", self.update_preview)
            
        self.has_shade_var.trace_add("write", self.update_shade_ui)
        
        # 初始化UI状态
        self.update_shade_ui()
        self.update_preview()
    
    def update_preview(self, *args):
        """更新预览图"""
        self.ax.clear()
        
        # 绘制容器轮廓（半透明）
        L, W, H = self.parent.container_size
        vertices = [
            [[0,0,0], [L,0,0], [L,W,0], [0,W,0]],  # 底面
            [[0,0,H], [L,0,H], [L,W,H], [0,W,H]],  # 顶面
            [[0,0,0], [L,0,0], [L,0,H], [0,0,H]],  # 前面
            [[0,W,0], [L,W,0], [L,W,H], [0,W,H]],  # 后面
            [[0,0,0], [0,W,0], [0,W,H], [0,0,H]],  # 左面
            [[L,0,0], [L,W,0], [L,W,H], [L,0,H]]   # 右面
        ]
        
        for verts in vertices:
            self.ax.add_collection3d(Poly3DCollection([verts], alpha=0.1, color='gray'))
        
        # 绘制灯泡位置
        x = self.x_pos_var.get() / 100  # 厘米转米
        y = self.y_pos_var.get() / 100
        z = H  # 顶部固定
        self.ax.scatter([x], [y], [z], color='yellow', s=100)
        
        # 绘制灯罩
        if self.has_shade_var.get():
            try:
                theta = np.linspace(0, 2*np.pi, 100)  # 增加分段数使灯罩更圆滑
                height = self.height_var.get() / 100
                z_shade = np.linspace(H - height, H, 40)
                Theta, Z = np.meshgrid(theta, z_shade)
                
                # 计算灯罩的半径（随高度线性变化）
                top_r = self.top_radius_var.get() / 100
                bottom_r = self.bottom_radius_var.get() / 100
                R = top_r + (bottom_r - top_r) * (H - Z) / height
                
                # 生成圆柱体基础坐标
                X = R * np.cos(Theta)
                Y = R * np.sin(Theta)
                Z = Z - H  # 相对高度

                # 获取角度
                angle_h = np.radians(float(self.angle_h_var.get()))
                angle_v = np.radians(float(self.angle_v_var.get()))

                # 先进行垂直倾斜（绕X轴旋转）
                Y_temp = Y * np.cos(angle_v) - Z * np.sin(angle_v)
                Z_temp = Y * np.sin(angle_v) + Z * np.cos(angle_v)

                # 再进行水平旋转（绕Z轴旋转）
                X_rot = X * np.cos(angle_h) - Y_temp * np.sin(angle_h)
                Y_rot = X * np.sin(angle_h) + Y_temp * np.cos(angle_h)
                Z_rot = Z_temp
                
                # 将坐标移回灯泡位置
                X_rot = x + X_rot
                Y_rot = y + Y_rot
                Z_rot = H + Z_rot
                
                self.ax.plot_surface(X_rot, Y_rot, Z_rot, alpha=0.3, color='gray')
            except Exception as e:
                print("灯罩绘制错误:", str(e))
        
        # 设置视图
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        
        # 设置容器显示比例和范围
        max_dim = max(L, W, H)
        margin = max_dim * 0.1  # 10%的边距
        
        # 设置相等的坐标轴比例
        self.ax.set_box_aspect((L/max_dim, W/max_dim, H/max_dim))
        
        # 设置固定的刻度位置
        x_ticks = np.linspace(0, L, 4)  # 3等分
        y_ticks = np.linspace(0, W, 3)  # 2等分
        z_ticks = np.linspace(0, H, 3)  # 2等分
        
        self.ax.set_xticks(x_ticks)
        self.ax.set_yticks(y_ticks)
        self.ax.set_zticks(z_ticks)
        
        # 设置坐标轴范围
        self.ax.set_xlim(-margin, L + margin)
        self.ax.set_ylim(-margin, W + margin)
        self.ax.set_zlim(-margin, H + margin)
        self.ax.view_init(elev=20, azim=45)
        
        # 刷新画布
        self.canvas.draw()
    
    def update_shade_ui(self, *args):
        """根据灯罩启用状态更新UI"""
        if self.has_shade_var.get():
            self.shade_params_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.shade_params_frame.pack_forget()
    
    def validate_inputs(self):
        """验证输入值"""
        try:
            # 验证功率
            power = self.power_var.get()
            if not (1 <= power <= 1000):
                raise ValueError("功率必须在1-1000W之间")
            
            # 验证位置
            x = self.x_pos_var.get()
            y = self.y_pos_var.get()
            max_x = self.parent.container_size[0] * 100
            max_y = self.parent.container_size[1] * 100
            
            if not (0 <= x <= max_x):
                raise ValueError(f"X位置必须在0-{max_x:.1f}cm之间")
            if not (0 <= y <= max_y):
                raise ValueError(f"Y位置必须在0-{max_y:.1f}cm之间")
            
            if self.has_shade_var.get():
                # 验证灯罩参数
                top_r = self.top_radius_var.get()
                bottom_r = self.bottom_radius_var.get()
                height = self.height_var.get()
                max_height = self.parent.container_size[2] * 100
                
                if not (0.1 <= top_r <= 50):
                    raise ValueError("顶部半径必须在0.1-50cm之间")
                if not (0.1 <= bottom_r <= 50):
                    raise ValueError("底部半径必须在0.1-50cm之间")
                if not (0.1 <= height <= max_height):
                    raise ValueError(f"高度必须在0.1-{max_height:.1f}cm之间")
                
                # 验证角度
                angle_h = self.angle_h_var.get()
                angle_v = self.angle_v_var.get()
                if not (-360 <= angle_h <= 360):
                    raise ValueError("水平旋转角必须在-360°到360°之间")
                if not (-90 <= angle_v <= 90):
                    raise ValueError("垂直倾斜角必须在-90°到90°之间")
            
            return True
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return False
        except Exception as e:
            messagebox.showerror("错误", f"输入值无效: {str(e)}")
            return False

    def apply_changes(self):
        """应用更改到主窗口"""
        if not self.validate_inputs():
            return
            
        try:
            # 更新灯具位置
            self.parent.bulb_pos = np.array([
                self.x_pos_var.get() / 100,  # 转换为米
                self.y_pos_var.get() / 100,
                self.parent.container_size[2]  # Z位置保持不变
            ])
            
            # 更新功率
            self.parent.power_var.set(self.power_var.get())
            
            # 更新灯罩参数
            self.parent.has_shade = self.has_shade_var.get()
            if self.has_shade_var.get():
                self.parent.shade_params = {
                    'top_radius': self.top_radius_var.get() / 100,
                    'bottom_radius': self.bottom_radius_var.get() / 100,
                    'height': self.height_var.get() / 100,
                    'angle_h': self.angle_h_var.get(),
                    'angle_v': self.angle_v_var.get()
                }
            else:
                self.parent.shade_params = None
            
            # 更新主窗口
            self.parent.update_plot()
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"应用更改时出错: {str(e)}")
