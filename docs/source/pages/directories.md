# Directories

## Change directories

Run `cd` or simply run the directory name as a command.

```sh
repository $ users 1000 # go to user with id 1000 
repository/users/1000 $
```

Use `TAB` for autocompletion. If no matching filename is found the nearest match is selected.

Make sure to use `cd` if directory is shadowed by a function.

## Show directory contents

Run `show` or simply double-tab `TAB`.

```sh
repository/users/1000 $ show
| keys   | values             |
|:-------|:-------------------|
| email  | name.0@company.com |
| name   | name_0             |
```

Alternatively use `list` for a short listing.

```sh
repository/users $ list # list ids in resource
1000
1001
```

```sh
repository/users/1000 $ list # list fields in resource
email
name
```
