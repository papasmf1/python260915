import random
from openpyxl import Workbook

# 전자제품 이름 후보 목록
product_names = [
    "노트북", "데스크탑", "모니터", "키보드", "마우스",
    "스피커", "헤드셋", "웹캠", "프린터", "스캐너",
    "태블릿", "스마트폰", "공유기", "외장하드", "USB메모리",
    "SSD", "그래픽카드", "메인보드", "파워서플라이", "쿨러",
]

wb = Workbook()
ws = wb.active
ws.title = "ProductList"

# 헤더 작성
ws.append(["제품ID", "제품명", "가격", "수량"])

# 전자제품 데이터 100개 생성
for product_id in range(1, 101):
    product_name = random.choice(product_names)
    price = random.randrange(10000, 2000001, 1000)
    quantity = random.randint(1, 200)
    ws.append([product_id, product_name, price, quantity])

wb.save("ProductList.xlsx")
print("ProductList.xlsx 파일이 생성되었습니다.")
