from __future__ import annotations
from collections import defaultdict

from common import Token, TokenPatternDefinition, builtin_tokens, Lexer
from plast import generate_nonterminal_parser, generate_terminal_parser, Parser, Visitor

class Grammar:
  def __init__(
    self,
    name: str,
    cbnf: Optional[str] = None,
    token_defs: Optional[dict[str, TokenPatternDefinition]] = None,
    node_parsers: Optional[dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]] = None,
    ignore: list[str] = [],
  ):
    if token_defs is None:
      if cbnf is None:
        # error type
        raise ValueError('provide either cbnf or both token_defs and node_parsers to generate a grammar')

      # lex grammar cbnf
      tokens: list[Token] = Lexer(
        cbnf_grammar,
        cbnf,
      ).tokens

      # parse grammar cbnf
      ast: Parser = Parser(cbnf_grammar, tokens).ast

      # generate token definitions and node parsers
      token_defs: dict[str, TokenPatternDefinition]
      node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]
      token_defs, node_parsers = Visitor(
        ast,
        token_def_node_parser_generator_node_visitors,
        {
          'productions': defaultdict(list),
          'nonterminals': set(),
          'terminals': set(),
        }
      ).ret
    elif node_parsers is None:
      raise ValueError('provide either cbnf or both token_defs and node_parsers to generate a grammar')

    # validate input
    self._name: str = name
    self._token_defs: dict[str, TokenPatternDefinition] = token_defs
    self._node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]] = node_parsers
    self._ignore = ignore

  @property
  def ignore(self) -> list[str]:
    return self._ignore

  @property
  def token_defs(self) -> dict[str, TokenPatternDefinition]:
    return self._token_defs

  def get_parser(self, node_type: str) -> Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]:
    return self._node_parsers[node_type]

  @property
  def entry_point_parser(self) -> Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]:
    return self._node_parsers[self._name]
    


cbnf_token_defs = {
  'identifier': builtin_tokens['identifier'],
  'escaped_string': builtin_tokens['escaped_string'],
  '<': TokenPatternDefinition.make_plain('<'),
  '>': TokenPatternDefinition.make_plain('>'),
  '::=': TokenPatternDefinition.make_plain('::='),
  ';': TokenPatternDefinition.make_plain(';'),
}

cbnf_node_parsers = {
  'cbnf': generate_nonterminal_parser(
    'cbnf',
    [
      ['rule', 'cbnf'],
      ['rule'],
    ],
  ),

  'rule': generate_nonterminal_parser(
    'rule',
    [
      ['nonterminal', '::=', 'expression', ';'],
    ],
  ),

  'expression': generate_nonterminal_parser(
    'expression',
    [
      ['term', 'expression'],
      ['term'],
    ],
  ),

  'term': generate_nonterminal_parser(
    'term',
    [
      ['nonterminal'],
      ['terminal'],
    ],
  ),

  'nonterminal': generate_nonterminal_parser(
    'nonterminal',
    [
      ['<', 'identifier', '>'],
    ],
  ),

  'terminal': generate_nonterminal_parser(
    'terminal',
    [
      ['escaped_string'],
      ['identifier'],
    ],
  ),

  '::=': generate_terminal_parser('::='),

  ';': generate_terminal_parser(';'),

  '<': generate_terminal_parser('<'),

  '>': generate_terminal_parser('>'),

  'identifier': generate_terminal_parser('identifier'),

  'escaped_string': generate_terminal_parser('escaped_string'),
}
    
cbnf_grammar: Grammar = Grammar(
  'cbnf',
  token_defs=cbnf_token_defs,
  node_parsers=cbnf_node_parsers,
)

def token_def_node_parser_generator_visit_cbnf(
  node: Node,
  visitor: Visitor,
) -> Any:
  visitor.visit(node.get(0))
  if node.production == 0:
    return visitor.visit(node.get(1))


  # at the end of the list of rules
  else:
    token_defs = {}
    node_parsers = {}

    # generate token definitions and node parsers for terminals
    for terminal in visitor.env['terminals']:
      token_defs[terminal] = builtin_tokens.get(
        terminal,
        TokenPatternDefinition.make_plain(terminal),
      )
      node_parsers[terminal] = generate_terminal_parser(terminal)

    # generate node parsers for nonterminals
    for nonterminal, productions in visitor.env['productions'].items():
      node_parsers[nonterminal] = generate_nonterminal_parser(nonterminal, productions)

    # check if all nonterminals have a parser
    for nonterminal in visitor.env['nonterminals']:
      if nonterminal not in node_parsers:
        # todo: error type
        raise ValueError(f'no rules defined for nonterminal <{nonterminal}>')

    return (token_defs, node_parsers)

def token_def_node_parser_generator_visit_rule(
  node: Node,
  visitor: Visitor,
) -> Any:
  nonterminal: str = node.get(0).get(1).literal
  visitor.env['productions'][nonterminal].append(visitor.visit(node.get(2)))

def token_def_node_parser_generator_visit_expression(
  node: Node,
  visitor: Visitor,
) -> Any:
  ret = [visitor.visit(node.get(0))]
  if node.production == 0:
    ret.extend(visitor.visit(node.get(1)))
  return ret

def token_def_node_parser_generator_visit_term(
  node: Node,
  visitor: Visitor,
) -> Any:
  return visitor.visit(node.get(0))

def token_def_node_parser_generator_visit_nonterminal(
  node: Node,
  visitor: Visitor,
) -> Any:
  nonterminal: str = node.get(1).literal
  visitor.env['nonterminals'].add(nonterminal)
  return nonterminal

def token_def_node_parser_generator_visit_terminal(
  node: Node,
  visitor: Visitor,
) -> Any:
  terminal: str = node.get(0).literal
  visitor.env['terminals'].add(terminal)
  return terminal

token_def_node_parser_generator_node_visitors = {
  'cbnf': token_def_node_parser_generator_visit_cbnf,
  'rule': token_def_node_parser_generator_visit_rule,
  'expression': token_def_node_parser_generator_visit_expression,
  'term': token_def_node_parser_generator_visit_term,
  'nonterminal': token_def_node_parser_generator_visit_nonterminal,
  'terminal': token_def_node_parser_generator_visit_terminal,
}
