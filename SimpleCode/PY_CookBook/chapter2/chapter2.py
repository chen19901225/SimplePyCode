import re

NAME=r'(?P<NAME>[a-zA-Z_][a-zA-Z_0-9])'
NUM=r'(?P<NUM>\d+)'
PLUS=r'(?P<PLUS>\+)'
TIMES=r'(?P<TIMES>\*)'
EQ=r'(?P<EQ>=)'
WS=r'(?P<WS>\s+)'

master_pat=re.compile('|'.join([NAME,NUM,PLUS,TIMES,EQ,WS]))

if __name__=="__main__":
    scanner=master_pat.scanner('foo=42')
    scanner.matcher()

