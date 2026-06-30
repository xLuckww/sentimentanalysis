# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 中文评论分析工具
使用 --onedir 模式，生成 macOS .app
"""

import os
import sys

block_cipher = None
BASE = os.path.dirname(os.path.abspath(SPEC))

# ── 数据文件 ──
datas = [
    # 前端静态文件
    (os.path.join(BASE, 'frontend'), 'frontend'),
    # 停用词表
    (os.path.join(BASE, 'app', 'resources', 'stopwords'), os.path.join('app', 'resources', 'stopwords')),
    # 中文字体
    (os.path.join(BASE, 'app', 'resources', 'fonts'), os.path.join('app', 'resources', 'fonts')),
]

# jieba 数据文件
import jieba
jieba_dir = os.path.dirname(jieba.__file__)
datas.append((jieba_dir, 'jieba'))

# snownlp 数据文件
import snownlp
snownlp_dir = os.path.dirname(snownlp.__file__)
datas.append((snownlp_dir, 'snownlp'))

# ── 分析配置 ──
a = Analysis(
    [os.path.join(BASE, 'main.py')],
    pathex=[BASE],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Flask
        'flask', 'flask_cors', 'werkzeug', 'jinja2',
        # pywebview
        'webview', 'webview.platforms.cocoa',
        # 数据处理
        'pandas', 'openpyxl', 'chardet',
        # 分词
        'jieba', 'jieba.posseg', 'jieba.finalseg',
        # 可视化
        'matplotlib', 'matplotlib.backends', 'matplotlib.backends.backend_agg',
        'wordcloud',
        # 情感分析
        'snownlp', 'snownlp.sentiment',
        # 其他
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的 matplotlib 后端
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qt4agg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_gtk3agg',
        'matplotlib.backends.backend_wxagg',
        'matplotlib.backends.backend_webagg',
        # 排除不需要的 GUI 框架
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'wx',
        # 排除测试模块（保留 unittest，pyparsing 依赖它）
        'pytest',
        # 排除 IPython
        'IPython', 'ipykernel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── 打包配置 ──
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='评论情感分析',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 不使用 UPX，避免兼容性问题
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='评论情感分析',
)

app = BUNDLE(
    coll,
    name='评论情感分析.app',
    icon=os.path.join(BASE, 'icons', 'icon.icns'),
    bundle_identifier='com.sentiment.analyzer',
    info_plist={
        'CFBundleName': '评论情感分析',
        'CFBundleDisplayName': '评论情感分析',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
