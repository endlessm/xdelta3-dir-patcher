xdelta3-dir-patcher
===================

### Usage
```
usage: xdelta3-dir-patcher [-h] [--debug] [--version] {apply,diff} ...

Creates and applies XDelta3-based directory diff tgz files

positional arguments:
  {apply,diff}
    apply       Apply a diff from a directory. See "apply -help" for more
                options
    diff        Generate a diff from a directory. See "diff -help" for more
                options

optional arguments:
  -h, --help    show this help message and exit
  --debug       Enable debugging output
  --version     show program's version number and exit

```

### Running tests
- Unittest builtin
```
python -m unittest discover
```

- Nosetests (requires nosetests module)
```
nosetests
```
