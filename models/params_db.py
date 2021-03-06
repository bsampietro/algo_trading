import json
from json.decoder import JSONDecodeError

from models.params import Params
from lib import core

class ParamsDb:
    _instance = None

    # get_instance
    @classmethod
    def gi(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


    # To load
    @staticmethod
    def create_params_from_attributes(attrs):
        params = Params()
        # Performance variables
        for variable, value in attrs.items():
            setattr(params, variable, value)
        return params


    # To save
    @staticmethod
    def get_attributes_from_params(params):
        attrs = {}
        # Performance attributes
        for variable, value in vars(params).items():
            if variable[-8:] == '_options':
                performance_variable = variable.replace('_options', '')
                attrs[performance_variable] = getattr(params, performance_variable)
        attrs['results'] = params.results
        attrs['id'] = params.id
        return attrs


    def __init__(self):
        self.params_list = None
        self.changed = False
        self.next_id = None # type: int
        self.custom_params_file_name = "./output/custom_params.json"
        self.file_name = "./output/params_list.json"
        self.load()


    def get_params(self, id):
        return core.find(lambda p: p.id == id, self.params_list)


    def add_or_modify(self, param):
        assert param.last_result is not None
        if param.id is None:
            param.id = self.get_next_id()
            param.results.append(param.last_result)
            self.params_list.append(param)
            self.changed = True
        elif param.id < 0:
            pass # do not store with id < 0
        else:
            stored_param = core.find(lambda p: p.id == param.id, self.params_list)
            if stored_param:
                # modify
                last_result_key_data = (param.last_result['average_pnl'], param.last_result['underlying'])
                if not core.find(
                        lambda r: (r['average_pnl'], r['underlying']) == last_result_key_data,
                        stored_param.results):
                    stored_param.results.append(param.last_result)
                    self.changed = True


    def save(self):
        if not self.changed:
            return
        self.params_list = [prm for prm in self.params_list if prm.id > 0]
        self.params_list.sort(key=lambda p: p.id)
        with open(self.file_name, 'w') as f:
            json.dump([type(self).get_attributes_from_params(p) for p in self.params_list], f, indent=4)
        self.changed = False


    def load(self):
        try:
            self.params_list = []
            with open(self.custom_params_file_name, 'r') as f:
                self.params_list += [type(self).create_params_from_attributes(attrs) for attrs in json.load(f)]
            with open(self.file_name, 'r') as f:
                self.params_list += [type(self).create_params_from_attributes(attrs) for attrs in json.load(f)]
        except FileNotFoundError as e:
            self.params_list = []
        except JSONDecodeError as e:
            self.file_name += ".tmp"
            self.params_list = []


    def get_next_id(self):
        if self.next_id is None:
            if len(self.params_list) == 0:
                self.next_id = 0
            else:
                self.next_id = max(p.id for p in self.params_list)
                if self.next_id < 0:
                    self.next_id = 0
        self.next_id += 1
        return self.next_id