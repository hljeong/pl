from __future__ import annotations
from collections import defaultdict

from common import Token
from lexer import Lexer
from parser import ASTParser, generate_nonterminal_parser, generate_terminal_parser
from ast import Visitor

class Grammar:
  def __init__(
    self,
    cbnf: Optional[str] = None,
    node_parsers: Optional[dict[str, Callable[[ASTParser, Optional[bool]], Optional[Union[ASTNode, Token]]]]] = None,
  ):
    # bootstrap
    if node_parsers is None:
      if cbnf is None:
        raise ValueError('at least one of cbnf and node_parsers must be given to generate a grammar')

      # parse grammar and generate parsers
      tokens: list[Token] = Lexer(cbnf).tokens
      ast: ASTParser = ASTParser(cbnf_grammar, tokens).ast
      node_parsers: Visitor = Visitor(
        ast,
        node_parser_generator_node_visitors,
        {
          'node_parsers': {},
          'rule_term_lists': defaultdict(list),
        }
      ).ret

    # validate input
    self._name = list(node_parsers.keys())[0]
    self._node_parsers = node_parsers

  def get_parser(self, node_type: str) -> Callable[[ASTParser, Optional[bool]], Optional[Union[ASTNode, Token]]]:
    return self._node_parsers[node_type]

  @property
  def entry_point_parser(self) -> Callable[[ASTParser, Optional[bool]], Optional[Union[ASTNode, Token]]]:
    return self._node_parsers[self._name]
    

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
    ],
  ),

  '::=': generate_terminal_parser(Token.Type.COLON_COLON_EQUAL),

  ';': generate_terminal_parser(Token.Type.SEMICOLON),

  '<': generate_terminal_parser(Token.Type.LESS_THAN),

  '>': generate_terminal_parser(Token.Type.GREATER_THAN),

  'identifier': generate_terminal_parser(Token.Type.IDENTIFIER),

  'escaped_string': generate_terminal_parser(Token.Type.ESCAPED_STRING),
}
    
cbnf_grammar: Grammar = Grammar(node_parsers=cbnf_node_parsers)

terminal_parsers = {
  'identifier': generate_terminal_parser(Token.Type.IDENTIFIER),
  'decimal_integer': generate_terminal_parser(Token.Type.DECIMAL_INTEGER),
  'escaped_string': generate_terminal_parser(Token.Type.ESCAPED_STRING),
  '::=': generate_terminal_parser(Token.Type.COLON_COLON_EQUAL),
  ';': generate_terminal_parser(Token.Type.SEMICOLON),
  '<': generate_terminal_parser(Token.Type.LESS_THAN),
  '>': generate_terminal_parser(Token.Type.GREATER_THAN),
}

def node_parser_generator_visit_cbnf(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  visitor.visit(node.get(0))
  if node.production == 0:
    visitor.visit(node.get(1))

  for nonterminal, rule_term_lists in visitor.env['rule_term_lists'].items():
    visitor.env['node_parsers'][nonterminal] = generate_nonterminal_parser(nonterminal, rule_term_lists)
  visitor.env['node_parsers'].update(terminal_parsers)
  return visitor.env['node_parsers']

def node_parser_generator_visit_rule(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  nonterminal: str = node.get(0).get(1).literal
  visitor.env['rule_term_lists'][nonterminal].append(visitor.visit(node.get(2)))

def node_parser_generator_visit_expression(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  ret = [visitor.visit(node.get(0))]
  if node.production == 0:
    ret.extend(visitor.visit(node.get(1)))
  return ret

def node_parser_generator_visit_term(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  return visitor.visit(node.get(0))

def node_parser_generator_visit_nonterminal(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  return node.get(1).literal

def node_parser_generator_visit_terminal(
  node: ASTNode,
  visitor: Visitor,
) -> Any:
  return node.get(0).literal

node_parser_generator_node_visitors = {
  'cbnf': node_parser_generator_visit_cbnf,
  'rule': node_parser_generator_visit_rule,
  'expression': node_parser_generator_visit_expression,
  'term': node_parser_generator_visit_term,
  'nonterminal': node_parser_generator_visit_nonterminal,
  'terminal': node_parser_generator_visit_terminal,
}
