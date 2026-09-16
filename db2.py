# db1.py 
import sqlite3
#연결객체(파일에 영구적 저장)
con = sqlite3.connect(r"c:\work\sample.db")
#커서객체 생성
cur = con.cursor()
#테이블 생성
cur.execute("CREATE TABLE PhoneBook (name text, phone text);")
#1건 입력 
cur.execute("INSERT INTO PhoneBook (name, phone) VALUES ('tom','010');")
#입력 매개변수 처리
name = "전우치"
phoneNum = "010-222"
cur.execute("INSERT INTO PhoneBook (name, phone) VALUES (?, ?);", 
    (name, phoneNum))
#여러건을 입력 
datalist = [
    ("홍길동", "010-111"),
    ("이순신", "010-333")
]
cur.executemany("INSERT INTO PhoneBook (name, phone) VALUES (?, ?);", 
    datalist)

#검색 
cur.execute("SELECT * FROM PhoneBook;")
#주석처리: ctrl + /  
for row in cur: 
    print(row[0], row[1])
#정상적 완료
con.commit()



