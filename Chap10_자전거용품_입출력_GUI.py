import sys
import sqlite3

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem,
    QMessageBox
)


DB_NAME = "MyProduct2.db"

STYLE_SHEET = """
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1f2b47, stop:1 #3a1c71
    );
}

QLabel {
    color: #f5f5f5;
    font-size: 14px;
    font-weight: bold;
}

QLabel#titleLabel {
    color: #ffd54f;
    font-size: 22px;
    font-weight: 800;
    background: transparent;
}

QLineEdit {
    background-color: #ffffff;
    border: 2px solid #8e44ad;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 13px;
    color: #2c3e50;
}

QLineEdit:focus {
    border: 2px solid #ffd54f;
}

QPushButton {
    background-color: #6c5ce7;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #a29bfe;
}

QPushButton:pressed {
    background-color: #4834d4;
}

QPushButton#insertBtn {
    background-color: #00b894;
}
QPushButton#insertBtn:hover {
    background-color: #55efc4;
}

QPushButton#updateBtn {
    background-color: #0984e3;
}
QPushButton#updateBtn:hover {
    background-color: #74b9ff;
}

QPushButton#deleteBtn {
    background-color: #d63031;
}
QPushButton#deleteBtn:hover {
    background-color: #ff7675;
}

QPushButton#searchBtn {
    background-color: #e17055;
}
QPushButton#searchBtn:hover {
    background-color: #fab1a0;
}

QPushButton#clearBtn {
    background-color: #636e72;
}
QPushButton#clearBtn:hover {
    background-color: #b2bec3;
}

QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f1e9ff;
    gridline-color: #dcdde1;
    border-radius: 8px;
    font-size: 13px;
    color: #2c3e50;
}

QTableWidget::item:selected {
    background-color: #6c5ce7;
    color: white;
}

QHeaderView::section {
    background-color: #341f97;
    color: white;
    font-weight: bold;
    padding: 6px;
    border: none;
}
"""


class MyProductDB:
    """MyProduct2.db의 MyProduct 테이블을 관리하는 클래스"""

    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS MyProduct (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL
        )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    def insert(self, name, price):
        self.cursor.execute(
            "INSERT INTO MyProduct (name, price) VALUES (?, ?)", (name, price)
        )
        self.conn.commit()

    def update(self, id, name, price):
        self.cursor.execute(
            "UPDATE MyProduct SET name = ?, price = ? WHERE id = ?",
            (name, price, id),
        )
        self.conn.commit()
        return self.cursor.rowcount

    def delete(self, id):
        self.cursor.execute("DELETE FROM MyProduct WHERE id = ?", (id,))
        self.conn.commit()
        return self.cursor.rowcount

    def select_all(self):
        self.cursor.execute("SELECT id, name, price FROM MyProduct ORDER BY id")
        return self.cursor.fetchall()

    def search_by_name(self, keyword):
        self.cursor.execute(
            "SELECT id, name, price FROM MyProduct WHERE name LIKE ? ORDER BY id",
            (f"%{keyword}%",),
        )
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = MyProductDB()
        self.setupUI()
        self.loadTableData()

    def setupUI(self):
        self.setWindowTitle("자전거용품 관리 프로그램")
        self.setGeometry(200, 200, 700, 560)
        self.setStyleSheet(STYLE_SHEET)

        # 타이틀
        self.titleLabel = QLabel("🚴  자전거용품 재고 관리", self)
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.move(20, 15)
        self.titleLabel.resize(660, 40)

        # id 입력
        QLabel("id", self).move(20, 75)
        self.idEdit = QLineEdit(self)
        self.idEdit.move(60, 75)
        self.idEdit.resize(80, 28)
        self.idEdit.setReadOnly(True)
        self.idEdit.setPlaceholderText("자동생성")

        # name 입력
        QLabel("이름", self).move(160, 75)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.move(200, 75)
        self.nameEdit.resize(200, 28)

        # price 입력
        QLabel("가격", self).move(420, 75)
        self.priceEdit = QLineEdit(self)
        self.priceEdit.move(460, 75)
        self.priceEdit.resize(110, 28)

        # 버튼들
        self.insertBtn = QPushButton("➕ 입력", self)
        self.insertBtn.setObjectName("insertBtn")
        self.insertBtn.move(20, 120)
        self.insertBtn.resize(80, 34)
        self.insertBtn.clicked.connect(self.insertProduct)

        self.updateBtn = QPushButton("✏ 수정", self)
        self.updateBtn.setObjectName("updateBtn")
        self.updateBtn.move(110, 120)
        self.updateBtn.resize(80, 34)
        self.updateBtn.clicked.connect(self.updateProduct)

        self.deleteBtn = QPushButton("🗑 삭제", self)
        self.deleteBtn.setObjectName("deleteBtn")
        self.deleteBtn.move(200, 120)
        self.deleteBtn.resize(80, 34)
        self.deleteBtn.clicked.connect(self.deleteProduct)

        self.searchEdit = QLineEdit(self)
        self.searchEdit.move(330, 120)
        self.searchEdit.resize(180, 34)
        self.searchEdit.setPlaceholderText("검색어(이름)")

        self.searchBtn = QPushButton("🔍 검색", self)
        self.searchBtn.setObjectName("searchBtn")
        self.searchBtn.move(520, 120)
        self.searchBtn.resize(80, 34)
        self.searchBtn.clicked.connect(self.searchProduct)

        self.clearBtn = QPushButton("📋 전체보기", self)
        self.clearBtn.setObjectName("clearBtn")
        self.clearBtn.move(20, 165)
        self.clearBtn.resize(580, 30)
        self.clearBtn.clicked.connect(self.loadTableData)

        # 하단 테이블
        self.tableWidget = QTableWidget(self)
        self.tableWidget.move(20, 210)
        self.tableWidget.resize(660, 330)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["id", "이름", "가격"])
        self.tableWidget.setColumnWidth(0, 100)
        self.tableWidget.setColumnWidth(1, 340)
        self.tableWidget.setColumnWidth(2, 200)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.cellClicked.connect(self.tableRowClicked)

    def loadTableData(self):
        rows = self.db.select_all()
        self.fillTable(rows)
        self.searchEdit.clear()

    def fillTable(self, rows):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(rows))
        for row_idx, (id, name, price) in enumerate(rows):
            self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(id)))
            self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(name))
            self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(str(price)))

    def tableRowClicked(self, row, column):
        self.idEdit.setText(self.tableWidget.item(row, 0).text())
        self.nameEdit.setText(self.tableWidget.item(row, 1).text())
        self.priceEdit.setText(self.tableWidget.item(row, 2).text())

    def clearInputs(self):
        self.idEdit.clear()
        self.nameEdit.clear()
        self.priceEdit.clear()

    def insertProduct(self):
        name = self.nameEdit.text().strip()
        price_text = self.priceEdit.text().strip()

        if not name or not price_text:
            QMessageBox.warning(self, "입력 오류", "이름과 가격을 입력하세요.")
            return

        try:
            price = int(price_text)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "가격은 숫자로 입력하세요.")
            return

        self.db.insert(name, price)
        QMessageBox.information(self, "완료", "상품이 입력되었습니다.")
        self.clearInputs()
        self.loadTableData()

    def updateProduct(self):
        id_text = self.idEdit.text().strip()
        name = self.nameEdit.text().strip()
        price_text = self.priceEdit.text().strip()

        if not id_text:
            QMessageBox.warning(self, "선택 오류", "수정할 항목을 테이블에서 선택하세요.")
            return

        if not name or not price_text:
            QMessageBox.warning(self, "입력 오류", "이름과 가격을 입력하세요.")
            return

        try:
            price = int(price_text)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "가격은 숫자로 입력하세요.")
            return

        affected = self.db.update(int(id_text), name, price)
        if affected == 0:
            QMessageBox.warning(self, "수정 실패", "해당 id의 상품이 없습니다.")
        else:
            QMessageBox.information(self, "완료", "상품이 수정되었습니다.")
            self.clearInputs()
            self.loadTableData()

    def deleteProduct(self):
        id_text = self.idEdit.text().strip()

        if not id_text:
            QMessageBox.warning(self, "선택 오류", "삭제할 항목을 테이블에서 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "삭제 확인", "정말 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        affected = self.db.delete(int(id_text))
        if affected == 0:
            QMessageBox.warning(self, "삭제 실패", "해당 id의 상품이 없습니다.")
        else:
            QMessageBox.information(self, "완료", "상품이 삭제되었습니다.")
            self.clearInputs()
            self.loadTableData()

    def searchProduct(self):
        keyword = self.searchEdit.text().strip()
        if not keyword:
            self.loadTableData()
            return
        rows = self.db.search_by_name(keyword)
        self.fillTable(rows)

    def closeEvent(self, event):
        self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
