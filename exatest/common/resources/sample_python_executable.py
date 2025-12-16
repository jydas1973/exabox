#!/usr/bin/python3

import os
import sys
import uuid


def run_test():
    tmp_file = os.path.expanduser(f"/tmp/{uuid.uuid4()}_file_args.txt")
    with open(tmp_file, "w") as _f:
        for arg in sys.argv:
            _f.write(arg)
    os.system(f"chmod u+x {tmp_file}")
    print(tmp_file)

if __name__ == '__main__':
    run_test()
