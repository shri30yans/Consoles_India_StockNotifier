import math
x=int(input("Enter number:"))
limit=int(input("Enter limit:"))


def func(x):
    sum=1
    for i in range(1,limit+1):
        ans=x**i/math.factorial(i)
        sum+=ans
    print(sum)

func(x)
# x=int(input("Enter number:"))
# limit=int(input("Enter limit:"))


# def func(x):


# func(x)


