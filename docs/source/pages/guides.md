# Guides

[toc]

## Introduction

### Use the shell

Use the example script `src/examples/shell.py`

```sh
python3 -m examples.shell
# Press ctrl-d to exit, ctrl-c to cancel, TAB for word completion, ? for help and ! for shell interop.
```

You can use `echo` to display text.


```sh
$ echo hello world
hello world
```

```sh
$ for i in {1..10}:
	echo $i
# 1 2 3 4 5 6 7 8 9 10
```

Run `?` or `help` to show the available commands.

```sh
$ ?
# Documented commands (type help <topic>):
# ========================================
# E                 cat   example  flatten  help     map      range   shell  vi
```

Run `help print` to show the description of the command `print`.

```sh
$ help print
# Write to stdout
```

#### Command line interface

Alternative you can run the 

```sh
python3 -m examples.shell echo hello world
# hello world
```



## Queries

Mash allows you to explore data intuitively.

### Use directories

See [directories](directories.md)

### Query JSON data

```sh
python3 -m examples.queries
# Press ctrl-d to exit, ctrl-c to cancel, TAB for word completion, ? for help and ! for shell interop.
repository $
repository $ list
# documents
# users
```

Let's explore the `users` dataset.

```sh
repository $ list
# documents
# users
repository $ show users
# |      | email              | name   |
# |-----:|:-------------------|:-------|
# | 1000 | name.0@company.com | name_0 |
# | 1001 | name.1@company.com | name_1 |
# | 1002 | name.2@company.com | name_2 |
```

Let's explore some queries

1. List documents of each user

```sh
repository $ { users documents | users.id = documents.owner }
```

2. Find users that own a at least one document

```sh
repository $ { users documents | users.id = documents.owner } | select users.id users.name | uniq
```

3. Find users that own documents about animals

```sh
repository $ {users documents | document.title = "*animal*" | users.id in documents.owner} | select users.name documents.title
```



## Other examples

### Interactive operations dashboard

**Show available resources**

```sh
repository $ list
# dev test acc prod
respository $ cd dev
respository/dev $
respository/dev $ list
# vms
# apis
respository/dev $ show vms
# vm0001 vm0002 vm0003
```

**Check status**

```sh
respository/dev $ status vms
# |     id |      role |  cpu |
# |-------:|:----------|:-----|
# | vm0001 |    router |  15% |
# | vm0002 |  database | 100% |
```

**Restart components**

```sh
respository/dev $ restart vms vm0002
# restart request send to vm002
# waiting...
```



### Simple API explorer

...

### API Facade

This example shows a *façade* of a complex API. The façade simplifies interfacing with the API.

```sh
python3 -m examples.api_facade
# Press ctrl-d to exit, ctrl-c to cancel, TAB for word completion, ? for help and ! for shell interop.
```

Let's see which users exist. The debug output shows the intermediate API calls.

```sh
respository $ users
respository/users $ show
#  (debug) GET /users
#  (debug) GET /users/9998
#  (debug) GET /users/10000
# |    id |               email |      role |
# |------:|:--------------------|:----------|
# |  9998 | charles@company.com | developer |
# | 10000 |    dave@company.com |     admin |
```

**Create a new user**

```sh
respository/users $ create developer alice@company.com
# creating new user alice@company.com
#  (debug)  POST /users {"email": "alice@company.com"} returned {"id": 10001}
# assigning role developer to alice@company.com
#  (debug) POST /roles/developer {"id": 10001} returned "OK"
# sending notification
```

**Remove a user**

```sh
respository/users $ del bob@company.com
# preparing to remove bob@company.com 
# finding user id: 9998
# removing inventory of user id 9998
# removing roles of user id 9998
# removing attributes of user id 9998
# removing the user user id 9998
```

