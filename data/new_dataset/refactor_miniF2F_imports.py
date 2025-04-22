minif2f_imports_path_raw = './data/miniF2F/miniF2F_raw_imports.txt'
minif2f_imports_path_processed = './data/miniF2F/miniF2F_processed_imports.txt'

def make_import_uppercase(raw_import: str) -> str:
    raw_import = raw_import.split('import ')[1]
    raw_import_split = raw_import.split('.')
    import_uppercase = list(map(lambda x: x.capitalize(), raw_import_split))
    return 'import ' + 'Mathlib.' + '.'.join(import_uppercase)


with open(minif2f_imports_path_processed, 'w', encoding='utf-8') as file:
    for line in open(minif2f_imports_path_raw):
        processed_line = make_import_uppercase(line)
        file.write(processed_line)
