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

import sys
import os
import ply.lex as lex
import ply.yacc as yacc
from ply.lex import TOKEN
import pywbem

reserved = {
    'any':'ANY',
    'as':'AS',
    'association':'ASSOCIATION',
    'class':'CLASS',
    'disableoverride':'DISABLEOVERRIDE',
    'boolean':'DT_BOOL',
    'char16':'DT_CHAR16',
    'datetime':'DT_DATETIME',
    'pragma':'PRAGMA',
    'real32':'DT_REAL32',
    'real64':'DT_REAL64',
    'sint16':'DT_SINT16',
    'sint32':'DT_SINT32',
    'sint64':'DT_SINT64',
    'sint8':'DT_SINT8',
    'string':'DT_STR',
    'uint16':'DT_UINT16',
    'uint32':'DT_UINT32',
    'uint64':'DT_UINT64',
    'uint8':'DT_UINT8',
    'enableoverride':'ENABLEOVERRIDE',
    'false':'FALSE',
    'flavor':'FLAVOR',
    'indication':'INDICATION',
    'instance':'INSTANCE',
    'method':'METHOD',
    'null':'NULL',
    'of':'OF',
    'parameter':'PARAMETER',
    'property':'PROPERTY',
    'qualifier':'QUALIFIER',
    'ref':'REF',
    'reference':'REFERENCE',
    'restricted':'RESTRICTED',
    'schema':'SCHEMA',
    'scope':'SCOPE',
    'tosubclass':'TOSUBCLASS',
    'translatable':'TRANSLATABLE',
    'true':'TRUE',
    }

tokens = reserved.values() + [
        'IDENTIFIER',
        'stringValue',
        'floatValue',
        'charValue',
        'binaryValue',
        'octalValue',
        'decimalValue',
        'hexValue',
    ]

literals = '#(){};[],$:='

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

utf8Char = r'(%s)|(%s)|(%s)|(%s)|(%s)|(%s)|(%s)|(%s)' % (utf8_2, utf8_3_1,
        utf8_3_2, utf8_3_3, utf8_3_4, utf8_4_1, utf8_4_2, utf8_4_3)

def t_COMMENT(t):
    r'//.*'
    pass

def t_MCOMMENT(t):
    r' /\*(.|\n)*?\*/'
    t.lineno += t.value.count('\n')


t_binaryValue = r'[+-]?[01]+[bB]'
t_octalValue = r'[+-]?0[0-7]+'
t_decimalValue = r'[+-]?([1-9][0-9]*|0)'
t_hexValue = r'[+-]?0[xX][0-9a-fA-F]+'
t_floatValue = r'[+-]?[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?'

simpleEscape = r"""[bfnrt'"\\]"""
hexEscape = r'x[0-9a-fA-F]{1,4}'
escapeSequence = r'[\\]((%s)|(%s))' % (simpleEscape, hexEscape)
cChar = r"[^'\\\n\r]|(%s)" % escapeSequence
sChar = r'[^"\\\n\r]|(%s)' % escapeSequence
charValue = r"'%s'" % cChar

t_stringValue = r'"(%s)*"' % sChar

identifier_re = r'([a-zA-Z_]|(%s))([0-9a-zA-Z_]|(%s))*' % (utf8Char, utf8Char)

@TOKEN(identifier_re)
def t_IDENTIFIER(t):
    t.type = reserved.get(t.value.lower(),'IDENTIFIER') # check for reserved word
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.linestart = t.lexpos

t_ignore = ' \r\t'

# Error handling rule
def t_error(t):
    msg = "Illegal character '%s' " % t.value[0]
    msg+= "Line %d, col %d" % (t.lineno, find_column(mof, t))
    print msg
    t.lexer.skip(1)

def p_mofSpecification(p):
    """mofSpecification : mofProductionList"""

def p_mofProductionList(p):
    """mofProductionList : empty
                         | mofProductionList mofProduction
                           """

def p_mofProduction(p):
    """mofProduction : compilerDirective
                     | classDeclaration
                     | assocDeclaration
                     | indicDeclaration
                     | qualifierDeclaration
                     | instanceDeclaration
                     """

def p_compilerDirective(p): 
    """compilerDirective : '#' PRAGMA pragmaName '(' pragmaParameter ')'"""
    directive = p[3].lower()
    param = p[5]
    if directive == 'include':
        fname = os.path.dirname(p.parser.file) + '/' + param
        print 'Compiling', fname
        f = open(fname, 'r')
        mof = f.read()
        f.close()
        parser = yacc.yacc()
        parser.file = fname
        parser.mof = mof
        lexer = lex.lex()
        lexer.parser = parser
        parser.ns = p.parser.ns
        parser.parse(mof, lexer=lexer)
    elif directive == 'namespace':
        p.parser.ns = param
    
    p[0] = None

def p_pragmaName(p):
    """pragmaName : identifier"""
    p[0] = p[1]

def p_pragmaParameter(p):
    """pragmaParameter : stringValue"""
    p[0] = p[1][1:-1]

def p_classDeclaration(p):
    """classDeclaration : CLASS className '{' classFeatureList '}' ';'
                        | CLASS className superClass '{' classFeatureList '}' ';'
                        | CLASS className alias '{' classFeatureList '}' ';'
                        | CLASS className alias superClass '{' classFeatureList '}' ';'
                        | qualifierList CLASS className '{' classFeatureList '}' ';'
                        | qualifierList CLASS className superClass '{' classFeatureList '}' ';'
                        | qualifierList CLASS className alias '{' classFeatureList '}' ';'
                        | qualifierList CLASS className alias superClass '{' classFeatureList '}' ';'
                        """

def p_classFeatureList(p):
    """classFeatureList : empty
                        | classFeatureList classFeature
                        """

def p_assocDeclaration(p):
    """assocDeclaration : '[' ASSOCIATION qualifierListEmpty ']' CLASS className '{' associationFeatureList '}' ';'
                        | '[' ASSOCIATION qualifierListEmpty ']' CLASS className superClass '{' associationFeatureList '}' ';'
                        | '[' ASSOCIATION qualifierListEmpty ']' CLASS className alias '{' associationFeatureList '}' ';'
                        | '[' ASSOCIATION qualifierListEmpty ']' CLASS className alias superClass '{' associationFeatureList '}' ';'
                        """
    
def p_qualifierListEmpty(p):
    """qualifierListEmpty : empty
                          | qualifierListEmpty ',' qualifier
                          """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[3]]

def p_associationFeatureList(p):
    """associationFeatureList : empty 
                              | associationFeatureList associationFeature
                              """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]

def p_indicDeclaration(p):
    """indicDeclaration : '[' INDICATION qualifierListEmpty ']' CLASS className '{' classFeatureList '}' ';'
                        | '[' INDICATION qualifierListEmpty ']' CLASS className superClass '{' classFeatureList '}' ';'
                        | '[' INDICATION qualifierListEmpty ']' CLASS className alias '{' classFeatureList '}' ';'
                        | '[' INDICATION qualifierListEmpty ']' CLASS className alias superClass '{' classFeatureList '}' ';'
                        """

def p_className(p):
    """className : identifier"""
    p[0] = p[1]

def p_alias(p):
    """alias : AS aliasIdentifier"""
    p[0] = p[2]

def p_aliasIdentifier(p):
    """aliasIdentifier : '$' identifier"""
    p[0] = p[2]

def p_superClass(p):
    """superClass : ':' className"""
    p[0] = p[2]

def p_classFeature(p):
    """classFeature : propertyDeclaration
                    | methodDeclaration
                    | referenceDeclaration
                    """
    p[0] = p[1]

def p_associationFeature(p):
    """associationFeature : classFeature"""
    p[0] = p[1]

def p_qualifierList(p):
    """qualifierList : '[' qualifier qualifierListEmpty ']'"""
    p[0] = [p[2]] + p[3]

def p_qualifier(p): 
    """qualifier : qualifierName
                 | qualifierName ':' flavorList
                 | qualifierName qualifierParameter
                 | qualifierName qualifierParameter ':' flavorList
                 """
    qname = p[1]
    qval = None
    flavorlist = []
    if len(p) == 3:
        qval = p[2]
    elif len(p) == 4:
        flavorlist = p[3]
    elif len(p) == 5:
        qval = p[2]
        flavorlist = p[4]
    # TODO build qualifier

def p_flavorList(p):
    """flavorList : flavor
                  | flavorList flavor
                  """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_qualifierParameter(p):
    """qualifierParameter : '(' constantValue ')'
                          | arrayInitializer
                          """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_flavor(p):
    """flavor : ENABLEOVERRIDE
              | DISABLEOVERRIDE
              | RESTRICTED
              | TOSUBCLASS
              | TRANSLATABLE
              """
    p[0] = p[1].upper()

def p_propertyDeclaration(p):
    """propertyDeclaration : dataType propertyName ';'
                           | dataType propertyName defaultValue ';'
                           | dataType propertyName array ';'
                           | dataType propertyName array defaultValue ';'
                           | qualifierList dataType propertyName ';'
                           | qualifierList dataType propertyName defaultValue ';'
                           | qualifierList dataType propertyName array ';'
                           | qualifierList dataType propertyName array defaultValue ';'
                           """

def p_referenceDeclaration(p):
    """referenceDeclaration : objectRef referenceName ';'
                            | objectRef referenceName defaultValue ';'
                            | qualifierList objectRef referenceName ';'
                            | qualifierList objectRef referenceName defaultValue ';'
                            """

def p_methodDeclaration(p):
    """methodDeclaration : dataType methodName '(' ')' ';'
                         | dataType methodName '(' parameterList ')' ';'
                         | qualifierList dataType methodName '(' ')' ';'
                         | qualifierList dataType methodName '(' parameterList ')' ';'
                         """

def p_propertyName(p):
    """propertyName : identifier"""
    p[0] = p[1]

def p_referenceName(p):
    """referenceName : identifier"""
    p[0] = p[1]

def p_methodName(p):
    """methodName : identifier"""
    p[0] = p[1]

def p_dataType(p):
    """dataType : DT_UINT8
                | DT_SINT8
                | DT_UINT16
                | DT_SINT16
                | DT_UINT32
                | DT_SINT32
                | DT_UINT64
                | DT_SINT64
                | DT_REAL32
                | DT_REAL64
                | DT_CHAR16
                | DT_STR
                | DT_BOOL
                | DT_DATETIME
                """
    p[0] = p[1].lower()

def p_objectRef(p):
    """objectRef : className REF"""

def p_parameterList(p):
    """parameterList : parameter
                     | parameterList ',' parameter
                     """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]
def p_parameter(p):
    """parameter : dataType parameterName
                 | dataType parameterName array
                 | qualifierList dataType parameterName
                 | qualifierList dataType parameterName array
                 | objectRef parameterName
                 | objectRef parameterName array
                 | qualifierList objectRef parameterName
                 | qualifierList objectRef parameterName array
                 """

def p_parameterName(p):
    """parameterName : identifier"""
    p[0] = p[1]

def p_array(p):
    """array : '[' ']'
             | '[' integerValue ']'
             """
    if len(p) == 3:
        p[0] = -1
    else:
        print p[2]
        p[0] = p[2]

def p_defaultValue(p):
    """defaultValue : '=' initializer"""
    p[0] = p[2]

def p_initializer(p):
    """initializer : constantValue
                   | arrayInitializer
                   | referenceInitializer"""

def p_arrayInitializer(p):
    """arrayInitializer : '{' constantValueList '}'
                        | '{' '}'
                        """
    if len(p) == 3:
        p[0] = []
    else:
        p[0] = p[2]

def p_constantValueList(p):
    """constantValueList : constantValue
                         | constantValueList ',' constantValue
                         """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_stringValueList(p):
    """stringValueList : stringValue
                       | stringValueList stringValue
                       """
    if len(p) == 2:
        p[0] = p[1][1:-1]
    else:
        p[0] = p[1] + p[2][1:-1]


def p_constantValue(p):
    """constantValue : integerValue
                     | floatValue
                     | charValue
                     | stringValueList
                     | booleanValue
                     | nullValue
                     """
    p[0] = p[1]

def p_integerValue(p):
    """integerValue : binaryValue
                    | octalValue
                    | decimalValue
                    | hexValue
                    """
    p[0] = int(p[1])
    # TODO deal with non-decimal values. 

def p_referenceInitializer(p):
    """referenceInitializer : objectHandle
                            | aliasIdentifier"""

def p_objectHandle(p):
    """objectHandle : identifier"""

def p_qualifierDeclaration(p):
    """qualifierDeclaration : QUALIFIER qualifierName qualifierType scope ';'
                            | QUALIFIER qualifierName qualifierType scope defaultFlavor ';'
                            """
    qualtype = p[3]
    dt, is_array, array_size, value = qualtype
    qualname = p[2]
    scopes = p[4]
    if len(p) == 5:
        flavors = {}
    else:
        flavors = p[5]
    p[0] = pywbem.CIMQualifierDeclaration(qualname, dt, value=value, 
                    is_array=is_array, array_size=array_size, 
                    scopes=scopes, flavors=flavors)
    print p[0]


def p_qualifierName(p):
    """qualifierName : identifier
                     | ASSOCIATION
                     | INDICATION
                     """
    p[0] = p[1]

def p_qualifierType(p):
    """qualifierType : qualifierTypeArray
                     | qualifierTypeNoArray
                     """
    p[0] = p[1]

def p_qualifierTypeArray(p):
    """qualifierTypeArray : ':' dataType array
                          | ':' dataType array defaultValue
                          """
    if len(p) == 4:
        dv = None
    else:
        dv = p[4]
    p[0] = (p[2], True, p[3], dv)

def p_qualifierTypeNoArray(p):
    """qualifierTypeNoArray : ':' dataType
                            | ':' dataType defaultValue
                            """
    if len(p) == 3:
        dv = None
    else:
        dv = p[3]
    p[0] = (p[2], False, -1, dv)

def p_scope(p):
    """scope : ',' SCOPE '(' metaElementList ')'"""
    slist = p[4]
    scopes = {}
    for i in ('SCHEMA',
              'CLASS',
              'ASSOCIATION',
              'INDICATION',
              'QUALIFIER',
              'PROPERTY',
              'REFERENCE',
              'METHOD',
              'PARAMETER',
              'ANY'):
        scopes[i] = i in slist
    p[0] = scopes

def p_metaElementList(p):
    """metaElementList : metaElement
                       | metaElementList ',' metaElement
                       """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_metaElement(p):
    """metaElement : SCHEMA
                   | CLASS
                   | ASSOCIATION
                   | INDICATION
                   | QUALIFIER
                   | PROPERTY
                   | REFERENCE
                   | METHOD
                   | PARAMETER
                   | ANY
                   """
    p[0] = p[1].upper()

def p_defaultFlavor(p):
    """defaultFlavor : ',' FLAVOR '(' flavorListWithComma ')'"""
    flist = p[4]
    flavors = {'ENABLEOVERRIDE':True,
               'TOSUBCLASS':True,
               'DISABLEOVERRIDE':False,
               'RESTRICTED':False,
               'TRANSLATABLE':False}
    for i in flist:
        flavors[i] = True
    p[0] = flavors


def p_flavorListWithComma(p):
    """flavorListWithComma : flavor
                           | flavorListWithComma ',' flavor
                           """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_instanceDeclaration(p):
    """instanceDeclaration : INSTANCE OF className '{' valueInitializerList '}' ';'
                           | INSTANCE OF className alias '{' valueInitializerList '}' ';'
                           | qualifierList INSTANCE OF className '{' valueInitializerList '}' ';'
                           | qualifierList INSTANCE OF className alias '{' valueInitializerList '}' ';'
                           """
    if p[1].lower() == 'instance': # no qualifiers
        quals = {}
        if p[4] == '{':
            props = p[5]
            alias = None
        else:
            props = p[6]
            alias = p[4]
    else:
        quals = {} # qualifiers on instances are deprecated -- rightly so. 
        if p[5] == '{':
            props = p[6]
            alias = None
        else:
            props = p[7]
            alias = p[5]

    # TODO: fetch class, create inst. 
    if alias is not None:
        p.parser.aliases[alias] = inst


def p_valueInitializerList(p):
    """valueInitializerList : valueInitializer
                            | valueInitializerList valueInitializer
                            """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]
    

def p_valueInitializer(p):
    """valueInitializer : identifier defaultValue ';'
                        | qualifierList identifier defaultValue ';'
                        """
    if len(p) == 4:
        id = p[1]
        val = p[2]
        quals = []
    else:
        quals = p[1]
        id = p[2]
        quals = p[3]
    p[0] = (quals, id, val)

def p_booleanValue(p):
    """booleanValue : FALSE
                    | TRUE
                    """
    p[0] = p[1].lower() == 'true'

def p_nullValue(p):
    """nullValue : NULL"""
    p[0] = None

def p_identifier(p):
    """identifier : IDENTIFIER
                  | ANY
                  | AS
                  | CLASS
                  | DISABLEOVERRIDE
                  | dataType 
                  | ENABLEOVERRIDE
                  | FLAVOR
                  | INSTANCE
                  | METHOD
                  | OF
                  | PARAMETER
                  | PRAGMA
                  | PROPERTY
                  | QUALIFIER
                  | REFERENCE
                  | RESTRICTED
                  | SCHEMA
                  | SCOPE
                  | TOSUBCLASS
                  | TRANSLATABLE
                  """
                  #| ASSOCIATION
                  #| INDICATION
    p[0] = p[1]

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    print 'Syntax Error in input!'
    print p
    print 'column: ', find_column(p.lexer.parser.mof, p)

def find_column(input, token):
    i = token.lexpos
    while i > 0:
        if input[i] == '\n':
            break
        i-= 1
    column = (token.lexpos - i)+1
    return column


if __name__ == '__main__':
    #lex.runmain()
    #sys.exit(0)
    global mof
    lexer = lex.lex()
    parser = yacc.yacc()
    fname = sys.argv[1]
    f = open(fname, 'r')
    parser.file = fname
    lexer.parser = parser
    parser.mof = f.read() 
    f.close()
    parser.ns = 'root/cimv2'
    parser.parse(parser.mof, lexer=lexer)
    sys.exit(0)

    for w in os.walk('/usr/share/mof'):
        for f in w[2]:
            if not f.endswith('.mof'):
                continue
            file = '%s/%s' % (w[0], f)
            print 'Parsing', file
            f = open(file, 'r')
            mof = f.read()
            f.close()
            parser.parse(mof, lexer=lexer)

