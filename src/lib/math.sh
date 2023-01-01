#!/usr/bin/python -m mash

# constants
pi <- float 3.141592653589793

# unary operators
fac (n): range n |> product
fac (n):
    b <- if $n > 0 then range $n |> product
    # TODO implement if-then-else or switch-case
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
