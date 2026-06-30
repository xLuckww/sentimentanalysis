"""
导出模块：导出 Excel、PNG
"""
import os
from datetime import datetime
from typing import List, Tuple, Optional
import pandas as pd
import matplotlib.pyplot as plt


class Exporter:
    """导出器"""

    @staticmethod
    def export_excel(
        original_df: pd.DataFrame,
        sentiment_results: list,
        word_freq: List[Tuple[str, int]],
        save_path: str
    ) -> Optional[str]:
        """
        导出分析结果为 Excel
        包含两个 sheet：原始数据+情感、词频统计
        """
        try:
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                # Sheet 1: 原始数据 + 情感得分
                df_export = original_df.copy()
                df_export['情感得分'] = [r.score for r in sentiment_results]
                df_export['情感分类'] = [r.label for r in sentiment_results]
                df_export.to_excel(writer, sheet_name='评论数据', index=False)

                # Sheet 2: 词频统计
                freq_df = pd.DataFrame(word_freq, columns=['词语', '频次'])
                freq_df.to_excel(writer, sheet_name='词频统计', index=False)

            return None
        except Exception as e:
            return f"导出失败：{str(e)}"

    @staticmethod
    def export_figure(fig: plt.Figure, save_path: str, dpi: int = 150) -> Optional[str]:
        """导出图表为 PNG"""
        try:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
            return None
        except Exception as e:
            return f"导出图片失败：{str(e)}"

    @staticmethod
    def get_default_filename(prefix: str, ext: str) -> str:
        """生成默认文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        return os.path.join(desktop, f'{prefix}_{timestamp}.{ext}')
