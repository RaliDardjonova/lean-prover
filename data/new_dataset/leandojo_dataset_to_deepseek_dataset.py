import hashlib
import json
import os
from typing import Optional, List, Tuple
from timeit import default_timer as timer
import lean_dojo
from lean_dojo.data_extraction.lean import LeanGitRepo, Theorem, Pos
from lean_dojo.data_extraction.trace import is_available_in_cache
from lean_dojo.interaction.dojo import Dojo, DojoInitError, TacticState
from tqdm import tqdm

data_path = 'data/leandojo_benchmark_4/novel_premises'
split = 'test'
lean_dojo_style_dataset_name = f'{data_path}/{split}.json'


def get_code_per_theorem_in_file(file_dict: dict) -> dict:
    return {
        premise['full_name']: premise['code']
        for premise in file_dict['premises']
    }

def get_code_per_theorem() -> dict:
    theorems_per_file = {}
    for line in open('data/corpus/corpus.jsonl'):
        file_dict = json.loads(line)
        theorems_per_file[file_dict['path']] = get_code_per_theorem_in_file(file_dict)

    return theorems_per_file

def create_import_str(imports: list) -> str:
    import_str = ""
    for i in imports:
        import_str += i
        import_str += '\n'
    return import_str

def get_imports_per_file() -> dict:
    imports_ = {}
    for line in open('data/corpus/corpus.jsonl'):
        file_dict = json.loads(line)
        imports_[file_dict['path']] = create_import_str(file_dict['imports'])
    return imports_

code_per_theorem = get_code_per_theorem()
imports_per_file = get_imports_per_file()


metadata = json.load(open(os.path.join(data_path, "../metadata.json")))
repo = LeanGitRepo(metadata["from_repo"]["url"], metadata["from_repo"]["commit"])



def create_deepseek_style_dict(theorem_dict: dict) -> dict:
    time1 = timer()
    code = code_per_theorem[theorem_dict['file_path']][theorem_dict['full_name']]
    theorem = Theorem(repo, theorem_dict['file_path'], theorem_dict['full_name'])
    time2 = timer()
    # print(theorem_dict['full_name'], timer() - time1)
    try:
        with Dojo(theorem) as (dojo, init_state):
            theorem_state = init_state.pp
    except DojoInitError:
        theorem_state = ''
    # print(theorem_dict['full_name'], timer() - time2)
    # print(theorem_state)

    return {
        "name": theorem_dict['full_name'],
        "split": "test",
        "informal_prefix": '',
        "formal_statement": code,
        "goal": theorem_state,
        "header": imports_per_file[theorem_dict['file_path']]
    }


with open(lean_dojo_style_dataset_name, 'r') as init_dataset_file:
    init_dataset = json.load(init_dataset_file)

deepseek_style_file_name = f'{data_path}/deepseek/{split}.json'
deep_seek_style_dataset = []
for theorem_dict in tqdm(init_dataset):
    deep_seek_style_dataset.append(create_deepseek_style_dict(theorem_dict))

with open(deepseek_style_file_name, 'w') as f:
    json.dump(deep_seek_style_dataset, f)


