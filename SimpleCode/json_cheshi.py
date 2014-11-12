
import json
class Person(object):
    def __init__(self):
        self.name="abc"

if __name__=="__main__":
    person=Person()
    data=dict(person_obj=person,age=20,gender="fermal")
    print  json.dumps(data)