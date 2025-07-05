# Language Reference

The language is a mix of Bash and Python. Statements are separated by whitespace and semicolons. Pipes are used to pass data between commands.

For examples, see [src.lib.math.sh](https://github.com/voschezang/mash/blob/main/src/lib/math.sh). The AST can be found [here](https://voschezang.github.io/mash-docs/pages/ast.html).

**Table of Contents**

- [Language Reference](#language-reference)
  - [By Type](#by-type)
    - [Standard Expressions](#standard-expressions)
    - [Conditions and Branches](#conditions-and-branches)
    - [Maps and Loops](#maps-and-loops)
    - [Shell Interop](#shell-interop)
    - [Environment Variables](#environment-variables)
      - [Environments](#environments)
    - [Globbing](#globbing)
    - [Functions](#functions)
      - [Inline Functions](#inline-functions)
      - [Multiline Functions](#multiline-functions)
    - [Built-in Commands](#built-in-commands)
  - [Symbol Reference](#symbol-reference)
    - [Keywords](#keywords)
    - [Built-in Functions](#built-in-functions)
  - [Proposals](#proposals)
    - [Queries](#queries)
      - [Show tabular data](#show-tabular-data)
      - [Inner join](#inner-join)

## By Type

### Standard Expressions

| Example                   | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `print hi hello`          | Run the method `do_print()` with arguments `"hi"` and `"hello"`. |
| `println 1 2 3`           | Print separated arguments on new lines.                      |
| `print 1, print 2`        | Run multiple methods.                                        |
| `print 1`&vert;`> print` | Pipe the output of one expression to another expression.     |

### Conditions and Branches

| Example                                                   | Description                     |
| --------------------------------------------------------- | ------------------------------- |
| `if 1 > 0 then print greater`                             | Run a command conditionally.    |
| `x <- if 1 > 0 then 10 else 20`                           | Conditional variable assignment |
| `if .. then if .. then print A else print B else print C` | Nested if-then-else statement   |

Multiline if-then-else statement

```python
if 10 < 1 then
 if 5 < 1 then
    print a
else if 1 < 1
  print b
else
 print c
```

### Maps and Loops

| Example                                     | Description                                                  |
| ------------------------------------------- | ------------------------------------------------------------ |
| `println 1 2`&vert;`> map print`            | Run a command for each line of the output of the previous expression. |
| `println 1 2`&vert;`> map print pre $ post` | Insert each line of the previous output into a new expression. |
| `println 1 2 >>= print`                     | `>>=` is an alias for &vert;`> map`                          |
| `foreach DIR >>= print`                     | Iterate over a directory.                                    |

### Shell Interop

Commands can be chained, similar to *Bash*. The main output `stdout` is used.

| Example                    | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `!echo hello`              | Invoke a system shell and run `echo hello` there |
| `print 1`&vert;`echo`     | Pipe the output of                               |
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

#### Inline Functions

| Example                                | Description                                              |
| -------------------------------------- | -------------------------------------------------------- |
| `f (x): $x`                            | Identity function. Echo the input.                       |
| `triple (i): $i $i $i`                 | Repeat a term.                                           |
| `add (a b): math $a + $b`              | Arithmetic.                                              |
| `f (x): math $x + $a`                  | Combine positional arguments with environment variables. |
| `powers (n): range $n >>= math $ ** 2` | A function that iterates over a loop.                    |
| `f (n): range $n`&vert;`> reduce sum 0`| Aggregate a sequence using a reduction operator.        |

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

## Symbol Reference

**Variable assignment**
`=` `->` `<-` `$`

**Function definition**
`function_name ( ):`

**Globbing**

`*` `?` `{` `}`

**Pipes (Bash)**
`|` `>-` `>>`

**Pipes (Python)**
 `|>` `>>=`

**Comparison Operators**
`==` `!=` `>` `<`

### Keywords

`if` `then` `else` `return`

### Built-in Functions

Logical operators: `and` `or` `not`
Other operators: `map` `math` `foreach`

## Proposals

Proposals for future changes.

**Predicate logic**

```python
a and b => not c
x > 1 for all x in X
x + y == 1 for any x in X, y in Y
```

**Basic Functions**

Inf loop: `f x = f x |> repeat x`

- TODO: Decide on whether states should be mutable or immutable.

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

**Performance & Parallelization**

Benefit

- Simplicity of Python and performance of Haskell and Erlang

```python
# inf streams
a *b = list_natural_numbers
# pure functions can be executed in parallel, using a thread pool
range 10 >>= math 10 * $ + 1 |> reduce sum
```

### Queries

#### Show tabular data

*"Show the users"*

```diff
- SELECT * FROM users
+ show users
|      | email              | name   |
|-----:|:-------------------|:-------|
| 1000 | name.0@company.com | name_0 |
| 1001 | name.1@company.com | name_1 |
| 1002 | name.2@company.com | name_2 |
```

#### Inner join

*"Find users that own a at least one document"*

```diff
- SELECT name FROM users INNER JOIN documents ON users.id == document.owner
+ {users | users.id in {documents.owner}} >>= show name
```

*"Show documents of each user"*

```diff
- SELECT users.name, documents.name FROM users LEFT JOIN documents ON users.id == document.owner
+ { users documents | users.id = documents.owner } >>= show $.u.email $.d.name
```

Note the similarity to ranges

```shell
{1..3}
1 2 3
```

