#!/usr/bin/env python3
"""
创建简单的程序图标
"""
from PIL import Image, ImageDraw

def create_icon():
    # 创建一个128x128的透明背景图像
    size = (128, 128)
    icon = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # 绘制灯泡形状
    bulb_color = (255, 223, 0, 255)  # 黄色
    border_color = (128, 128, 128, 255)  # 灰色边框
    center = (64, 64)
    radius = 40

    # 绘制灯泡主体（圆形）
    draw.ellipse([
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius
    ], fill=bulb_color, outline=border_color, width=2)

    # 绘制灯泡底座
    base_width = 20
    base_height = 15
    base_top = center[1] + radius - 5
    draw.rectangle([
        center[0] - base_width//2,
        base_top,
        center[0] + base_width//2,
        base_top + base_height
    ], fill=(192, 192, 192, 255), outline=border_color, width=2)

    # 添加光线效果
    for angle in range(0, 360, 45):
        from math import sin, cos, radians
        length = 25
        start_x = center[0] + (radius + 5) * cos(radians(angle))
        start_y = center[1] + (radius + 5) * sin(radians(angle))
        end_x = center[0] + (radius + length) * cos(radians(angle))
        end_y = center[1] + (radius + length) * sin(radians(angle))
        draw.line([(start_x, start_y), (end_x, end_y)], 
                 fill=(255, 255, 0, 128), width=3)

    # 保存为ICO格式
    import os
    
    # 确保保存在assets目录中
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    icon.save(icon_path, format='ICO')
    return icon_path

if __name__ == '__main__':
    icon_path = create_icon()
    print(f"图标文件已创建: {icon_path}")
