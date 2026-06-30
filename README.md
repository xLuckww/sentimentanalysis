# 中文评论分析工具 (CN Comment Analyzer)

一个开箱即用的中文评论情感分析桌面应用。上传数据集 → 选择评论列 → 一键完成分词、词频统计、词云生成、情感分析。

> 🎯 面向产品经理、运营、市场人员，无需编程基础即可使用。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PyInstaller](https://img.shields.io/badge/PyInstaller-6.20-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 功能特性

### 核心功能
- 📁 **多格式支持** — CSV、Excel (.xlsx/.xls)、JSON (JSONL)
- 🔤 **智能分词** — 基于 jieba 的中文分词，内置 793 个停用词
- 📊 **词频统计** — 交互式条形图，支持自定义 Top-N
- ☁️ **词云生成** — 多种配色方案可选
- 💬 **情感分析** — SnowNLP 词典法，正面/中性/负面三分类
- 📥 **结果导出** — Excel 多 Sheet 导出、PNG 图片导出

### 交互功能
- 🔍 **情感筛选** — 按正面/中性/负面筛选查看全部评论
- ↕️ **得分排序** — 点击表头升序/降序切换
- 📄 **分页加载** — 大数据量自动分页，不卡顿
- ✏️ **自定义停用词** — 输入框 + 标签管理，叠加到内置词表
- 🔄 **更换文件** — 随时切换数据集

## 📥 下载安装

### macOS (推荐)

1. 下载 [评论情感分析.dmg](../../releases/latest)
2. 双击打开 DMG
3. 将 `评论情感分析.app` 拖入 `Applications` 文件夹
4. 从启动台打开即可

> ⚠️ 首次打开提示"无法验证开发者"：右键 → 打开

### 从源码运行

```bash
# 克隆项目
git clone https://github.com/xLuckww/sentimentanalysis.git
cd sentimentanalysis

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 界面 | pywebview + HTML/CSS/JS（毛玻璃拟态风格）|
| 后端 | Flask API |
| 分词 | jieba |
| 情感分析 | SnowNLP |
| 可视化 | matplotlib + wordcloud |
| 打包 | PyInstaller (--onedir) |

## 📂 项目结构

```
sentimentanalysis/
├── main.py                     # 应用入口（Flask + pywebview）
├── app/
│   ├── core/                   # 业务逻辑层
│   │   ├── data_loader.py      # 文件读取、编码检测
│   │   ├── text_cleaner.py     # 文本清洗
│   │   ├── tokenizer.py        # jieba 分词 + 停用词
│   │   ├── word_freq.py        # 词频统计
│   │   ├── sentiment.py        # 情感分析（SnowNLP）
│   │   ├── visualizer.py       # 条形图、词云图
│   │   └── exporter.py         # 导出 Excel/PNG
│   └── resources/
│       ├── stopwords/          # 内置停用词表
│       └── fonts/              # 中文字体
├── frontend/                   # 前端 UI
│   ├── index.html
│   ├── style.css               # 毛玻璃拟态 + 渐变色
│   └── main.js                 # 前端交互逻辑
├── sentiment.spec              # PyInstaller 打包配置
├── requirements.txt
├── PRD.md                      # 产品需求文档
└── README.md
```

## 🎨 UI 设计

采用**毛玻璃拟态 (Glassmorphism)** 设计风格：
- 🪟 半透明卡片 + 模糊背景
- 🌈 紫蓝渐变色系 (#667eea → #764ba2)
- ✨ 微交互动画（悬停、展开、脉冲）

## 📊 使用流程

```
上传文件 → 选择评论列 → 配置参数 → 查看结果
   │            │            │          │
   │            │            │          ├─ 词频条形图
   │            │            │          ├─ 词云图
   │            │            │          ├─ 情感分布饼图
   │            │            │          ├─ 情感明细表格（筛选/排序/分页）
   │            │            │          └─ 导出 Excel / PNG
   │            │            │
   │            │            ├─ 高频词数量 (10-100)
   │            │            ├─ 是否启用情感分析
   │            │            └─ 自定义停用词
   │            │
   │            └─ 自动推荐文本列
   │
   └─ CSV / Excel / JSON
```

## 🔧 重新打包

```bash
# 安装打包依赖
pip install pyinstaller

# 打包 macOS .app
pyinstaller sentiment.spec --noconfirm --clean

# 产物位置
dist/评论情感分析.app
```

## 📝 数据格式示例

**CSV / Excel：**

| label | review |
|-------|--------|
| 1 | 外卖速度很快，味道也不错 |
| 0 | 难吃死了，再也不买了 |

**JSON (JSONL)：**

```json
{"label": 1, "content": "外卖速度很快，味道也不错"}
{"label": 0, "content": "难吃死了，再也不买了"}
```

## 📄 License

MIT

## 🙏 致谢

- [jieba](https://github.com/fxsjy/jieba) — 中文分词
- [SnowNLP](https://github.com/isnowfy/snownlp) — 中文情感分析
- [wordcloud](https://github.com/amueller/word_cloud) — 词云生成
- [pywebview](https://github.com/r0x0r/pywebview) — 轻量桌面窗口
