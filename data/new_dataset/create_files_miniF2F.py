import json

minif2f_jsonl = 'data/miniF2F/minif2f.jsonl'
minif2f_imports_file = 'data/miniF2F/miniF2F_processed_imports.txt'

with open(minif2f_imports_file, 'r', encoding='utf-8') as file:
    minif2f_imports = file.read()

for line in open(minif2f_jsonl, 'r', encoding='utf-8'):
    theorem_dict = json.loads(line)
    theorem_name = theorem_dict['name']
    file_name = f'data/new_dataset/miniF2F_single_files/{theorem_dict["split"]}/{theorem_name}.lean'

    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(minif2f_imports)
        file.write('\n')
        file.write(theorem_dict['informal_prefix'])
        file.write('\n')
        file.write(theorem_dict['formal_statement'])
