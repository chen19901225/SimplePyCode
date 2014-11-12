import inspect

__author__ = 'Administrator'

def example(a,b=1,*c,**f):
    pass



def get_arguments(func,args,kwargs):
    argsments=kwargs.copy()
    spec=inspect.getargspec(func)
    argsments.update(zip(spec.args,args))

    if spec.defaults:
        for i,name in enumerate(spec.args[-len(spec.defaults):]):
            if name not in argsments:
                argsments[name]=spec.defaults[i]

    return argsments



def validate_arguments(func,args,kwargs):
    arguments=get_arguments(func,args,kwargs)
    spec=inspect.getargspec(func)
    declared_args=spec.args[:]





if __name__=="__main__":
    get_arguments(example,(1,),{'f':4})