"""
네이버 증권(stock.naver.com/market/stock/kr) 국내 증시 종목 크롤링

주의:
stock.naver.com 페이지는 리액트(Next.js) 기반으로 동작해서, 종목 표(테이블)는
requests로 받은 원본 HTML에는 들어있지 않고 브라우저가 자바스크립트로 내부 API를
호출한 뒤 채워 넣습니다. 그래서 BeautifulSoup으로 원본 HTML을 그대로 파싱하면
빈 결과만 나옵니다.

대신 페이지가 내부적으로 호출하는 JSON API(m.stock.naver.com)를 requests로 직접
호출해서 데이터를 얻고, 필요한 값만 뽑아서 CSV로 저장합니다.
"""

import csv
import time

import requests

API_URL = "https://m.stock.naver.com/api/stocks/marketValue/{market}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}
PAGE_SIZE = 20


def get_stock_list(market="KOSPI", max_pages=5):
    """market: KOSPI 또는 KOSDAQ. max_pages 만큼 페이지를 순회해서 종목 목록을 모은다."""
    stocks = []

    for page in range(1, max_pages + 1):
        params = {"page": page, "pageSize": PAGE_SIZE}
        response = requests.get(
            API_URL.format(market=market), params=params, headers=HEADERS, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        page_stocks = data.get("stocks", [])
        if not page_stocks:
            break

        for item in page_stocks:
            stocks.append(
                {
                    "시장": market,
                    "종목코드": item.get("itemCode"),
                    "종목명": item.get("stockName"),
                    "현재가": item.get("closePrice"),
                    "전일대비": item.get("compareToPreviousClosePrice"),
                    "등락률": item.get("fluctuationsRatio"),
                    "거래량": item.get("accumulatedTradingVolume"),
                    "시가총액(억원)": item.get("marketValue"),
                }
            )

        if page * PAGE_SIZE >= data.get("totalCount", 0):
            break

        time.sleep(0.3)  # 서버 부하 방지

    return stocks


def save_to_csv(rows, filename="국내증시_종목리스트.csv"):
    if not rows:
        print("저장할 데이터가 없습니다.")
        return

    fieldnames = list(rows[0].keys())
    with open(filename, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)}개 종목을 '{filename}' 파일로 저장했습니다.")


if __name__ == "__main__":
    all_stocks = get_stock_list("KOSPI", max_pages=5) + get_stock_list("KOSDAQ", max_pages=5)
    save_to_csv(all_stocks)
