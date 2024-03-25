from __future__ import annotations
from collections import defaultdict

from common import Monad, Log, to_tree_string
from lexical import Token, TokenPatternDefinition, builtin_tokens, Lexer

from .parser import ExpressionTerm, Parser
from .visitor import visit_it, Visitor

class Grammar:
  def __init__(
    self,
    name: str,
    xbnf: Optional[str] = None,
    token_defs: Optional[dict[str, TokenPatternDefinition]] = None,
    node_parsers: Optional[dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]]] = None,
    # todo: better way to encode regex vs exact match patterns
    ignore: list[str] = ['[ \t\n]+'],
  ):
    if token_defs is None:
      if xbnf is None:
        # error type
        raise ValueError('provide either xbnf or both token_defs and node_parsers to generate a grammar')

      ast: ASTNode = Monad(xbnf) \
        .then(Lexer(xbnf_grammar).lex) \
        .then(Parser(xbnf_grammar).parse) \
        .value

      # todo: delete
      # Log.begin_d()
      # Log.d(f'ast for {name} grammar:')
      # Log.d(to_tree_string(ast))
      # Log.end_d()

      # generate token definitions and node parsers
      token_defs: dict[str, TokenPatternDefinition]
      node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]]
      token_def_node_parser_generator = TokenDefNodeParserGenerator(ast)
      token_defs = token_def_node_parser_generator.token_defs
      node_parsers = token_def_node_parser_generator.node_parsers

    elif node_parsers is None:
      raise ValueError('provide either xbnf or both token_defs and node_parsers to generate a grammar')

    # validate input
    self._name: str = name
    self._token_defs: dict[str, TokenPatternDefinition] = token_defs
    self._node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]] = node_parsers
    self._ignore = ignore

  @property
  def ignore(self) -> list[str]:
    return self._ignore

  @property
  def token_defs(self) -> dict[str, TokenPatternDefinition]:
    return self._token_defs

  def get_parser(self, node_type: str) -> Callable[[Parser, Optional[bool]], Optional[ASTNode]]:
    return self._node_parsers[node_type]

  @property
  def entry_point_parser(self) -> Callable[[Parser, Optional[bool]], Optional[ASTNode]]:
    return self._node_parsers[f'<{self._name}>']

# todo: temp solution
xbnf_token_defs = {
  '"<"': TokenPatternDefinition.make_temp('"<"'),
  'identifier': builtin_tokens['identifier'],
  '">"': TokenPatternDefinition.make_temp('">"'),
  '"::="': TokenPatternDefinition.make_temp('"::="'),
  '"\\+"': TokenPatternDefinition.make_temp('"\\+"'),
  '";"': TokenPatternDefinition.make_temp('";"'),
  'escaped_string': builtin_tokens['escaped_string'],
  '"\\("': TokenPatternDefinition.make_temp('"\\("'),
  '"\\?"': TokenPatternDefinition.make_temp('"\\?"'),
  '"\\)"': TokenPatternDefinition.make_temp('"\\)"'),
  '"\\*"': TokenPatternDefinition.make_temp('"\\*"'),
  '"\\|"': TokenPatternDefinition.make_temp('"\\|"'),
}

xbnf_node_parsers = {
  '<xbnf>': Parser.generate_nonterminal_parser(
    '<xbnf>',
    [
      [ExpressionTerm('<production>', '+')],
    ],
  ),

  '<production>': Parser.generate_nonterminal_parser(
    '<production>',
    [
      [
        ExpressionTerm('<nonterminal>'),
        ExpressionTerm('"::="'),
        ExpressionTerm('<body>'),
        ExpressionTerm('";"'),
      ],
    ],
  ),

  '<nonterminal>': Parser.generate_nonterminal_parser(
    '<nonterminal>',
    [
      [
        ExpressionTerm('"<"'),
        ExpressionTerm('identifier'),
        ExpressionTerm('">"'),
      ],
    ],
  ),

  '<body>': Parser.generate_nonterminal_parser(
    '<body>',
    [
      [
        ExpressionTerm('<expression>'),
        ExpressionTerm('<body>:1', '*'),
      ],
    ],
  ),

  '<body>:1': Parser.generate_nonterminal_parser(
    '<body>:1',
    [
      [
        ExpressionTerm('"\\|"'),
        ExpressionTerm('<expression>'),
      ],
    ],
  ),

  '<expression>': Parser.generate_nonterminal_parser(
    '<expression>',
    [
      [
        ExpressionTerm('<expression>:0', '+'),
      ],
    ],
  ),

  '<expression>:0': Parser.generate_nonterminal_parser(
    '<expression>:0',
    [
      [
        ExpressionTerm('<group>'),
        ExpressionTerm('<multiplicity>', '?'),
      ],
    ],
  ),

  '<group>': Parser.generate_nonterminal_parser(
    '<group>',
    [
      [ExpressionTerm('<term>')],
      [
        ExpressionTerm('"\\("'),
        ExpressionTerm('<body>'),
        ExpressionTerm('"\\)"'),
      ]
    ],
  ),

  '<term>': Parser.generate_nonterminal_parser(
    '<term>',
    [
      [ExpressionTerm('<nonterminal>')],
      [ExpressionTerm('<terminal>')],
    ],
  ),

  '<terminal>': Parser.generate_nonterminal_parser(
    '<terminal>',
    [
      [ExpressionTerm('escaped_string')],
      [ExpressionTerm('identifier')],
    ],
  ),

  '<multiplicity>': Parser.generate_nonterminal_parser(
    '<multiplicity>',
    [
      [ExpressionTerm('"\\?"')],
      [ExpressionTerm('"\\*"')],
      [ExpressionTerm('"\\+"')],
      [ExpressionTerm('decimal_integer')],
    ],
  ),

  '"::="': Parser.generate_terminal_parser('"::="'),
  '";"': Parser.generate_terminal_parser('";"'),
  '"<"': Parser.generate_terminal_parser('"<"'),
  '">"': Parser.generate_terminal_parser('">"'),
  '"\\|"': Parser.generate_terminal_parser('"\\|"'),
  '"\\("': Parser.generate_terminal_parser('"\\("'),
  '"\\)"': Parser.generate_terminal_parser('"\\)"'),
  'escaped_string': Parser.generate_terminal_parser('escaped_string'),
  'identifier': Parser.generate_terminal_parser('identifier'),
  '"\\?"': Parser.generate_terminal_parser('"\\?"'),
  '"\\*"': Parser.generate_terminal_parser('"\\*"'),
  '"\\+"': Parser.generate_terminal_parser('"\\+"'),
  'decimal_integer': Parser.generate_terminal_parser('decimal_integer'),
}
    
xbnf_grammar: Grammar = Grammar(
  'xbnf',
  token_defs=xbnf_token_defs,
  node_parsers=xbnf_node_parsers,
)

class TokenDefNodeParserGenerator:
  def __init__(self, ast: ASTNode):
    node_visitors: dict[str, Callable[[ASTNode, Visitor], Any]] = {
      '<xbnf>': self.visit_xbnf,
      '<production>': self.visit_production,
      '<body>': self.visit_body,
      '<expression>': self.visit_expression,
      '<group>': self.visit_group,
      '<multiplicity>': self.visit_multiplicity,
    }
    self._productions = defaultdict(list[ExpressionTerm])
    self._lhs_stack: list[str] = []
    self._idx_stack: list[int] = []
    self._token_defs: dict[str, TokenPatternDefinition] = {}
    self._used_nonterminals: set[str] = set()
    # entry nonterminal is used
    self._used_nonterminals.add(f'<{ast[0][0][0][1].lexeme}>')
    self._node_parsers: dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]] = {}
    Visitor(node_visitors).visit(ast)

    for nonterminal in self._used_nonterminals:
      if nonterminal not in self._node_parsers:
        Log.e(f'no productions defined for {nonterminal}')
        # todo: error type
        raise ValueError(f'no productions defined for {nonterminal}')

    # todo: analyze tree from entry nonterminal to determine disconnected components
    # todo: currently this does not detect <x> ::= <y>; <y> ::= <x>;
    for node_type in self._node_parsers:
      if node_type not in self._token_defs and node_type not in self._used_nonterminals:
        Log.w(f'productions are defined for {node_type} but not used')

  @property
  def token_defs(self) -> dict[str, TokenPatternDefinition]:
    return self._token_defs

  @property
  def node_parsers(self) -> dict[str, Callable[[Parser, Optional[bool]], Optional[ASTNode]]]:
    return self._node_parsers

  def add_terminal(self, terminal: str) -> None:
    if terminal not in self._token_defs:
      self._token_defs[terminal] = builtin_tokens.get(
        terminal,
        TokenPatternDefinition.make_temp(terminal),
      )

    if terminal not in self._node_parsers:
      self._node_parsers[terminal] = Parser.generate_terminal_parser(terminal)

  def add_nonterminal(self, nonterminal: str, body: list[list[ExpressionTerm]]) -> None:
    if nonterminal not in self._node_parsers:
      self._node_parsers[nonterminal] = Parser.generate_nonterminal_parser(nonterminal, body)
    else:
      Log.w(f'multiple production definitions for {nonterminal} are disregarded')

  def visit_xbnf(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> Any:
    # node[0]: <production>+
    # production: <production>
    for production in node[0]:
      visitor.visit(production)

  def visit_production(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> Any:
    nonterminal: str = f'<{node[0][1].lexeme}>'

    self._lhs_stack.append(nonterminal)
    self._idx_stack.append(0)

    # not using extend => force 1 production definition for each nonterminal
    self.add_nonterminal(nonterminal, visitor.visit(node[2]))

    self._idx_stack.pop()
    self._lhs_stack.pop()

  def visit_body(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> list[list[ExpressionTerm]]:
    productions: list[list[ExpressionTerm]] = []

    # only 1 production
    if len(node[1]) == 0:
      # node[0]: <expression>
      productions.append(visitor.visit(node[0]))

    # multiple productions
    else:

      auxiliary_nonterminal = f'{self._lhs_stack[-1]}~{self._idx_stack[-1]}'
      self._lhs_stack.append(auxiliary_nonterminal)
      self._idx_stack.append(0)

      # node[0]: <expression>
      productions.append(visitor.visit(node[0]))

      self._idx_stack.pop()
      self._lhs_stack.pop()
      self._idx_stack[-1] += 1

    # node[1]: ("\|" <expression>)*
    # or_production: "\|" <expression>
    for or_production in node[1]:
      auxiliary_nonterminal = f'{self._lhs_stack[-1]}~{self._idx_stack[-1]}'
      self._lhs_stack.append(auxiliary_nonterminal)
      self._idx_stack.append(0)

      # or_production[1]: <expression>
      productions.append(visitor.visit(or_production[1]))

      self._idx_stack.pop()
      self._lhs_stack.pop()
      self._idx_stack[-1] += 1

    return productions

  def visit_expression(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> list[ExpressionTerm]:
    ret = []

    # node[0]: (<group> <multiplicity>?)+
    # expression_term: <group> <multiplicity>?
    for expression_term in node[0]:
      # multiplicity: <multiplicity>?
      optional_multiplicity: ListNonterminalASTNode = expression_term[1]

      # default multiplicity is 1
      if len(optional_multiplicity) == 0:
        multiplicity: Union[str, int] = 1

      else:
        multiplicity: Union[str, int] = visitor.visit(optional_multiplicity[0])

      # expression_term[0]: <group>
      group: str = visitor.visit(expression_term[0])

      ret.append(ExpressionTerm(group, multiplicity))

    return ret

  def visit_group(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> str:
    match node.choice:
      # node: <term>
      case 0:
        # term: <nonterminal> | <terminal>
        term = node[0]

        self._idx_stack[-1] += 1
    
        match term.choice:
          # term: <nonterminal>
          case 0:
            nonterminal = f'<{term[0][1].lexeme}>'
            self._used_nonterminals.add(nonterminal)
            return nonterminal
    
          # term: <terminal>
          case 1:
            # term[0]: escaped_string | identifier
            terminal = term[0][0].lexeme
    
            self.add_terminal(terminal)
            return terminal
    
      # node: "\(" <body> "\)"
      case 1:
        auxiliary_nonterminal = f'{self._lhs_stack[-1]}:{self._idx_stack[-1]}'
        self._lhs_stack.append(auxiliary_nonterminal)
        self._idx_stack.append(0)
        self._used_nonterminals.add(auxiliary_nonterminal)
   
        # node[1]: <body>
        self.add_nonterminal(auxiliary_nonterminal, visitor.visit(node[1]))
    
        self._idx_stack.pop()
        self._lhs_stack.pop()
        self._idx_stack[-1] += 1
    
        return auxiliary_nonterminal

  def visit_multiplicity(
    self,
    node: ASTNode,
    visitor: Visitor,
  ) -> Union[str, int]:
    match node.choice:
      # node: "\?" | "\*" | "\+"
      case 0 | 1 | 2:
        return node[0].lexeme
    
      # node: decimal_integer
      case 1:
        return node[0].xliteral
