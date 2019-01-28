import re
import os
import json

from luxon.exceptions import FieldMissing
from luxon.exceptions import NotFoundError

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

# For TOKEN_RE, refer to https://tools.ietf.org/html/rfc7950#section-6.1.2
# Double quoted str with escaped double quotes
TOKEN_RE = [r'"[^\\"]*(?:\\.[^\\"]*)*"']
# Single quoted string
TOKEN_RE.append(r"'[^']*'")
# Single line comment
TOKEN_RE.append(r'//.*')
# Multi Line comment
TOKEN_RE.append(r'/\*[^(?:\*/)]*\*/')
# Semicolon (";"), or braces ("{" or "}")
TOKEN_RE.append(r'[{};]')
# Keywords and unquoted strings
TOKEN_RE.append(r'[^ \s;{}]+')

TOKEN_RE = '|'.join(TOKEN_RE)

# See cardinality in
# https://tools.ietf.org/html/rfc7950#section-7.1.1
# "0..n" keywords may be present, and have multiple entries
# "0..1" keywords may be present, but is not required
# "1" keywords must be present
SUBSTATEMENTS = json.load(open(os.path.join(__location__,
                                            './yang_substatements.json')))


def last_bracket_index(l):
    """Returns the index of the last occurrence of '}' in a list.

    Args:
         l (list): List to search

    Returns:
        Int value of last index of '}' in a list
    """
    # Note:(Vuader) the double reverse method is faster than
    # reverse iterator, reverse slicing as well as iterating backwards
    # until '}' is found
    l.reverse()
    r = l.index('}')
    l.reverse()
    return len(l) - 1 - r


class YangStatement:
    """YangStatements Base Class

    Creates a YANG Statement object from a list of YANG tokens.

    Eg.:
        [keyword, argument, ';']
        or
        [keyword, argument, '{', sub_keyword, sub_argument,...]

    Attributes:
        name (str): Keyword name
        node (str): Argument value (= None if not present)
        sub_statements (list): List of YangStatement() obj's
        processed (int): Number of tokens processed in order to create this
                         obj.

    Args:
        tokens (list): List of YANG tokens

    """
    def __init__(self, tokens):
        self.name = tokens[0]
        self.node = tokens[1].strip('"').strip("'")
        self.sub_statements = []
        # A Statement is typically 3 tokens:
        # statement [string] (";" / "{" )
        self.processed = 3  # assuming argument was given
        # But argument aka node not required
        if tokens[1] == ';' or tokens[1] == '{':
            self.node = None
            self.processed = 2
        # And sometimes they are comments
        if tokens[0].startswith('//') or tokens[0].startswith('/*'):
            self.name = ''
            self.node = tokens[0]
            self.processed = 1

        # Sub Statements present
        if tokens[self.processed - 1] == '{':
            self._process_subs(tokens[self.processed:])

    def _process_subs(self, tokens):
        """Processes list of Sub Statements.

        Creates YangStatement() objs, and appends them to the sub_statements
        attribute.

        Args:
             tokens (list): List of tokens following '{'
        """
        _tokens_remain = len(tokens)
        i = 0
        while i < _tokens_remain:
            self.processed += 1
            t = tokens[i]
            if t == '}':
                break
            sub_statement = YangStatement(tokens[i:])
            self.sub_statements.append(sub_statement)
            self.processed += sub_statement.processed - 1
            i += sub_statement.processed


class YangKeyword:
    """YangKeyword Base class

    Similar to a YangStatement, but sub_statements is a list of YangKeyword()
    obj's, and takes obj as init arg instead of list of tokens.

    References YANG Sub statements, and raises error if required sub statements
    are not present. The sub statements are defined in yang_substatements.json,
    and supports version 1 and 1.1.

    Keywords can be accessed as the obj's attributes, or key, eg.:

    ..code:: python

        keyword = YangKeyword(yang_model, yang_statement)

    keyword['name'] will be equal to keyword.name

    For Keywords that can appear multiple times, access the specific entry
    by specifying the argument as a key, eg:

    ..code:: python

        keyword['revision']['2010-01-01']

    Args:
        model (obj): YangModel() obj
        statement (obj): YangKeyword() or YangStatement() obj

    Attributes:
        name (str): Keyword name
        node (str): Argument value (= None if not present)
        sub_statements (list): List of YangKeyword() obj's
        _items (dict): Containing either the keyword/argument value pairs, in
                       the case where the statement contained no sub
                       statements, or YangKeyword() obj otherwise
    """
    def __init__(self, model, statement):
        self.model = model
        self.name = statement.name
        self.node = statement.node
        self.sub_statements = []
        self._items = {}

        for s in statement.sub_statements:
            self.sub_statements.append(YangKeyword(model, s))

        try:
            _SUB_STATEMENTS = SUBSTATEMENTS[self.model.version]
        except KeyError:
            raise NotFoundError(
                "Version '%s' not supported" % (self.model.version,))

        try:
            _SUB_STATEMENTS = _SUB_STATEMENTS[self.name]
        except KeyError:
            pass
        try:
            _REQUIRED = _SUB_STATEMENTS['1']
        except KeyError:
            _REQUIRED = []
        try:
            _OPTIONAL = _SUB_STATEMENTS['0..1']
        except KeyError:
            _OPTIONAL = []
        try:
            _MULTIPLE = _SUB_STATEMENTS['0..n']
        except KeyError:
            _MULTIPLE = []

        # Singular keywords become attributes and keys
        for kword in _REQUIRED + _OPTIONAL:
            _kword = kword.replace('-', '_')
            setattr(self, _kword, None)
            self.__setitem__(_kword, None)

        # Multiple keywords become attribute/key lists
        for kword in _MULTIPLE:
            _kword = kword.replace('-', '_')
            setattr(self, _kword, {})
            self.__setitem__(_kword, {})

        # Now processing the sub statements
        for s in self.sub_statements:
            _name = s.name.replace('-', '_')
            if s.name in _REQUIRED + _OPTIONAL:
                # When the sub statement has no sub statements,
                # we set the actual value
                if len(s.sub_statements) == 0:
                    setattr(self, _name, s.node)
                    self.__setitem__(_name, s.node)
                # Otherwise the attribute/key becomes a YangKeyword obj
                else:
                    setattr(self, _name, s)
                    self.__setitem__(_name, s)
            elif s.name in _MULTIPLE:
                getattr(self, _name)[s.node] = s
                self[_name][s.node] = s

        # Moan if the required keywords were missing
        for r in _REQUIRED:
            if not getattr(self, r.replace('-', '_')):
                raise FieldMissing(field=r, label=r,
                                   description="'%s' is required" % r)

    def __getitem__(self, item):
        return self._items[item]

    def __setitem__(self, key, value):
        self._items[key] = value


class YangModel(YangKeyword):
    """Class YangModel

    Child class of YangKeyword.
    Creates an obj that takes the structure of a YANG model. Eg.:

    ..code:: python

        model = YangModel(yang_text)

        def print_yang(s,indent=''):
            if len(s.sub_statements):
                print('%s%s "%s" {' % (indent,s.name,s.node))
                indent += "    "
                for s in s.sub_statements:
                    print_yang(s,indent)
                print(indent[:-4] + '}')
            else:
                if s.node.startswith('//') or s.node.startswith('/*'):
                    print('%s%s' % (indent,s.node))
                else:
                    print('%s%s "%s";' % (indent,s.name,s.node))

        print_yang(model)

    Args:
        yang_text (str): Text containing YANG model.
    """
    def __init__(self, yang_text):
        _tokens = re.findall(TOKEN_RE, yang_text)

        # Need to determine version
        _statement = YangStatement(_tokens)
        for s in _statement.sub_statements:
            if s.name == 'yang-version':
                self.version = s.node

        # In YANG version 1 the yang-version keyword was not required.
        # Assuming version 1 if 'yang-version' is not present.
        try:
            getattr(self, 'version')
        except AttributeError:
            self.version = '1'

        super().__init__(self, _statement)
