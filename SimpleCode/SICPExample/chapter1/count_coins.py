__author__ = 'Administrator'





coin_list=[1,5,10,25,50]
coin_list.sort(reverse=True)

"""
总结：这个我之前想的有问题：
比如：
在做cache_count的时候，我把key仅仅跟max_count有关了，
事实上，key不仅跟max_count有关，还跟要使用的硬币有关。
"""





def count_coins(max_count,coin_list):
    cache_count={0:1}
    indent=0
    len_list=len(coin_list)
    def fast_count(max_count,index,indent=indent):
        print  " "*4*indent+"Count  Value:"+str(max_count)
        dict_key="%s_%s"%(max_count,index)
        if dict_key in cache_count:
            return cache_count[dict_key]
        else:
            if max_count<0:
                return 0
            if max_count==0:
                cache_count[dict_key]=1
                return 1

            if  index>=len_list:
                return 0
            cache_count[dict_key]=sum(fast_count(max_count-coin,for_index+index,indent+1) for for_index,coin in enumerate(coin_list[index:]))
            return cache_count[dict_key]
            sum_result=0
            for coin in coin_list:
                if coin>max_count:
                    break
                else:
                    sum_result+=fast_count(max_count-coin,indent+1)

            cache_count[max_count]=sum_result
            return sum_result


    return fast_count(max_count,0),cache_count

count_value,cache_dict= count_coins(100,coin_list)
print count_value
