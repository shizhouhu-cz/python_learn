contacts = {"xiaoming": "1213123", "xiaohua": "321321"}
contacts["xiaohu"] = "123"

print("xiaohu" in contacts)  # check exist
del contacts["xiaohu"]  # delete element
print(contacts)

example_tuple = ("zhangwei", "18")
contacts[example_tuple] = "8988"
print(contacts)
