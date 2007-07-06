#
# (C) Copyright 2003-2007 Hewlett-Packard Development Company, L.P.
# (C) Copyright 2006-2007 Novell, Inc. 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#   
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

# Author: Bart Whiteley <bwhiteley@suse.de>

import ply.lex as lex

tokens = (
        'ANY', 
        'AS',
        'ASSOCIATION',
        'CLASS',
        'DISABLEOVERRIDE',
        'DT_BOOL',
        'DT_CHAR16',
        'DT_DATETIME',
        'DT_REAL32',
        'DT_REAL64',
        'DT_SINT16',
        'DT_SINT32',
        'DT_SINT64',
        'DT_SINT8',
        'DT_STR',
        'DT_UINT16',
        'DT_UINT32',
        'DT_UINT64',
        'DT_UINT8',
        'ENABLEOVERRIDE',
        'FALSE',
        'FLAVOR',
        'INDICATION',
        'INSTANCE',
        'METHOD',
        'NULL',
        'OF',
        'PARAMETER',
        'PRAGMA',
        'PROPERTY',
        'QUALIFIER',
        'REF',
        'REFERENCE',
        'RESTRICTED',
        'SCHEMA',
        'SCOPE',
        'TOSUBCLASS',
        'TRANSLATABLE',
        'TRUE',
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'SEMICOLON',
        'LBRACK',
        'RBRACK',
        'COMMA',
        'DOLLAR',
        'COLON',
        'EQUALS',
        'IDENTIFIER',
        'stringValue',
        'floatValue',
        'charValue',
        'binaryValue',
        'octalValue',
        'decimalValue',
        'hexValue',
    )


# UTF-8 (from Unicode 4.0.0 standard):
# Table 3-6. Well-Formed UTF-8 Byte Sequences Code Points
# 1st Byte 2nd Byte 3rd Byte 4th Byte
# U+0000..U+007F     00..7F
# U+0080..U+07FF     C2..DF   80..BF
# U+0800..U+0FFF     E0       A0..BF   80..BF
# U+1000..U+CFFF     E1..EC   80..BF   80..BF
# U+D000..U+D7FF     ED       80..9F   80..BF
# U+E000..U+FFFF     EE..EF   80..BF   80..BF
# U+10000..U+3FFFF   F0       90..BF   80..BF   80..BF
# U+40000..U+FFFFF   F1..F3   80..BF   80..BF   80..BF
# U+100000..U+10FFFF F4       80..8F   80..BF   80..BF

utf8_2 = r'[\xC2-\xDF][\x80-\xBF]'
utf8_3_1 = r'\xE0[\xA0-\xBF][\x80-\xBF]'
utf8_3_2 = r'[\xE1-\xEC][\x80-\xBF][\x80-\xBF]'
utf8_3_3 = r'\xED[\x80-\x9F][\x80-\xBF]'
utf8_3_4 = r'[\xEE-\xEF][\x80-\xBF][\x80-\xBF]'
utf8_4_1 = r'\xF0[\x90-\xBF][\x80-\xBF][\x80-\xBF]'
utf8_4_2 = r'[\xF1-\xF3][\x80-\xBF][\x80-\xBF][\x80-\xBF]'
utf8_4_3 = r'\xF4[\x80-\x8F][\x80-\xBF][\x80-\xBF]'

utf8Char = r'{utf8_2}|{utf8_3_1}|{utf8_3_2}|{utf8_3_3}|{utf8_3_4}|{utf8_4_1}|'\
        '{utf8_4_2}|{utf8_4_3}'

def t_COMMENT(t):
    r'//.*'
    pass

t_IDENTIFIER = r'([a-zA-Z_]|{utf8Char})([0-9a-zA-Z_]|{utf8Char})*'

t_binaryValue = r'[+-]?[01]+[bB]'
t_octalValue = r'[+-]?"0"[0-7]+'
t_decimalValue = r'[+-]?([1-9][0-9]*|"0")'
t_hexValue = r'[+-]?"0"[xX][0-9a-fA-F]+'
t_floatValue = r'[+-]?[0-9]*"."[0-9]+([eE][+-]?[0-9]+)?'

simpleEscape = r"""[bfnrt'"\\]"""
hexEscape = r'"x"[0-9a-fA-F]{1,4}'
escapeSequence = r'[\\]({simpleEscape}|{hexEscape})'
cChar = r"[^'\\\n\r]|{escapeSequence}"
sChar = r'[^"\\\n\r]|{escapeSequence}'
charValue = r"\'{cChar}\'"
#t_stringValue = r'\"{sChar}*\"'
ws = r'[ \t]+'
#t_stringValue = r'1*("*{sChar}")'
t_stringValue = r'"(\\"|[^"])*"'

def t_CLASS(t):
    r'class'
    return t

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMICOLON = r'\;'
t_LBRACK = r'\['
t_RBRACK = r'\]'
t_COMMA = r'\,'
t_DOLLAR = r'\$'
t_COLON = r'\:'
t_EQUALS = r'\='

t_TRUE = r'true'
t_FALSE = r'false'

t_ANY = r'any'
t_AS = r'as'
t_ASSOCIATION = r'association'
#t_CLASS = r'class'
t_DISABLEOVERRIDE = r'disableoverride'
t_DT_BOOL = r'boolean'
t_DT_CHAR16 = r'char16'
t_DT_DATETIME = r'datetime'
t_DT_REAL32 = r'real32'
t_DT_REAL64 = r'real64'
t_DT_SINT16 = r'sint16'
t_DT_SINT32 = r'sint32'
t_DT_SINT64 = r'sint64'
t_DT_SINT8 = r'sint8'
t_DT_STR = r'string'
t_DT_UINT16 = r'uint16'
t_DT_UINT32 = r'uint32'
t_DT_UINT64 = r'uint64'
t_DT_UINT8 = r'uint8'
t_ENABLEOVERRIDE = r'enableoverride'
t_FLAVOR = r'flavor'
t_INDICATION = r'indication'
t_INSTANCE = r'instance'
t_METHOD = r'method'
t_NULL = r'null'
t_OF = r'of'
t_PARAMETER = r'parameter'
t_PRAGMA = r'\#pragma'
t_PROPERTY = r'property'
t_QUALIFIER = r'qualifier'
t_REF = r'ref'
t_REFERENCE = r'reference'
t_RESTRICTED = r'restricted'
t_SCHEMA = r'schema'
t_SCOPE = r'scope'
t_TOSUBCLASS = r'tosubclass'
t_TRANSLATABLE = r'translatable'

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
lex.lex(debug=1)


if __name__ == '__main__':
    lex.runmain()
