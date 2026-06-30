"""
停用词资源模块
"""
import os

STOPWORDS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STOPWORDS_PATH = os.path.join(STOPWORDS_DIR, 'default_stopwords.txt')
