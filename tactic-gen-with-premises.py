import random
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from common_utils.corpus import Corpus
from premise_retriever import retrieve, encode

tokenizer = AutoTokenizer.from_pretrained("kaiyuy/leandojo-lean4-retriever-tacgen-byt5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("kaiyuy/leandojo-lean4-retriever-tacgen-byt5-small")

num_premises=64
state = "n : ℕ\n⊢ gcd n n = n"
corpus = Corpus('corpus/corpus.jsonl')
print(len(corpus.all_premises))

state_emb = encode(state)
selected_premises = []

def update_selected_premises(current_selected_premises: list, premise_batch: list) -> list:
    serialized_premises = [premise.serialize() for premise in premise_batch]
    premise_embs = encode(serialized_premises)
    scores = (state_emb @ premise_embs.T)
    premise_batch_scores = zip(premise_batch, scores)
    current_selected_premises += premise_batch_scores
    return sorted(current_selected_premises, key=lambda x: x[1], reverse=True)[:32]

for i in range(0, 5):
    new_premise_batch = random.sample(corpus.all_premises, 16) # corpus.all_premises[i:i+16]
    print(f'Batch: {i//16} out of {len(corpus.all_premises)//16}')
    selected_premises = update_selected_premises(selected_premises, new_premise_batch)

print('Selected premises: ')
print(selected_premises)

selected_premises = [premise for premise, score in selected_premises] # random.sample(corpus.all_premises, num_premises)
premises = [premise.serialize() for premise in selected_premises]
print(f'Length of premises: {len(premises)}')
retrieved_premises = retrieve(state, premises, k=4)

input = "\n\n".join(retrieved_premises + [state])
print("------ INPUT ------\n", input)
tokenized_input = tokenizer(input, return_tensors="pt", max_length=2300, truncation=True)

# Generate a single tactic.
tactic_ids = model.generate(tokenized_input.input_ids, max_length=1024)
tactic = tokenizer.decode(tactic_ids[0], skip_special_tokens=True)
print("\n------ OUTPUT ------")
print(tactic, end="\n\n")

# Generate multiple tactics via beam search.
tactic_candidates_ids = model.generate(
    tokenized_input.input_ids,
    max_length=1024,
    num_beams=4,
    length_penalty=0.0,
    do_sample=False,
    num_return_sequences=4,
    early_stopping=False,
)
tactic_candidates = tokenizer.batch_decode(
    tactic_candidates_ids, skip_special_tokens=True
)
for tac in tactic_candidates:
    print(tac)