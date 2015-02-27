xdelta3-dir-patcher
===================

This script is a tool for generating and applying recursive XDelta3 diffs from sources in various forms (zip, tgz, folder) since no tool exists to do this efficiently right now. The code was written with portability in mind so its in Python3 and contained in one script (even though it makes developments a bit tricky). While the code has decent tests and robust QA process, it was developed for a very specific use case and should be treated as alpha software but it's open source so feel free to open pull requests for it.

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

### License
MIT

### Running tests
- Prerequisites:
 - python3-nose
 - python3-mock

- Unittest builtin
```
python3 -m unittest discover
```

- Nosetests (requires prerequisite modules/packages)
```
nosetests3
```

© 2014-2015 Endless Mobile
