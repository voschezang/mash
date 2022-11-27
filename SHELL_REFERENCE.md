## Syntax

There are build-in methods and user-defined methods. Commands such as `print` are bound to methods with the name `do_print`.

### By Type

#### Standard Expressions

| Example            | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| `print hi hello`   | Run the method `do_print()` with arguments `"hi"` and `"hello"`. |
| `println 1 2 3`    | Print separated arguments on new lines.                      |
| `print 1, print 2` | Run multiple methods.                                        |
| `print 1 |> print` | Pipe the output of one expression to another expression.     |

#### Maps and Loops

| Example                                    | Description                                                  |
| ------------------------------------------ | ------------------------------------------------------------ |
| `print 1 2 |> foreach print`               | Run a command for each term of the output of the previous expression. |
| `println 1 2 |> map print`                 | Run a command for each line of the previous output.          |
| `println 1 2 |> map print prefix $ suffix` | Insert each line of the previous output into a new expression. |
| `println 1 2 >>= print`                    | `>>=` is an alias for `|> map`                               |

#### Shell Interop

Commands can be chained, similar to *Bash*. The main output `stdout` is used.

| Example                    | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `!echo hello`              | Invoke a system shell and run `echo hello` there |
| `print 1 | echo`           | Pipe the output of                               |
| `print 1 > somefilename `  | Write the output of an expression to a file      |
| `print 1 >> somefilename ` | Append the output of an expression to a file     |

#### Environment Variables

| Example         | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `a = 100`       | Assign the value `100`  to the variable `a`                  |
| `b <- print 10` | Assign the result of the left-hand-side expression to the variable `b` |
| `print 20 -> c` | Assign the result of the right-hand-side expression to the variable `b` |
| `print $a $b`   | Pass the values of the variables `a` and `b` to the command `print` |

**Environments**
An environment is a key-value map.

| Command  | Description                             |
| -------- | --------------------------------------- |
| `env`    | Show all environment variables.         |
| `save`   | Copy the current environment to a file. |
| `reload` | Reload the default environment.         |

#### Globbing

| Example     | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `print *`   | `*` is replaced with all items from the autocomplete list. |
| `print ab?` | `?` is a wildcard for a single character.                  |

#### Built-in Commands

| Command             | Description                                           |
| ------------------- | ----------------------------------------------------- |
| `help`              | Show info.                                            |
| `help CMD`          | Show the usage of the command `CMD`                   |
| `E`                 | Show details of the last error message.               |
| `print SOME TEXT`   | Print the words `SOME` and `TEXT`                     |
| `println SOME TEXT` | Print the words `SOME` and `TEXT` on different lines. |



### Symbol Reference

**Variable assignment**
`=` `->` `<-` `$`

**Pipes (Bash)**
`|` `>` `>>`

**Pipes (Python)**
 `|>` `>>=`

