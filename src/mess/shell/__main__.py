#!/usr/bin/python3
import sys
if __name__ == '__main__':
    sys.path.append('src')
    sys.path.append('src/shell')
    import shell

    from .shell import main

    main()
