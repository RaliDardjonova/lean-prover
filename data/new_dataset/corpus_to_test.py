
import json

minif2f_jsonl_leandojo = 'data/miniF2F/miniF2F-leandojo.jsonl'

def create_test_dict(corpus_theorem: dict, path: str) -> dict:


    return {
        "url": "https://github.com/yangky11/miniF2F-lean4",
        "commit": "eddb5ca1fa7dea7268d3feabd7e6fd451b5ef3dd",
        "file_path": path,
        "full_name": corpus_theorem['full_name'],
        "start": corpus_theorem['start'],
        "end": corpus_theorem['end'],
        "traced_tactics": []
    }

def get_dataset_type(path: str) -> str:
    return path.split('/')[3]

test_dataset = []
valid_dataset = []
for line in open(minif2f_jsonl_leandojo, 'r', encoding='utf-8'):
    file_dict = json.loads(line)
    path = file_dict['path']
    for theorem in file_dict['premises']:
        eval_dict = create_test_dict(theorem, path)
        if get_dataset_type(path) == 'test':
            test_dataset.append(eval_dict)
        else:
            valid_dataset.append(eval_dict)


test_dataset_file_name = 'data/miniF2F/datasets/test.json'
with open(test_dataset_file_name, 'w') as file:
    json.dump(test_dataset, file)

valid_dataset_file_name = 'data/miniF2F/datasets/valid.json'
with open(valid_dataset_file_name, 'w') as file:
    json.dump(valid_dataset, file)

