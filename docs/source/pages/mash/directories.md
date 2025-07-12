# Directories

This page uses the following example.

```sh
cd src
python3 -m examples.query_json_data
# Press ctrl-d to exit, ctrl-c to cancel, TAB for word completion, ? for help and ! for shell interop.
$ 
```



## Change directories

Run `cd` or simply run the directory name as a command.

```sh
repository $ users 1000 # go to user with id 1000 
repository/users/1000 $
```

Use `TAB` for autocompletion. If no matching filename is found the nearest match is selected.

Make sure to use `cd` if directory is shadowed by a function.



## Show directory contents

Run `list` or simply double-tab `TAB` to display the directory contents.

```sh
repository $ list # list ids in resource
users
documents
...
```

```sh
repository $ list users # list ids in resource
1000
1001
...
```

Run `show` to display the directory contents as a table.

```sh
repository $ cd users 1000
repository/users/1000 $ show
| keys   | values             |
|:-------|:-------------------|
| email  | name.0@company.com |
| name   | name_0             |
```

Run `tree` to show directory hierarchies.

```sh
repository $ tree
{ 'documents': { 0: '500 INTERNAL SERVER ERROR (500)',
                 1: '500 INTERNAL SERVER ERROR (500)',
                 ...
  'users': { 1000: {'email': 'name.0@company.com', 'name': 'name_0'},
             1001: {'email': 'name.1@company.com', 'name': 'name_1'},
             ...
```



## Edit directories

```sh
# remove a variable
env/variables $ del x
```





## Other directories

Directories are used to browse folders, files, APIs and even the environment itself.

```sh
$ list env
repository
variables
$ cd env variables
env/variables $ show
| keys | values |
|:-----|:-------|
|    a |     10 |
|    b |     20 |
```





