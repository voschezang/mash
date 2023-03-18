# Syntax

The syntax and grammar is a mix of Bash and Python. It relies on pipes to pass strings between commands. Statements are mainly separated by whitespace and semicolons.

There are build-in methods and user-defined functions. Methods such as `print` are bound to methods with the name `do_print`. Functions can be either one-liners or multiline functions.

For examples, see [lib](https://github.com/voschezang/mash/blob/main/src/lib/math.sh).

[toc]

## By Type

### Standard Expressions

| Example                   | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `print hi hello`          | Run the method `do_print()` with arguments `"hi"` and `"hello"`. |
| `println 1 2 3`           | Print separated arguments on new lines.                      |
| `print 1, print 2`        | Run multiple methods.                                        |
| `print 1 `&vert;`> print` | Pipe the output of one expression to another expression.     |

### Conditions and Branches

| Example                                                   | Description                                      |
| --------------------------------------------------------- | ------------------------------------------------ |
| `if 1 > 0 then print greater`                             | Run a command conditionally.                     |
| `x <- if 1 > 0 then 10`                                   | Set `x` to either a value or to an empty string. |
| `if 1 then print A else print B`                          | If-then-else statement                           |
| `if .. then if .. then print A else print B else print C` | Nested if-then-else statement                    |

Multiline if-then-else statement

```python
if 10 < 1 then
	print 1
else
	print 2
```

Assignment

```bash
x <- if today then yes else no
```

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
| `a b = 10 20`   | Assign the values `10`, `20` to the variables `a`,`b`, respectively |
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

| Example                                | Description                                              |
| -------------------------------------- | -------------------------------------------------------- |
| `f (x): $x`                            | Identity function. Echo the input.                       |
| `triple (i): $i $i $i`                 | Repeat a term.                                           |
| `add (a b): math $a + $b`              | Arithmetic.                                              |
| `f (x): math $x + $a`                  | Combine positional arguments with environment variables. |
| `powers (n): range $n >>= math $ ** 2` | A function that iterates over a loop.                    |
| `f (n): range $n |> reduce sum 0`      | Aggregate a sequence using a reduction operator.         |

#### Multiline Functions

Using the `return` keyword.

```bash
b = 10 # a global variable

f (x):
    # a magic formula
    x <- math $x * 3 # a local variable
    if x > 2:
        return $x
    return math 2 * $x + $b

# call the function with argument '10'
f 10
```

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

**Function definition**
` ( ):`

**Globbing**

`*` `?` `{` `}`

**Pipes (Bash)**
`|` `>-` `>>`

**Pipes (Python)**
 `|>` `>>=`

**Comparison Operators**
`==` `!=` `>` `<`

### Keywords

`if` `then` `return`

## Proposals

Proposals for future changes.



**Predicate logic**

```python
a and b or c
a and b => not c
x > 1 for all x in X
x + y == 1 for any x in X, y in Y
```



**Basic Functions**

Inf loop: `f x = f x |> repeat x` 

- TODO: Decide on whether states should be mutable or immutable.



**Skip `then` keyword in if-then statements**

```python
if 1:
  print 1
```



**Unpack sequences**

*Proposal: Never expand LHS `*` symbols.*

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



**Performance & Parallelization**

Benefit

- Simplicity of Python and performance of Haskell and Erlang

```python
# inf streams
a *b = list_natural_numbers
# pure functions can be executed in parallel, using a thread pool
range 10 >>= math 10 * $ + 1 |> reduce sum
```

