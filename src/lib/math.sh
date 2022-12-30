#!/usr/bin/python -m mash

# unary operators
# id (i): i
fac (n): range n |> product
fac (n):
    less <- math $n < 0
    more <- math $n > 0
    eq <- math $n == 0
    if $less then fail
    # TODO implement if-then-else
    a <- if $eq then echo 1
    b <- if $more then range $n |> product
    return strip $a $b

# binary operators
add (a b): math a + b
sub (a b): math a - b
mul (a b): math a * b

# reduction
sum (x): echo x |> reduce add 0
product (x): echo x |> reduce mul 1
