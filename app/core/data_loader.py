"""
数据加载模块：读取 CSV/Excel 文件，自动检测编码
"""
import os
import chardet
import pandas as pd
from typing import Tuple, Optional


class DataLoader:
    """文件加载器，支持 CSV/Excel/JSON，自动检测编码"""

    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}
    MAX_FILE_SIZE_MB = 50
    MAX_ROWS_WARNING = 100_000

    @staticmethod
    def load_file(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        加载文件，返回 (DataFrame, 错误信息)
        成功时错误信息为 None，失败时 DataFrame 为 None
        """
        if not os.path.exists(file_path):
            return None, "文件不存在"

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in DataLoader.SUPPORTED_EXTENSIONS:
            return None, f"不支持的文件格式：{ext}，请上传 CSV 或 Excel 文件"

        # 检查文件大小
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        size_warning = ""
        if file_size_mb > DataLoader.MAX_FILE_SIZE_MB:
            size_warning = f"文件较大（{file_size_mb:.1f}MB），分析可能较慢"

        try:
            if ext == '.csv':
                df = DataLoader._load_csv(file_path)
            elif ext == '.json':
                df = DataLoader._load_json(file_path)
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            return None, f"文件解析失败：{DataLoader._friendly_error(e)}"

        if df is None or df.empty:
            return None, "文件为空或解析后无数据"

        # 行数警告
        row_warning = ""
        if len(df) > DataLoader.MAX_ROWS_WARNING:
            row_warning = f"数据量较大（{len(df):,} 行），分析可能较慢"

        warning = size_warning or row_warning or None
        return df, warning

    @staticmethod
    def _load_json(file_path: str) -> Optional[pd.DataFrame]:
        """加载 JSON 文件，支持 JSONL（每行一个 JSON）和标准 JSON 数组"""
        try:
            # 先尝试 JSONL 格式（每行一个 JSON）
            df = pd.read_json(file_path, lines=True)
            if not df.empty:
                return df
        except Exception:
            pass

        try:
            # 再尝试标准 JSON 数组
            df = pd.read_json(file_path, lines=False)
            if not df.empty:
                return df
        except Exception:
            pass

        return None

    @staticmethod
    def _load_csv(file_path: str) -> Optional[pd.DataFrame]:
        """加载 CSV，自动尝试多种编码"""
        encodings = ['utf-8', 'gbk', 'gb18030', 'gb2312', 'latin1']

        # 先用 chardet 探测
        with open(file_path, 'rb') as f:
            raw = f.read(10000)
            result = chardet.detect(raw)
            detected = result.get('encoding', '').lower()
            if detected and detected not in [e.lower() for e in encodings]:
                encodings.insert(0, detected)

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                if not df.empty:
                    return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                continue

        return None

    @staticmethod
    def _friendly_error(e: Exception) -> str:
        """将异常转换为用户可理解的提示"""
        error_type = type(e).__name__
        if 'Unicode' in error_type or 'decode' in str(e).lower():
            return "文件编码无法识别，请确认文件是否为有效的 CSV 格式"
        if 'EmptyDataError' in error_type:
            return "文件为空"
        if 'ParserError' in error_type:
            return "文件格式错误，请检查是否为有效的 CSV/Excel 文件"
        if 'openpyxl' in str(e).lower() or 'xlrd' in str(e).lower():
            return "Excel 文件解析失败，请确认文件未损坏"
        return str(e)[:100]
