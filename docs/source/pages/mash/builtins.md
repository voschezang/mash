# Built-in commands

This page shows all built-in Mash commands.



## Keywords

These langauge constructs use infix, prefix and suffix arguments.

- Conditions: `if` `then` `else`

- Logical operators: `and` `or`



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



## Alphabetical Commands

### E

Show details of the last error message (if available).

### del

Remove (unset) the variable `$x`.

### env

Show the environment variables

```sh
$	env
| keys | values |
|:-----|:-------|
|    a |     10 |
|    b |     20 |
$ env a
10
```

### int

Convert arguments to integers

### fail

### help

Show available commands.

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

Explain  a specific command

```sh
$ help print
Write to stdout
```

### foreach

### map

### math

Evaluate mathematical expressions.

```sh
math (1 + 1) * 10
```

### not

Negate an expression.

### print

Print text.

```sh
$ print 1 2 3
1 2 3
```

### println

Print while seperated the arguments by newlines.

```sh
$ print 1 2 3
1
2
3
```

### reload

Reload the default environment.

### return

### save

Copy the current environment (session) to a file.

### shell

Use the system shell.

```sh
shell cat myfile
```

### show

### tree

### undo

Attempt to undo a command. This requires `undo_CMD` to be denfined in the DSL.

