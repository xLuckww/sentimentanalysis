"""
文本清洗模块：去除 URL、@用户名、表情符号、标点等
"""
import re
from typing import List


class TextCleaner:
    """文本清洗器"""

    # URL 模式
    _URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    # @用户名
    _MENTION_PATTERN = re.compile(r'@\w+')
    # 文本表情 [微笑] [开心] 等
    _EMOJI_PATTERN = re.compile(r'\[[一-龥]+\]')
    # HTML 标签
    _HTML_PATTERN = re.compile(r'<[^>]+>')
    # 多余空白符
    _WHITESPACE_PATTERN = re.compile(r'\s+')
    # 标点符号（保留中文字符和字母数字）
    _PUNCTUATION_PATTERN = re.compile(r'[^一-龥a-zA-Z0-9\s]')

    @staticmethod
    def clean(text: str) -> str:
        """清洗单条文本"""
        if not isinstance(text, str):
            text = str(text)

        text = TextCleaner._URL_PATTERN.sub('', text)
        text = TextCleaner._MENTION_PATTERN.sub('', text)
        text = TextCleaner._EMOJI_PATTERN.sub('', text)
        text = TextCleaner._HTML_PATTERN.sub('', text)
        text = TextCleaner._PUNCTUATION_PATTERN.sub('', text)
        text = TextCleaner._WHITESPACE_PATTERN.sub(' ', text)

        return text.strip()

    @staticmethod
    def clean_batch(texts: List[str]) -> List[str]:
        """批量清洗文本"""
        return [TextCleaner.clean(t) for t in texts]
