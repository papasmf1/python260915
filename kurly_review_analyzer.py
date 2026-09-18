"""
마켓컬리 상품 리뷰 300개 크롤링, 감성 분석(Pandas) 및 PyQt6 GUI 대시보드
- 대상 URL: https://www.kurly.com/goods/1001353793?collectionCode=sale231107
- 기능:
  1. BeautifulSoup & Requests를 활용한 상품 정보 및 리뷰 데이터 수집
  2. Pandas 및 한국어 도메인 특화 감성 사전을 활용한 긍정/부정/중립 감성 분석
  3. Matplotlib FigureCanvas를 활용한 고품질 바(Bar) 차트 시각화
  4. PyQt6 기반의 직관적이고 미려한 좌우 분할(Splitter) GUI 대시보드
"""

import sys
import os
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# PyQt6 UI 모듈
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QGroupBox, QTabWidget, QFileDialog, QMessageBox,
    QFrame, QSizePolicy, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon

# Matplotlib PyQt6 연동 모듈
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Matplotlib 한글 폰트 설정 (Windows 기본 맑은 고딕 지원)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# ==============================================================================
# 1. 한국어 식품/이커머스 도메인 특화 감성 사전 및 분석 로직
# ==============================================================================

POSITIVE_KEYWORDS = [
    '맛있', '맛나', '좋아', '좋네', '좋았', '추천', '최고', '편해', '편하', '간편',
    '만족', '재구매', '신선', '깔끔', '알차', '푸짐', '감칠맛', '괜찮', '굿', '훌륭',
    '혜자', '대박', '바삭', '부드러', '짱', '든든', '고소', '담백', '촉촉', '쫄깃',
    '예쁘', '유용', '빠르', '친절', '감동', '넉넉', '재주문', '실속', '풍성', '착한'
]

NEGATIVE_KEYWORDS = [
    '아쉽', '실망', '비싸', '느끼', '짜다', '짜서', '짜네', '너무 짜', '싱겁', '밍밍',
    '부실', '딱딱', '냄새', '비추', '불만', '부족', '작아', '작네', '양 적', '양이 적',
    '양은 적', '기름지', '기름져', '기름 많', '질기', '불편', '최악', '후회', '상했',
    '맛없', '맛 없', '안 좋', '안좋', '퍽퍽', '눅눅', '잡내', '비린', '비려',
    '탈락', '돈아깝', '돈 아깝', '터져', '깨져', '덜익', '덜 익'
]

NEGATION_PATTERNS = [
    r'안\s+', r'못\s+', r'전혀\s+안', r'별로\s+안', r'그닥\s+안', r'그다지\s+안'
]
NEGATION_SUFFIXES = [
    r'지\s*않', r'는\s*아님', r'진\s*않', r'지는\s*않', r'지\s*못'
]

EXCLUDE_WORDS = {
    '별로': ['종류별로', '개인별로', '월별로', '항목별로', '크기별로', '등급별로', '부위별로', '선택별로']
}

def analyze_review_sentiment(text):
    """단일 리뷰 텍스트에 대한 감성 분석 (긍정, 부정, 중립)"""
    if not isinstance(text, str) or not text.strip():
        return {
            'sentiment': '중립',
            'score': 0,
            'pos_count': 0,
            'neg_count': 0,
            'pos_words': '',
            'neg_words': ''
        }

    clean_text = text.strip()
    pos_detected = []
    neg_detected = []

    # 부정 키워드 탐색
    for nw in NEGATIVE_KEYWORDS:
        if nw in clean_text:
            if nw == '별로':
                is_excl = any(excl in clean_text for excl in EXCLUDE_WORDS['별로'])
                if not is_excl or clean_text.count('별로') > sum(clean_text.count(excl) for excl in EXCLUDE_WORDS['별로']):
                    neg_detected.append('별로')
            else:
                neg_detected.append(nw)

    if '별로' not in neg_detected and '별로' in clean_text:
        is_excl = any(excl in clean_text for excl in EXCLUDE_WORDS['별로'])
        if not is_excl or clean_text.count('별로') > sum(clean_text.count(excl) for excl in EXCLUDE_WORDS['별로']):
            neg_detected.append('별로')

    # 긍정 키워드 탐색 (부정 맥락 필터링 적용)
    for pw in POSITIVE_KEYWORDS:
        for m in re.finditer(re.escape(pw), clean_text):
            start = max(0, m.start() - 12)
            prefix = clean_text[start:m.start()]
            end = min(len(clean_text), m.end() + 12)
            suffix = clean_text[m.end():end]

            is_negated = False
            for pat in NEGATION_PATTERNS:
                if re.search(pat, prefix):
                    is_negated = True
                    break
            if not is_negated:
                for pat in NEGATION_SUFFIXES:
                    if re.search(pat, suffix):
                        is_negated = True
                        break

            if is_negated:
                neg_detected.append(f"{pw}(부정맥락)")
            else:
                pos_detected.append(pw)

    pos_unique = sorted(list(set(pos_detected)))
    neg_unique = sorted(list(set(neg_detected)))

    score = len(pos_unique) - len(neg_unique)
    if score > 0:
        sentiment = '긍정'
    elif score < 0:
        sentiment = '부정'
    else:
        sentiment = '중립'

    return {
        'sentiment': sentiment,
        'score': score,
        'pos_count': len(pos_unique),
        'neg_count': len(neg_unique),
        'pos_words': ", ".join(pos_unique),
        'neg_words': ", ".join(neg_unique)
    }


# ==============================================================================
# 2. 백그라운드 크롤링 & 분석 스레드 (QThread)
# ==============================================================================

class ReviewCrawlerWorker(QThread):
    progress = pyqtSignal(int, str)      # 진행률 (0~100), 상태 메시지
    finished = pyqtSignal(object, str)   # (pd.DataFrame, 상품명)
    error = pyqtSignal(str)              # 에러 메시지

    def __init__(self, url, target_count=300):
        super().__init__()
        self.url = url
        self.target_count = target_count

    def run(self):
        try:
            self.progress.emit(5, "상품 페이지 접속 및 메타데이터 파싱 중...")
            match = re.search(r'/goods/(\d+)', self.url)
            if not match:
                raise ValueError("입력된 URL에서 올바른 상품 번호(ID)를 찾을 수 없습니다.")
            product_id = match.group(1)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.url,
                'Origin': 'https://www.kurly.com',
                'Accept': 'application/json, text/plain, */*'
            }

            # 1. BeautifulSoup을 사용한 상품 페이지 기본 정보 스크래핑
            product_title = "마켓컬리 상품"
            try:
                page_res = requests.get(self.url, headers={'User-Agent': headers['User-Agent']}, timeout=10)
                if page_res.status_code == 200:
                    soup = BeautifulSoup(page_res.text, 'html.parser')
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        product_title = og_title['content'].strip()
                    elif soup.title and soup.title.string:
                        product_title = soup.title.string.strip()
            except Exception as e:
                print(f"BeautifulSoup 안내: {e}")

            self.progress.emit(15, f"상품 확인 완료: {product_title[:25]}... 리뷰 수집 시작")

            # 2. 컬리 페이지네이션 API를 통한 리뷰 실시간 크롤링 (300개 목표)
            reviews_raw = []
            cursor = None
            batch_size = 50

            while len(reviews_raw) < self.target_count:
                params = {
                    'sortType': 'RECENTLY',
                    'size': batch_size,
                    'onlyImage': 'false'
                }
                if cursor and isinstance(cursor, dict):
                    params.update(cursor)
                elif cursor:
                    params['after'] = cursor

                api_url = f'https://api.kurly.com/product-review/v4/contents-products/{product_id}/reviews'
                res = requests.get(api_url, headers=headers, params=params, timeout=10)
                if res.status_code != 200:
                    break

                data = res.json().get('data', {})
                items = data.get('reviews', [])
                if not items:
                    break

                for item in items:
                    reviews_raw.append({
                        'review_no': item.get('no'),
                        'author': item.get('ownerName', '익명'),
                        'date': item.get('registeredAt', '')[:10],
                        'contents': item.get('contents', '').strip(),
                        'like_count': item.get('likeCount', 0),
                        'product_name': item.get('dealProductName', product_title)
                    })
                    if len(reviews_raw) >= self.target_count:
                        break

                current_len = len(reviews_raw)
                pct = int(15 + (current_len / self.target_count) * 65)
                self.progress.emit(pct, f"리뷰 데이터 수집 중... ({current_len}/{self.target_count}건)")

                cursor = data.get('nextCursor')
                if not cursor:
                    break

            if not reviews_raw:
                raise ValueError("리뷰 데이터를 수집하지 못했습니다. 네트워크 상태나 상품 번호를 확인해 주세요.")

            # 3. Pandas를 활용한 자연어 감성 분석
            self.progress.emit(85, f"Pandas 기반 감성 분석 및 통계 집계 중... (총 {len(reviews_raw)}건)")
            df = pd.DataFrame(reviews_raw)
            analysis_results = df['contents'].apply(analyze_review_sentiment)
            analysis_df = pd.DataFrame(list(analysis_results))
            df = pd.concat([df, analysis_df], axis=1)

            # 데이터 정렬
            cols = ['review_no', 'sentiment', 'score', 'author', 'date', 'contents', 'pos_words', 'neg_words', 'pos_count', 'neg_count', 'like_count', 'product_name']
            df = df[[c for c in cols if c in df.columns]]

            # 로컬 CSV 캐시 백업
            try:
                df.to_csv('kurly_reviews_300.csv', index=False, encoding='utf-8-sig')
            except Exception:
                pass

            self.progress.emit(100, f"수집 및 감성 분석 완료! (총 {len(df)}건)")
            self.finished.emit(df, product_title)

        except Exception as e:
            self.error.emit(str(e))


# ==============================================================================
# 3. PyQt6 메인 윈도우 UI 클래스
# ==============================================================================

class KurlySentimentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("마켓컬리 상품 리뷰 감성 분석기 (Market Kurly Review Sentiment Analyzer)")
        self.resize(1420, 880)
        self.setMinimumSize(1100, 720)

        self.df = None
        self.product_title = "부침명장 명품 모둠전"
        self.worker = None

        self.init_ui()
        self.apply_styles()

        # 기존에 저장된 데이터가 있으면 자동 로드하여 즉시 UI 구성
        default_csv = 'kurly_reviews_300.csv'
        if os.path.exists(default_csv):
            self.load_csv_data(default_csv)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 상단 Header & 제어 패널 (URL 입력, 개수 선택, 버튼들)
        # -------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)

        # 제목 및 브랜드 뱃지
        title_row = QHBoxLayout()
        logo_label = QLabel("🛒 마켓컬리 상품 리뷰 감성 분석 대시보드")
        logo_label.setObjectName("mainTitleLabel")
        
        self.subtitle_label = QLabel("BeautifulSoup 웹 스크래핑 · Pandas 자연어 감성 분석 · PyQt6 시각화")
        self.subtitle_label.setObjectName("subTitleLabel")

        title_row.addWidget(logo_label)
        title_row.addStretch()
        title_row.addWidget(self.subtitle_label)
        header_layout.addLayout(title_row)

        # 제어 컨트롤 행 (URL 입력, 수집 개수, 시작 버튼, 저장 버튼)
        control_row = QHBoxLayout()
        control_row.setSpacing(10)

        url_label = QLabel("상품 URL:")
        url_label.setStyleSheet("font-weight: bold; color: #334155;")
        self.url_input = QLineEdit("https://www.kurly.com/goods/1001353793?collectionCode=sale231107")
        self.url_input.setPlaceholderText("컬리 상품 페이지 URL을 입력하세요...")

        count_label = QLabel("수집 개수:")
        count_label.setStyleSheet("font-weight: bold; color: #334155;")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(10, 1000)
        self.count_spin.setValue(300)
        self.count_spin.setSuffix(" 건")

        self.btn_crawl = QPushButton("▶ 크롤링 & 분석 시작")
        self.btn_crawl.setObjectName("btnCrawl")
        self.btn_crawl.clicked.connect(self.start_crawling)

        self.btn_load_cache = QPushButton("⚡ 샘플 데이터 로드")
        self.btn_load_cache.setObjectName("btnLoadCache")
        self.btn_load_cache.clicked.connect(lambda: self.load_csv_data('kurly_reviews_300.csv'))

        self.btn_export = QPushButton("💾 CSV 내보내기")
        self.btn_export.setObjectName("btnExport")
        self.btn_export.clicked.connect(self.export_csv)

        control_row.addWidget(url_label)
        control_row.addWidget(self.url_input, stretch=4)
        control_row.addWidget(count_label)
        control_row.addWidget(self.count_spin, stretch=1)
        control_row.addWidget(self.btn_crawl, stretch=2)
        control_row.addWidget(self.btn_load_cache)
        control_row.addWidget(self.btn_export)

        header_layout.addLayout(control_row)

        # 진행 바 및 상태 메시지
        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(16)

        self.status_label = QLabel("준비 완료. [크롤링 & 분석 시작] 버튼을 누르면 컬리 리뷰를 수집합니다.")
        self.status_label.setStyleSheet("color: #64748B; font-size: 9pt;")

        progress_row.addWidget(self.progress_bar, stretch=2)
        progress_row.addWidget(self.status_label, stretch=3)
        header_layout.addLayout(progress_row)

        main_layout.addWidget(header_frame)

        # -------------------------------------------------------------
        # 본문: QSplitter를 활용한 좌(댓글 목록) / 우(바차트 및 요약) 분할
        # -------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # ================= [좌측 패널: 댓글 리스트 및 상세] =================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 좌측 상단: 필터 및 검색 컨트롤
        left_top_box = QFrame()
        left_top_box.setObjectName("panelCard")
        left_top_layout = QVBoxLayout(left_top_box)
        left_top_layout.setContentsMargins(10, 8, 10, 8)
        left_top_layout.setSpacing(6)

        filter_row = QHBoxLayout()
        filter_label = QLabel("감성 필터:")
        filter_label.setStyleSheet("font-weight: bold; color: #475569;")
        filter_row.addWidget(filter_label)

        self.filter_group = QButtonGroup(self)
        self.rb_all = QRadioButton("전체 (0)")
        self.rb_pos = QRadioButton("긍정 (0)")
        self.rb_neg = QRadioButton("부정 (0)")
        self.rb_neu = QRadioButton("중립 (0)")
        self.rb_all.setChecked(True)

        for i, rb in enumerate([self.rb_all, self.rb_pos, self.rb_neg, self.rb_neu]):
            self.filter_group.addButton(rb, i)
            filter_row.addWidget(rb)
            rb.toggled.connect(self.apply_filter)

        filter_row.addStretch()
        left_top_layout.addLayout(filter_row)

        search_row = QHBoxLayout()
        search_icon = QLabel("🔍")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("댓글 내용 또는 작성자 검색...")
        self.search_input.textChanged.connect(self.apply_filter)
        search_row.addWidget(search_icon)
        search_row.addWidget(self.search_input)
        left_top_layout.addLayout(search_row)

        left_layout.addWidget(left_top_box)

        # 좌측 중단: 댓글 QTableWidget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["No", "감성", "점수", "작성자", "작성일", "댓글 내용"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 테이블 헤더 너비 설정
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.table.itemSelectionChanged.connect(self.on_row_selected)
        left_layout.addWidget(self.table, stretch=5)

        # 좌측 하단: 선택된 댓글 상세 보기
        detail_group = QGroupBox("💬 선택된 댓글 상세 정보 및 감성 태그")
        detail_group.setObjectName("detailGroup")
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(6)

        self.detail_meta_label = QLabel("리뷰를 선택하면 상세 메타데이터와 분석 근거가 표시됩니다.")
        self.detail_meta_label.setStyleSheet("font-weight: bold; color: #1E293B;")
        detail_layout.addWidget(self.detail_meta_label)

        self.detail_tags_label = QLabel("감지된 긍정/부정 키워드가 여기에 표시됩니다.")
        self.detail_tags_label.setWordWrap(True)
        self.detail_tags_label.setStyleSheet("color: #475569; font-size: 9pt;")
        detail_layout.addWidget(self.detail_tags_label)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("선택된 댓글 본문이 여기에 표시됩니다...")
        self.detail_text.setFixedHeight(85)
        detail_layout.addWidget(self.detail_text)

        left_layout.addWidget(detail_group, stretch=2)
        splitter.addWidget(left_widget)

        # ================= [우측 패널: 바차트 및 시각화 대시보드] =================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 우측 상단: 4개 KPI 요약 카드 (총수, 긍정, 부정, 중립)
        kpi_frame = QFrame()
        kpi_frame.setObjectName("kpiFrame")
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(8, 8, 8, 8)
        kpi_layout.setSpacing(8)

        self.card_total = self.create_kpi_card("총 수집 리뷰", "0건", "100%", "#475569", "#F1F5F9")
        self.card_pos = self.create_kpi_card("긍정 의견", "0건", "0.0%", "#059669", "#ECFDF5")
        self.card_neg = self.create_kpi_card("부정 의견", "0건", "0.0%", "#DC2626", "#FEF2F2")
        self.card_neu = self.create_kpi_card("중립 의견", "0건", "0.0%", "#64748B", "#F8FAFC")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_pos)
        kpi_layout.addWidget(self.card_neg)
        kpi_layout.addWidget(self.card_neu)
        right_layout.addWidget(kpi_frame)

        # 우측 중단: Matplotlib FigureCanvas (바차트 시각화)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("chartTabWidget")

        # 탭 1: 종합 바(Bar) 차트 (감성 분포 + 주요 키워드 TOP 5)
        self.fig_bar = Figure(figsize=(7.5, 6), facecolor='#ffffff')
        self.canvas_bar = FigureCanvas(self.fig_bar)
        self.tab_widget.addTab(self.canvas_bar, "📊 감성 분포 및 키워드 바차트")

        # 탭 2: 감성 비율 파이 & 점수 분포 차트
        self.fig_pie = Figure(figsize=(7.5, 6), facecolor='#ffffff')
        self.canvas_pie = FigureCanvas(self.fig_pie)
        self.tab_widget.addTab(self.canvas_pie, "🍩 감성 비율 & 점수 분포")

        right_layout.addWidget(self.tab_widget, stretch=5)

        # 우측 하단: 데이터 분석 종합 리포트 카드
        insight_group = QGroupBox("💡 데이터 분석 인사이트 리포트")
        insight_group.setObjectName("insightGroup")
        insight_layout = QVBoxLayout(insight_group)
        insight_layout.setContentsMargins(10, 8, 10, 8)

        self.insight_label = QLabel("데이터를 수집하면 종합 분석 요약 리포트가 생성됩니다.")
        self.insight_label.setWordWrap(True)
        self.insight_label.setStyleSheet("color: #334155; font-size: 9.5pt; line-height: 1.4;")
        insight_layout.addWidget(self.insight_label)

        right_layout.addWidget(insight_group, stretch=1)
        splitter.addWidget(right_widget)

        # Splitter 비율 설정 (좌 52% : 우 48%)
        splitter.setSizes([720, 660])
        main_layout.addWidget(splitter)

    def create_kpi_card(self, title, count_text, pct_text, text_color, bg_color):
        """KPI 메트릭 요약 카드 위젯 생성"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 6px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 9pt; color: #64748B; font-weight: bold;")
        
        c_lbl = QLabel(count_text)
        c_lbl.setObjectName("countLabel")
        c_lbl.setStyleSheet(f"font-size: 15pt; font-weight: bold; color: {text_color};")
        
        p_lbl = QLabel(pct_text)
        p_lbl.setObjectName("pctLabel")
        p_lbl.setStyleSheet("font-size: 9pt; color: #475569;")

        layout.addWidget(t_lbl)
        layout.addWidget(c_lbl)
        layout.addWidget(p_lbl)
        return frame

    # --------------------------------------------------------------------------
    # 크롤링 및 데이터 로딩 처리
    # --------------------------------------------------------------------------
    def start_crawling(self):
        url = self.url_input.text().strip()
        count = self.count_spin.value()

        if not url:
            QMessageBox.warning(self, "경고", "마켓컬리 상품 URL을 입력해 주세요.")
            return

        self.btn_crawl.setEnabled(False)
        self.btn_load_cache.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("크롤링 작업 시작 중...")

        self.worker = ReviewCrawlerWorker(url, count)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def on_worker_finished(self, df, product_title):
        self.btn_crawl.setEnabled(True)
        self.btn_load_cache.setEnabled(True)
        self.df = df
        self.product_title = product_title
        self.subtitle_label.setText(f"상품명: {product_title}")
        self.status_label.setText(f"수집 완료: 총 {len(df)}개 리뷰 분석 완료")
        self.update_dashboard()

    def on_worker_error(self, err_msg):
        self.btn_crawl.setEnabled(True)
        self.btn_load_cache.setEnabled(True)
        self.status_label.setText(f"오류 발생: {err_msg}")
        
        # 캐시 데이터가 있는지 확인
        if os.path.exists('kurly_reviews_300.csv'):
            reply = QMessageBox.question(
                self, "크롤링 안내",
                f"온라인 수집 중 오류가 발생했습니다:\n{err_msg}\n\n로컬에 저장된 300개 리뷰 캐시 데이터를 대신 로드할까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.load_csv_data('kurly_reviews_300.csv')
        else:
            QMessageBox.critical(self, "오류", f"리뷰 수집 중 오류가 발생했습니다:\n{err_msg}")

    def load_csv_data(self, filepath):
        try:
            if not os.path.exists(filepath):
                QMessageBox.warning(self, "파일 없음", f"데이터 파일을 찾을 수 없습니다: {filepath}")
                return
            df = pd.read_csv(filepath)
            # 만약 감성 분석 컬럼이 없으면 즉시 분석 적용
            if 'sentiment' not in df.columns and 'contents' in df.columns:
                results = df['contents'].apply(analyze_review_sentiment)
                analysis_df = pd.DataFrame(list(results))
                df = pd.concat([df, analysis_df], axis=1)

            self.df = df
            if 'product_name' in df.columns and len(df) > 0 and pd.notna(df['product_name'].iloc[0]):
                self.product_title = str(df['product_name'].iloc[0])
            self.subtitle_label.setText(f"상품명: {self.product_title}")
            self.progress_bar.setValue(100)
            self.status_label.setText(f"로컬 데이터 로드 완료: 총 {len(df)}건")
            self.update_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "로드 실패", f"데이터 로딩 중 오류:\n{e}")

    # --------------------------------------------------------------------------
    # 대시보드 및 시각화 갱신
    # --------------------------------------------------------------------------
    def update_dashboard(self):
        if self.df is None or len(self.df) == 0:
            return

        total_cnt = len(self.df)
        counts = self.df['sentiment'].value_counts()
        pos_cnt = counts.get('긍정', 0)
        neg_cnt = counts.get('부정', 0)
        neu_cnt = counts.get('중립', 0)

        pos_pct = (pos_cnt / total_cnt * 100) if total_cnt > 0 else 0
        neg_pct = (neg_cnt / total_cnt * 100) if total_cnt > 0 else 0
        neu_pct = (neu_cnt / total_cnt * 100) if total_cnt > 0 else 0

        # KPI 카드 텍스트 갱신
        self.card_total.findChild(QLabel, "countLabel").setText(f"{total_cnt:,}건")
        self.card_pos.findChild(QLabel, "countLabel").setText(f"{pos_cnt:,}건")
        self.card_pos.findChild(QLabel, "pctLabel").setText(f"비율: {pos_pct:.1f}%")
        self.card_neg.findChild(QLabel, "countLabel").setText(f"{neg_cnt:,}건")
        self.card_neg.findChild(QLabel, "pctLabel").setText(f"비율: {neg_pct:.1f}%")
        self.card_neu.findChild(QLabel, "countLabel").setText(f"{neu_cnt:,}건")
        self.card_neu.findChild(QLabel, "pctLabel").setText(f"비율: {neu_pct:.1f}%")

        # 라디오 버튼 레이블 갱신
        self.rb_all.setText(f"전체 ({total_cnt})")
        self.rb_pos.setText(f"긍정 ({pos_cnt})")
        self.rb_neg.setText(f"부정 ({neg_cnt})")
        self.rb_neu.setText(f"중립 ({neu_cnt})")

        # 좌측 테이블 필터링 및 렌더링
        self.apply_filter()

        # 우측 바차트 렌더링
        self.draw_bar_charts()
        self.draw_pie_charts()

        # 하단 인사이트 리포트 생성
        pos_words = [w.strip() for words in self.df['pos_words'].dropna() for w in words.split(',') if w.strip()]
        neg_words = [w.strip() for words in self.df['neg_words'].dropna() for w in words.split(',') if w.strip()]
        top_pos = pd.Series(pos_words).value_counts().head(3)
        top_neg = pd.Series(neg_words).value_counts().head(3)

        pos_summary = ", ".join([f"'{k}'({v}회)" for k, v in top_pos.items()]) if not top_pos.empty else "없음"
        neg_summary = ", ".join([f"'{k}'({v}회)" for k, v in top_neg.items()]) if not top_neg.empty else "없음"

        insight_text = (
            f"📌 <b>분석 요약</b>: 전체 <b>{total_cnt}개</b>의 리뷰 중 긍정 의견이 <b>{pos_pct:.1f}%({pos_cnt}건)</b>로 "
            f"압도적인 만족도를 나타내고 있습니다.<br>"
            f"• <b>주요 호평 요인</b>: {pos_summary} 등 전반적인 맛과 간편성에 대한 만족도가 높습니다.<br>"
            f"• <b>주요 개선 의견</b>: 부정 비율은 <b>{neg_pct:.1f}%({neg_cnt}건)</b>로 낮으나 {neg_summary} 등의 피드백이 일부 확인되었습니다."
        )
        self.insight_label.setText(insight_text)

    def apply_filter(self):
        """감성 라디오 버튼 및 검색어에 따른 테이블 필터링"""
        if self.df is None:
            return

        filtered = self.df.copy()

        # 감성 라디오 버튼 필터
        if self.rb_pos.isChecked():
            filtered = filtered[filtered['sentiment'] == '긍정']
        elif self.rb_neg.isChecked():
            filtered = filtered[filtered['sentiment'] == '부정']
        elif self.rb_neu.isChecked():
            filtered = filtered[filtered['sentiment'] == '중립']

        # 검색어 필터
        query = self.search_input.text().strip().lower()
        if query:
            filtered = filtered[
                filtered['contents'].astype(str).str.lower().str.contains(query) |
                filtered['author'].astype(str).str.lower().str.contains(query)
            ]

        self.render_table(filtered)

    def render_table(self, df_subset):
        """테이블 위젯에 필터링된 데이터 채우기"""
        self.table.setRowCount(len(df_subset))
        self.filtered_df = df_subset.reset_index(drop=True)

        for row_idx, row in self.filtered_df.iterrows():
            # 0. 번호
            item_no = QTableWidgetItem(str(row_idx + 1))
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, item_no)

            # 1. 감성 뱃지
            sentiment = str(row.get('sentiment', '중립'))
            item_sent = QTableWidgetItem(sentiment)
            item_sent.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if sentiment == '긍정':
                item_sent.setBackground(QColor('#DCFCE7')) # 연초록
                item_sent.setForeground(QColor('#15803D')) # 진초록
            elif sentiment == '부정':
                item_sent.setBackground(QColor('#FEE2E2')) # 연빨강
                item_sent.setForeground(QColor('#B91C1C')) # 진빨강
            else:
                item_sent.setBackground(QColor('#F1F5F9')) # 연회색
                item_sent.setForeground(QColor('#475569'))
            self.table.setItem(row_idx, 1, item_sent)

            # 2. 감성 점수
            score = int(row.get('score', 0))
            score_str = f"+{score}" if score > 0 else str(score)
            item_score = QTableWidgetItem(score_str)
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, item_score)

            # 3. 작성자
            item_author = QTableWidgetItem(str(row.get('author', '익명')))
            item_author.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, item_author)

            # 4. 작성일
            item_date = QTableWidgetItem(str(row.get('date', '')))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, item_date)

            # 5. 댓글 내용 (1줄 미리보기)
            raw_text = str(row.get('contents', '')).replace('\n', ' ')
            item_text = QTableWidgetItem(raw_text)
            self.table.setItem(row_idx, 5, item_text)

        # 첫 번째 행 기본 선택
        if len(self.filtered_df) > 0:
            self.table.selectRow(0)

    def on_row_selected(self):
        """테이블에서 특정 행 클릭 시 하단 상세 뷰 갱신"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows or not hasattr(self, 'filtered_df'):
            return

        row_idx = selected_rows[0].row()
        if row_idx >= len(self.filtered_df):
            return

        row = self.filtered_df.iloc[row_idx]
        sentiment = row.get('sentiment', '중립')
        score = row.get('score', 0)
        author = row.get('author', '익명')
        date = row.get('date', '')
        pos_words = row.get('pos_words', '')
        neg_words = row.get('neg_words', '')
        contents = str(row.get('contents', ''))

        score_sign = f"+{score}" if score > 0 else str(score)
        self.detail_meta_label.setText(
            f"작성자: {author}  |  작성일: {date}  |  감성: {sentiment} (점수: {score_sign})"
        )

        tags_html = ""
        if pd.notna(pos_words) and str(pos_words).strip():
            tags_html += f"<span style='color: #059669; font-weight: bold;'>[긍정 감지]</span> {pos_words}&nbsp;&nbsp;&nbsp;&nbsp;"
        if pd.notna(neg_words) and str(neg_words).strip():
            tags_html += f"<span style='color: #DC2626; font-weight: bold;'>[부정 감지]</span> {neg_words}"
        if not tags_html:
            tags_html = "<span style='color: #64748B;'>특이 감성 키워드 없음 (중립적 리뷰)</span>"

        self.detail_tags_label.setText(tags_html)
        self.detail_text.setPlainText(contents)

    # --------------------------------------------------------------------------
    # Matplotlib 바(Bar) 차트 렌더링
    # --------------------------------------------------------------------------
    def draw_bar_charts(self):
        """상단 감성 분포 바차트 + 하단 긍정/부정 TOP 키워드 가로 바차트 렌더링"""
        self.fig_bar.clear()

        gs = self.fig_bar.add_gridspec(2, 2, height_ratios=[1.1, 1.1], hspace=0.42, wspace=0.32)

        # 1. 감성 분포 세로 바 차트 (상단 전체 너비)
        ax1 = self.fig_bar.add_subplot(gs[0, :])
        counts = self.df['sentiment'].value_counts()
        categories = ['긍정', '중립', '부정']
        values = [counts.get(cat, 0) for cat in categories]
        colors = ['#10B981', '#94A3B8', '#EF4444'] # Green, Slate, Red
        total = sum(values)

        bars = ax1.bar(categories, values, color=colors, width=0.45, zorder=3)
        ax1.set_title(f'고객 리뷰 감성 분포 현황 (총 {total}건)', fontsize=12, fontweight='bold', pad=10, color='#1E293B')
        ax1.set_ylabel('리뷰 수 (건)', fontsize=9, color='#475569')
        ax1.set_ylim(0, max(values) * 1.25 if values and max(values) > 0 else 10)
        ax1.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        ax1.set_axisbelow(True)

        for bar, val in zip(bars, values):
            pct = (val / total * 100) if total > 0 else 0
            height = bar.get_height()
            ax1.annotate(f'{val}건\n({pct:.1f}%)',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 4), textcoords="offset points",
                         ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#1E293B')

        for spine in ['top', 'right', 'left']:
            ax1.spines[spine].set_visible(False)
        ax1.spines['bottom'].set_color('#CBD5E1')

        # 키워드 데이터 추출
        pos_words = [w.strip() for words in self.df['pos_words'].dropna() for w in words.split(',') if w.strip()]
        neg_words = [w.strip() for words in self.df['neg_words'].dropna() for w in words.split(',') if w.strip()]

        top_pos = pd.Series(pos_words).value_counts().head(5) if pos_words else pd.Series(dtype=int)
        top_neg = pd.Series(neg_words).value_counts().head(5) if neg_words else pd.Series(dtype=int)

        # 2. 긍정 주요 키워드 가로 바 차트 (하단 좌측)
        ax2 = self.fig_bar.add_subplot(gs[1, 0])
        if not top_pos.empty:
            y_pos = np.arange(len(top_pos))
            bars_pos = ax2.barh(y_pos, top_pos.values[::-1], color='#10B981', height=0.55, zorder=3)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(top_pos.index[::-1], fontsize=9.5, fontweight='bold', color='#1E293B')
            ax2.set_title('긍정 주요 키워드 TOP 5', fontsize=10.5, fontweight='bold', pad=8, color='#065F46')
            ax2.set_xlabel('언급 빈도 (회)', fontsize=8.5, color='#475569')
            ax2.grid(axis='x', linestyle='--', alpha=0.5, zorder=0)
            ax2.set_axisbelow(True)
            for bar in bars_pos:
                w = bar.get_width()
                ax2.annotate(f'{int(w)}회',
                             xy=(w, bar.get_y() + bar.get_height() / 2),
                             xytext=(4, 0), textcoords="offset points",
                             ha='left', va='center', fontsize=9, fontweight='bold', color='#1E293B')
        else:
            ax2.text(0.5, 0.5, "긍정 키워드 데이터 없음", ha='center', va='center', color='#94A3B8')

        for s in ['top', 'right', 'left']:
            ax2.spines[s].set_visible(False)
        ax2.spines['bottom'].set_color('#CBD5E1')

        # 3. 부정 주요 키워드 가로 바 차트 (하단 우측)
        ax3 = self.fig_bar.add_subplot(gs[1, 1])
        if not top_neg.empty:
            y_neg = np.arange(len(top_neg))
            bars_neg = ax3.barh(y_neg, top_neg.values[::-1], color='#EF4444', height=0.55, zorder=3)
            ax3.set_yticks(y_neg)
            ax3.set_yticklabels(top_neg.index[::-1], fontsize=9.5, fontweight='bold', color='#1E293B')
            ax3.set_title('부정 주요 키워드 TOP 5', fontsize=10.5, fontweight='bold', pad=8, color='#991B1B')
            ax3.set_xlabel('언급 빈도 (회)', fontsize=8.5, color='#475569')
            ax3.grid(axis='x', linestyle='--', alpha=0.5, zorder=0)
            ax3.set_axisbelow(True)
            for bar in bars_neg:
                w = bar.get_width()
                ax3.annotate(f'{int(w)}회',
                             xy=(w, bar.get_y() + bar.get_height() / 2),
                             xytext=(4, 0), textcoords="offset points",
                             ha='left', va='center', fontsize=9, fontweight='bold', color='#1E293B')
        else:
            ax3.text(0.5, 0.5, "부정 키워드 데이터 없음", ha='center', va='center', color='#94A3B8')

        for s in ['top', 'right', 'left']:
            ax3.spines[s].set_visible(False)
        ax3.spines['bottom'].set_color('#CBD5E1')

        self.canvas_bar.draw()

    def draw_pie_charts(self):
        """보너스 탭: 도넛형 감성 비율 차트 및 점수 분포 히스토그램"""
        self.fig_pie.clear()
        gs = self.fig_pie.add_gridspec(1, 2, wspace=0.3)

        # 1. 도넛 차트
        ax1 = self.fig_pie.add_subplot(gs[0, 0])
        counts = self.df['sentiment'].value_counts()
        categories = ['긍정', '중립', '부정']
        values = [counts.get(cat, 0) for cat in categories]
        colors = ['#10B981', '#94A3B8', '#EF4444']

        wedges, texts, autotexts = ax1.pie(
            values, labels=categories, autopct='%1.1f%%',
            startangle=140, colors=colors,
            pctdistance=0.75, textprops=dict(color="#1E293B", fontweight="bold")
        )
        # 도넛 구멍 만들기
        centre_circle = plt.Circle((0, 0), 0.55, fc='white')
        ax1.add_artist(centre_circle)
        ax1.set_title('감성 점유율 (Donut Chart)', fontsize=11, fontweight='bold', pad=10)

        # 2. 감성 점수 분포 히스토그램
        ax2 = self.fig_pie.add_subplot(gs[0, 1])
        scores = self.df['score'].dropna()
        score_counts = scores.value_counts().sort_index()
        
        bar_colors = ['#EF4444' if x < 0 else ('#10B981' if x > 0 else '#94A3B8') for x in score_counts.index]
        bars = ax2.bar(score_counts.index, score_counts.values, color=bar_colors, width=0.6, zorder=3)
        ax2.set_title('리뷰 감성 점수 분포', fontsize=11, fontweight='bold', pad=10)
        ax2.set_xlabel('감성 점수 (음수: 부정 / 양수: 긍정)', fontsize=9, color='#475569')
        ax2.set_ylabel('리뷰 수 (건)', fontsize=9, color='#475569')
        ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        ax2.set_axisbelow(True)

        for bar in bars:
            h = bar.get_height()
            ax2.annotate(f'{int(h)}',
                         xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 3), textcoords="offset points",
                         ha='center', va='bottom', fontsize=8.5, fontweight='bold')

        for spine in ['top', 'right', 'left']:
            ax2.spines[spine].set_visible(False)

        self.canvas_pie.draw()

    # --------------------------------------------------------------------------
    # CSV / Excel 내보내기
    # --------------------------------------------------------------------------
    def export_csv(self):
        if self.df is None or len(self.df) == 0:
            QMessageBox.warning(self, "저장 불가", "저장할 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "감성 분석 결과 CSV 저장", "kurly_review_sentiment_result.csv", "CSV Files (*.csv)"
        )
        if file_path:
            try:
                self.df.to_csv(file_path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "저장 완료", f"성공적으로 저장되었습니다:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류:\n{e}")

    # --------------------------------------------------------------------------
    # 전체 QSS 스타일시트 디자인
    # --------------------------------------------------------------------------
    def apply_styles(self):
        qss = """
            QMainWindow {
                background-color: #F8FAFC;
            }
            #headerFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
            #mainTitleLabel {
                font-size: 15pt;
                font-weight: bold;
                color: #5f0080; /* 컬리 시그니처 보라색 */
            }
            #subTitleLabel {
                font-size: 9.5pt;
                color: #64748B;
            }
            QLineEdit, QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9.5pt;
                color: #1E293B;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1.5px solid #5f0080;
            }
            #btnCrawl {
                background-color: #5f0080;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 10pt;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
            }
            #btnCrawl:hover {
                background-color: #7b1fa2;
            }
            #btnCrawl:disabled {
                background-color: #CBD5E1;
                color: #94A3B8;
            }
            #btnLoadCache {
                background-color: #F1F5F9;
                color: #334155;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 7px 12px;
            }
            #btnLoadCache:hover {
                background-color: #E2E8F0;
            }
            #btnExport {
                background-color: #F1F5F9;
                color: #334155;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 7px 12px;
            }
            #btnExport:hover {
                background-color: #E2E8F0;
            }
            QProgressBar {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                background-color: #F1F5F9;
                text-align: center;
                font-size: 8.5pt;
                color: #334155;
            }
            QProgressBar::chunk {
                background-color: #5f0080;
                border-radius: 3px;
            }
            #panelCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QRadioButton {
                font-size: 9.5pt;
                font-weight: bold;
                color: #334155;
                spacing: 4px;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #F1F5F9;
                font-size: 9.5pt;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                border: none;
                border-bottom: 1px solid #CBD5E1;
                padding: 6px;
                font-weight: bold;
                color: #475569;
            }
            #detailGroup, #insightGroup {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-weight: bold;
                color: #1E293B;
                margin-top: 8px;
            }
            #detailGroup::title, #insightGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 6px;
                font-size: 9.5pt;
                color: #1E293B;
                line-height: 1.4;
            }
            #chartTabWidget::pane {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                color: #64748B;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #5f0080;
                border-top: 2px solid #5f0080;
            }
        """
        self.setStyleSheet(qss)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KurlySentimentApp()
    window.show()
    sys.exit(app.exec())
