__author__ = 'Administrator'



def func_1(n):
    """
     ex 1.11
    """
    if n<3:
        return n
    else:
        return func_1(n-1)+2*func_1(n-2)+3*func_1(n-3)


#print func_1(1)
#print func_1(2)
#print func_1(3)
#print func_1(4)



def func_12(n):
    """
    example 1.12
    """
    know_dict={1:[1]}
    def fast_pas_func(the_n_row):
        if the_n_row in know_dict:
            return know_dict[the_n_row]
        else:
            prev_row_list=fast_pas_func(the_n_row-1)
            new_row_list=[1]
            for walk_index,walk_item in enumerate(prev_row_list[:-1]):
                new_row_list.append(walk_item+prev_row_list[walk_index+1])
            new_row_list.append(1)
            know_dict[the_n_row]=new_row_list
            return new_row_list
    return fast_pas_func(n)
#for  n in range(5):
    #print func_12(n+1)





def func_16(a,n,pow_number):

    def fast_calculate(pow_number):
        if pow_number==0:
            return 1
        elif pow_number%2:
            return fast_calculate(pow_number-1)*n
        else:
            result_num=1
            for  i in xrange(pow_number/2):
                result_num*=n*n
            return result_num
    return a*fast_calculate(pow_number)


#print func_16(1,2,3)
#print func_16(2,2,3)
#print func_16(1,2,4)





def func_17_multi(a,b):
    def mul_ti(a,b):
        if b==0:
            return 0
        else:
            return a+mul_ti(a,b-1)

    def double(a):
        return a+a
    def halve(a):
        return a/2

    def fast_expt(a,b):
        if b==0:
            return 0
        if double(halve(b)) !=b:
            return a+fast_expt(a,b-1)
        else:
            return fast_expt(double(a),halve(b))
    return fast_expt(a,b)

print func_17_multi(2,5)
print func_17_multi(3,5)
print func_17_multi(4,5)


def func_18(a,b):
    def double(a):
        return a+a
    def halve(a):
        return a/2

    def fast_exp(a,b):
        if b==0:
            return 0
        elif b%2==1:
            return fast_exp(a,b-1)+a
        else:
            return fast_exp(double(a),halve(b))






