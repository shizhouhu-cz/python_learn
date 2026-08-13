class CuteCat:
    def __init__(self):
        self.name = "lambton"

    def speak(self):
        print(f"miao's name is {self.name}")


cat1 = CuteCat()

print(cat1.name)
print(f"cat's name is {cat1.name}")


# 继承
class meiduan(CuteCat):
    def read(self):
        print(self.name)


cat2 = meiduan()
cat2.read()
