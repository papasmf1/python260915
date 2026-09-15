#부모 클래스 정의 
class Person:
    def __init__(self, name, phoneNumber):
        self.name = name
        self.phoneNumber = phoneNumber
    def printInfo(self):
        print("Info(Name:{0}, Phone Number: {1})".format(
            self.name, self.phoneNumber))
    def working(self):
        print("지금 작업중")
    def sleeping(self):
        print("지금 휴식중")

class Student(Person):
    #상속받고 덮어쓰기 
    def __init__(self, name, phoneNumber, subject, studentID):
        super().__init__(name, phoneNumber)
        self.subject = subject
        self.studentID = studentID
    #덮어쓰기(재정의, override)
    def printInfo(self):
        print("Info(Name:{0}, Phone Number: {1})".format(
            self.name, self.phoneNumber))
        print("Info(학과:{0}, 학번: {1})".format(
            self.subject, self.studentID))
        
p = Person("전우치", "010-222-1234")
s = Student("이순신", "010-111-1234", "컴공", "26001")
#메서드 
p.printInfo() 
s.printInfo()
s.working() 
s.sleeping() 

