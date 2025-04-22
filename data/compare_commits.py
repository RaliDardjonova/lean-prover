import json
from typing import Any

import git
from diskcache.core import full_name
from git import Commit, DiffIndex
from git import Diff
import re

repo = git.Repo('/home/ralitsadardjonova/Documents/moi/doktorantura/mathlib4')
commits_list = list(repo.iter_commits())


# --- To compare the current HEAD against the bare init commit
o_commit = commits_list[-1]
a_commit = repo.commit('29dcec074de168ac2bf835a77ef68bbe069194c5')
b_commit = repo.commit('HEAD') # commits_list[0]

diffs = a_commit.diff(b_commit)

diffs_a_from_init = o_commit.diff(a_commit)
d = diffs[-1]
print(d.a_blob, d.a_mode)
t = diffs[-1]
# print(t.a_blob.data_stream.read().decode('utf-8'))
# print(t.b_blob.data_stream.read().decode('utf-8'))
# print(diffs[260])

def get_diff_path(d: Diff) -> str:
    if d.a_blob:
        return d.a_blob.path
    elif d.b_blob:
        return d.b_blob.path

# def get_substring_between_str(file: str, start: str, end: str) -> str:
#     file_except_start = file.split(start)
#     if len(file_except_start) == 1:
#         return file
#
#     file_except_start = start.join(file_except_start)
#
#     file_except_end = file_except_start.split(end)
#     if len(file_except_end) == 1:
#         return file_except_end[0]
#
#     return end.join(file_except_end[:-1])


def strip_comments(code):
    code = str(code)
    strip_multiline =  re.sub(r'(?m)^ */--(.|\n)*?-/', '', code)
    strip_multiline = re.sub(r'(?m)^ */-!(.|\n)*?-/', '', strip_multiline)
    strip_multiline = re.sub(r'(?m) *--.*\n?', '\n', strip_multiline)
    strip_multiline = re.sub(r'(?m)"(.|\n)*?"', '', strip_multiline)
    return strip_multiline

def get_toplevel_namespaces(file: str, file_path) -> list[tuple[str, str]]:

    all_namespaces = []
    split_namespaces = file.split('\nnamespace ')
    # all_namespaces.append(('', split_namespaces[0]))

    # if len(split_namespaces) ==  1:
    #     return all_namespaces

    while len(split_namespaces) > 0:
        if len(split_namespaces) == 1:
            all_namespaces.append(('', split_namespaces[0]))
            return all_namespaces

        # if file_path == 'Archive/Examples/IfNormalization/Statement.lean' or file_path == "Mathlib/Data/Finsupp/Basic.lean":
        #     print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$', split_namespaces)
        # print(f'^^^^^^^^^^^^^^^^^ {split_namespaces}')
        all_namespaces.extend(get_toplevel_namespaces(split_namespaces[0], file_path))
        file_without_start = '\nnamespace '.join(split_namespaces[1:])
        namespace_name = split_namespaces[1].split()[0]

        file_without_start_split_end = file_without_start.split(f'\nend {namespace_name}\n')
        file_without_end = file_without_start_split_end[0]
        all_namespaces.append((namespace_name, file_without_end))
        split_namespaces = f'\nend {namespace_name}\n'.join(file_without_start_split_end[1:]).split('\nnamespace ')

    return all_namespaces



def parse_inner_namespace(name: str, namespace: str, file_path: str) -> tuple[list[tuple], list[tuple]]:
    pattern = re.compile('^(.*[A-Za-z].*)$') # '^(\d+|[A-Za-z_][\w_.\'-]*)$')
    all_theorems = []
    all_aliases = []

    file_before_split = namespace.split(' theorem ')
    if len(file_before_split) > 1:
        for theorem in file_before_split[1:]:
            theorem_name = theorem.split()[0]
            if pattern.match(theorem_name): # ':=' in theorem:
                all_theorems.append((file_path, name, theorem.split()[0]))

    file_before_split = namespace.split('\ntheorem ')
    if len(file_before_split) > 1:
        for theorem in file_before_split[1:]:
            theorem_name = theorem.split()[0]
            if pattern.match(theorem_name): # ':=' in theorem:
                all_theorems.append((file_path, name, theorem.split()[0]))

    file_before_split = namespace.split(' lemma ')
    if len(file_before_split) > 1:
        for theorem in file_before_split[1:]:
            theorem_name = theorem.split()[0]
            if pattern.match(theorem_name):
                all_theorems.append((file_path, name, theorem.split()[0]))

    file_before_split = namespace.split('\nlemma ')
    if len(file_before_split) > 1:
        for theorem in file_before_split[1:]:
            theorem_name = theorem.split()[0]
            if pattern.match(theorem_name):
                all_theorems.append((file_path, name, theorem.split()[0]))

    # if file_path == 'Mathlib/Algebra/Group/Equiv/Basic.lean':
    #     print('Found theorems: ', all_theorems)

    file_a_split_alias = namespace.split('@[deprecated')
    if len(file_a_split_alias) > 1:
        for alias in file_a_split_alias[1:]:
            alias_split = alias.split('alias ')
            if len(alias_split) > 1 and ':=' in alias_split[1]:
                all_aliases.append((file_path, name, alias_split[1].split()[0]))

    return all_theorems, all_aliases

def parse_namespace(current_namespace_name: str, current_namespace: str, file_path: str)  -> tuple[list[tuple], list[tuple]]:

    # if file_path == "Mathlib/Data/Finsupp/Basic.lean":
        # print(get_toplevel_namespaces(current_namespace))

    toplevel_namespaces = get_toplevel_namespaces(current_namespace, file_path)
    # if file_path == 'Mathlib/FieldTheory/SeparableDegree.lean':
    #     print('Toplevel namespaces: ', toplevel_namespaces)
    all_theorems = []
    all_aliases = []
    for name, namespace in toplevel_namespaces:
        if name == '':
            theorems, aliases = parse_inner_namespace(current_namespace_name, namespace, file_path)
            all_theorems.extend(theorems)
            all_aliases.extend(aliases)
        else:
            # if file_path == 'Mathlib/Algebra/Group/Equiv/Basic.lean':
            #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            #     print(f'${current_namespace_name}$', f'*{name}*')
            extended_namespace_name = '.'.join([current_namespace_name, name]) if current_namespace_name else name
            #if file_path == 'Mathlib/Algebra/Group/Equiv/Basic.lean':
                # print(extended_namespace_name)
                # print([current_namespace_name, name])
                # if current_namespace:
                #     print('yes')
            theorems, aliases = parse_namespace(extended_namespace_name, namespace, file_path)
            all_theorems.extend(theorems)
            all_aliases.extend(aliases)

    # if file_path == 'Mathlib/LinearAlgebra/TensorProduct/Matrix.lean':
    #     print('####################################')
    #     print(current_namespace_name)
    #     print(current_namespace)
    #     print(all_theorems)
    return all_theorems, all_aliases

def compare_commits(diffs_: DiffIndex):
    a = 0
    theorems_first = []
    aliases_first = []
    theorems_second = []
    aliases_second = []
    for diff_item in diffs_:
        if diff_item.a_path.endswith('.lean'):
            file_before = diff_item.a_blob.data_stream.read().decode('utf-8') if diff_item.a_blob else ''
            file_before = strip_comments(file_before)
            # if diff_item.a_path == 'Mathlib/RingTheory/LaurentSeries.lean':
            #     print(file_before)
            theorems, aliases = parse_namespace('', file_before, diff_item.a_path)
            theorems_first.extend(theorems)
            aliases_first.extend(aliases)

            file_after = diff_item.b_blob.data_stream.read().decode('utf-8') if diff_item.b_blob else ''
            file_after = strip_comments(file_after)
            theorems, aliases = parse_namespace('', file_after, diff_item.b_path)
            theorems_second.extend(theorems)
            aliases_second.extend(aliases)
        # a += 1
        # if a > 50:
        #     break


    return theorems_first, theorems_second, aliases_first, aliases_second

theorems_a, theorems_b, aliases_a, aliases_b = compare_commits(diffs)

theorems_o, theorems_ao, aliases_o, aliases_ao = compare_commits(diffs_a_from_init)

print('Theorems A: ', len(set(theorems_a)))
print('Theorems B', len(set(theorems_b)))
print('Theorems O: ', len(theorems_o))
print(theorems_o)
print('Theorems A from 0: ', len(set(theorems_ao) - set(theorems_a)))
theorems_a = list(set(theorems_a + theorems_ao))
print('Theorems A: ', len(set(theorems_a)))

removed_theorems = set(theorems_a) - set(theorems_b)
removed_theorems -= set(aliases_b)

theorems_a_only_names = [(namespace, thm) for _, namespace, thm in theorems_a]
theorems_b_only_names = [(namespace, thm) for _, namespace, thm in theorems_b]
aliases_a_only_names = [(namespace, thm) for _, namespace, thm in aliases_a]
aliases_b_only_names = [(namespace, thm) for _, namespace, thm in aliases_b]

removed_only_names = set(theorems_a_only_names) - set(theorems_b_only_names)
removed_only_names -= set(aliases_b_only_names)
print('Removed names and file(: ', len(removed_theorems))
print('Removed only names(removed without moved): ', len(removed_only_names))
print('Aliases that were added: ', len(set(theorems_a) & (set(aliases_b) - set(aliases_a))))

added_theorems = set(theorems_b) - set(theorems_a)
added_only_names = set(theorems_b_only_names) - set(theorems_a_only_names)

print(len(removed_theorems)/len(theorems_a))
print(len(removed_only_names)/len(theorems_a))


def get_full_name_tuples(init_theorems):
    full_names = []
    for (file, namespace, thm) in init_theorems:
        if not file.startswith('Mathlib/'):
            continue

        if thm.startswith('_root_.'):
            thm = thm.split('_root_.')[1]
            full_names.append((file, thm))
            continue

        if thm.startswith('«') and thm.endswith('»'):
            thm = thm[1:-1]

        if namespace:
            full_names.append((file, '.'.join([namespace, thm])))
        else:
            full_names.append((file, thm))
    return full_names

full_name_a = get_full_name_tuples(theorems_a)
full_name_b = get_full_name_tuples(list(set(theorems_b + list(set(theorems_ao) - set(theorems_a)))))
print('Stripped theorems A: ', len(full_name_a))
print(print(len(removed_only_names)/len(full_name_a)))
print('Stripped theorems B: ', len(full_name_b))
# full_name_a = set([(file, '.'.join([namespace, thm])) if namespace else (file, thm) for (file, namespace, thm) in theorems_a])

# print(theorems_a)

finsupp_thm = [(file, thm) for (file, thm) in full_name_a if 'hasDerivAt_update' in thm]#  file == 'Mathlib/Analysis/Calculus/Deriv/Pi.lean']
print(finsupp_thm)
# print(finsupp_thm)

jsonl_path = 'data/leandojo_benchmark_4/corpus.jsonl'

def count_theorems(filea) -> Any:
    premises = filea['premises']
    missing_thms = []

    theoremss = [(filea['path'], premise['full_name'])
                 for premise in premises
                 if ' theorem ' in premise['code'] or
                  '\ntheorem ' in premise['code'] or
                premise['code'].startswith('theorem ') or
                 premise['kind'] == 'lemma']

    # for thm in theoremss:
    #     if thm not in full_name_a:
    #         missing_thms.append(thm)
    #         # print(thm)
    return len(theoremss), theoremss, missing_thms



i = 0
count_thm = 0
jsonl_theorems = []
missing_theorems_290_commit = []

for line in open(jsonl_path):
    i +=1
    file_dict = json.loads(line)
    if file_dict['path'].startswith('Mathlib'):
        new_count, theorems, missing = count_theorems(file_dict)
        count_thm += new_count
        jsonl_theorems.extend(theorems)
        missing_theorems_290_commit.extend(missing)

print('missing theorems: ', len(missing_theorems_290_commit))
print(missing_theorems_290_commit)

# jsonl_theorems_set = set(jsonl_theorems)
# for thm in full_name_a:
#     if thm not in jsonl_theorems_set:
#         print(thm)

print(i)
print(count_thm)

with open('/home/ralitsadardjonova/Documents/moi/doktorantura/lean-prover/data/leandojo_benchmark_4/random/test.json') as f:
    random_test = json.load(f)

missing_random_test_a = []
for thm in random_test:
    if (thm['file_path'], thm['full_name']) not in full_name_a:
        missing_random_test_a.append((thm['file_path'], thm['full_name']))

print('Missing random test: ', len(missing_random_test_a))

with open('/home/ralitsadardjonova/Documents/moi/doktorantura/lean-prover/data/leandojo_benchmark_4/novel_premises/test.json') as f:
    novel_test = json.load(f)

missing_novel_test_a = []
for thm in novel_test:
    if (thm['file_path'], thm['full_name']) not in full_name_a:
        missing_novel_test_a.append((thm['file_path'], thm['full_name']))

print('Missing novel test: ', len(missing_novel_test_a))

with open('/home/ralitsadardjonova/Documents/moi/doktorantura/lean-prover/data/leandojo_benchmark_4/random/test.json') as f:
    random_test = json.load(f)

missing_random_test = []
for thm in random_test:
    if (thm['file_path'], thm['full_name']) not in full_name_b:
        missing_random_test.append((thm['file_path'], thm['full_name']))

print('Missing random test in latest: ', len(missing_random_test))

with open('/home/ralitsadardjonova/Documents/moi/doktorantura/lean-prover/data/leandojo_benchmark_4/novel_premises/test.json') as f:
    novel_test = json.load(f)

missing_novel_test = []
for thm in novel_test:
    if (thm['file_path'], thm['full_name']) not in full_name_b:
        missing_novel_test.append((thm['file_path'], thm['full_name']))

print('Missing novel test in latest: ', len(missing_novel_test))

removed_theorems = set(theorems_a) - set(theorems_b)
removed_theorems -= set(aliases_b)

theorems_a_only_names = [(namespace, thm) for _, namespace, thm in theorems_a]
theorems_b_only_names = [(namespace, thm) for _, namespace, thm in theorems_b]
aliases_a_only_names = [(namespace, thm) for _, namespace, thm in aliases_a]
aliases_b_only_names = [(namespace, thm) for _, namespace, thm in aliases_b]

removed_only_names = set(theorems_a_only_names) - set(theorems_b_only_names)
removed_only_names -= set(aliases_b_only_names)
print('Removed names and file(: ', len(removed_theorems))
print('Removed only names(removed without moved): ', len(removed_only_names))

theorems_a_only_full_names = [thm for _, thm in get_full_name_tuples(theorems_a)]
theorems_b_only_full_names = [thm for _, thm in get_full_name_tuples(theorems_b)]
aliases_a_only_full_names = [thm for _, thm in get_full_name_tuples(aliases_a)]
aliases_b_only_full_names = [thm for _, thm in get_full_name_tuples(aliases_b)]
added_only_full_names = set(theorems_b_only_full_names) - set(theorems_a_only_full_names)

removed_only_full_names = set(theorems_a_only_full_names) - set(theorems_b_only_full_names)
removed_only_full_names -= set(aliases_b_only_full_names)
print('Removed only full names: ', len(removed_only_full_names))

print(len(added_only_full_names))
# print(set(full_name_b) - set(full_name_a))


missing_random_by_corpus = []
all_theorems_corpus = []
for line in open(jsonl_path):
    file_dict = json.loads(line)
    if file_dict['path'].startswith('Mathlib'):
        premises = file_dict['premises']
        missing_thms = []

        theorems = [(file_dict['path'], premise['full_name'])
                     for premise in premises
                     if ' theorem ' in premise['code'] or
                     '\ntheorem ' in premise['code'] or
                     premise['code'].startswith('theorem ') or
                     premise['kind'] == 'lemma']
        all_theorems_corpus.extend(theorems)


random_test_theorems = [(thm['file_path'], thm['full_name']) for thm in random_test]
novel_test_theorems = [(thm['file_path'], thm['full_name']) for thm in novel_test]
missing_random_by_corpus = set(random_test_theorems) - set(all_theorems_corpus)
missing_novel_by_corpus = set(novel_test_theorems) - set(all_theorems_corpus)

print('Missing random test from corpus:', len(missing_random_by_corpus))
print('Missing novel test from corpus:', len(missing_novel_by_corpus))


# Missing from Mathlib altogether:

random_test_theorems_not_mathlib = [(thm['file_path'], thm['full_name']) for thm in random_test if not thm['file_path'].startswith('Mathlib')]
novel_test_theorems_not_mathlib = [(thm['file_path'], thm['full_name']) for thm in novel_test if not thm['file_path'].startswith('Mathlib')]

print('Missing random test from mathlib:', len(random_test_theorems_not_mathlib))
print('Missing novel test from mathlib:', len(novel_test_theorems_not_mathlib))


print('Missing random test without not in mathlib: ', len(set(missing_random_test_a) - set(random_test_theorems_not_mathlib)))
print('Missing novel test without not in mathlib: ', len(set(missing_novel_test_a) - set(novel_test_theorems_not_mathlib)))


# get missing premises

def get_used_premises(theorem: dict) -> list:
    # print(theorem)
    traced_tactics = theorem['traced_tactics']

    return [
        premise["full_name"]
        for tactic in traced_tactics
        for premise in tactic['annotated_tactic'][1]
    ]


def are_premised_deprecated(theorem: dict) -> bool:
    used_premises = get_used_premises(theorem)
    return len(set(used_premises) & set(removed_only_full_names)) > 0

def deprecated_or_deprecated_premises(theorem: dict) -> bool:
    return ((theorem['file_path'].startswith('Mathlib/') and (theorem['file_path'], theorem['full_name']) not in full_name_b )
            or are_premised_deprecated(theorem))

theorems_with_deprecated_premises_random = list(filter(lambda x: x, [are_premised_deprecated(thm) for thm in random_test]))
theorems_with_deprecated_premises_novel = list(filter(lambda x: x, [are_premised_deprecated(thm) for thm in novel_test]))

deprecated_theorems_random = list(filter(lambda x: x, [deprecated_or_deprecated_premises(thm) for thm in random_test]))
deprecated_theorems_novel = list(filter(lambda x: x, [deprecated_or_deprecated_premises(thm) for thm in novel_test]))

print('Removed only full names: ', len(removed_only_full_names))
print('Theorems in random test with deprecated premises: ', len(theorems_with_deprecated_premises_random))
print('Theorems in novel test with deprecated premises: ', len(theorems_with_deprecated_premises_novel))


print('Theorems in random test deprecated: ', len(deprecated_theorems_random))
print('Theorems in novel test deprecated: ', len(deprecated_theorems_novel))