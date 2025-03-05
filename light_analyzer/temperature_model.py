import numpy as np
from numba import njit, prange

# 物理参数设置
POWER = 15  # 灯泡功率 (W)
RADIUS = 0.025  # 灯泡半径 (m)
AIR_CONDUCTIVITY = 0.026  # 空气导热系数 (W/m·K)
SURFACE_HEAT_TRANSFER = 5  # 表面换热系数 (W/m²·K)
WALL_THICKNESS = 0.001  # 容器壁厚 (m)

# 材料参数设置
MATERIAL_PROPERTIES = {
    'PP': {
        'name': 'PP塑料',
        'conductivity': 0.22,  # W/m·K
        'type': 'normal'
    },
    'PVC': {
        'name': 'PVC塑料',
        'conductivity': 0.19,  # W/m·K
        'type': 'normal'
    },
    'Glass': {
        'name': '玻璃',
        'conductivity': 0.93,  # W/m·K
        'type': 'normal'
    },
    'Insulated': {
        'name': '完全保温',
        'conductivity': 0.001,  # 近似为0
        'type': 'insulated'
    },
    'Open': {
        'name': '完全开放',
        'conductivity': float('inf'),
        'type': 'open'
    }
}

@njit(cache=True)
def get_material_conductivity(material):
    """获取材料的导热系数"""
    if material == 'PP':
        return 0.22
    elif material == 'PVC':
        return 0.19
    elif material == 'Glass':
        return 0.93
    elif material == 'Insulated':
        return 0.001
    else:  # Open
        return float('inf')

def get_material_type(material):
    """获取材料类型"""
    if material == 'Insulated':
        return 'insulated'
    elif material == 'Open':
        return 'open'
    else:
        return 'normal'

@njit(cache=True)
def calculate_temperature(x, y, z, power, t_amb, bulb_pos, container_size,
                      wall_thickness,
                      front_cond, back_cond, left_cond, right_cond,
                      top_cond, bottom_cond, conductivities,
                      has_hole=False, hole_face=None, hole_type=None,
                      hole_x=0.0, hole_y=0.0, hole_diameter=0.0,
                      hole_width=0.0, hole_height=0.0,
                      has_shade=False, 
                      shade_height=0.0, shade_angle_h=0.0, shade_angle_v=0.0,
                      shade_top_radius=0.0, shade_bottom_radius=0.0):
    """使用改进的有限差分法计算温度"""
    # 计算到灯泡的距离并向量化
    d = np.sqrt((x - bulb_pos[0])**2 + (y - bulb_pos[1])**2 + (z - bulb_pos[2])**2)

    # 计算热源温度
    surface_area = 4 * np.pi * RADIUS**2
    ts = t_amb + (power * 3.5) / (SURFACE_HEAT_TRANSFER * surface_area)
    
    # 使用改进的导热系数计算
    k_air = AIR_CONDUCTIVITY * (1 + 0.003 * (max(t_amb, ts) - 293))  # 考虑温度对导热系数的影响
    
    # 优化的温度衰减计算
    power_factor = power / max(15.0, 1e-6)  # 防止除零
    r_norm = max(RADIUS, d) / max(RADIUS, 1e-6)  # 防止除零
    distance_factor = 1 / max(r_norm * r_norm, 1e-6)  # 使用更精确的平方反比衰减，防止除零
    
    # 计算基础温升
    delta_t = (ts - t_amb) * distance_factor * power_factor
    
    # 改进的壁面影响计算
    wall_distances = np.array([
        y,                     # front
        container_size[1] - y, # back
        x,                     # left
        container_size[0] - x, # right
        container_size[2] - z, # top
        z                      # bottom
    ])
    
    # 获取最近壁面距离
    wall_distance = float('inf')
    
    nearest_wall_conductivity = None
    for i in range(len(wall_distances)):
        dist = wall_distances[i]
        cond = conductivities[i]
        if cond != float('inf') and dist < wall_distance:
            wall_distance = dist
            nearest_wall_conductivity = cond
    
    # 优化的热阻和热量累积计算
    heat_resistance = 1.0
    heat_accumulation = 1.0

    # 检查所有面的导热系数
    all_insulated = True
    any_conducting = False
    for cond in conductivities:
        if cond == float('inf'):  # Open
            all_insulated = False
            any_conducting = True
            break
        elif cond > 0.001:  # Normal material
            all_insulated = False
            any_conducting = True
    
    # 如果所有面都不导热，增加热量累积效应
    if all_insulated:
        # 在密闭空间中，温度会随时间累积
        heat_accumulation = 4.0  # 显著增加热量累积效应
        heat_resistance = 25.0   # 更高的热阻以模拟完全隔热效果
    else:
        if wall_distance < wall_thickness:
            # 多层热阻模型
            if nearest_wall_conductivity == float('inf'):  # Open
                heat_resistance = 0.1  # 很小的热阻表示容易散热
            elif nearest_wall_conductivity < 0.001:  # Insulated
                heat_resistance = 25.0  # 很大的热阻表示难以散热
            else:  # normal材料
                r_wall = wall_thickness / nearest_wall_conductivity
                r_air = wall_distance / max(k_air, 1e-6)
                total_conductance = 1.0/max(r_wall, 1e-6) + 1.0/max(r_air, 1e-6)
                heat_resistance = 1.0 / max(total_conductance, 1e-6)

    # 增强与热源距离的影响
    source_distance = np.sqrt((x - bulb_pos[0])**2 + (y - bulb_pos[1])**2 + (z - bulb_pos[2])**2)
    if source_distance < RADIUS * 3:  # 扩大热源影响范围
        # 使用指数衰减计算热量影响
        distance_factor = np.exp(-source_distance / (RADIUS * 2))
        heat_accumulation *= (2.0 + distance_factor * 3.0)  # 显著增强近距离效应
    
    # 改进的壁面温度因子
    wall_factor = 1.0
    if wall_distance < 0.05:
        if wall_distance < wall_thickness:
            wall_factor = 0.75
        else:
            wall_factor = 0.75 + 0.25 * np.sqrt((wall_distance - wall_thickness) / 0.05)
    
    # 处理开孔
    if has_hole:
        if hole_type == 'circle':
            hx = hole_x / 100
            hy = hole_y / 100
            radius = hole_diameter / 200
            
            if hole_face == 'front' and abs(y) < wall_thickness:
                dx = x - hx
                dy = z - hy
                if np.sqrt(dx**2 + dy**2) < radius:
                    # 增加对流换热
                    h_conv = 10.0  # W/(m²·K)
                    delta_t *= np.exp(-h_conv * wall_distance / k_air)
        
        elif hole_type == 'rectangle':
            hx = hole_x / 100
            hy = hole_y / 100
            hw = hole_width / 200
            hh = hole_height / 200
            
            if hole_face == 'front' and abs(y) < wall_thickness:
                if (abs(x - hx) < hw) and (abs(z - hy) < hh):
                    # 增加对流换热
                    h_conv = 10.0  # W/(m²·K)
                    delta_t *= np.exp(-h_conv * wall_distance / k_air)
    
    # 考虑灯罩效应
    if has_shade:
        angle_h = np.radians(shade_angle_h)
        angle_v = np.radians(shade_angle_v)
        
        dx = x - bulb_pos[0]
        dy = y - bulb_pos[1]
        dz = bulb_pos[2] - z
        
        dx_h = dx * np.cos(angle_h) + dy * np.sin(angle_h)
        dy_h = -dx * np.sin(angle_h) + dy * np.cos(angle_h)
        
        dy_rot = dy_h * np.cos(angle_v) - dz * np.sin(angle_v)
        dz_rot = dy_h * np.sin(angle_v) + dz * np.cos(angle_v)
        
        if dz_rot > 0:
            r = np.sqrt(dx_h**2 + dy_rot**2)
            max_r = (shade_top_radius + 
                    (shade_bottom_radius - shade_top_radius) 
                    * dz_rot / shade_height)
            if r > max_r:
                return t_amb
            
        # 改进的反射计算
        reflection_factor = 0.95
        power_reflected = power * reflection_factor
        delta_t *= (1 + power_reflected/power * np.cos(np.arctan2(r, dz_rot)))
    
    # 最终温度计算，考虑热量累积效应
    t = t_amb + (delta_t * np.exp(-d/(2.5*RADIUS)) * wall_factor * heat_resistance * heat_accumulation)
    
    # 确保温度不超过物理上合理的限制（例如灯丝温度）
    max_temp = ts * 1.5 if all_insulated else ts
    return min(max(t, t_amb), max_temp)

def run_performance_test():
    """运行性能测试"""
    print("开始性能测试...")
    
    # 测试参数设置
    container_size = [0.3, 0.2, 0.2]  # 容器尺寸(m)
    power = 15  # 功率(W)
    t_amb = 25  # 环境温度(°C)
    bulb_pos = [0.15, 0.1, 0.1]  # 灯泡位置
    wall_thickness = 0.001  # 壁厚(m)
    materials = ['PP', 'PP', 'PP', 'PP', 'PP', 'PP']  # 默认全部使用PP材料
    
    # 创建测试点网格
    plane = "XY"
    pos = [0, 0, 0.1]
    
    # 预热JIT编译
    print("预热JIT编译...")
    _ = calculate_slice_temperature(
        plane, pos, container_size, power, t_amb,
        bulb_pos, wall_thickness,
        *materials,  # 解包材料列表
        has_shade=False,
        shade_height=0.0, shade_angle_h=0.0, shade_angle_v=0.0,
        shade_top_radius=0.0, shade_bottom_radius=0.0
    )
    
    # 性能测试
    print("执行计算时间测试...")
    iterations = 5
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        coords, temps = calculate_slice_temperature(
            plane, pos, container_size, power, t_amb,
            bulb_pos, wall_thickness,
            *materials,  # 解包材料列表
            has_shade=False,
            shade_height=0.0, shade_angle_h=0.0, shade_angle_v=0.0,
            shade_top_radius=0.0, shade_bottom_radius=0.0
        )
        end_time = time.time()
        times.append(end_time - start_time)
        print(f"迭代 {i+1}: {times[-1]:.3f} 秒")
    
    avg_time = sum(times) / len(times)
    print(f"\n平均计算时间: {avg_time:.3f} 秒")
    print(f"最快时间: {min(times):.3f} 秒")
    print(f"最慢时间: {max(times):.3f} 秒")
    
    return avg_time

@njit(cache=True)
def _vectorized_calculate(x_coords, y_coords, z_coords, power, t_amb, bulb_pos, 
                        container_size, wall_thickness,
                        front_cond, back_cond, left_cond, right_cond,
                        top_cond, bottom_cond,
                        has_hole=False, hole_face=None, hole_type=None,
                        hole_x=0.0, hole_y=0.0, hole_diameter=0.0,
                        hole_width=0.0, hole_height=0.0,
                        has_shade=False,
                        shade_height=0.0, shade_angle_h=0.0, shade_angle_v=0.0,
                        shade_top_radius=0.0, shade_bottom_radius=0.0):
    """向量化温度计算核心函数"""
    shape = x_coords.shape
    result = np.empty(shape)
    for i in range(shape[0]):
        for j in range(shape[1]):
            conds = [front_cond, back_cond, left_cond, right_cond, 
                    top_cond, bottom_cond]
            result[i,j] = calculate_temperature(
                x_coords[i,j], y_coords[i,j], z_coords[i,j],
                power, t_amb, bulb_pos, container_size,
                wall_thickness,
                front_cond, back_cond, left_cond, right_cond,
                top_cond, bottom_cond, conds,
                has_hole, hole_face, hole_type,
                hole_x, hole_y, hole_diameter,
                hole_width, hole_height,
                has_shade,
                shade_height, shade_angle_h, shade_angle_v,
                shade_top_radius, shade_bottom_radius
            )
    return result

def calculate_slice_temperature(plane, pos, container_size, power, t_amb, bulb_pos,
                              wall_thickness,
                              front_material, back_material, left_material, right_material,
                              top_material, bottom_material,
                              has_hole=False, hole_face=None, hole_type=None,
                              hole_x=0.0, hole_y=0.0, hole_diameter=0.0,
                              hole_width=0.0, hole_height=0.0,
                              has_shade=False,
                              shade_height=0.0, shade_angle_h=0.0, shade_angle_v=0.0,
                              shade_top_radius=0.0, shade_bottom_radius=0.0):
    """计算剖切面的温度分布（向量化版本）"""
    # 生成三维坐标网格
    if plane == "XY":
        x = np.linspace(0, container_size[0], 50)
        y = np.linspace(0, container_size[1], 50)
        X, Y = np.meshgrid(x, y, indexing='ij')
        Z = np.full_like(X, pos[2])
        coords = (X, Y)
    elif plane == "YZ":
        y = np.linspace(0, container_size[1], 50)
        z = np.linspace(0, container_size[2], 50) 
        Y, Z = np.meshgrid(y, z, indexing='ij')
        X = np.full_like(Y, pos[0])
        coords = (Y, Z)
    else:  # XZ
        x = np.linspace(0, container_size[0], 50)
        z = np.linspace(0, container_size[2], 50)
        X, Z = np.meshgrid(x, z, indexing='ij')
        Y = np.full_like(X, pos[1])
        coords = (X, Z)
    
    # 向量化计算温度场
    # Convert material names to conductivities
    conductivities = [
        get_material_conductivity(front_material),
        get_material_conductivity(back_material),
        get_material_conductivity(left_material),
        get_material_conductivity(right_material),
        get_material_conductivity(top_material),
        get_material_conductivity(bottom_material)
    ]
    
    temps = _vectorized_calculate(X, Y, Z, power, t_amb, bulb_pos, container_size,
                                wall_thickness,
                                *conductivities,
                                has_hole, hole_face, hole_type,
                                hole_x, hole_y, hole_diameter,
                                hole_width, hole_height,
                                has_shade,
                                shade_height, shade_angle_h, shade_angle_v,
                                shade_top_radius, shade_bottom_radius)
    
    return coords, temps
