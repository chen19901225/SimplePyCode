import re

import heapq


url="delemploreylist?ids=\[1\]"

print re.match("delemploreylist\?ids=(?P<ids>\[[^\]]+\])",url)