__author__ = 'Administrator'



condition=0.0000001

def find_lifa(x):
    guess=x/3.0
    try_time=1
    found=False
    while abs(guess**3-x)>=condition :
        try_time+=1
        guess=(float(x)/float(guess**2)+2*guess)/float(3)

    print 'try_time',try_time
    return guess


print find_lifa(9)
print find_lifa(8)
print find_lifa(27)
