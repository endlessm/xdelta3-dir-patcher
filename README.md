xdelta3-dir-patcher
===================

This script is a tool for generating and applying recursive XDelta3 diffs from sources in various forms (zip, tgz, folder) since no tool exists to do this efficiently right now. The code was written with portability in mind so its in Python3 and contained in one script (even though it makes developments a bit tricky). While the code has decent tests and robust QA process, it was developed for a very specific use case and should be treated as alpha software but it's open source so feel free to open pull requests for it.

### Usage
```
usage: xdelta3-dir-patcher [-h] [-s [STAGING_DIR]] [--debug] [--verbose]
                           [--version]
                           {apply,diff} ...

Creates and applies XDelta3-based directory diff archive files

positional arguments:
  {apply,diff}
    apply               Apply a diff from a directory. See "apply -help" for
                        more options
    diff                Generate a diff from directories/files. See "diff
                        -help" for more options

optional arguments:
  -h, --help            show this help message and exit
  -s [STAGING_DIR], --staging-dir [STAGING_DIR]
                        Use this directory for all staging output of this
                        program. Defaults to /tmp.
  --debug               Enable debugging output
  --verbose             Enable extremely verbose debugging output
  --version             show program's version number and exit
```

### License
LGPL v2.1

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
