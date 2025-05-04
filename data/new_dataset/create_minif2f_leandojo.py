
import json

minif2f_jsonl = 'data/miniF2F/minif2f.jsonl'
minif2f_imports_file = 'data/miniF2F/miniF2F_processed_imports.txt'

# def get_start_pos(file_name: str) -> int:
#     lookup = 'theorem '
#     with open(file_name) as file:
#         for num, line in enumerate(file, 1):
#             if lookup in line:
#                 return num
#     return num
#
# def get_end_pos(file_name: str) -> int:
#     return sum(1 for _ in open(file_name)) + 1

def get_imports() -> list[str]:
    file_name = 'data/miniF2F/miniF2F_processed_imports.txt'
    imports = []
    for line in open(file_name):
        if line.startswith('import '):
            stripped_line = line.split('import ')[1]
            stripped_line = stripped_line.strip('\n')
            file_path = '/'.join(stripped_line.split('.')) + '.lean'
            imports.append(file_path)
    return imports


valid_theorems = {}
with open('data/miniF2F/repo/Valid.lean', 'r') as f:
    theorem_name = ''
    code = ''
    for index, line in enumerate(f, 1):
        print(theorem_name)
        if 'theorem ' in line:
            theorem_name = line.split('theorem ')[1].split()[0]
            start_pos = index
        if line == '\n' and theorem_name:
            end_pos = index
            valid_theorems[theorem_name] = {'start_pos': start_pos, 'end_pos': end_pos}
            theorem_name = ''

    end_pos = index
    valid_theorems[theorem_name] = {'start_pos': start_pos, 'end_pos': end_pos}

test_theorems = {}
with open('data/miniF2F/repo/Test.lean', 'r') as f:
    theorem_name = ''
    for index, line in enumerate(f, 1):
        if 'theorem ' in line:
            theorem_name = line.split('theorem ')[1].split()[0]
            start_pos = index
        if line == '\n' and theorem_name:
            end_pos = index
            test_theorems[theorem_name] = {'start_pos': start_pos, 'end_pos': end_pos}
            theorem_name = ''

    end_pos = index
    test_theorems[theorem_name] = {'start_pos': start_pos, 'end_pos': end_pos}


print(valid_theorems)
print(test_theorems)

# def create_leandojo_dict(theorem_dict: dict, file_name: str, split: str) -> dict:
#     return {
#         "path": "MiniF2F/Test.lean" if split == 'test' else "MiniF2F/Valid.lean",
#         "imports": get_imports(file_name),
#         "premises": [
#                         {
#                             "full_name": theorem_dict['name'],
#                             "code": theorem_dict['formal_statement'],
#                             "start": [get_start_pos(file_name), 1],
#                             "end": [get_end_pos(file_name), 1],
#                             "kind": "commanddeclaration"
#                         }
#
#         ]
#     }


def create_leandojo_dict(file_name: str, premise_list: list) -> dict:
    return {
        "path": file_name,
        "imports": get_imports(),
        "premises": premise_list
    }

def get_premise_dict(thm_dict: dict, split: str) -> dict:
    start_p = valid_theorems[thm_dict['name']]['start_pos'] if split == 'valid' else test_theorems[thm_dict['name']]['start_pos']
    end_p = valid_theorems[thm_dict['name']]['end_pos'] if split == 'valid' else test_theorems[thm_dict['name']]['end_pos']

    return  {
                            "full_name": thm_dict['name'],
                            "code": thm_dict['formal_statement'],
                            "start": [start_p, 1],
                            "end": [end_p, 1],
                            "kind": "commanddeclaration"
                        }

print('.................................................')
print(test_theorems['numbertheory_notEquiv2i2jasqbsqdiv8'])

final_json_list = []
premises_list_valid = []
premises_list_test = []
for line in open(minif2f_jsonl, 'r', encoding='utf-8'):
    theorem_dict = json.loads(line)
    theorem_name = theorem_dict['name']
    if theorem_dict['split'] == 'valid':
        premises_list_valid.append(get_premise_dict(theorem_dict, 'valid'))
    else:
        premises_list_test.append(get_premise_dict(theorem_dict, 'test'))

final_json_list.append(create_leandojo_dict("MiniF2F/Valid.lean", premises_list_valid))
final_json_list.append(create_leandojo_dict("MiniF2F/Test.lean", premises_list_test))

mathlib_corpus_path = 'data/leandojo_benchmark_4/corpus.jsonl'

mathlib_corpus = {}
with open(mathlib_corpus_path) as file:
    for line in file:
        file_dict = json.loads(line)
        mathlib_corpus[file_dict['path']] = file_dict

all_dependencies = []

def trace_import_dependencies(path: str) -> None:
    path_imports = mathlib_corpus[path]['imports']

    for path_import in path_imports:
        if path_import not in all_dependencies:
            trace_import_dependencies(path_import)
            print('Path import: ', path_import, len(all_dependencies))
            all_dependencies.append(path_import)



for path in get_imports():
    print(f'Getting dependencies for import: {path}')
    trace_import_dependencies(path)
    if path not in all_dependencies:
        all_dependencies.append(path)


path_dicts_dependencies = [mathlib_corpus[path] for path in all_dependencies]



final_jsonl_name = 'data/miniF2F/miniF2F-leandojo2.jsonl'
with open(final_jsonl_name, 'w') as file:
    for path_dict in path_dicts_dependencies:
        file.write(json.dumps(path_dict))
        file.write('\n')

    for theorem_json in final_json_list:
        file.write(json.dumps(theorem_json))
        file.write('\n')

