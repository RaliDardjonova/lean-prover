import pickle

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from premise_retriever import retrieve, encode

tokenizer = AutoTokenizer.from_pretrained("kaiyuy/leandojo-lean4-retriever-tacgen-byt5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("kaiyuy/leandojo-lean4-retriever-tacgen-byt5-small")

batch_size = 32
state1 = "n : ℕ\n⊢ gcd n n = n"
state = "n : ℕ\nih : n.gcd n = n\n⊢ (Order.succ n).gcd (Order.succ n) = Order.succ n"
indexed_corpus = pickle.load(open('data/corpus/indexed_corpus', "rb"))
corpus = indexed_corpus.corpus
corpus_embeddings = indexed_corpus.embeddings

print(len(corpus.all_premises))
print(corpus_embeddings.shape)

# corpus = Corpus('corpus/indexed_corpus')
# print(len(corpus.all_premises))
#
state_emb = encode(state)
selected_premises = []


def update_selected_premises(current_selected_premises: list, premise_batch: list, premise_embs: torch.tensor) -> list:
    # serialized_premises = [premise.serialize() for premise in premise_batch]
    # premise_embs = encode(serialized_premises)
    scores = (state_emb @ premise_embs.T)
    premise_batch_scores = zip(premise_batch, scores)
    current_selected_premises += premise_batch_scores
    return sorted(current_selected_premises, key=lambda x: x[1], reverse=True)[:batch_size]


for i in range(0, len(corpus.all_premises), batch_size):
    new_premise_batch = corpus.all_premises[i:i+batch_size]
    new_embs = corpus_embeddings[i:i+batch_size, :]
    #print(f'Batch: {i // batch_size} out of {len(corpus.all_premises) // batch_size}')
    selected_premises = update_selected_premises(selected_premises, new_premise_batch, new_embs)

print('Selected premises: ')
print(selected_premises)

selected_premises = [premise for premise, score in
                     selected_premises]  # random.sample(corpus.all_premises, num_premises)
premises = [premise.serialize() for premise in selected_premises]
print(f'Length of premises: {len(premises)}')
retrieved_premises = retrieve(state, premises, k=32)

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
    num_beams=8,
    length_penalty=0.0,
    do_sample=False,
    num_return_sequences=8,
    early_stopping=False,
)
tactic_candidates = tokenizer.batch_decode(
    tactic_candidates_ids, skip_special_tokens=True
)
for tac in tactic_candidates:
    print(tac)
