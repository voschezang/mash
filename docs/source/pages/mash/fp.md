# Functional Programming

This means:

- Reliable code, due to pure functions, immutable data & strong static typing.
- Performant code. Easy to parallelize, safe concurrency. Lazy evaluation by default.



Downsides

- Strong typing requires type definitions -> less intuitive
- Type inference -> additional complexity



Requirements

- REPL without needing type definitions
- Read directories & json data



**Roadmap**

- [ ] Implement commands & variables.
- [ ] Implement datatypes: `lists, records`
  - [ ] Update syntax for records.

- [ ] Implement pipes.
  - [ ] Implement list filters.

- [ ] Support multiline syntax by using a token preprocessor that groups indented blocks and drops newlines inside braces.
  - [ ]  Implement multiline if-conditions
- [ ] Implement for-loops.
- [ ] Implement user-defined functions.
  - [ ]  Implement pipes & streaming.
- [ ] Optimize...

[toc]

## Syntax

### Commands & Directories

```sh
cd users  # enter directory "users"
print "hello world"  # display text on screen
```

### Pipes

With single values

```sh
f $x | g | h  # function composition
```

With streams.

```sh
tail myfile.log | grep admin | uniq  # search in end of logfile
```

### Variables

```sh
x = 10
print $x  # expanded to "print 10"
```

### Datastructures

```python
int, float, list, map
```

#### Mappings

```sh
initial = { x = 10, y = 20 }  # C-style records
updated = { initial | x = 1000 }  # use a record with an updated value on left-hand side
```

#### Lists

```sh
x = [1, 2] + [3, 4]  # x: [1, 2, 3, 4]
y = $x + [5]  # y: = [1, 2, 3, 4, 5]
```

List comprehensions

```sh
x = [ "number: $i" for i in {1..4} ]
```

Joins, streams and filters

```sh
# for each user, find documents with the same id
# SELECT * FROM users, documents WHERE users.id == documents.id
x = [ users documents |> users.id == documents.id ]

# add more filters
x = [ users documents |> users.id == documents.id
                      |> users.owner == '[aA]*'
                      |> users.age > 25 ]
# add more filters
x = [ users documents |> users.id == documents.id,
                         users.owner == '[aA]*',
                         users.age > 25 ]
```

Streaming

```sh
data = {1..10000} # list of numbers
data |> "even" if $ % 2 == 0 else "odd"
		 |> uniq  # reduce
		 | sort
cat data >>= "even" if $ % 2 == 0 else "odd"
		 >>= uniq  # reduce
		 | sort
```

Pipes are used for both function compositions and streaming.

### Pattern Matching

```python
a, b, c = 10, 20, 30
head, *tail = 10, 20, 30  # Python-style unpacking
head, *tail = {1..100}
head, *_ = {1..100}
#[ a | _ ] = {1..3}  # head and tail
#[ x | _ ] = get_users  # x is the first users
#[ x | X ] = get_users  # X will contain the rest of the users
match name:
  first, middle, last ->
	    set firstname $first
      set middlename $middle
      set lastname $last
  first, last ->
      set firstname  $first
      set lastname $last
  _ ->
      fail "first or last name missing"
```

### Conditions & Loops

If-statements

```python
# oneline
x = 1 if 2 > 2 else 3
# multiline
if $x > 2:
    result = "high"
else if	$x == 2:
    result = "equal"
else
    result = "low"
```

For-loops

```python
for x in $X:
    print $x
```

User-defined functions - with/without type inference?

```elm
add (a b):
    return $a + $b

map : (a -> b) -> List a -> List b
map ( f items ):
    return [ f $x for x in items ]
```

Type Aliasses?

```haskell
type Money = Euro | Dollar
type alias Model = { vars : Map
										 funs : List[Callable[Model -> Model]]
										}
```

## DSL

```sh
f ():
    # use a stream
		for line in $(cat):
				print $line

f ( x, y ):
    ...

f ( x ):
    # handle multiple arguments
    match $x:
    		x, y, z ->
    		    print $x + $y * $z
    		x, y ->
    				print $x * $y
    		x ->
    				print $x
    if args:
        print $args
    else:  # emtpy list/tuple
        print "no arguments given"

f ( *items ):
    # handle a list (stream) of items
    for item in items:
        print $item
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



