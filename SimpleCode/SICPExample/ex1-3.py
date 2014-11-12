__author__ = 'Administrator'


def find_sum(*a):
    return sum(a)-min(a)


print find_sum(1,2,3)