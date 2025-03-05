#!/usr/bin/env python3
"""
可视化模块
处理容器和温度分布的3D显示
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as colors
import matplotlib.cm as cm

def draw_container(ax, size, front_material, back_material, left_material,
                  right_material, top_material, bottom_material, hole_params,
                  bulb_pos, has_shade, shade_params, cut_plane, slice_pos):
    """绘制容器3D图"""
    # 清除当前图形
    ax.clear()
    
    # 设置视角
    ax.view_init(elev=20, azim=45)
    
    # 容器顶点坐标
    l, w, h = size  # 长宽高
    vertices = [
        [[0, 0, 0], [l, 0, 0], [l, w, 0], [0, w, 0]],  # 底面
        [[0, 0, h], [l, 0, h], [l, w, h], [0, w, h]],  # 顶面
        [[0, 0, 0], [l, 0, 0], [l, 0, h], [0, 0, h]],  # 前面
        [[0, w, 0], [l, w, 0], [l, w, h], [0, w, h]],  # 后面
        [[0, 0, 0], [0, w, 0], [0, w, h], [0, 0, h]],  # 左面
        [[l, 0, 0], [l, w, 0], [l, w, h], [l, 0, h]]   # 右面
    ]
    
    # 设置不同面的颜色和透明度
    materials = [bottom_material, top_material, front_material,
                back_material, left_material, right_material]
    alphas = [0.3] * 6  # 所有面的透明度

    # 根据剖切面调整显示
    if cut_plane == "XY":
        if slice_pos[2] < h:
            vertices = vertices[:2]  # 只显示底面和顶面
            materials = materials[:2]
            alphas = alphas[:2]
    elif cut_plane == "YZ":
        if slice_pos[0] < l:
            vertices = [vertices[2], vertices[3]]  # 只显示前面和后面
            materials = materials[2:4]
            alphas = alphas[2:4]
    else:  # XZ
        if slice_pos[1] < w:
            vertices = [vertices[4], vertices[5]]  # 只显示左面和右面
            materials = materials[4:]
            alphas = alphas[4:]

    # 设置材料颜色
    material_colors = {
        "Glass": "#add8e6",  # 浅蓝色
        "PP": "#f0f0f0",     # 浅灰色
        "PE": "#e0e0e0",     # 中灰色
        "AL": "#c0c0c0"      # 深灰色
    }
    face_colors = [material_colors.get(mat, "#ffffff") for mat in materials]
    
    # 绘制容器外轮廓和面
    for face, color, alpha in zip(vertices, face_colors, alphas):
        # 绘制面
        poly3d = Poly3DCollection([face])
        poly3d.set_facecolor(color)
        poly3d.set_alpha(alpha)
        poly3d.set_edgecolor('black')  # 添加黑色边框
        poly3d.set_linewidth(2)  # 加粗边框线条
        poly3d.set_edgecolor('#000000')  # 使用纯黑色
        ax.add_collection3d(poly3d)

    # 绘制剖切面及其边缘
    if cut_plane == "XY":
        z = slice_pos[2]
        if 0 < z < h:
            xx, yy = np.meshgrid([0, l], [0, w], indexing='ij')
            zz = np.full_like(xx, z)
            # 绘制剖切平面（使用更显眼的颜色和透明度）
            ax.plot_surface(xx, yy, zz, alpha=0.4, color='lightblue')
            # 绘制剖切面边缘
            ax.plot([0, l, l, 0, 0], [0, 0, w, w, 0], [z, z, z, z, z], 
                   color='black', linewidth=2)
    elif cut_plane == "YZ":
        x = slice_pos[0]
        if 0 < x < l:
            yy, zz = np.meshgrid([0, w], [0, h], indexing='ij')
            xx = np.full_like(yy, x)
            # 绘制剖切平面（使用更显眼的颜色和透明度）
            ax.plot_surface(xx, yy, zz, alpha=0.4, color='lightblue')
            # 绘制剖切面边缘
            ax.plot([x, x, x, x, x], [0, w, w, 0, 0], [0, 0, h, h, 0], 
                   color='black', linewidth=2)
    else:  # XZ
        y = slice_pos[1]
        if 0 < y < w:
            xx, zz = np.meshgrid([0, l], [0, h], indexing='ij')
            yy = np.full_like(xx, y)
            # 绘制剖切平面（使用更显眼的颜色和透明度）
            ax.plot_surface(xx, yy, zz, alpha=0.4, color='lightblue')
            # 绘制剖切面边缘
            ax.plot([0, l, l, 0, 0], [y, y, y, y, y], [0, 0, h, h, 0], 
                   color='black', linewidth=2)

    # 设置视图为等比例
    ax.set_box_aspect((l/max(l,w,h), w/max(l,w,h), h/max(l,w,h)))
    
    # 绘制灯泡位置
    if bulb_pos is not None:
        ax.scatter(*bulb_pos, color='yellow', s=100, marker='*')
    
    # 绘制灯罩（如果有）
    if has_shade and shade_params:
        draw_shade(ax, bulb_pos, shade_params)
    
    # 设置坐标轴范围
    ax.set_xlim(0, size[0])
    ax.set_ylim(0, size[1])
    ax.set_zlim(0, size[2])
    
    # 设置标签
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    
    # 设置标题
    ax.set_title('容器3D视图')

def draw_shade(ax, bulb_pos, shade_params):
    """绘制灯罩"""
    if not all(key in shade_params for key in 
              ['height', 'angle_h', 'angle_v', 'top_radius', 'bottom_radius']):
        return
    
    # 提取参数
    height = shade_params['height']
    angle_h = shade_params['angle_h']
    angle_v = shade_params['angle_v']
    r_top = shade_params['top_radius']
    r_bottom = shade_params['bottom_radius']
    
    # 计算灯罩顶部和底部的圆环
    theta = np.linspace(0, 2*np.pi, 32)
    
    # 顶部圆环
    x_top = bulb_pos[0] + r_top * np.cos(theta)
    y_top = bulb_pos[1] + r_top * np.sin(theta)
    z_top = np.full_like(theta, bulb_pos[2])
    
    # 底部圆环
    x_bottom = bulb_pos[0] + r_bottom * np.cos(theta)
    y_bottom = bulb_pos[1] + r_bottom * np.sin(theta)
    z_bottom = np.full_like(theta, bulb_pos[2] - height)
    
    # 绘制灯罩表面
    surf_x = np.vstack((x_top, x_bottom))
    surf_y = np.vstack((y_top, y_bottom))
    surf_z = np.vstack((z_top, z_bottom))
    
    ax.plot_surface(surf_x, surf_y, surf_z, alpha=0.3, color='gray')

def draw_temperature_plot(ax, coords, temps, t_amb, plane, xlims, ylims):
    """绘制温度分布图"""
    # 清除当前图形
    ax.clear()
    
    # 创建网格
    X, Y = coords  # Unpack the coordinate tuple
    x = np.unique(X)
    y = np.unique(Y)
    X, Y = np.meshgrid(x, y, indexing='ij')
    Z = temps.reshape((len(x), len(y)))
    
    # 创建更平滑的等温线图
    levels = np.linspace(t_amb - 10, t_amb + 50, 100)  # 增加等温线数量
    # 使用RdYlBu colormap并添加插值
    im = ax.contourf(X, Y, Z, levels=levels, cmap='RdYlBu_r', extend='both')
    
    # 添加等温线
    contour = ax.contour(X, Y, Z, levels=levels[::10], colors='black', linewidths=0.5, alpha=0.3)
    
    # 使用平滑填充
    ax.set_rasterization_zorder(-1)  # 确保填充区域在背景
    
    # 设置等比例显示
    ax.set_aspect('equal')
    
    # 设置标签
    if plane == "XY":
        xlabel, ylabel = 'X (m)', 'Y (m)'
    elif plane == "YZ":
        xlabel, ylabel = 'Y (m)', 'Z (m)'
    else:  # XZ
        xlabel, ylabel = 'X (m)', 'Z (m)'
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    # 设置标题
    ax.set_title(f'{plane}平面温度分布')
    
    # 设置坐标轴范围
    ax.set_xlim(xlims)
    ax.set_ylim(ylims)
    
    return im
