__author__ = 'Administrator'
#coding=utf-8
def power(a,b,max_num=10**8):
    if b==1:
        return a%max_num
    else :
        return (a*a,b-1,max_num)
if __name__=="__main__":
    one_yi=10**8
    num_list=[2,3,4]
    firstnum=5
    for num in num_list[::-1]:
        firstnum=pow(num,firstnum,one_yi)
        print firstnum
    print firstnum,"End"

