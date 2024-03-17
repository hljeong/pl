from pytest import main, raises, fixture
from copy import copy

from context import common
from common import Cursor, CursorRange, Token

@fixture
def cursors():
  return [
    Cursor(1, 1),
    Cursor(1, 1),
    Cursor(1, 2),
    Cursor(2, 1),
    Cursor(2, 2),
  ]

@fixture
def cursor_ranges(cursors):
  return [
    CursorRange(cursors[0], cursors[1]),
    CursorRange(cursors[0], cursors[1]),
    CursorRange(cursors[0], cursors[2]),
    CursorRange(cursors[0], cursors[3]),
    CursorRange(cursors[2], cursors[3]),
  ]

@fixture
def tokens(cursor_ranges):
  return [
    Token(Token.Type.EOF, '', None, cursor_ranges[0]),
    Token(Token.Type.EOF, '', None, cursor_ranges[0]),
    Token(Token.Type.LEFT_PAREN, '(', None, cursor_ranges[0]),
    Token(Token.Type.RIGHT_PAREN, ')', None, cursor_ranges[0]),
  ]

def test_cursor_constructor_range_check():
  with raises(ValueError) as e:
    Cursor(0, 1)
  assert str(e.value) == 'line number (0) has to be at least 1'

  with raises(ValueError) as e:
    Cursor(1, 0)
  assert str(e.value) == 'column number (0) has to be at least 1'

def test_cursor_to_string(cursors):
  cursors_to_string = [
    'l1c1',
    'l1c1',
    'l1c2',
    'l2c1',
    'l2c2',
  ]

  cursors_to_string_verbose = [
    'line 1 column 1',
    'line 1 column 1',
    'line 1 column 2',
    'line 2 column 1',
    'line 2 column 2',
  ]

  for i in range(len(cursors)):
    assert cursors[i].to_string() == cursors_to_string[i]
    assert cursors[i].to_string(True) == cursors_to_string_verbose[i]

def test_cursor_lt(cursors):
  truth = [
    [False, False, True, True, True],
    [False, False, True, True, True],
    [False, False, False, True, True],
    [False, False, False, False, True],
    [False, False, False, False, False],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] < cursors[j]) == truth[i][j]

def test_cursor_le(cursors):
  truth = [
    [True, True, True, True, True],
    [True, True, True, True, True],
    [False, False, True, True, True],
    [False, False, False, True, True],
    [False, False, False, False, True],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] <= cursors[j]) == truth[i][j]

def test_cursor_gt(cursors):
  truth = [
    [False, False, False, False, False],
    [False, False, False, False, False],
    [True, True, False, False, False],
    [True, True, True, False, False],
    [True, True, True, True, False],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] > cursors[j]) == truth[i][j]

def test_cursor_ge(cursors):
  truth = [
    [True, True, False, False, False],
    [True, True, False, False, False],
    [True, True, True, False, False],
    [True, True, True, True, False],
    [True, True, True, True, True],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] >= cursors[j]) == truth[i][j]

def test_cursor_eq(cursors):
  truth = [
    [True, True, False, False, False],
    [True, True, False, False, False],
    [False, False, True, False, False],
    [False, False, False, True, False],
    [False, False, False, False, True],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] == cursors[j]) == truth[i][j]

def test_cursor_ne(cursors):
  truth = [
    [False, False, True, True, True],
    [False, False, True, True, True],
    [True, True, False, True, True],
    [True, True, True, False, True],
    [True, True, True, True, False],
  ]

  for i in range(len(cursors)):
    for j in range(len(cursors)):
      assert (cursors[i] != cursors[j]) == truth[i][j]

def test_cursor_copy():
  a = Cursor(1, 1)
  b = copy(a)
  assert a == b and a is not b

def test_cursor_range_constructor_validity_check(cursors):
  with raises(ValueError) as e:
    CursorRange(cursors[2], cursors[0])
  assert str(e.value) == 'end (l1c1) cannot come before start (l1c2)'

  with raises(ValueError) as e:
    CursorRange(cursors[3], cursors[2])
  assert str(e.value) == 'end (l1c2) cannot come before start (l2c1)'

def test_cursor_range_to_string(cursor_ranges):
  cursor_ranges_to_string = [
    'l1c1',
    'l1c1',
    'l1c1-2',
    'l1c1-l2c1',
    'l1c2-l2c1',
  ]

  cursor_ranges_to_string_verbose = [
    'line 1 column 1',
    'line 1 column 1',
    'line 1 columns 1-2',
    'line 1 column 1 - line 2 column 1',
    'line 1 column 2 - line 2 column 1',
  ]

  for i in range(len(cursor_ranges)):
    assert cursor_ranges[i].to_string() == cursor_ranges_to_string[i]
    assert cursor_ranges[i].to_string(True) == cursor_ranges_to_string_verbose[i]

def test_cursor_range_eq(cursor_ranges):
  truth = [
    [True, True, False, False, False],
    [True, True, False, False, False],
    [False, False, True, False, False],
    [False, False, False, True, False],
    [False, False, False, False, True],
  ]

  for i in range(len(cursor_ranges)):
    for j in range(len(cursor_ranges)):
      assert (cursor_ranges[i] == cursor_ranges[j]) == truth[i][j]

def test_cursor_range_ne(cursor_ranges):
  truth = [
    [False, False, True, True, True],
    [False, False, True, True, True],
    [True, True, False, True, True],
    [True, True, True, False, True],
    [True, True, True, True, False],
  ]

  for i in range(len(cursor_ranges)):
    for j in range(len(cursor_ranges)):
      assert (cursor_ranges[i] != cursor_ranges[j]) == truth[i][j]

def test_cursor_range_copy():
  a = Cursor(1, 1)
  b = CursorRange(a, Cursor(1, 2))
  c = copy(b)
  assert a == c.start and b == c and b is not c

def test_token_to_string(tokens):
  tokens_to_string = [
    'EOF(\'\')@l1c1',
    'EOF(\'\')@l1c1',
    'LEFT_PAREN(\'(\')@l1c1',
    'RIGHT_PAREN(\')\')@l1c1',
  ]

  tokens_to_string_verbose = [
    'EOF(\'\') at line 1 column 1',
    'EOF(\'\') at line 1 column 1',
    'LEFT_PAREN(\'(\') at line 1 column 1',
    'RIGHT_PAREN(\')\') at line 1 column 1',
  ]

  for i in range(len(tokens)):
    assert tokens[i].to_string() == tokens_to_string[i]
    assert tokens[i].to_string(True) == tokens_to_string_verbose[i]

def test_token_eq(tokens):
  truth = [
    [True, True, False, False],
    [True, True, False, False],
    [False, False, True, False],
    [False, False, False, True],
  ]

  for i in range(len(tokens)):
    for j in range(len(tokens)):
      assert (tokens[i] == tokens[j]) == truth[i][j]

def test_token_ne(tokens):
  truth = [
    [False, False, True, True],
    [False, False, True, True],
    [True, True, False, True],
    [True, True, True, False],
  ]

  for i in range(len(tokens)):
    for j in range(len(tokens)):
      assert (tokens[i] != tokens[j]) == truth[i][j]

if __name__ == '__main__':
  main()
