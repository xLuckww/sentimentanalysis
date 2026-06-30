/**
 * 评论情感分析 - 前端逻辑
 * V1.1：情感筛选 + 排序分页 + 导出 + 自定义停用词
 */

const API_BASE = '';

// ── 状态 ──
let currentData = null;
let currentColumn = null;
let customStopwords = [];
let sentimentState = {
    label: 'all',
    sortBy: 'score',
    sortOrder: 'desc',
    page: 1,
    pageSize: 50,
    total: 0,
    totalPages: 0,
};
let currentColorScheme = '默认';

// ── DOM ──
const $ = (sel) => document.querySelector(sel);
const uploadZone = $('#upload-zone');
const fileInput = $('#file-input');
const dataSection = $('#data-section');
const loadingSection = $('#loading-section');
const resultSection = $('#result-section');
const columnSelect = $('#column-select');
const topNSlider = $('#top-n');
const topNValue = $('#top-n-value');
const analyzeBtn = $('#analyze-btn');
const sentimentToggle = $('#sentiment-toggle');
const sentimentFilter = $('#sentiment-filter');

// ── 初始化 ──
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    setupControls();
});

// ── 文件上传 ──
function setupUpload() {
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });
}

// ── 控件设置 ──
function setupControls() {
    topNSlider.addEventListener('input', (e) => {
        topNValue.textContent = e.target.value;
    });

    columnSelect.addEventListener('change', (e) => {
        currentColumn = e.target.value;
        fetch(`${API_BASE}/api/set-column`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: currentColumn }),
        });
    });

    analyzeBtn.addEventListener('click', () => runAnalysis());

    // 更换文件
    $('#change-file-btn').addEventListener('click', () => {
        dataSection.classList.add('hidden');
        resultSection.classList.add('hidden');
        loadingSection.classList.add('hidden');
        uploadZone.parentElement.classList.remove('hidden');
        fileInput.value = '';
        currentData = null;
        currentColumn = null;
    });

    // 返回修改
    $('#reanalyze-btn').addEventListener('click', () => {
        resultSection.classList.add('hidden');
        dataSection.classList.remove('hidden');
    });

    // 情感筛选标签
    document.querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            sentimentState.label = tag.dataset.label;
            sentimentState.page = 1;
            loadSentimentPage();
        });
    });

    // 情感得分排序
    const scoreHeader = document.querySelector('th[data-sort="score"]');
    if (scoreHeader) {
        scoreHeader.addEventListener('click', () => {
            if (sentimentState.sortOrder === 'desc') {
                sentimentState.sortOrder = 'asc';
                scoreHeader.className = 'sortable asc';
            } else {
                sentimentState.sortOrder = 'desc';
                scoreHeader.className = 'sortable desc';
            }
            sentimentState.page = 1;
            loadSentimentPage();
        });
    }

    // 导出按钮
    $('#export-excel-btn').addEventListener('click', () => exportExcel());
    $('#export-bar-btn').addEventListener('click', () => exportImage('bar'));
    $('#export-wc-btn').addEventListener('click', () => exportImage('wordcloud'));

    // 自定义停用词
    setupStopwords();
}

// ── 自定义停用词 ──
function setupStopwords() {
    const input = $('#stopwords-input');
    const addBtn = $('#add-stopword-btn');

    const addWord = () => {
        const word = input.value.trim();
        if (!word) return;
        if (customStopwords.includes(word)) {
            input.value = '';
            return;
        }
        customStopwords.push(word);
        input.value = '';
        renderStopwordsTags();
    };

    addBtn.addEventListener('click', addWord);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') addWord();
    });
}

function renderStopwordsTags() {
    const container = $('#stopwords-tags');
    container.innerHTML = customStopwords.map((word, i) => `
        <span class="stopword-tag">
            ${escapeHtml(word)}
            <span class="remove" data-index="${i}">×</span>
        </span>
    `).join('');

    container.querySelectorAll('.remove').forEach(btn => {
        btn.addEventListener('click', () => {
            const index = parseInt(btn.dataset.index);
            customStopwords.splice(index, 1);
            renderStopwordsTags();
        });
    });
}

// ── 处理文件 ──
async function handleFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    $('#file-name').textContent = file.name;

    try {
        const res = await fetch(`${API_BASE}/api/parse-file`, {
            method: 'POST',
            body: formData,
        });

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        currentData = data;

        $('#total-rows').textContent = data.total_rows.toLocaleString();
        $('#total-cols').textContent = data.columns.length;

        renderTable(data.columns, data.preview);

        columnSelect.innerHTML = data.columns
            .map((col) => `<option value="${col}">${col}</option>`)
            .join('');

        const defaultCol = data.columns.find(c =>
            ['content', 'review', 'comment', 'text', '评论', '内容'].includes(c.toLowerCase())
        ) || data.columns[0];
        columnSelect.value = defaultCol;
        currentColumn = defaultCol;

        fetch(`${API_BASE}/api/set-column`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: currentColumn }),
        });

        if (data.warning) {
            alert('⚠️ ' + data.warning);
        }

        dataSection.classList.remove('hidden');
        uploadZone.parentElement.classList.add('hidden');

    } catch (err) {
        alert('文件解析失败，请检查文件格式');
        console.error(err);
    }
}

// ── 渲染表格 ──
function renderTable(columns, rows) {
    const thead = $('#table-head');
    const tbody = $('#table-body');

    thead.innerHTML = `<tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map(row =>
        `<tr>${columns.map(c => `<td title="${escapeHtml(String(row[c] || ''))}">${truncate(String(row[c] || ''), 60)}</td>`).join('')}</tr>`
    ).join('');
}

function truncate(str, len) {
    return str.length > len ? str.slice(0, len) + '...' : str;
}

// ── 执行分析 ──
async function runAnalysis() {
    if (!currentData || !currentColumn) return;

    dataSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                top_n: parseInt(topNSlider.value),
                enable_sentiment: sentimentToggle.value === 'true',
                custom_stopwords: customStopwords,
            }),
        });

        const data = await res.json();

        if (data.error) {
            alert(data.error);
            loadingSection.classList.add('hidden');
            dataSection.classList.remove('hidden');
            return;
        }

        renderResults(data);

    } catch (err) {
        alert('分析失败，请重试');
        console.error(err);
        loadingSection.classList.add('hidden');
        dataSection.classList.remove('hidden');
    }
}

// ── 渲染结果 ──
function renderResults(data) {
    loadingSection.classList.add('hidden');
    resultSection.classList.remove('hidden');

    $('#result-total').textContent = data.total_words.toLocaleString();
    $('#result-unique').textContent = data.unique_words.toLocaleString();

    renderFreqChart(data.top_freq);
    $('#wordcloud-img').src = `data:image/png;base64,${data.wordcloud}`;

    // 情感分析
    if (data.sentiment_dist) {
        $('#sentiment-section').classList.remove('hidden');
        $('#sentiment-img').src = `data:image/png;base64,${data.sentiment_chart}`;

        const stats = $('#sentiment-stats');
        const dist = data.sentiment_dist;
        const total = dist['正面'] + dist['中性'] + dist['负面'];
        stats.innerHTML = `
            <div class="stat-item positive">
                <span class="stat-label">正面</span>
                <span class="stat-value">${dist['正面']}</span>
                <span class="stat-pct">${(dist['正面'] / total * 100).toFixed(1)}%</span>
            </div>
            <div class="stat-item neutral">
                <span class="stat-label">中性</span>
                <span class="stat-value">${dist['中性']}</span>
                <span class="stat-pct">${(dist['中性'] / total * 100).toFixed(1)}%</span>
            </div>
            <div class="stat-item negative">
                <span class="stat-label">负面</span>
                <span class="stat-value">${dist['负面']}</span>
                <span class="stat-pct">${(dist['负面'] / total * 100).toFixed(1)}%</span>
            </div>
        `;

        // 重置筛选状态
        sentimentState = { label: 'all', sortBy: 'score', sortOrder: 'desc', page: 1, pageSize: 50, total: 0, totalPages: 0 };
        document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
        document.querySelector('.filter-tag[data-label="all"]').classList.add('active');

        // 加载第一页
        loadSentimentPage();
    } else {
        $('#sentiment-section').classList.add('hidden');
    }
}

// ── 词频条形图 ──
function renderFreqChart(freqData) {
    const container = $('#freq-chart');
    const maxCount = freqData[0]?.count || 1;

    container.innerHTML = freqData.map((item, i) => {
        const width = (item.count / maxCount * 100).toFixed(1);
        const delay = i * 30;
        return `
            <div class="freq-bar" style="animation: fadeInUp 0.4s ease ${delay}ms forwards; opacity: 0;">
                <span class="freq-word">${escapeHtml(item.word)}</span>
                <div class="freq-track">
                    <div class="freq-fill" style="width: 0%"></div>
                </div>
                <span class="freq-count">${item.count}</span>
            </div>
        `;
    }).join('');

    requestAnimationFrame(() => {
        setTimeout(() => {
            container.querySelectorAll('.freq-fill').forEach((el, i) => {
                el.style.width = `${(freqData[i].count / maxCount * 100).toFixed(1)}%`;
            });
        }, 100);
    });
}

// ── 情感分页加载 ──
async function loadSentimentPage() {
    try {
        const res = await fetch(`${API_BASE}/api/sentiment-page`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                label: sentimentState.label,
                sort_by: sentimentState.sortBy,
                sort_order: sentimentState.sortOrder,
                page: sentimentState.page,
                page_size: sentimentState.pageSize,
            }),
        });

        const data = await res.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        sentimentState.total = data.total;
        sentimentState.totalPages = data.total_pages;

        $('#filter-count').textContent = `共 ${data.total} 条`;

        renderSentimentTable(data.details);
        renderPagination(data);

    } catch (err) {
        console.error('加载情感数据失败:', err);
    }
}

// ── 情感表格 ──
function renderSentimentTable(details) {
    const tbody = $('#sentiment-tbody');

    tbody.innerHTML = details.map(d => {
        const cls = d.label === '正面' ? 'positive' : d.label === '负面' ? 'negative' : 'neutral';
        return `
            <tr>
                <td title="${escapeHtml(d.text)}">${escapeHtml(truncate(d.text, 120))}</td>
                <td>${d.score}</td>
                <td><span class="tag ${cls}">${d.label}</span></td>
            </tr>
        `;
    }).join('');
}

// ── 分页控件 ──
function renderPagination(data) {
    const container = $('#pagination');
    if (data.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }

    const { page, total_pages } = data;
    let html = '';

    html += `<button ${page <= 1 ? 'disabled' : ''} data-page="${page - 1}">上一页</button>`;

    // 显示页码（最多 7 个）
    let start = Math.max(1, page - 3);
    let end = Math.min(total_pages, start + 6);
    if (end - start < 6) start = Math.max(1, end - 6);

    if (start > 1) {
        html += `<button data-page="1">1</button>`;
        if (start > 2) html += `<span class="page-info">...</span>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    if (end < total_pages) {
        if (end < total_pages - 1) html += `<span class="page-info">...</span>`;
        html += `<button data-page="${total_pages}">${total_pages}</button>`;
    }

    html += `<button ${page >= total_pages ? 'disabled' : ''} data-page="${page + 1}">下一页</button>`;

    container.innerHTML = html;

    container.querySelectorAll('button[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            sentimentState.page = parseInt(btn.dataset.page);
            loadSentimentPage();
        });
    });
}

// ── 导出 Excel ──
async function exportExcel() {
    const btn = $('#export-excel-btn');
    btn.disabled = true;
    btn.textContent = '⏳ 导出中...';

    try {
        const res = await fetch(`${API_BASE}/api/export-excel`, { method: 'POST' });
        const data = await res.json();

        if (data.error) {
            alert('导出失败：' + data.error);
        } else {
            alert(`✅ 导出成功！\n已保存到桌面：${data.filename}`);
        }
    } catch (err) {
        alert('导出失败，请重试');
    } finally {
        btn.disabled = false;
        btn.textContent = '📥 导出 Excel';
    }
}

// ── 导出图片 ──
async function exportImage(type) {
    const btn = type === 'bar' ? $('#export-bar-btn') : $('#export-wc-btn');
    btn.disabled = true;
    btn.textContent = '⏳ 导出中...';

    try {
        const res = await fetch(`${API_BASE}/api/export-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type }),
        });
        const data = await res.json();

        if (data.error) {
            alert('导出失败：' + data.error);
        } else {
            alert(`✅ 导出成功！\n已保存到桌面：${data.filename}`);
        }
    } catch (err) {
        alert('导出失败，请重试');
    } finally {
        btn.disabled = false;
        btn.textContent = type === 'bar' ? '📊 导出条形图' : '☁️ 导出词云图';
    }
}

// ── 工具函数 ──
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
