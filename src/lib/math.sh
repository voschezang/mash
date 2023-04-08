#!/usr/bin/python -m mash

# constants
pi <- float 3.141592653589793

# unary operators
abs (x):
    if $x >= 0 then
        return $x
    else
        return math - $x


fac (n):
    if $n < 0 then fail

    if $n == 0 then 
        return 1

    return range $n |> product


# binary operators
add (a b): math a + b
sub (a b): math a - b
mul (a b): math a * b

# reduction
sum (x): echo $x |> reduce add 0
product (x): echo $x |> reduce mul 1
