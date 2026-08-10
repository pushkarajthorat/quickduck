import math

def printDivisors(n) :
    # Note that this loop runs till square root
    i = 1
    while i <= math.sqrt(n):
        if (n % i == 0) :
            # If divisors are equal, print only one
            if (n / i == i) :
                yield(i)
            else :
                yield(i)
                yield(int(n/i))
        i = i + 1

divisors = list(printDivisors(int(input())))
even_divisors = len(list(filter(lambda x:x%2==0, divisors)))
odd_divisors = len(list(filter(lambda x:x%2!=0, divisors)))

if even_divisors < odd_divisors:
    print("BUY")
elif even_divisors > odd_divisors:
    print("SELL")
else:
    print("PASS")
    