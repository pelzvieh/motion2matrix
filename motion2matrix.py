#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
import asyncio
from motion2matrix.main import motion2matrixmain
if __name__ == '__main__':
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", '', sys.argv[0])
    asyncio.get_event_loop().run_until_complete(motion2matrixmain())

