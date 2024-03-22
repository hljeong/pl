from __future__ import annotations
from collections import defaultdict

from common import Token, TokenPatternDefinition, builtin_tokens, Lexer, ast_to_tree_string
from plast import generate_nonterminal_parser, generate_extended_nonterminal_parser, generate_terminal_parser, ExpressionTerm, Parser, Visitor

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
      token_def_node_parser_generator = CBNFTokenDefNodeParserGenerator(ast)
      token_defs = token_def_node_parser_generator.token_defs
      node_parsers = token_def_node_parser_generator.node_parsers

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

class CBNFTokenDefNodeParserGenerator:
  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'cbnf': self.visit_cbnf,
      'rule': self.visit_rule,
      'expression': self.visit_expression,
      'term': self.visit_term,
      'nonterminal': self.visit_nonterminal,
      'terminal': self.visit_terminal,
    }
    self._productions = defaultdict(list)
    self._nonterminals = set()
    self._terminals = set()
    self._token_defs: dict[str, TokenPatternDefinition]
    self._node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]
    self._token_defs, self._node_parsers = Visitor(
      ast,
      node_visitors,
    ).ret

  @property
  def token_defs(self) -> dict[str, TokenPatternDefinition]:
    return self._token_defs

  @property
  def node_parsers(self) -> dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]:
    return self._node_parsers

  def visit_cbnf(
    self,
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
      for terminal in self._terminals:
        token_defs[terminal] = builtin_tokens.get(
          terminal,
          TokenPatternDefinition.make_plain(terminal),
        )
        node_parsers[terminal] = generate_terminal_parser(terminal)

      # generate node parsers for nonterminals
      for nonterminal, productions in self._productions.items():
        node_parsers[nonterminal] = generate_nonterminal_parser(nonterminal, productions)

      # check if all nonterminals have a parser
      for nonterminal in self._nonterminals:
        if nonterminal not in node_parsers:
          # todo: error type
          raise ValueError(f'no rules defined for nonterminal <{nonterminal}>')

      return (token_defs, node_parsers)

  def visit_rule(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    nonterminal: str = node.get(0).get(1).literal
    self._productions[nonterminal].append(visitor.visit(node.get(2)))

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    ret = [visitor.visit(node.get(0))]
    if node.production == 0:
      ret.extend(visitor.visit(node.get(1)))
    return ret

  def visit_term(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    return visitor.visit(node.get(0))

  def visit_nonterminal(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    nonterminal: str = node.get(1).literal
    self._nonterminals.add(nonterminal)
    return nonterminal

  def visit_terminal(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    terminal: str = node.get(0).literal
    self._terminals.add(terminal)
    return terminal



class XBNFGrammar:
  def __init__(
    self,
    name: str,
    xbnf: Optional[str] = None,
    token_defs: Optional[dict[str, TokenPatternDefinition]] = None,
    node_parsers: Optional[dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]] = None,
    ignore: list[str] = [],
  ):
    if token_defs is None:
      if xbnf is None:
        # error type
        raise ValueError('provide either xbnf or both token_defs and node_parsers to generate a grammar')

      # lex grammar cbnf
      tokens: list[Token] = Lexer(
        xbnf_grammar,
        xbnf,
      ).tokens

      # parse grammar xbnf
      ast: Parser = Parser(xbnf_grammar, tokens).ast
      # print(ast_to_tree_string(ast))

      # generate token definitions and node parsers
      token_defs: dict[str, TokenPatternDefinition]
      node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]
      token_def_node_parser_generator = XBNFTokenDefNodeParserGenerator(ast)
      token_defs = token_def_node_parser_generator.token_defs
      node_parsers = token_def_node_parser_generator.node_parsers

    elif node_parsers is None:
      raise ValueError('provide either xbnf or both token_defs and node_parsers to generate a grammar')

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

xbnf_token_defs = {
  '<': TokenPatternDefinition.make_plain('<'),
  'identifier': builtin_tokens['identifier'],
  '>': TokenPatternDefinition.make_plain('>'),
  '::=': TokenPatternDefinition.make_plain('::='),
  '\\+': TokenPatternDefinition.make_plain('\\+'),
  ';': TokenPatternDefinition.make_plain(';'),
  'escaped_string': builtin_tokens['escaped_string'],
  '\\(': TokenPatternDefinition.make_plain('\\('),
  '\\?': TokenPatternDefinition.make_plain('\\?'),
  '\\)': TokenPatternDefinition.make_plain('\\)'),
  '\\*': TokenPatternDefinition.make_plain('\\*'),
  '\\|': TokenPatternDefinition.make_plain('\\|'),
}

xbnf_node_parsers = {
  'xbnf': generate_extended_nonterminal_parser(
    'xbnf',
    [
      [ExpressionTerm('production', '+')],
    ],
  ),

  'production': generate_extended_nonterminal_parser(
    'production',
    [
      [
        ExpressionTerm('nonterminal'),
        ExpressionTerm('::='),
        ExpressionTerm('body'),
        ExpressionTerm(';'),
      ],
    ],
  ),

  'nonterminal': generate_extended_nonterminal_parser(
    'nonterminal',
    [
      [
        ExpressionTerm('<'),
        ExpressionTerm('identifier'),
        ExpressionTerm('>'),
      ],
    ],
  ),

  'body': generate_extended_nonterminal_parser(
    'body',
    [
      [
        ExpressionTerm('expression'),
        ExpressionTerm('body:1', '*'),
        # CompoundExpressionTerm(
        #   [
        #     [
        #       ExpressionTerm('\|'),
        #       ExpressionTerm('expression'),
        #     ],
        #   ],
        #   '*'
        # ),
      ],
    ],
  ),

  'body:1': generate_extended_nonterminal_parser(
    'body:1',
    [
      [
        ExpressionTerm('\\|'),
        ExpressionTerm('expression'),
      ],
    ],
  ),

  'expression': generate_extended_nonterminal_parser(
    'expression',
    [
      [
        ExpressionTerm('expression:0', '+'),
        # CompoundExpressionTerm(
        #   [
        #     [
        #       ExpressionTerm('group'),
        #       ExpressionTerm('multiplicity', '?'),
        #     ],
        #   ],
        #  ExpressionTerm('+'),
        # ),
      ],
    ],
  ),

  'expression:0': generate_extended_nonterminal_parser(
    'expression:0',
    [
      [
        ExpressionTerm('group'),
        ExpressionTerm('multiplicity', '?'),
      ],
    ],
  ),

  'group': generate_extended_nonterminal_parser(
    'group',
    [
      [ExpressionTerm('group~0')],
      [ExpressionTerm('group~1')],
    ],
  ),

  'group~0': generate_extended_nonterminal_parser(
    'group~0',
    [
      [ExpressionTerm('term')],
    ],
  ),

  'group~1': generate_extended_nonterminal_parser(
    'group~1',
    [
      [
        ExpressionTerm('\\('),
        ExpressionTerm('body'),
        ExpressionTerm('\\)'),
      ]
    ],
  ),

  'term': generate_extended_nonterminal_parser(
    'term',
    [
      [ExpressionTerm('term~0')],
      [ExpressionTerm('term~1')],
    ],
  ),

  'term~0': generate_extended_nonterminal_parser(
    'term~0',
    [
      [ExpressionTerm('nonterminal')],
    ],
  ),

  'term~1': generate_extended_nonterminal_parser(
    'term~1',
    [
      [ExpressionTerm('terminal')],
    ],
  ),

  'terminal': generate_extended_nonterminal_parser(
    'terminal',
    [
      [ExpressionTerm('terminal~0')],
      [ExpressionTerm('terminal~1')],
      [ExpressionTerm('terminal~2')],
    ],
  ),

  'terminal~0': generate_extended_nonterminal_parser(
    'terminal~0',
    [
      [ExpressionTerm('e')],
    ],
  ),

  'terminal~1': generate_extended_nonterminal_parser(
    'terminal~1',
    [
      [ExpressionTerm('escaped_string')],
    ],
  ),

  'terminal~2': generate_extended_nonterminal_parser(
    'terminal~2',
    [
      [ExpressionTerm('identifier')],
    ],
  ),

  'multiplicity': generate_extended_nonterminal_parser(
    'multiplicity',
    [
      [ExpressionTerm('multiplicity~0')],
      [ExpressionTerm('multiplicity~1')],
      [ExpressionTerm('multiplicity~2')],
      [ExpressionTerm('multiplicity~3')],
    ],
  ),

  'multiplicity~0': generate_extended_nonterminal_parser(
    'multiplicity~0',
    [
      [ExpressionTerm('\\?')],
    ],
  ),

  'multiplicity~1': generate_extended_nonterminal_parser(
    'multiplicity~1',
    [
      [ExpressionTerm('\\*')],
    ],
  ),

  'multiplicity~2': generate_extended_nonterminal_parser(
    'multiplicity~2',
    [
      [ExpressionTerm('\\+')],
    ],
  ),

  'multiplicity~3': generate_extended_nonterminal_parser(
    'multiplicity~3',
    [
      [ExpressionTerm('decimal_integer')],
    ],
  ),

  '::=': generate_terminal_parser('::='),
  ';': generate_terminal_parser(';'),
  '<': generate_terminal_parser('<'),
  '>': generate_terminal_parser('>'),
  '\\|': generate_terminal_parser('\\|'),
  '\\(': generate_terminal_parser('\\('),
  '\\)': generate_terminal_parser('\\)'),
  'e': generate_terminal_parser('e'),
  'escaped_string': generate_terminal_parser('escaped_string'),
  'identifier': generate_terminal_parser('identifier'),
  '\\?': generate_terminal_parser('\\?'),
  '\\*': generate_terminal_parser('\\*'),
  '\\+': generate_terminal_parser('\\+'),
  'decimal_integer': generate_terminal_parser('decimal_integer'),
}
    
xbnf_grammar: Grammar = Grammar(
  'xbnf',
  token_defs=xbnf_token_defs,
  node_parsers=xbnf_node_parsers,
)

class XBNFTokenDefNodeParserGenerator:
  def __init__(self, ast: Node):
    node_visitors: dict[str, Callable[[Node, Visitor], Any]] = {
      'xbnf': self.visit_xbnf,
      'production': self.visit_production,
      'body': self.visit_body,
      'expression': self.visit_expression,
      'group': visit_it,
      'group~0': visit_it,
      'group~1': self.visit_group_option1,
      'term': visit_it,
      'term~0': visit_it,
      'term~1': visit_it,
      'nonterminal': self.visit_nonterminal,
      'terminal': self.visit_terminal,
      'multiplicity': visit_it,
      'multiplicity~0': lambda node, visitor: node.get(0).lexeme,
      'multiplicity~1': lambda node, visitor: node.get(0).lexeme,
      'multiplicity~2': lambda node, visitor: node.get(0).lexeme,
      'multiplicity~3': lambda node, visitor: node.get(0).literal,
      'terminal~0': lambda node, visitor: node.get(0).lexeme,
      'terminal~1': lambda node, visitor: node.get(0).literal,
      'terminal~2': lambda node, visitor: node.get(0).lexeme,
    }
    self._productions = defaultdict(list[ExpressionTerm])
    self._lhs_stack: list[str] = []
    self._idx_stack: list[int] = []
    self._nonterminals = set()
    self._terminals = set()
    self._token_defs: dict[str, TokenPatternDefinition]
    self._node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]
    self._token_defs, self._node_parsers = Visitor(
      ast,
      node_visitors,
    ).ret
    # for nonterminal in self._productions:
    #   print(f'{nonterminal}: {self._productions[nonterminal]}')

  @property
  def token_defs(self) -> dict[str, TokenPatternDefinition]:
    return self._token_defs

  @property
  def node_parsers(self) -> dict[str, Callable[[Parser, Optional[bool]], Optional[Union[Node, Token]]]]:
    return self._node_parsers

  def visit_xbnf(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    # node.get(0): <production>+
    # production: <production>
    for production in node.get(0):
      visitor.visit(production)

    token_defs = {}
    node_parsers = {}

    # generate token definitions and node parsers for terminals
    print(self._terminals)
    for terminal in self._terminals:
      token_defs[terminal] = builtin_tokens.get(
        terminal,
        TokenPatternDefinition.make_plain(terminal),
      )
      node_parsers[terminal] = generate_terminal_parser(terminal)

    # generate node parsers for nonterminals
    for nonterminal, body in self._productions.items():
      # todo: fix bad hack
      if len(body) == 1:
        node_parsers[nonterminal] = generate_extended_nonterminal_parser(nonterminal, body)

      # branch nonterminal
      else:
        node_parsers[nonterminal] = generate_extended_nonterminal_parser(nonterminal, body)

    # check if all nonterminals have a parser
    for nonterminal in self._nonterminals:
      if nonterminal not in node_parsers:
        # todo: error type
        raise ValueError(f'no productions defined for nonterminal <{nonterminal}>')

    return (token_defs, node_parsers)

  def visit_production(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Any:
    nonterminal: str = node.get(0).get(1).literal

    self._lhs_stack.append(nonterminal)
    self._idx_stack.append(0)

    # not using extend => force 1 production definition for each nonterminal
    self._productions[nonterminal] = visitor.visit(node.get(2))

    self._idx_stack.pop()
    self._lhs_stack.pop()

  def visit_body(
    self,
    node: Node,
    visitor: Visitor,
  ) -> list[list[ExpressionTerm]]:
    productions: list[list[ExpressionTerm]] = []

    # only 1 production
    if len(node.get(1)) == 0:
      # node.get(0): <expression>
      productions.append(visitor.visit(node.get(0)))

    # multiple productions
    else:
      # self._nonterminals.add(self._lhs_stack[-1])

      auxiliary_nonterminal = f'{self._lhs_stack[-1]}~{self._idx_stack[-1]}'
      self._nonterminals.add(auxiliary_nonterminal)
      productions.append([ExpressionTerm(auxiliary_nonterminal)])
      self._lhs_stack.append(auxiliary_nonterminal)
      self._idx_stack.append(0)

      # node.get(0): <expression>
      self._productions[auxiliary_nonterminal] = [visitor.visit(node.get(0))]

      self._idx_stack.pop()
      self._lhs_stack.pop()
      self._idx_stack[-1] += 1

    # node.get(1): ("\|" <expression>)*
    # or_production: "\|" <expression>
    for or_production in node.get(1):
      auxiliary_nonterminal = f'{self._lhs_stack[-1]}~{self._idx_stack[-1]}'
      productions.append([ExpressionTerm(auxiliary_nonterminal)])
      self._nonterminals.add(auxiliary_nonterminal)
      self._lhs_stack.append(auxiliary_nonterminal)
      self._idx_stack.append(0)

      # or_production.get(1): <expression>
      self._productions[auxiliary_nonterminal] = [visitor.visit(or_production.get(1))]

      self._idx_stack.pop()
      self._lhs_stack.pop()
      self._idx_stack[-1] += 1

    return productions

  def visit_expression(
    self,
    node: Node,
    visitor: Visitor,
  ) -> list[ExpressionTerm]:
    ret = []

    # node.get(0): (<group> <multiplicity>?)+
    # expression_term: <group> <multiplicity>?
    for expression_term in node.get(0):
      # multiplicity: <multiplicity>?
      optional_multiplicity: list[Node] = expression_term.get(1)

      # default multiplicity is 1
      if len(optional_multiplicity) == 0:
        multiplicity: Union[str, int] = 1

      else:
        multiplicity: Union[str, int] = visitor.visit(optional_multiplicity[0])

      # expression_term.get(0): <group>
      group: str = visitor.visit(expression_term.get(0))

      ret.append(ExpressionTerm(group, multiplicity))

    return ret

  def visit_group(
    self,
    node: Node,
    visitor: Visitor,
  ) -> str:
    pass
    
    # match node.production:
    #   # node: <term>
    #   case 0:
    #     # term: <nonterminal> | <terminal>
    #     term = node.get(0)
    # 
    #     match term.production:
    #       # term: <nonterminal>
    #       case 0:
    #         nonterminal = term.get(0).get(1).lexeme
    #         self._nonterminals.add(nonterminal)
    #         return nonterminal
    #
    #       # term: <terminal>
    #       case 1:
    #         # terminal_node: "e" | escaped_string | identifier
    #         terminal_node = term.get(0)
    #
    #         match terminal_node.production:
    #           # terminal_node: "e"
    #           case 0:
    #             terminal = terminal_node.get(0).lexeme
    #
    #           # terminal_node: escaped_string
    #           case 1:
    #             terminal = terminal_node.get(0).literal
    #
    #           # terminal_node: identifier
    #           case 2:
    #             terminal = terminal_node.get(0).lexeme
    #
    #         self._terminals.add(terminal)
    #         return terminal
    #
    #   # node: "\(" <body> "\)"
    #   case 1:
    #     auxiliary_nonterminal = f'{self._lhs_stack[-1]}:{self._idx_stack[-1]}'
    #     self._lhs_stack.append(auxiliary_nonterminal)
    #     self._idx_stack.append(0)
    #     self._nonterminals.add(auxiliary_nonterminal)
    #
    #     # node.get(1): <body>
    #     self._productions[auxiliary_nonterminal] = visitor.visit(node.get(1))
    #
    #     self._idx_stack.pop()
    #     self._lhs_stack.pop()
    #     self._idx_stack[-1] += 1
    #
    #     return auxiliary_nonterminal

  def visit_group_option1(
    self,
    node: Node,
    visitor: Visitor,
  ) -> str:
    auxiliary_nonterminal = f'{self._lhs_stack[-1]}:{self._idx_stack[-1]}'
    self._lhs_stack.append(auxiliary_nonterminal)
    self._idx_stack.append(0)
    self._nonterminals.add(auxiliary_nonterminal)

    # node.get(1): <body>
    self._productions[auxiliary_nonterminal] = visitor.visit(node.get(1))

    self._idx_stack.pop()
    self._lhs_stack.pop()
    self._idx_stack[-1] += 1

    return auxiliary_nonterminal

  def visit_nonterminal(
    self,
    node: Node,
    visitor: Visitor,
  ) -> str:
    nonterminal = node.get(1).lexeme
    self._nonterminals.add(nonterminal)
    return nonterminal

  def visit_terminal(
    self,
    node: Node,
    visitor: Visitor,
  ) -> str:
    terminal = visitor.visit(node.get(0))
    print(terminal)
    self._terminals.add(terminal)
    return terminal

  def visit_multiplicity(
    self,
    node: Node,
    visitor: Visitor,
  ) -> Union[str, int]:
    pass

    # match node.production:
    #   # node: "\?" | "\*" | "\+"
    #   case 0 | 1 | 2:
    #     return node.get(0).lexeme
    # 
    #   # node: decimal_integer
    #   case 1:
    #     return node.get(0).literal

def visit_it(
  node: Node,
  visitor: Visitor,
) -> Any:
  return visitor.visit(node.get(0))
