import json
import random

DATA_SET_SIZE = 244
minif2f_jsonl = 'data/miniF2F/minif2f.jsonl'

def write_lean_dojo_dataset_to_file(new_dataset: list[dict]) -> None:
    file_name = f'data/miniF2F/sampled_datasets/lean_dojo_{len(new_dataset)}.json'
    with open(file_name, 'w') as f:
        json.dump(new_dataset, f)

def write_deepseek_dataset_to_file(new_dataset: list[dict]) -> None:
    file_name = f'data/miniF2F/sampled_datasets/deepseek_{len(new_dataset)}.jsonl'
    with open(file_name, 'w') as f:
        for theorem_json in new_dataset:
            f.write(json.dumps(theorem_json))
            f.write('\n')


def get_theorems_from_minif2f(size: int) -> None:
    with open('data/miniF2F/datasets/test.json') as f:
        minif2f_full_lean_dojo = json.load(f)
        minif2f_len = len(minif2f_full_lean_dojo)

    minif2f_full_deepseek = []

    for line in open(minif2f_jsonl, 'r', encoding='utf-8'):
        minif2f_full_deepseek.append(json.loads(line))

    minif2f_full_deepseek = [theorem for theorem in minif2f_full_deepseek if theorem['split'] == 'test']

    print(len(minif2f_full_lean_dojo), len(minif2f_full_deepseek))
    assert minif2f_len == len(minif2f_full_deepseek)

    minif2f_full_deepseek_dict = {theorem['name']: theorem for theorem in minif2f_full_deepseek}

    sampled_theorems_lean_dojo = random.sample(minif2f_full_lean_dojo, size)
    theorem_names = [theorem['full_name'] for theorem in sampled_theorems_lean_dojo]

    sampled_theorems_deepseek = [
        minif2f_full_deepseek_dict[theorem_name]
        for theorem_name in theorem_names
    ]

    write_lean_dojo_dataset_to_file(sampled_theorems_lean_dojo)
    write_deepseek_dataset_to_file(sampled_theorems_deepseek)


get_theorems_from_minif2f(DATA_SET_SIZE)


