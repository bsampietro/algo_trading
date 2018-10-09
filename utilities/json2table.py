import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import json
from lib import html


if __name__ == "__main__":
    args = sys.argv + 10 * [""]
    append_filename = ""

    params = []
    
    with open(args[1], 'r') as f:
        params = json.load(f)

    if args[3] != "":
        new_params = []
        for param in params:
            ids = [int(id) for id in args[3].split(',')]
            if param['id'] in ids:
                new_params.append(param)
        params = new_params
        append_filename += "_sids"

    params.sort(key=lambda p: p['results'][0]['average_pnl'], reverse=True)

    with open(f"/media/ramd/table_{args[2]}{append_filename}.html", "w") as f:
        keys = []
        row = []
        rows = []
        header_created = False
        for param in params:
            if args[2] not in param['results'][0]['underlying']:
                continue
            for k, v in param.items():
                if k == 'results':
                    if not header_created:
                        keys += [k1 for k1, v1 in v[0].items()]
                    row += [v1 for k1, v1 in v[0].items()]
                else:
                    if not header_created:
                        keys.append(k)
                    row.append(v)
            # rows.append(list(param.values()))

            rows.append(row)
            row = []
            header_created = True
        
        for row in rows:
            for i in range(len(row)):
                if isinstance(row[i], float):
                    row[i] = round(row[i], 2)

        # keys = list(params[0].keys())
        for i in range(len(keys)):
            keys[i] = keys[i].replace("_", "\n")
        f.write(html.table(rows, header_row=keys,
            style="border: 1px solid #000000; border-collapse: collapse; font: 12px arial, sans-serif;"))