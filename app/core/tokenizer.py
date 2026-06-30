"""
分词模块：jieba 分词 + 停用词过滤
"""
import os
import re
from typing import List, Set, Optional
import jieba


class Tokenizer:
    """中文分词器"""

    def __init__(self):
        self._stopwords: Set[str] = set()
        self._filter_single_char = True
        self._filter_numbers = True
        self._custom_dict_loaded = False

    def load_stopwords(self, filepath: str) -> None:
        """加载停用词表"""
        self._stopwords.clear()
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    self._stopwords.add(word)

    def add_stopwords(self, words: List[str]) -> None:
        """添加自定义停用词"""
        self._stopwords.update(words)

    def remove_stopwords(self, words: List[str]) -> None:
        """移除停用词"""
        self._stopwords -= set(words)

    def get_stopwords(self) -> Set[str]:
        """获取当前停用词表"""
        return self._stopwords.copy()

    def set_filter_single_char(self, enabled: bool) -> None:
        """设置是否过滤单字词"""
        self._filter_single_char = enabled

    def set_filter_numbers(self, enabled: bool) -> None:
        """设置是否过滤纯数字"""
        self._filter_numbers = enabled

    def load_custom_dict(self, filepath: str) -> None:
        """加载 jieba 自定义词典"""
        if os.path.exists(filepath):
            jieba.load_userdict(filepath)
            self._custom_dict_loaded = True

    def tokenize(self, text: str) -> List[str]:
        """对单条文本分词并过滤"""
        if not text or not isinstance(text, str):
            return []

        words = jieba.lcut(text)
        return self._filter_words(words)

    def tokenize_batch(self, texts: List[str]) -> List[List[str]]:
        """批量分词"""
        return [self.tokenize(t) for t in texts]

    def _filter_words(self, words: List[str]) -> List[str]:
        """过滤词语"""
        result = []
        for w in words:
            w = w.strip()
            if not w:
                continue
            if w in self._stopwords:
                continue
            if self._filter_single_char and len(w) == 1:
                continue
            if self._filter_numbers and re.match(r'^\d+$', w):
                continue
            result.append(w)
        return result
