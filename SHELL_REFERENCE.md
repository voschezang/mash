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

| Example     | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `print *`   | `*` is replaced with all items from the autocomplete list. |
| `print ab?` | `?` is a wildcard for a single character.                  |

### Functions

| Example                | Description                        |
| ---------------------- | ---------------------------------- |
| `f x = x`              | Identity function. Echo the input. |
| `triple i = i i i`     | Repeat a term.                     |
| `add a b = math a + b` | Arithmetic.                        |

### Built-in Commands

| Command             | Description                                           |
| ------------------- | ----------------------------------------------------- |
| `help`              | Show info.                                            |
| `help CMD`          | Show the usage of the command `CMD`.                  |
| `E`                 | Show details of the last error message.               |
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

**User-definable Functions**

Avoid shell expansion (`$var`, `*`, `a??`), as it would complicate lazy evaluation of functions. Treat `$` as macro's.

- Syntax for constant variables: `x = 1 ; a = $x`
- Syntax for functions: `f x = x` - without `$`

The latter requires "local" variable scopes. *Proposal: use the class `FileSystem` for this.*



**Basic Functions**

Options for syntax.

- Constants

    -  `f x = x`

    -  `f x = $x`

    - `f x = print x`

    - `f x = print $x`

- Expressions

    - `f x = math x + 10`
    - `f x = math $x + 10`





Identity: `f x = x` or `f x = print x`

- but not `f x = $x`

Constant: `k x = "a"` for a constant string,  `k x = a` for a constant variable.

Duplicate `r x = x x` or `r *x = *x *x`

Inf loop: `f x = f x |> repeat x` 

Range `g x n = `

Append: `append a b = $b "$a"`



Multiline functions

```haskell
f x = x
	|> repeat
	|> tail
```



**Unpack sequences**

*Proposal: Never expand RHS `*` symbols.*

````python
f *x = x
print <| f 1 2 3 # "1 2 3"
````

Alternative syntax:

```python
head x @xs = x
tail x @xs = xs
end @xs x = x
```



**Math**

Numbers: `int 1`, `float 1.0` 

Shorthand notation:  `a = $100.0`, `b = $2e3`, `c = $2^2`

Using [Polish notation](https://en.wikipedia.org/wiki/Polish_notation):

```python
+ x y # addition
- x y # subtraction
```

