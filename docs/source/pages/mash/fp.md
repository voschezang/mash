# Functional Programming

This means:

- Reliable code, due to pure functions, immutable data & strong static typing.
- Performance code. Easy to parallelize, safe concurrency. Lazy evaluation by default.



[toc]

## Syntax

### Primitive Datatypes

```python
int, float, list, map, set
```

### Pipes

```sh
f x | g | h
map (+1) x | (*2)
```

### Pattern Matching

```python
a, b, c = 10, 20, 30
a, _ = {1..3} # head and tail
[ x | _ ] = get_users() # x is the first users
[ x | X ] = get_users() # X will containt the rest of the users
```

### List Comprehensions

```sh
x = [ $i for $i in {1..4} ]
```

### Set Comprehensions

Filters are applied in series, lazily.

```sh
# for each user, find documents with the same id
# SELECT * FROM users, documents WHERE users.id == documents.id
x = { users documents || users.id == documents.id }

# extend filter, limit search to users with 
x = { users documents || users.id == documents*.id,
                         users.owner == '[aA]*',
                         users.age > 25 }
```

### Maps / Records

```sh
initial = {x = 10, y = 20}
updated = { initial | x = 1000 }
```

### Conditions & Loops

```python
# oneline
x = 1 if 2 > 2 else 3
# multiline
if $x > 2:
  print "high"
else
 print "low"
```



```python
for $x in $X:
 …

```



### Type Aliasses?

```haskell
type Money = Euro | Dollar
type alias Model = { vars : Map
										 funs : List[Callable[Model -> Model]]
										}
```





## Implementation

Mutation is handled through a data model. I.e. your environment. In the REPL, each line replaces the model.

```sh
$ x, y = 10, 20
$ x = 1000
# env: {'x': 1000, 'y': 20}
```

Side effects are handled in between updates of the model.





## MVC (elm)

Model view controller.

- View displays the page, based on the `model`.
- Update takes in a `msg` and uses it to update the `model`.



```elm
type Msg
    = PickFile
    | GotFile File
    | ReadFile (Result File.Error String)

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    ...
    -- print ~ side effect
    out = { model | out = model.out + "hello world" }
    return ()

view : Model -> Html Msg
view model =
```





## Lexer

```
x = 5 + 3
[ LetTok, IdentTok "x", EqualsTok, IntTok 5, PlusTok, IntTok 3 ]
```



```
lexer : String -> List Token
lexer str =
    ...
    
type Token
    = LetTok
    | IdentTok String
    | IntTok Int
    | PlusTok
    | EqualsTok
```



