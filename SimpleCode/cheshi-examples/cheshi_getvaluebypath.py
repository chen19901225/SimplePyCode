import utils

__author__ = 'Administrator'


import unittest

class GetValueByPath(unittest.TestCase):

    def test_findbyattr(self):

        value1={"a":"chenqinghe","b":"XXX"}

        self.assertEqual("chenqinghe",utils.get_value_by_search_path(value1,"a"))
        self.assertEqual("XXX",utils.get_value_by_search_path(value1,"b"))

   def test_findbyCondition(self):
      d1={"name":1,"value":11}
      d2={"name":2,"value":22}
      d3={"name":3,"value":33}
      d4={"name":"4","value":44}
      l1=[d1,d2,d3,d4]
      self.assertEqual(d1,utils.get_value_by_search_path(l1,"[name=1]"))
      self.assertEqual(d3,utils.get_value_by_search_path(l1,"[name=3]"))
      self.assertEqual(d4,utils.get_value_by_search_path(l1,'[name="4"]'))

if __name__=="__main__":
    unittest.main()





