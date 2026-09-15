# 사람을 표현하는 가장 기본적인 클래스예요.
# 클래스는 "붕어빵 틀"이고, 인스턴스는 그 틀로 찍어낸 "붕어빵"이라고 생각하면 돼요.
class Person:
    # __init__ 은 붕어빵을 만들 때(인스턴스를 만들 때) 딱 한 번 자동으로 실행되는 함수예요.
    # self는 "나 자신"을 가리켜요. 즉, 지금 만들어지는 그 사람 자신이에요.
    def __init__(self, id, name):
        self.id = id      # 이 사람의 번호(아이디)를 저장해요.
        self.name = name  # 이 사람의 이름을 저장해요.

    # 이 사람의 정보를 화면에 예쁘게 보여주는 함수예요.
    def printInfo(self):
        print(f"id: {self.id}, name: {self.name}")


# Manager(관리자) 클래스는 Person을 그대로 물려받아요(상속).
# 상속은 부모가 가진 것(id, name, printInfo)을 자식도 그대로 쓸 수 있게 되는 거예요.
# 그리고 Manager만 가지는 특별한 것(title, 직급)을 추가로 가져요.
class Manager(Person):
    def __init__(self, id, name, title):
        # super()는 "부모(Person)"를 가리켜요.
        # 부모의 __init__을 먼저 실행해서 id, name을 저장하게 해요.
        super().__init__(id, name)
        self.title = title  # 관리자만 가지고 있는 직급 정보예요.

    # 부모의 printInfo를 다시 써서(오버라이드) title도 같이 출력하도록 만들어요.
    def printInfo(self):
        super().printInfo()      # 먼저 부모가 하던 대로 id, name을 출력하고
        print(f"title: {self.title}")  # 추가로 title도 출력해요.


# Employee(직원) 클래스도 Person을 물려받아요.
# Employee만 가지는 특별한 것은 skill(잘하는 기술)이에요.
class Employee(Person):
    def __init__(self, id, name, skill):
        super().__init__(id, name)  # 부모의 id, name 저장 기능을 그대로 사용해요.
        self.skill = skill          # 직원만 가지고 있는 특기(기술) 정보예요.

    def printInfo(self):
        super().printInfo()        # 부모처럼 id, name을 먼저 출력하고
        print(f"skill: {self.skill}")  # 추가로 skill도 출력해요.


# 이 파일을 직접 실행했을 때만 아래 코드가 동작해요.
# (다른 파일에서 이 파일을 가져다 쓸 때는 실행되지 않아요.)
if __name__ == "__main__":
    # Manager와 Employee 붕어빵을 총 10개 만들어서 리스트(바구니)에 담아요.
    people = [
        Manager(1, "김철수", "팀장"),
        Manager(2, "이영희", "부장"),
        Manager(3, "박민수", "과장"),
        Employee(4, "최지훈", "Python"),
        Employee(5, "정수아", "Java"),
        Employee(6, "한도윤", "JavaScript"),
        Employee(7, "오서연", "SQL"),
        Manager(8, "강태우", "이사"),
        Employee(9, "윤하늘", "C++"),
        Employee(10, "임소민", "React"),
    ]

    # 바구니 안에 담긴 사람들을 한 명씩 꺼내서
    for person in people:
        person.printInfo()   # 그 사람의 정보를 출력하고
        print("-" * 20)      # 구분선을 그어서 보기 쉽게 해요.
