
import collections

Person=collections.namedtuple('Person','name age gender')

print 'Type of Person:',type(Person)

bob=Person(name='Bob',age=30,gender='male')
print '\n Representation:',bob

jane=Person(name='Jane',age=29,gender='female')




