

import sys
print 'all args',sys.argv
if len(sys.argv)<2:
    print 'No arguments'
    exit(0)
elif     len(sys.argv)%2==0:
    print 'arguments not matched'
    exit(0)
else:
    start=1
    for  index,value in enumerate(sys.argv[start::2]):
        print sys.argv[start+2*index:start+2*index+2]
    print 'OK!'
