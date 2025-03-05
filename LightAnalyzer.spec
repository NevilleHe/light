# -*- mode: python ; coding: utf-8 -*-

import os
import matplotlib
import sys
block_cipher = None

# 项目根目录
BASE_PATH = os.path.abspath(os.path.dirname('launcher.py'))

# 确保创建assets目录
assets_dir = os.path.join('light_analyzer', 'assets')
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

a = Analysis(
    ['launcher.py'],
    pathex=[
        BASE_PATH,
        os.path.join(BASE_PATH, 'light_analyzer')
    ],
    binaries=[],
    datas=[
        # 添加matplotlib字体和配置文件
        (matplotlib.get_data_path(), 'matplotlib/mpl-data'),
        # 添加项目资源文件及源代码
        ('light_analyzer/assets', 'light_analyzer/assets'),
        ('light_analyzer/*.py', 'light_analyzer'),
    ],
    hiddenimports=[
        # 数值计算相关
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'numpy.random',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'tkinter',
        'tkinter.ttk',
        'PIL._tkinter_finder',
        'PIL.ImageDraw',
        'PIL.Image',
        'PIL.ImageTk',
        'mpl_toolkits',
        'mpl_toolkits.mplot3d',
        'numba',
        'numba.core',
        'numba.core.runtime',
        'numba.core.typing',
        'numba.core.types',
        'numba.core.dispatcher',
        'numba.np.arraymath',
        'numba.np.random',
        'light_analyzer',
        'light_analyzer.temperature_model',
        'light_analyzer.visualization',
        'light_analyzer.ui_windows',
        'light_analyzer.main'
    ],
    hookspath=[],
    hooksconfig={
        "matplotlib": {
            "backends": ["TkAgg"],
        }
    },
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'gtk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉不需要的matplotlib后端
def remove_matplotlib_backends(analysis):
    backend_excludes = {'qt5agg.py', 'qt5cairo.py', 'gtk3agg.py', 'gtk3cairo.py',
                       'wxagg.py', 'wx.py', 'macosx.py'}
    analysis.binaries = [(name, path, type_)
                        for name, path, type_ in analysis.binaries
                        if not any(backend in name.lower() for backend in backend_excludes)]
    return analysis

a = remove_matplotlib_backends(a)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LightAnalyzer',
    debug=True,  # 临时启用调试模式以查看详细错误信息
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 暂时启用控制台以查看错误信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='light_analyzer/assets/icon.ico'
)
