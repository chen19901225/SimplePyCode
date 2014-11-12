__author__ = 'Administrator'
import string
class ModelField(object):
    def validate(self):
        success_obj=True
        for key,value in self.__dict__.iteritems():
            if not key.endswith('error'):
                success_obj=value.validate()
                if not success_obj:
                    break
        return success_obj
