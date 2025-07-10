# Language Reference

The language is a mix of Bash and Python. Statements are separated by whitespace and semicolons. Pipes are used to pass data between commands.

For examples, see [src.lib.math.sh](https://github.com/voschezang/mash/blob/main/src/lib/math.sh). The AST can be found [here](https://voschezang.github.io/mash-docs/pages/ast.html).

[toc]


## By Type

### Standard Expressions

| Example                   | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `print hi hello`          | Print the strings `"hi"` and `"hello"`. |
| `println 1 2 3`           | Print while seperated the arguments by newlines. |
| `print 1; print 2` |  |
| `print 1`&vert;` print` | Pipe the output of one command to another. |

### Help

Run `help` to show the available commands.

```sh
$ help
Documented commands (type help <topic>):
========================================
E                 cat   example  flatten  help     map      range   shell  vi
...

Undocumented commands:
======================
bool  float  int  math
```

Run `help CMD` to explain  a specific command

```sh
$ help print
Write to stdout
```

### Conditions and Branches

Conditions can be chosen using **if-statements**.

```python
if 1 > 0 then print greater
```

For more complex conditions, **nested** if-statement can be used.

```python
if .. then if .. then print A else print B else print C
```

To improve readibility, use a **multiline** if-statements.

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

### Math

Run `math` to evaluate mathematical expressions.

```sh
math (1 + 1) * 10
```

### Shell Interop

When commands are unknown, a corresponding binary is sought in the `PATH`.

| Example                    | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `shell echo hello` | Use the system shell to run `echo hello` |
| `echo hello`              | Invoke `echo` directly. This is forbidden is *safe mode*. |
| `print 1`&vert;`echo`     | Pipe the output of a Mash command to the system shell. |
| `print 1 > somefilename`  | *Write* the output of a command to a file |
| `print 1 >> somefilename` | *Append* the output of a command to a file |

### Environments

Environments allow you to save and recall variables, denoted with `$` symbols. See also [directories](directories.md).

#### Variables

The operator `=` is used for variable assignment. The operators `<-` and `->` are used for post-evaluation assignment (borrowed from [R](https://www.r-project.org/)).

 `$`-referenced variables are expanded immediately, prior to function invocation.

| Example         | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `a = 100`       | Assign the value `100`  to the variable `a`                  |
| `a b = 10 20`   | Assign the values `10`, `20` to the variables `a`,`b`, respectively |
| `print $a $b`   | Pass the values of the variables `a` and `b` to the command `print` |
| `b <- print 10` | Assign the result of the right-hand-side expression to the variable `b` |
| `print 20 -> c` | Assign the result of the left-hand-side expression to the variable `b` |

#### Environments

An environment is a key-value map.

| Command  | Description                                       |
| -------- | ------------------------------------------------- |
| `env`    | Show all environment variables.                   |
| `del $x` | Remove (unset) the variable `$x`.                 |
| `save`   | Copy the current environment (session) to a file. |
| `reload` | Reload the default environment.                   |

### Globbing

| Example        | Description                                                |
| -------------- | ---------------------------------------------------------- |
| `print ab*`    | `*` is replaced with all items from the autocomplete list. |
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



## Proposals

Proposals for future changes.

`all` `any`

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

```
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

