"""
情感分析模块：使用 SnowNLP 进行情感打分
"""
from dataclasses import dataclass
from typing import List, Optional
from snownlp import SnowNLP


@dataclass
class SentimentResult:
    """情感分析结果"""
    score: float          # 0-1 情感得分
    label: str            # 正面/中性/负面
    text: str             # 原始文本


class SentimentAnalyzer:
    """情感分析器"""

    # 情感分档阈值
    POSITIVE_THRESHOLD = 0.6
    NEGATIVE_THRESHOLD = 0.4

    @staticmethod
    def analyze(text: str) -> SentimentResult:
        """分析单条文本的情感"""
        if not text or not isinstance(text, str):
            return SentimentResult(score=0.5, label='中性', text=str(text))

        try:
            s = SnowNLP(text)
            score = s.sentiments
        except Exception:
            score = 0.5

        label = SentimentAnalyzer._classify(score)
        return SentimentResult(score=score, label=label, text=text)

    @staticmethod
    def analyze_batch(texts: List[str], progress_callback=None) -> List[SentimentResult]:
        """批量分析情感"""
        results = []
        total = len(texts)
        for i, text in enumerate(texts):
            result = SentimentAnalyzer.analyze(text)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total)
        return results

    @staticmethod
    def _classify(score: float) -> str:
        """根据得分分类"""
        if score >= SentimentAnalyzer.POSITIVE_THRESHOLD:
            return '正面'
        elif score <= SentimentAnalyzer.NEGATIVE_THRESHOLD:
            return '负面'
        else:
            return '中性'

    @staticmethod
    def get_distribution(results: List[SentimentResult]) -> dict:
        """获取情感分布统计"""
        dist = {'正面': 0, '中性': 0, '负面': 0}
        for r in results:
            dist[r.label] += 1
        return dist
