"""Kurly 상품 후기 300개 수집 및 간단한 감성 분석 GUI.

Kurly 후기는 자바스크립트로 렌더링되므로 Selenium으로 화면을 준비한 뒤,
렌더링된 page_source를 BeautifulSoup으로 파싱한다.
"""

import re
import sys
from collections import Counter

import pandas as pd
from bs4 import BeautifulSoup
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


PRODUCT_URL = "https://www.kurly.com/goods/1001353793?collectionCode=sale231107"
TARGET_COUNT = 300
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

POSITIVE_WORDS = (
    "좋아요", "맛있", "신선", "만족", "추천", "최고", "재구매", "훌륭", "괜찮",
    "편해", "좋았", "맛나", "깔끔", "빠르",
)
NEGATIVE_WORDS = (
    "별로", "맛없", "상했", "상하", "불만", "실망", "비싸", "늦", "나쁘",
    "아쉽", "아쉬", "불편", "적어요", "적다", "문제", "환불",
)


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def classify_review(review):
    positive_score = sum(review.count(word) for word in POSITIVE_WORDS)
    negative_score = sum(review.count(word) for word in NEGATIVE_WORDS)
    if positive_score > negative_score:
        return "긍정"
    if negative_score > positive_score:
        return "부정"
    return "중립"


def parse_reviews(page_source, limit=TARGET_COUNT):
    """렌더링된 Kurly HTML에서 후기처럼 보이는 텍스트를 추출한다."""
    soup = BeautifulSoup(page_source, "html.parser")
    selectors = [
        "[data-testid*='review']",
        "[data-testid*='Review']",
        "[class*='review']",
        "[class*='Review']",
        "[class*='comment']",
        "[class*='Comment']",
    ]
    candidates = []
    for selector in selectors:
        candidates.extend(soup.select(selector))

    reviews = []
    seen = set()
    for tag in candidates:
        text = normalize_text(tag.get_text(" ", strip=True))
        if not 10 <= len(text) <= 1000:
            continue
        if text in seen:
            continue
        if any(word in text for word in ("상품후기", "후기 작성", "로그인", "더보기")):
            continue
        seen.add(text)
        reviews.append(text)
        if len(reviews) >= limit:
            break
    return reviews


def collect_reviews(url=PRODUCT_URL, limit=TARGET_COUNT):
    """Chrome으로 동적 후기를 로드하고 BeautifulSoup으로 파싱한다."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as error:
        raise RuntimeError("selenium 패키지가 필요합니다. requirements.txt를 설치하세요.") from error

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,2200")
    options.add_argument("--lang=ko-KR")
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda current_driver: current_driver.execute_script("return document.readyState") == "complete"
        )

        # 후기 탭을 먼저 눌러야 후기 DOM이 생성되는 상품 페이지가 있다.
        for element in driver.find_elements(By.XPATH, "//*[contains(normalize-space(.), '상품후기')]"):
            if element.is_displayed():
                try:
                    driver.execute_script("arguments[0].click();", element)
                    break
                except Exception:
                    pass

        previous_height = 0
        for _ in range(20):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 3).until(
                lambda current_driver: current_driver.execute_script("return document.body.scrollHeight") >= previous_height
            )
            current_height = driver.execute_script("return document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height
            if len(parse_reviews(driver.page_source, limit)) >= limit:
                break
        reviews = parse_reviews(driver.page_source, limit)
    finally:
        driver.quit()

    if not reviews:
        raise RuntimeError(
            "후기를 찾지 못했습니다. Kurly의 DOM 구조가 변경되었거나 Chrome이 실행되지 않았습니다."
        )
    return reviews


class CrawlThread(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("Kurly 페이지를 열고 후기를 수집하는 중...")
            reviews = collect_reviews()
            self.progress.emit(f"{len(reviews)}개 후기 분석 중...")
            frame = pd.DataFrame({"댓글": reviews})
            frame["판정"] = frame["댓글"].map(classify_review)
            self.completed.emit(frame)
        except Exception as error:
            self.failed.emit(str(error))


class ChartCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        super().__init__(self.figure)

    def draw_frame(self, counts):
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        labels = ["긍정", "부정", "중립"]
        values = [counts.get(label, 0) for label in labels]
        bars = axes.bar(labels, values, color=["#1f9d8b", "#e76f51", "#8395a7"])
        axes.set_title("Kurly 상품 후기 감성 분석")
        axes.set_ylabel("댓글 수")
        axes.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values):
            axes.text(bar.get_x() + bar.get_width() / 2, value, str(value), ha="center", va="bottom")
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.frame = pd.DataFrame(columns=["댓글", "판정"])
        self.worker = None
        self.setWindowTitle("Kurly 상품 후기 감성 분석")
        self.resize(1200, 720)
        self.setStyleSheet(
            "QMainWindow { background: #f5f7f4; } QLabel { color: #20322e; font-size: 14px; }"
            " QPushButton { background: #1f9d8b; color: white; border: 0; padding: 9px 16px;"
            " border-radius: 5px; font-weight: bold; } QPushButton:hover { background: #16796d; }"
            " QListWidget { background: white; border: 1px solid #d7e2dd; font-size: 13px; }"
        )

        title = QLabel("Kurly 상품 후기 300개 감성 분석")
        self.status_label = QLabel("수집 버튼을 누르면 분석이 시작됩니다.")
        self.start_button = QPushButton("후기 수집 및 분석")
        self.save_button = QPushButton("CSV 저장")
        self.save_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_crawling)
        self.save_button.clicked.connect(self.save_csv)

        self.review_list = QListWidget()
        self.chart = ChartCanvas()
        splitter = QSplitter()
        splitter.addWidget(self.review_list)
        splitter.addWidget(self.chart)
        splitter.setSizes([560, 640])

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.save_button)
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)
        layout.addWidget(splitter)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_crawling(self):
        self.start_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.review_list.clear()
        self.status_label.setText("준비 중...")
        self.worker = CrawlThread()
        self.worker.progress.connect(self.status_label.setText)
        self.worker.completed.connect(self.show_result)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(lambda: self.start_button.setEnabled(True))
        self.worker.start()

    def show_result(self, frame):
        self.frame = frame
        for number, row in frame.iterrows():
            self.review_list.addItem(f"{number + 1:03d}. [{row['판정']}] {row['댓글']}")
        counts = Counter(frame["판정"])
        self.chart.draw_frame(counts)
        self.status_label.setText(f"총 {len(frame)}개 후기 분석 완료: {dict(counts)}")
        self.save_button.setEnabled(True)

    def show_error(self, message):
        self.status_label.setText("수집에 실패했습니다.")
        QMessageBox.critical(self, "크롤링 오류", message)

    def save_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, "CSV 저장", "kurly_reviews.csv", "CSV 파일 (*.csv)")
        if filename:
            self.frame.to_csv(filename, index=False, encoding="utf-8-sig")
            self.status_label.setText(f"CSV 저장 완료: {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())