#전역변수 
strName = "Not Class Member"

class DemoString:
    def __init__(self):
        #멤버변수 
        self.strName = "" 
    def set(self, msg):
        self.strName = msg
    def print(self):
        #꼼꼼하게 명시할 필요가 있다
        print(self.strName)

d = DemoString()
d.set("First Message")
d.print()
