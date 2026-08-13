# f = open("./data.txt", "rb")
# print(f)
# content = f.read(8)
# print(f"the binary '{content}' represent {content.decode('utf-8')}")

# f.close()


# with open("./data.txt", "r", encoding="utf-8") as ff:
#     print(ff.read())

with open("./data.txt", "r+", encoding="utf-8") as f:
    # f.write("hello!")
    # f.write("yoooo")
    print(f.read())
