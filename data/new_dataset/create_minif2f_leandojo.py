
import json

minif2f_jsonl = 'data/miniF2F/minif2f.jsonl'
minif2f_imports_file = 'data/miniF2F/miniF2F_processed_imports.txt'

def get_start_pos(file_name: str) -> int:
    lookup = 'theorem '
    with open(file_name) as file:
        for num, line in enumerate(file, 1):
            if lookup in line:
                return num
    return num

def get_end_pos(file_name: str) -> int:
    return sum(1 for _ in open(file_name)) + 1

def get_imports(file_name: str) -> list[str]:
    imports = []
    for line in open(file_name):
        if line.startswith('import '):
            stripped_line = line.split('import ')[1]
            stripped_line = stripped_line.strip('\n')
            imports.append(stripped_line)
    return imports

def create_leandojo_dict(theorem_dict: dict, file_name: str) -> dict:
    return {
        "path": file_name,
        "imports": get_imports(file_name),
        "premises": [
                        {
                            "full_name": theorem_dict['name'],
                            "code": theorem_dict['formal_statement'],
                            "start": [get_start_pos(file_name), 1],
                            "end": [get_end_pos(file_name), 1],
                            "kind": "commanddeclaration"
                        }

        ]
    }

final_json_list = []
for line in open(minif2f_jsonl, 'r', encoding='utf-8'):
    theorem_dict = json.loads(line)
    theorem_name = theorem_dict['name']
    single_file_name = f'data/new_dataset/miniF2F_single_files/{theorem_dict["split"]}/{theorem_name}.lean'
    final_json_list.append(create_leandojo_dict(theorem_dict, single_file_name))

final_jsonl_name = 'data/miniF2F/miniF2F-leandojo.jsonl'
with open(final_jsonl_name, 'w') as file:
    for theorem_json in final_json_list:
        file.write(json.dumps(theorem_json))
        file.write('\n')

