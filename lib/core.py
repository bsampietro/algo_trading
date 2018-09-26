def find(f, seq):
    for item in seq:
        if f(item): 
            return item

def index(f, seq):
    for index, item in enumerate(seq):
        if f(item): 
            return index

def safe_execute(default, exception, function, *args):
    try:
        return function(*args)
    except exception:
        return default