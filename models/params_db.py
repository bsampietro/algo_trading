import json
import uuid

class ParamsDb:
    _instance = None

    # get_instance
    @classmethod
    def gi(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


    # Will be used for second part...
    @staticmethod
    def create_params_from_attributes(attrs):
        params = Params()
        # Performance variables
        for variable, value in attrs:
            setattr(params, variable, value)
        # Data variables
        params.id = attrs['id']
        params.average_pnl = attrs['average_pnl']
        params.nr_of_winners = attrs['nr_of_winners']
        params.nr_of_loosers = attrs['nr_of_loosers']
        return params


    @staticmethod
    def get_attributes_from_params(params):
        attrs = {}
        # Performance attributes
        for variable, value in vars(params).items():
            if variable[-8:] == '_options':
                performance_variable = variable.replace('_options', '')
                attrs[performance_variable] = getattr(params, performance_variable)
        # Data attributes
        if params.id is None:
            attrs['id'] = str(uuid.uuid4())
        else:
            attrs['id'] = params.id
        attrs['average_pnl'] = round(params.average_pnl, 2)
        attrs['nr_of_winners'] = params.nr_of_winners
        attrs['nr_of_loosers'] = params.nr_of_loosers
        return attrs


    def __init__(self):
        self.params_list = []
        self.changed = False


    def add(self, param):
        self.changed = True
        self.params_list.append(param)


    def save(self):
        if not self.changed:
            return
        with open('./data/params_list.json', 'w') as f:
            json.dump([type(self).get_attributes_from_params(p) for p in self.params_list], f, indent=4)
        self.changed = False


    def load(self):
        try:
            with open('./data/params_list.json', 'r') as f:
                params_attributes = json.load(f)
                self.params_list = [type(self).create_params_from_attributes(attrs) for attrs in params_attributes]
        except (JSONDecodeError, FileNotFoundError) as e:
            self.params_list = []
