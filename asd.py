from lean_dojo import *

repo = LeanGitRepo("https://github.com/yangky11/lean4-example", "7b6ecb9ad4829e4e73600a3329baeb3b5df8d23f")
theorem = Theorem(repo, "Lean4Example.lean", "hello_world")

with Dojo(theorem) as (dojo, init_state):
  print(init_state)
  state1 = dojo.run_tac(init_state, "rw [add_assoc]")
  state2 = dojo.run_tac(state1, "rw [add_comm b]")
  state3 = dojo.run_tac(state2, "rw [←add_assocccc]")
  print('State3', state3)
  state3 = dojo.run_tac(state2, "rw [←add_assoc]")
  print(state3)
  # result = dojo.run_tac(init_state, "rw [add_assoc, add_comm b, ←add_assoc]")
  assert isinstance(state3, ProofFinished)
  print(state3)

theorem2 = Theorem(repo, "Lean4Example.lean", "foo")
print('**************************')

with Dojo(theorem2) as (dojo, init_state):
  print(init_state)
  result = dojo.run_tac(init_state, "rfl")
  assert isinstance(result, ProofFinished)
  print(result)