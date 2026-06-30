"""
可视化模块：生成条形图、词云图
"""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud
from typing import List, Tuple, Optional
import tempfile


def _resource_path(relative_path):
    """获取资源路径，兼容 PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)


class Visualizer:
    """可视化生成器"""

    # 字体候选路径（优先使用打包内的字体）
    FONT_CANDIDATES = [
        _resource_path('app/resources/fonts/STHeiti.ttc'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'fonts', 'STHeiti.ttc'),
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    ]

    # 词云配色方案
    COLOR_SCHEMES = {
        '默认': 'viridis',
        '蓝紫色': 'cool',
        '暖色调': 'autumn',
    }

    def __init__(self):
        self._font_path = self._find_font()
        self._font_prop = FontProperties(fname=self._font_path) if self._font_path else None

    def _find_font(self) -> Optional[str]:
        """查找可用的中文字体"""
        for path in self.FONT_CANDIDATES:
            if os.path.exists(path):
                return path
        return None

    def create_bar_chart(
        self,
        word_freq: List[Tuple[str, int]],
        title: str = '词频统计',
        figsize: Tuple[int, int] = (10, 8)
    ) -> plt.Figure:
        """生成词频条形图"""
        if not word_freq:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=16)
            return fig

        words = [w for w, _ in word_freq]
        counts = [c for _, c in word_freq]

        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.barh(range(len(words)), counts, color=plt.cm.cool(
            [i / len(words) for i in range(len(words))]
        ))

        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontproperties=self._font_prop, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel('出现次数', fontproperties=self._font_prop, fontsize=12)
        ax.set_title(title, fontproperties=self._font_prop, fontsize=14, fontweight='bold')

        # 添加数值标签
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    str(count), va='center', fontsize=10)

        plt.tight_layout()
        return fig

    def create_wordcloud(
        self,
        word_freq_dict: dict,
        color_scheme: str = '默认',
        width: int = 800,
        height: int = 500
    ) -> plt.Figure:
        """生成词云图"""
        colormap = self.COLOR_SCHEMES.get(color_scheme, 'viridis')

        wc = WordCloud(
            font_path=self._font_path,
            background_color='white',
            width=width,
            height=height,
            max_words=200,
            colormap=colormap,
            prefer_horizontal=0.7,
            min_font_size=10,
            max_font_size=100,
            relative_scaling=0.5,
        )

        if word_freq_dict:
            wc.generate_from_frequencies(word_freq_dict)
        else:
            wc.generate_from_frequencies({'暂无数据': 1})

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        plt.tight_layout(pad=0)

        return fig

    def create_sentiment_pie(self, distribution: dict) -> plt.Figure:
        """生成情感分布饼图"""
        labels = list(distribution.keys())
        sizes = list(distribution.values())
        colors = ['#4CAF50', '#FFC107', '#F44336']  # 绿、黄、红

        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontproperties': self._font_prop, 'fontsize': 12}
        )

        for autotext in autotexts:
            autotext.set_fontsize(11)

        ax.set_title('情感分布', fontproperties=self._font_prop, fontsize=14, fontweight='bold')
        plt.tight_layout()

        return fig
