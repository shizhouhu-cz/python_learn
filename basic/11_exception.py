try:
    user_weight = float(input("weight"))
    user_height = float(input("height"))
    bmi = user_height * user_weight
except ValueError:
    print("error")
