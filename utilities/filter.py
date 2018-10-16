import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import json

if __name__ == "__main__":
    args = sys.argv + 10 * [""]

    with open(args[1], 'r') as f:
        params = json.load(f)

    keep_params = []
    for prm in params:
        for result in prm['results']:
            if result['nr_of_winners'] + result['nr_of_loosers'] > 20:
                keep_params.append(prm)
                continue

    with open(args[1], 'w') as f:
        json.dump(keep_params, f, indent=4)