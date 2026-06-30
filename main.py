"""
中文评论分析工具 - 桌面应用
使用 pywebview + Flask，毛玻璃拟态 UI
"""
import os
import sys
import json
import base64
import threading
import time
import socket
from datetime import datetime
from io import BytesIO

import webview
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS


# ── 资源路径（兼容 PyInstaller 打包） ──
def resource_path(relative_path):
    """获取资源文件绝对路径，兼容开发环境和 PyInstaller 打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


BASE_DIR = resource_path('')

# ── 导入分析模块 ──
sys.path.insert(0, BASE_DIR)
from app.core.data_loader import DataLoader
from app.core.tokenizer import Tokenizer
from app.core.word_freq import WordFrequency
from app.core.sentiment import SentimentAnalyzer
from app.core.visualizer import Visualizer

# ── Flask 应用 ──
app = Flask(__name__)
CORS(app)

# 全局状态
current_df = None
current_column = None
tokenizer = Tokenizer()
analysis_result = None  # 缓存分析结果，用于导出

# 加载内置停用词
_stopwords_path = resource_path('app/resources/stopwords/default_stopwords.txt')
if os.path.exists(_stopwords_path):
    tokenizer.load_stopwords(_stopwords_path)


# ── 前端路由 ──
FRONTEND_DIR = resource_path('frontend')

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ── API 路由 ──
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/parse-file', methods=['POST'])
def parse_file():
    """解析上传的文件"""
    global current_df

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    filename = file.filename

    tmp_path = os.path.join(BASE_DIR, '_tmp_upload' + os.path.splitext(filename)[1])
    file.save(tmp_path)

    try:
        df, warning = DataLoader.load_file(tmp_path)
        if df is None:
            return jsonify({'error': warning or '文件解析失败'}), 400

        current_df = df

        return jsonify({
            'columns': df.columns.tolist(),
            'preview': df.head(20).fillna('').to_dict(orient='records'),
            'total_rows': len(df),
            'warning': warning,
        })
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route('/api/set-column', methods=['POST'])
def set_column():
    """设置评论列"""
    global current_column
    data = request.json
    column = data.get('column')

    if current_df is None:
        return jsonify({'error': '请先上传文件'}), 400

    if column not in current_df.columns:
        return jsonify({'error': f'列 {column} 不存在'}), 400

    current_column = column

    preview = current_df[column].dropna().head(10).tolist()
    non_null = int(current_df[column].dropna().count())
    null_count = int(current_df[column].isna().sum())

    return jsonify({
        'preview': preview,
        'non_null': non_null,
        'null_count': null_count,
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """执行分析"""
    global current_df, current_column, analysis_result

    if current_df is None or current_column is None:
        return jsonify({'error': '请先上传文件并选择列'}), 400

    data = request.json
    top_n = data.get('top_n', 30)
    color_scheme = data.get('color_scheme', '默认')
    enable_sentiment = data.get('enable_sentiment', True)
    filter_single = data.get('filter_single_char', True)
    filter_numbers = data.get('filter_numbers', True)
    custom_stopwords = data.get('custom_stopwords', [])

    # 设置分词器
    tokenizer.set_filter_single_char(filter_single)
    tokenizer.set_filter_numbers(filter_numbers)

    # 加载内置停用词
    if os.path.exists(_stopwords_path):
        tokenizer.load_stopwords(_stopwords_path)

    # 添加自定义停用词
    if custom_stopwords:
        tokenizer.add_stopwords(custom_stopwords)

    # 获取文本
    texts = current_df[current_column].dropna().astype(str).tolist()
    if not texts:
        return jsonify({'error': '没有有效数据'}), 400

    # 分词
    all_words_list = []
    for text in texts:
        words = tokenizer.tokenize(text)
        all_words_list.append(words)

    # 词频
    counter = WordFrequency.count(all_words_list)
    word_freq = WordFrequency.top_n(counter, top_n)
    word_freq_dict = WordFrequency.to_dict(counter)

    # 词云
    visualizer = Visualizer()
    wc_fig = visualizer.create_wordcloud(word_freq_dict, color_scheme=color_scheme)
    buf = BytesIO()
    wc_fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    wordcloud_b64 = base64.b64encode(buf.read()).decode('utf-8')

    # 条形图
    bar_fig = visualizer.create_bar_chart(word_freq)
    buf_bar = BytesIO()
    bar_fig.savefig(buf_bar, format='png', dpi=150, bbox_inches='tight', pad_inches=0.1)
    buf_bar.seek(0)
    bar_b64 = base64.b64encode(buf_bar.read()).decode('utf-8')

    import matplotlib.pyplot as plt
    plt.close(wc_fig)
    plt.close(bar_fig)

    result = {
        'total_words': sum(len(w) for w in all_words_list),
        'unique_words': len(set(w for words in all_words_list for w in words)),
        'top_freq': [{'word': w, 'count': c} for w, c in word_freq],
        'all_freq': [{'word': w, 'count': c} for w, c in counter.most_common()],
        'wordcloud': wordcloud_b64,
        'bar_chart': bar_b64,
    }

    # 情感分析
    sentiment_results = []
    if enable_sentiment:
        sentiment_results = SentimentAnalyzer.analyze_batch(texts)
        sentiment_dist = SentimentAnalyzer.get_distribution(sentiment_results)

        sent_fig = visualizer.create_sentiment_pie(sentiment_dist)
        buf2 = BytesIO()
        sent_fig.savefig(buf2, format='png', dpi=120, bbox_inches='tight')
        buf2.seek(0)
        sentiment_b64 = base64.b64encode(buf2.read()).decode('utf-8')
        plt.close(sent_fig)

        result['sentiment_dist'] = sentiment_dist
        result['sentiment_chart'] = sentiment_b64
        result['sentiment_total'] = len(sentiment_results)
        # 只返回前 50 条预览，其余通过分页接口获取
        result['sentiment_details'] = [
            {'text': r.text[:200], 'score': round(r.score, 3), 'label': r.label}
            for r in sentiment_results[:50]
        ]

    # 缓存分析结果用于导出
    analysis_result = {
        'original_df': current_df,
        'column_name': current_column,
        'word_freq': word_freq,
        'all_freq': counter.most_common(),
        'sentiment_results': sentiment_results,
        'enable_sentiment': enable_sentiment,
    }

    return jsonify(result)


@app.route('/api/sentiment-page', methods=['POST'])
def sentiment_page():
    """情感分析分页接口"""
    global analysis_result

    if analysis_result is None:
        return jsonify({'error': '请先执行分析'}), 400

    data = request.json
    label_filter = data.get('label', 'all')  # all/正面/中性/负面
    sort_by = data.get('sort_by', 'score')    # score
    sort_order = data.get('sort_order', 'desc')  # asc/desc
    page = data.get('page', 1)
    page_size = data.get('page_size', 50)

    results = analysis_result['sentiment_results']

    # 筛选
    if label_filter != 'all':
        results = [r for r in results if r.label == label_filter]

    # 排序
    reverse = (sort_order == 'desc')
    if sort_by == 'score':
        results = sorted(results, key=lambda r: r.score, reverse=reverse)

    # 分页
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = results[start:end]

    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'details': [
            {'text': r.text[:200], 'score': round(r.score, 3), 'label': r.label}
            for r in page_data
        ],
    })


@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    """导出 Excel"""
    global analysis_result

    if analysis_result is None:
        return jsonify({'error': '请先执行分析'}), 400

    import pandas as pd

    df = analysis_result['original_df']
    column_name = analysis_result['column_name']
    enable_sentiment = analysis_result['enable_sentiment']
    all_freq = analysis_result['all_freq']

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'分析结果_{timestamp}.xlsx'
    filepath = os.path.join(os.path.expanduser('~'), 'Desktop', filename)

    try:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet1: 原始数据 + 情感
            df_export = df.copy()
            if enable_sentiment and analysis_result['sentiment_results']:
                df_export['情感得分'] = [r.score for r in analysis_result['sentiment_results']]
                df_export['情感分类'] = [r.label for r in analysis_result['sentiment_results']]
            df_export.to_excel(writer, sheet_name='原始数据', index=False)

            # Sheet2: 词频统计
            freq_df = pd.DataFrame(all_freq, columns=['词语', '频次'])
            freq_df.to_excel(writer, sheet_name='词频统计', index=False)

        return jsonify({'success': True, 'path': filepath, 'filename': filename})
    except Exception as e:
        return jsonify({'error': f'导出失败：{str(e)}'}), 500


@app.route('/api/export-image', methods=['POST'])
def export_image():
    """导出图片"""
    global analysis_result

    if analysis_result is None:
        return jsonify({'error': '请先执行分析'}), 400

    data = request.json
    image_type = data.get('type')  # bar / wordcloud
    color_scheme = data.get('color_scheme', '默认')

    visualizer = Visualizer()

    if image_type == 'bar':
        fig = visualizer.create_bar_chart(analysis_result['word_freq'])
        prefix = '词频条形图'
    elif image_type == 'wordcloud':
        word_freq_dict = dict(analysis_result['all_freq'])
        fig = visualizer.create_wordcloud(word_freq_dict, color_scheme=color_scheme)
        prefix = '词云图'
    else:
        return jsonify({'error': '未知图片类型'}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{prefix}_{timestamp}.png'
    filepath = os.path.join(os.path.expanduser('~'), 'Desktop', filename)

    try:
        fig.savefig(filepath, dpi=150, bbox_inches='tight', pad_inches=0.1)
        import matplotlib.pyplot as plt
        plt.close(fig)
        return jsonify({'success': True, 'path': filepath, 'filename': filename})
    except Exception as e:
        return jsonify({'error': f'导出失败：{str(e)}'}), 500


# ── 启动 ──
PORT = 5001

def find_available_port(start_port=5001):
    """查找可用端口"""
    for port in range(start_port, start_port + 100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                return port
        except Exception:
            return port
    return start_port

def start_server():
    global PORT
    PORT = find_available_port(5001)
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    window = webview.create_window(
        '中文评论分析工具',
        url=f'http://127.0.0.1:{PORT}',
        width=1100,
        height=750,
        resizable=True,
        min_size=(900, 600),
    )
    webview.start()
