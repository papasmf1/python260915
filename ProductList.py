import sqlite3
import random


class ProductList:
    """MyProduct.db의 Products 테이블을 관리하는 클래스"""

    def __init__(self, db_name="MyProduct.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Products (
            productID INTEGER PRIMARY KEY,
            productName TEXT NOT NULL,
            productPrice INTEGER NOT NULL
        )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    def insert_product(self, product_id, product_name, product_price):
        sql = "INSERT INTO Products (productID, productName, productPrice) VALUES (?, ?, ?)"
        self.cursor.execute(sql, (product_id, product_name, product_price))
        self.conn.commit()

    def insert_products(self, products):
        """products: (productID, productName, productPrice) 튜플 리스트"""
        sql = "INSERT INTO Products (productID, productName, productPrice) VALUES (?, ?, ?)"
        self.cursor.executemany(sql, products)
        self.conn.commit()

    def update_product(self, product_id, product_name=None, product_price=None):
        if product_name is not None:
            self.cursor.execute(
                "UPDATE Products SET productName = ? WHERE productID = ?",
                (product_name, product_id),
            )
        if product_price is not None:
            self.cursor.execute(
                "UPDATE Products SET productPrice = ? WHERE productID = ?",
                (product_price, product_id),
            )
        self.conn.commit()

    def delete_product(self, product_id):
        sql = "DELETE FROM Products WHERE productID = ?"
        self.cursor.execute(sql, (product_id,))
        self.conn.commit()

    def delete_all(self):
        self.cursor.execute("DELETE FROM Products")
        self.conn.commit()

    def select_all(self):
        self.cursor.execute("SELECT productID, productName, productPrice FROM Products")
        return self.cursor.fetchall()

    def select_by_id(self, product_id):
        sql = "SELECT productID, productName, productPrice FROM Products WHERE productID = ?"
        self.cursor.execute(sql, (product_id,))
        return self.cursor.fetchone()

    def count(self):
        self.cursor.execute("SELECT COUNT(*) FROM Products")
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()


def make_sample_data(count=1000):
    """전자제품 샘플 데이터 count개 생성"""
    categories = [
        "노트북", "스마트폰", "모니터", "키보드", "마우스",
        "이어폰", "스피커", "태블릿", "냉장고", "세탁기",
        "청소기", "에어컨", "TV", "충전기", "카메라",
    ]
    brands = ["삼성", "LG", "애플", "소니", "샤오미", "델", "레노버", "HP", "에이수스"]

    products = []
    for i in range(1, count + 1):
        category = random.choice(categories)
        brand = random.choice(brands)
        name = f"{brand} {category} {i}호"
        price = random.randrange(10000, 3000001, 1000)
        products.append((i, name, price))
    return products


def main():
    product_list = ProductList()

    # 기존 데이터 초기화 후 샘플 데이터 1000개 삽입
    product_list.delete_all()
    sample_data = make_sample_data(1000)
    product_list.insert_products(sample_data)
    print(f"샘플 데이터 삽입 완료: {product_list.count()}건")

    # 조회 예제
    first_product = product_list.select_by_id(1)
    print("1번 제품:", first_product)

    # 수정 예제
    product_list.update_product(1, product_name="갤럭시 노트북 특가", product_price=999000)
    print("수정 후 1번 제품:", product_list.select_by_id(1))

    # 삭제 예제
    product_list.delete_product(1000)
    print("1000번 제품 삭제 후 전체 건수:", product_list.count())

    product_list.close()


if __name__ == "__main__":
    main()
