#coding:utf-8


import unittest

class SelfConfigDict(dict):

    def __init__(self,*args,**kwargs):
        self._meta={}
        self._onchange=lambda  key,value:None
        if args or kwargs:
            self.update(*args,**kwargs)


    def update(self,*args,**kwargs):
        if args:
            try_prefix=args[0]
            assert isinstance(try_prefix,basestring),"Key必须为字符串 "
            prefix=try_prefix.strip('.')+'.'
            args=args[1:]
        for key,value in dict(*args,**kwargs):
            self[prefix+key]=value

    def __setitem__(self, key, value):
        assert isinstance(key,basestring),"Key必须为字符串"
        value=self._meta.get(key,{}).get('filter',lambda  x:x)(value)
        if key in self and self[key] is value :
            return
        self._onchange(key,value)
        dict.__setitem__(self,key,value)

    def load_dict(self,param_dict,prefix=''):
        for key,value in param_dict.items():
            prefix=prefix.strip('.')+'.'
            if isinstance(value,dict):
                self.load_dict(value,prefix+key)
            else:
                self[prefix+key]=value
    def meta_set(self,key,in_filter_name,in_filter_func):
        assert  isinstance(in_filter_name,basestring),in_filter_name+"必须为字符串"
        self._meta.setdefault(key,{}).setdefault(in_filter_name,in_filter_func)


#import Class-SelfConfigDict
class TestConfDict(unittest.TestCase):

    def test_isadict(self):
        """ SelfConfigDict should behaves like a normal dict. """
        # It is a dict-subclass, so this kind of pointless, but it doen't hurt.
        d, m = dict(), SelfConfigDict()
        d['key'], m['key'] = 'value', 'value'
        d['k2'], m['k2'] = 'v1', 'v1'
        d['k2'], m['k2'] = 'v2', 'v2'
        self.assertEqual(d.keys(), m.keys())
        self.assertEqual(list(d.values()), list(m.values()))
        self.assertEqual(d.get('key'), m.get('key'))
        self.assertEqual(d.get('cay'), m.get('cay'))
        self.assertEqual(list(iter(d)), list(iter(m)))
        self.assertEqual([k for k in d], [k for k in m])
        self.assertEqual(len(d), len(m))
        self.assertEqual('key' in d, 'key' in m)
        self.assertEqual('cay' in d, 'cay' in m)
        self.assertRaises(KeyError, lambda: m['cay'])

    def test_write(self):
        c = SelfConfigDict()
        c['key'] = 'value'
        self.assertEqual(c['key'], 'value')
        self.assertTrue('key' in c)
        c['key'] = 'value2'
        self.assertEqual(c['key'], 'value2')

    def test_update(self):
        c = SelfConfigDict()
        c['key'] = 'value'
        c.update(key='value2', key2='value3')
        self.assertEqual(c['key'], 'value2')
        self.assertEqual(c['key2'], 'value3')

    def test_namespaces(self):
        c = SelfConfigDict()
        c.update('a.b', key='value')
        self.assertEqual(c['a.b.key'], 'value')

    def test_meta(self):
        c = SelfConfigDict()
        c.meta_set('bool', 'filter', bool)
        c.meta_set('int', 'filter', int)
        c['bool'] = 'I am so true!'
        c['int']  = '6'
        self.assertTrue(c['bool'] is True)
        self.assertEqual(c['int'], 6)
        self.assertRaises(ValueError, lambda: c.update(int='not an int'))

    def test_load_dict(self):
        c = SelfConfigDict()
        d = dict(a=dict(b=dict(foo=5, bar=6), baz=7))
        c.load_dict(d)
        self.assertEqual(c['a.b.foo'], 5)
        self.assertEqual(c['a.b.bar'], 6)
        self.assertEqual(c['a.baz'], 7)

if __name__ == '__main__': #pragma: no cover
    unittest.main()

