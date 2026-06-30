"""
词频统计模块
"""
from collections import Counter
from typing import List, Tuple, Dict


class WordFrequency:
    """词频统计"""

    @staticmethod
    def count(words_list: List[List[str]]) -> Counter:
        """统计所有分词结果的词频"""
        counter = Counter()
        for words in words_list:
            counter.update(words)
        return counter

    @staticmethod
    def top_n(counter: Counter, n: int = 30) -> List[Tuple[str, int]]:
        """获取 Top N 高频词"""
        return counter.most_common(n)

    @staticmethod
    def to_dict(counter: Counter) -> Dict[str, int]:
        """转换为字典"""
        return dict(counter)
