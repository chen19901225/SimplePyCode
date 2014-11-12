from base.backend.task.task import datamanager as task_manager
from model.data import datamanager as data_manager


def load_fixtrue():
    print('-------------load_fixtrue--------------')


Fixtrue_Path_Data = '/opt/advert/source/model/data/fixtrue'
Fixtrue_Path_Task = '/opt/advert/source/model/task/fixtrue'

data_manager.load_fixtrue(Fixtrue_Path_Data)
task_manager.load_fixtrue(Fixtrue_Path_Task)