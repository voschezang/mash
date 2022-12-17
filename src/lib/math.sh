#!/usr/bin/python -m mash

# unary operators
fac (n): range n |> product

# binary operators
add (a b): math a + b
sub (a b): math a - b
mul (a b): math a * b

# reduction
sum (x): echo x |> reduce add 0
product (x): echo x |> reduce mul 1
