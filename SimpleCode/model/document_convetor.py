import json

from mongokit import Document
from mongokit.document import DocumentProperties
from bson.objectid import ObjectId

from model.data.datamanager import *
#from model.task.datamanager import *
from model.data.datamanager import *


class DocumentConvetor:

    def __init__(self, documents = {}, level = 10):
        self.documents = documents
        self.__level__ = level

    def __map_documents_id(self, _documents):
        dic_ids = {}

        def wrap_ids(document, structure, _dic_ids):

            if issubclass(type(document), Document):
                for key, value in document.items():

                    if key == '_id' :
                        continue

                    if key not in document.structure:
                        continue

                    key_class = None

                    if isinstance(value, list):
                        key_class = document.structure[key][0]
                    else:
                        key_class = document.structure[key]

                    result = []

                    if isinstance(key_class, DocumentProperties):

                        if isinstance(value, list):
                            for i in value:
                                if isinstance(i, ObjectId):
                                    result.append(i)
                        else:
                            if isinstance(value, ObjectId):
                                    result.append(value)
                    else:
                        continue

                    if _dic_ids.has_key(key_class):
                        _dic_ids[key_class].extend(result)
                    else:
                        _dic_ids[key_class] = result

        def wrap_documents(in_documents, in_dic_ids):
            for key, value in in_documents.items():
                if isinstance(value, list):
                    for i in value:
                        if isinstance(i, Document):
                            wrap_ids(i, i.structure, in_dic_ids)

                elif isinstance(value, Document):
                    wrap_ids(value, value.structure, in_dic_ids)

        db_documents = []

        for number in range(0, self.__level__):
            #print('__level__  ', number)

            result = {}

            if len(db_documents) == 0:
                wrap_documents(self.documents, result)
            else:
                wrap_documents({'items': db_documents}, result)

            managers = {}

            for class_type, object_id in result.items():
                db_documents = []

                object_ids = object_id

                if not isinstance(object_ids, list):
                    object_ids = [object_id]

                if not managers.has_key(class_type):
                    managers[class_type] = []

                managers[class_type].extend(object_ids)

            for class_type, object_ids in managers.items():
                # print(object_ids)
                if len(object_ids) == 0:
                    continue

                manager = eval(class_type().manager)()
                db_objects = manager.get_by_ids(object_ids)
                db_documents.extend([i for i in db_objects])

            if len(result.items()) == 0:
                break

            for class_type, object_id in result.items():
                if not dic_ids.has_key(class_type):
                    dic_ids[class_type] = set()
                    # set().add()

                if dic_ids.has_key(class_type):
                    if isinstance(object_id, list):
                        for i in object_id:
                            dic_ids[class_type].add(i)
                    else:
                        dic_ids[class_type].add(object_id)

        return dic_ids

    def __fetch_data_from_mapping(self, _mapping):
        data = {}

        for key, value in _mapping.items():
            if len(value) == 0:
                continue

            manager = eval(key().manager)()

            items = manager.get_by_ids(list(value))
            data[key] = [json.loads(i.to_json()) for i in items]

        data_flat = {}

        for key, values in data.items():
            for i in values:
                data_flat[i['_id']['$oid']] = i

        return data_flat

    def __make_dict_by_data(self, _documents, _data_mapping):
        result = {}

        def wrap_document(document, data_mapping):
            _result = {}

            if isinstance(document, Document):
                _result = json.loads(document.to_json())
            else:
                _result = document

            for key, value in _result.items():

                if isinstance(_result[key], dict) and key != '_id' and len(_result[key].items()) == 1 and \
                        _result[key].has_key('$oid') and data_mapping.has_key(_result[key]['$oid']):
                    _result[key] = data_mapping[_result[key]['$oid']]

                    wrap_document(_result[key], data_mapping)

                elif isinstance(_result[key], list):
                    items = []

                    for i in _result[key]:
                        if isinstance(i, dict) and i.has_key('$oid') and data_mapping.has_key(i['$oid']):
                            items.append(data_mapping[i['$oid']])

                            wrap_document(data_mapping[i['$oid']], data_mapping)
                        else:
                            items.append(i)



                    _result[key] = items

            return _result

        for key, value in _documents.items():
            if isinstance(value, list):
                result[key] = []

                for i in value:
                    result[key].append(wrap_document(i, _data_mapping))
            else:
                result[key] = wrap_document(value, _data_mapping)

        return result

    def to_dict(self):
        mapping_ids = self.__map_documents_id(self.documents)
        data_mapping = self.__fetch_data_from_mapping(mapping_ids)

        return self.__make_dict_by_data(self.documents, data_mapping)

    def add_documents(self, items = {}):
        for key, value in items.items():
            if self.documents.has_key(key):
                if isinstance(self.documents[key], list):
                    self.documents[key].append(value)
                else:
                    self.documents[key] = [value]
            else:
                self.documents[key] = value
