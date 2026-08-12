# mood_index = input("对象今天的心情指数是：")
# mood_index = int(mood_index)

# if mood_index >=60:
#     print("quba pikaqiu")
# else:
#     print('nonono')

user_weight = float(input("体重"))
user_height = float(input("身高"))

# 逻辑与：and
# 逻辑或：or
if user_height > 80 and user_height < 120 or user_weight == 90:
    print("haha")
    if user_weight > 80:
        print("fat boy")
    else:
        print("slim boy")
elif user_height > 60:
    print("nonon")
else:
    print("lalalal")
