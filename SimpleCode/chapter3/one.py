
class API(object):
    def _print_values(self,obj):
        def _print_value(key):
            if key.startswith('_'):
                return ''
            value=getattr(obj,key)
            if not hasattr(value,'im_func'):
                doc=type(value).__name__
            else:
                if value.__doc__ is None:
                    doc="no docstring"
                else:
                    doc=value.__doc__
            return '%s:%s'%(key,doc)
        res=[_print_value(el) for el in dir(obj)]
        return '\n'.join([ el for el in res if el!=''])
    def __get__(self,instance,klass):
        if instance is not None:
            return self._print_values(instance)
        else:
            return self._print_values(klass)
class MyClass(object):
    __doc__=API()
    def __init__(self):
        self.a=2
    def meth(self):
        """ my method"""
        return 1




if __name__=="__main__":
   print  MyClass.__doc__

   instance=MyClass()
   print instance.__doc__
   print 12*60*60*300