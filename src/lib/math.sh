#!/usr/bin/python -m mash

# constants
pi <- float 3.141592653589793

# unary operators
abs (x):
    a <- if $x < 0 then math - $x
    b <- if $x >= 0 then $x
    return strip $a $b

fac (n): range n |> product
fac (n):
    # TODO implement break-like behaviour of `return`
    if $n < 0 then fail
    a <- if $n == 0 then echo 1
    b <- if $n > 0 then range $n |> product
    return strip $a $b

# binary operators
add (a b): math a + b
sub (a b): math a - b
mul (a b): math a * b

# reduction
sum (x): echo x |> reduce add 0
product (x): echo x |> reduce mul 1
