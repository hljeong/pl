from __future__ import annotations
from typing import DefaultDict, Iterator, Optional
from collections import defaultdict

from common import Log

class NFA:
  class Constructor:
    def __init__(self):
      self.n: int = 1
      self.d: DefaultDict[tuple[int, str], set[int]] = defaultdict(set)
      self.F: DefaultDict[int, set[str]] = defaultdict(set)

    def state(self) -> int:
      self.n += 1
      return self.n - 1

    def transition(
      self,
      fro: int,
      char: str,
      to: int,
    ) -> None:
      self.d[(fro, char)].add(to)

    def accept(
      self,
      state: int,
      pattern_name: str,
    ) -> None:
      self.F[state].add(pattern_name)

    def construct(self) -> NFA:
      return NFA(
        self.n,
        self.d,
        self.F,
      )

  def __init__(
    self, 
    n: int,
    d: DefaultDict[tuple[int, str], set[int]],
    F: DefaultDict[int, set[str]],
  ):
    self._n: int = n
    self._d: DefaultDict[tuple[int, str], set[int]] = d
    self._F: DefaultDict[int, set[str]] = F
    self._epsilon_closure: dict[int, set[int]] = {}
    for state in range(self._n):
      self.__compute_epsilon_closure(state)

  def __compute_epsilon_closure(self, state: int):
    if state in self._epsilon_closure:
      return

    self._epsilon_closure[state] = set([state])
    for next_state in self._d[(state, '')]:
      self.__compute_epsilon_closure(next_state)
      self._epsilon_closure[state].update(self._epsilon_closure[next_state])

  @property
  def n(self) -> int:
    return self._n

  @property
  def d(self) -> DefaultDict[tuple[int, str], set[int]]:
    return self._d

  @property
  def F(self) -> DefaultDict[int, set[str]]:
    return self._F

  def run(self, s: str) -> tuple[str]:
    current_states: set[int] = set(self._epsilon_closure[0])

    for ch in s:
      current_states = set().union(
        *map(
          lambda next_state: self._epsilon_closure[next_state],
          set().union(
            *map(
              lambda current_state: self._d[(current_state, ch)],
              current_states,
            )
          ),
        )
      )

    accepts: tuple[str] = tuple(set().union(
      *map(
        lambda final_state: self._F[final_state],
        current_states,
      )
    ))

    return accepts

  def match_exact(pattern: str, pattern_name: Optional[str] = None) -> NFA:
    if not pattern_name:
      pattern_name = pattern

    constructor: NFA.Constructor = NFA.Constructor()
    current: int = 0
    for ch in pattern:
      next_state: int = constructor.state()
      constructor.transition(current, ch, next_state)
      current = next_state
    constructor.accept(current, pattern_name)
    return constructor.construct()

  # todo: ugly
  def match_union(nfa1: NFA, nfa2: NFA) -> NFA:
    constructor: NFA.Constructor = NFA.Constructor()

    constructor.transition(0, '', constructor.n)
    for fro, ch in nfa1.d:
      for to in nfa1.d[(fro, ch)]:
        constructor.d[(constructor.n + fro, ch)].add(constructor.n + to)
    for state in range(nfa1.n):
      constructor.F[constructor.n + state] = nfa1.F[state]
    constructor.n += nfa1.n

    constructor.transition(0, '', constructor.n)
    for fro, ch in nfa2.d:
      for to in nfa2.d[(fro, ch)]:
        constructor.d[(constructor.n + fro, ch)].add(constructor.n + to)
    for state in range(nfa2.n):
      constructor.F[constructor.n + state] = nfa2.F[state]
    constructor.n += nfa2.n

    return constructor.construct()

  # todo: ugly
  # todo: havent done anything to this yet this is a copy of match_union
  # todo: how to handle pattern names???
  def match_concat(nfa1: NFA, nfa2: NFA) -> NFA:
    constructor: NFA.Constructor = NFA.Constructor()

    constructor.transition(0, '', constructor.n)
    for fro, ch in nfa1.d:
      for to in nfa1.d[(fro, ch)]:
        constructor.d[(constructor.n + fro, ch)].add(constructor.n + to)
    for state in range(nfa1.n):
      constructor.F[constructor.n + state] = nfa1.F[state]
    constructor.n += nfa1.n

    constructor.transition(0, '', constructor.n)
    for fro, ch in nfa2.d:
      for to in nfa2.d[(fro, ch)]:
        constructor.d[(constructor.n + fro, ch)].add(constructor.n + to)
    for state in range(nfa2.n):
      constructor.F[constructor.n + state] = nfa2.F[state]
    constructor.n += nfa2.n

    return constructor.construct()

  def match_kleene_closure(nfa: NFA) -> NFA:
    pass



class OldNFA:
  class State:
    def __init__(self):
      self._transitions: DefaultDict[str, set[State]] = defaultdict(set)
      self._accept: set[str] = set()
      self._epsilon_closure: set[State] = None

    def __getitem__(self, char: str) -> set[State]:
      return self._transitions[char]

    @property
    def accept(self) -> tuple[str]:
      return tuple(self._accept)

    @property
    def epsilon_closure(self) -> set[State]:
      return self._epsilon_closure
    
    def accepts(self, pattern_name: str) -> None:
      self._accept.add(pattern_name)

    def transition(self, char: str, to: State) -> None:
      self._transitions[char].add(to)

    def compute_epsilon_closure(self) -> None:
      self._epsilon_closure: set[State] = set()
      self.__epsilon_closure(self._epsilon_closure)

    def __epsilon_closure(self, epsilon_closure: set[State]) -> None:
      if self in epsilon_closure:
        return

      if self._epsilon_closure:
        epsilon_closure.update(self._epsilon_closure)
        return

      epsilon_closure.add(self)
      for next_state in self['']:
        next_state.__epsilon_closure(epsilon_closure)

  def __init__(self):
    self._initial: NFA.State = NFA.State(0)
    self._states: list[NFA.State] = [self._initial]
    self._done: bool = False

  def __getitem__(self, idx: int) -> NFA.State:
    return self._states[idx]

  def __iter__(self) -> Iterator[NFA.State]:
    return iter(self._states)

  def __assert_done(self) -> None:
    if not self._done:
      # todo: error msg and type
      raise ValueError('NFA not done')

  def __assert_not_done(self) -> None:
    if self._done:
      # todo: error msg and type
      raise ValueError('NFA already done')

  @property
  def initial(self) -> NFA.State:
    return self._initial

  def state(self) -> NFA.State:
    self.__assert_not_done()
    state_id: int = len(self._states)
    self._states.append(NFA.State(state_id))
    return self._states[state_id]

  def transition(
    self,
    fro: int,
    char: str,
    to: int,
  ) -> None:
    self.__assert_not_done()
    self[fro].transition(char, self[to])

  def done(self) -> None:
    self.__assert_not_done()

    for state in self:
      state.compute_epsilon_closure()

    self._done = True

  def run(self, s: str) -> tuple[str]:
    current_states: set[NFA.State] = set(self._initial.epsilon_closure)

    for ch in s:
      current_states = set().union(
        *map(
          lambda next_state: next_state.epsilon_closure,
          set().union(
            *map(
              lambda current_state: current_state[ch],
              current_states,
            )
          ),
        )
      )

    accepts: tuple[str] = tuple(set().union(
      *map(
        lambda final_state: final_state.accept,
        current_states,
      )
    ))

    return accepts

  def match_exact(pattern: str, pattern_name: Optional[str] = None) -> NFA:
    if not pattern_name:
      pattern_name = pattern

    nfa: NFA = NFA()
    current: NFA.State = nfa.initial
    for ch in pattern:
      next_state: NFA.State = nfa.state()
      current.transition(ch, next_state)
      current = next_state
    current.accepts(pattern_name)
    nfa.done()
    return nfa

  def match_union(nfa1: NFA, nfa2: NFA) -> NFA:
    nfa: NFA = NFA()

  def match_concat(nfa1: NFA, nfa2: NFA) -> NFA:
    pass

  def match_kleene_closure(nfa: NFA) -> NFA:
    pass

class DFA:
  class State:
    def __init__(self, state_id: int):
      self._state_id = state_id
      self._transitions: dict[str, State] = dict()
      self._accept: set[str] = set()

    def __getitem__(self, ch: str) -> State:
      return self._transitions[ch]

    def __setitem__(self, ch: str, state: State) -> None:
      self._transitions[ch] = state

    @property
    def state_id(self) -> int:
      return self._state_id

    @property
    def accept(self) -> tuple[str]:
      return tuple(self._accept)

    def transition(self, ch: str, to: State) -> None:
      if ch in self._transitions:
        if to == self[ch]:
          Log.w(f'duplicate transition on \'{ch}\'')
        else:
          Log.w(f'overwriting transition on \'{ch}\'')

      self[ch] = to

  def __init__(self):
    self._initial: State = State()
    self._states: list[State] = [self._initial]
    self._done: bool = False

  def __getitem__(self, idx: int) -> State:
    return self._states[idx]

  def __iter__(self) -> Iterator[State]:
    return iter(self._states)

  def __assert_done(self) -> None:
    if not self._done:
      # todo: error msg and type
      raise ValueError('NFA not done')

  def __assert_not_done(self) -> None:
    if self._done:
      # todo: error msg and type
      raise ValueError('NFA already done')

  def state(self, accept: str = '') -> int:
    self.__assert_not_done()
    state_id: int = len(self._states)
    self._states.append(State(state_id, accept))
    return state_id

  def transition(
    self,
    fro: int,
    char: str,
    to: int,
  ) -> None:
    self.__assert_not_done()
    self[fro].transition(char, self[to])

  def done(self) -> None:
    self.__assert_not_done()
    self._done = True

  def run(self, s: str) -> str:
    self.__assert_done()
    state: State = self._initial

    for ch in s:
      state = state[ch]

    return state.accept
