import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QFileDialog
)
from openpyxl import Workbook
import MyCustManager



class CustomerView(QMainWindow):
    """고객 정보 화면(UI) 처리 클래스"""

    def __init__(self):
        super().__init__()
        self.manager = MyCustManager.CustomerManager()
        self.init_ui()
        self.load_customer_list()

    def init_ui(self):
        self.setWindowTitle("고객정보 관리")
        self.resize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 왼쪽: 버튼 영역
        self.btn_add = QPushButton("입력")
        self.btn_update = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")
        self.btn_search = QPushButton("검색")
        self.btn_export = QPushButton("엑셀저장")

        self.btn_add.clicked.connect(self.on_add_clicked)
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_search.clicked.connect(self.on_search_clicked)
        self.btn_export.clicked.connect(self.on_export_clicked)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_update)
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_search)
        button_layout.addWidget(self.btn_export)
        button_layout.addStretch()

        # 오른쪽: 입력 컨트롤 영역
        self.edit_custID = QLineEdit()
        self.edit_custID.setReadOnly(True)
        self.edit_custName = QLineEdit()
        self.edit_custTitle = QLineEdit()
        self.edit_search = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("고객ID"), self.edit_custID)
        form_layout.addRow(QLabel("고객명"), self.edit_custName)
        form_layout.addRow(QLabel("직함"), self.edit_custTitle)
        form_layout.addRow(QLabel("검색어"), self.edit_search)

        top_layout = QHBoxLayout()
        top_layout.addLayout(button_layout)
        top_layout.addLayout(form_layout)

        # 하단: 테이블 영역
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["고객ID", "고객명", "직함"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_table_row_selected)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

        central_widget.setLayout(main_layout)

    def load_customer_list(self):
        rows = self.manager.get_all_customers()
        self.fill_table(rows)

    def fill_table(self, rows):
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def on_add_clicked(self):
        custName = self.edit_custName.text().strip()
        custTitle = self.edit_custTitle.text().strip()

        if not custName:
            QMessageBox.warning(self, "입력 오류", "고객명을 입력하세요.")
            return

        self.manager.add_customer(custName, custTitle)
        self.load_customer_list()
        self.clear_inputs()

    def on_update_clicked(self):
        custID = self.edit_custID.text().strip()
        custName = self.edit_custName.text().strip()
        custTitle = self.edit_custTitle.text().strip()

        if not custID:
            QMessageBox.warning(self, "선택 오류", "수정할 고객을 목록에서 선택하세요.")
            return
        if not custName:
            QMessageBox.warning(self, "입력 오류", "고객명을 입력하세요.")
            return

        self.manager.update_customer(custID, custName, custTitle)
        self.load_customer_list()
        self.clear_inputs()

    def on_delete_clicked(self):
        custID = self.edit_custID.text().strip()

        if not custID:
            QMessageBox.warning(self, "선택 오류", "삭제할 고객을 목록에서 선택하세요.")
            return

        self.manager.delete_customer(custID)
        self.load_customer_list()
        self.clear_inputs()

    def on_search_clicked(self):
        keyword = self.edit_search.text().strip()
        rows = self.manager.search_customer(keyword)
        self.fill_table(rows)

    def on_export_clicked(self):
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()

        if row_count == 0:
            QMessageBox.warning(self, "저장 오류", "저장할 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일로 저장", "Customers.xlsx", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Customers"

        headers = [self.table.horizontalHeaderItem(col).text() for col in range(col_count)]
        ws.append(headers)

        for row in range(row_count):
            row_data = [self.table.item(row, col).text() for col in range(col_count)]
            ws.append(row_data)

        wb.save(file_path)
        QMessageBox.information(self, "저장 완료", f"엑셀 파일로 저장되었습니다.\n{file_path}")

    def on_table_row_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        self.edit_custID.setText(self.table.item(row, 0).text())
        self.edit_custName.setText(self.table.item(row, 1).text())
        self.edit_custTitle.setText(self.table.item(row, 2).text())

    def clear_inputs(self):
        self.edit_custID.clear()
        self.edit_custName.clear()
        self.edit_custTitle.clear()

    def closeEvent(self, event):
        self.manager.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = CustomerView()
    view.show()
    sys.exit(app.exec())
