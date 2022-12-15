# Syntax

There are build-in methods and user-defined methods. Commands such as `print` are bound to methods with the name `do_print`.

[toc]

## By Type

### Standard Expressions

| Example                   | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `print hi hello`          | Run the method `do_print()` with arguments `"hi"` and `"hello"`. |
| `println 1 2 3`           | Print separated arguments on new lines.                      |
| `print 1, print 2`        | Run multiple methods.                                        |
| `print 1 `&vert;`> print` | Pipe the output of one expression to another expression.     |

### Maps and Loops

| Example                                    | Description                                                  |
| ------------------------------------------ | ------------------------------------------------------------ |
| `print 1 2 `&vert;`> foreach print`         | Run a command for each term of the output of the previous expression. |
| `println 1 2 `&vert;`> map print`            | Run a command for each line of the previous output.          |
| `println 1 2 `&vert;`> map print pre $ post` | Insert each line of the previous output into a new expression. |
| `println 1 2 >>= print`                    | `>>=` is an alias for &vert;`> map`                          |

### Shell Interop

Commands can be chained, similar to *Bash*. The main output `stdout` is used.

| Example                    | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `!echo hello`              | Invoke a system shell and run `echo hello` there |
| `print 1 `&vert;` echo`     | Pipe the output of                               |
| `print 1 > somefilename`  | Write the output of an expression to a file      |
| `print 1 >> somefilename` | Append the output of an expression to a file     |

### Environment Variables

The operator `=` is used for variable assignment. The operator `<-` is used for post-evaluation assignment (borrowed from [R](https://www.r-project.org/)). `$`-referenced variables are expanded immediately, prior to function invocation.

| Example         | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `a = 100`       | Assign the value `100`  to the variable `a`                  |
| `b <- print 10` | Assign the result of the left-hand-side expression to the variable `b` |
| `print 20 -> c` | Assign the result of the right-hand-side expression to the variable `b` |
| `print $a $b`   | Pass the values of the variables `a` and `b` to the command `print` |

#### Environments

An environment is a key-value map.

| Command  | Description                             |
| -------- | --------------------------------------- |
| `env`    | Show all environment variables.         |
| `save`   | Copy the current environment to a file. |
| `reload` | Reload the default environment.         |


### Globbing

| Example        | Description                                                |
| -------------- | ---------------------------------------------------------- |
| `print *`      | `*` is replaced with all items from the autocomplete list. |
| `print ab?`    | `?` is a wildcard for a single character.                  |
| `print {1..3}` | Create a range.                                            |

### Functions

| Example                 | Description                                              |
| ----------------------- | -------------------------------------------------------- |
| `f (x): x`              | Identity function. Echo the input.                       |
| `triple (i): i i i`     | Repeat a term.                                           |
| `add (a b): math a + b` | Arithmetic.                                              |
| `f (x): math x + $a`    | Combine positional arguments with environment variables. |

### Built-in Commands

| Command             | Description                                           |
| ------------------- | ----------------------------------------------------- |
| `help`              | Show info.                                            |
| `help CMD`          | Show the usage of the command `CMD`.                  |
| `E`                 | Show details of the last error message.               |
| `echo [INPUT]`      | Return the input.                                     |
| `print SOME TEXT`   | Print the words `SOME` and `TEXT`.                    |
| `println SOME TEXT` | Print the words `SOME` and `TEXT` on different lines. |
| `math 1 + 10`       | Evaluate math expressions.                            |

## Symbols

**Variable assignment**
`=` `->` `<-` `$`

**Pipes (Bash)**
`|` `>` `>>`

**Pipes (Python)**
 `|>` `>>=`



## Proposals

Proposals for future changes.


**Basic Functions**

Inf loop: `f x = f x |> repeat x` 

- TODO: Decide on whether states should be mutable or immutable.



**Multiline functions**

```haskell
f x = x
	|> repeat
	|> tail
```

or

```bash
fun f(x) { # ignore newlines in this scope
  # local variable
  a <- math 2 ** 3 ;
  # use the last expression as return value
  math x + a
}
```

or

```elm
-- inline
sum (x y): math x + y

mul (x y):
  math y * x

-- let .. in
g (x y):
  let a = 10, b = 3, k <- math x ** a + b
  in x

-- keyword: fun
fun g (x y):
  let a = 10, b = 3, k <- math x ** a + b
  in x

fun g (x y):
  let
    a = 10 ;
    b = 3 ;
    k <- math x ** a ;
  in
    x
```



**Unpack sequences**

*Proposal: Never expand RHS `*` symbols.*

````python
a b = println 10 20
print a # 10

a *b = {1..10} # a = 1, b = 2-10
````

Alternative syntax:

```python
head x @xs = x
tail x @xs = xs
end @xs x = x
```

*TODO: Decide on whether to support lazy evaluation*



**Math**

Numbers: `int 1`, `float 1.0` 

Shorthand notation:  `a = $100.0`, `b = $2e3`, `c = $2^2`

Using [Polish notation](https://en.wikipedia.org/wiki/Polish_notation):

```python
+ x y # addition
- x y # subtraction
```

