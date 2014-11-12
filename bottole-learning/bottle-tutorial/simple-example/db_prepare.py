import datetime

__author__ = 'cqh'
import pymongo,functools

def get_collection(db_name='test',collection_name='test'):
    client=pymongo.Connection(host='127.0.0.1',port=27017)
    db_instance=client[db_name]
    collection_instance=db_instance[collection_name]
    return db_instance,collection_instance




def  data_insert():
    record_count=1000000
    local_db,local_collection=get_collection()
    if local_collection.count()>record_count/2:
        print "Record exists "
        return 
    for i  in xrange(record_count):
        local_collection.insert({"foo":"bar","baz":i,"z":10-i})

    print "Insert Over"

def count_time_wrapper(fn):
    @functools.wraps(fn)
    def fn_invoke():
        start_time=datetime.datetime.now()
        fn()
        end_time=datetime.datetime.now()
        print '{0} cost {1}'.format(fn.__name__,end_time-start_time)
    return fn_invoke

@count_time_wrapper
def datamoved1():
    local_db,local_collection=get_collection()
    local_collection.remove()
    local_collection.find_one()

@count_time_wrapper
def datamoved2():
    local_db,local_collection=get_collection()
    local_db.drop_collection('test')


if __name__=="__main__":
    #global datamoved1,datamoved2
    for drop_action in (datamoved1,datamoved2):
        data_insert()
        drop_action()
    print 'action over'






