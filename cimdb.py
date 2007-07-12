#
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

# Author: Jon Carey <jcarey novell.com>

import os, pywbem, apsw
import cPickle as pickle
import operator

_REPDIR = './repository'

##############################################################################
def _createdb(dbname):
    conn = apsw.Connection(dbname)
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE QualifierTypes('
            'name TEXT NOT NULL COLLATE NOCASE,'
            'data BLOB NOT NULL,'
            'PRIMARY KEY(name COLLATE NOCASE));'
        'CREATE TABLE Classes('
            'cid INTEGER PRIMARY KEY,'
            'name TEXT NOT NULL COLLATE NOCASE,'
            'data BLOB NOT NULL,'
            'UNIQUE(name COLLATE NOCASE));'
        'CREATE TABLE SuperClasses('
            'subcid INTEGER NOT NULL CHECK(subcid > 0),'
            'supercid INTEGER NOT NULL CHECK(supercid > 0),'
            'depth INTEGER NOT NULL CHECK(depth > 0),'
            'CHECK(subcid != supercid),'
            'PRIMARY KEY(subcid, supercid),'
            'UNIQUE(subcid, depth));'
        'CREATE INDEX SuperCIDNDX on SuperClasses(supercid, depth);'
        'CREATE TABLE Instances('
            'classname TEXT NOT NULL COLLATE NOCASE,'
            'strkey TEXT NOT NULL,'
            'data BLOB NOT NULL,'
            'PRIMARY KEY(classname COLLATE NOCASE, strkey));'
        'CREATE TABLE RefInfo('
            'assoccid INTEGER NOT NULL,'
            'refpropcid INTEGER NOT NULL,'
            'refpropname TEXT NOT NULL COLLATE NOCASE,'
            'PRIMARY KEY(assoccid, refpropcid, refpropname));')
    return conn

##############################################################################
def _makedbname(namespace):
    int_ns = '~'.join([x for x in namespace.split('/') if x]) + '.db'
    return _REPDIR + '/' + int_ns

##############################################################################
def _namespace_exists(namespace):
    return os.path.exists(_makedbname(namespace))

##############################################################################
def _getdbconnection(namespace):
    if not namespace or not _namespace_exists(namespace):
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_NAMESPACE,
            'Namespace %s does not exist' % namespace)
    dbname = _makedbname(namespace)
    return apsw.Connection(dbname)

##############################################################################
class GeneratorConnection(object):
    def __init__(self, connection):
        self.conn = connection
        self.cursors = []
    def __del__(self):
        self.close()
    def close(self):
        if self.cursors:
            for c in self.cursors:
                c.close(True)
            operator.delslice(self.cursors, 0, len(self.cursors))
        self.conn.close(True)
    def get_cursor(self):
        c = self.conn.cursor()
        self.cursors.append(c)
        return c

##############################################################################
def _get_generator_connection(namespace):
    conn = _getdbconnection(namespace)
    return GeneratorConnection(conn)

##############################################################################
def DeleteNamespace(namespace):
    if not _namespace_exists(namespace):
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_NAMESPACE)
    os.remove(_makedbname(namespace))
        
##############################################################################
def CreateNamespace(namespace):
    if _namespace_exists(namespace):
        raise pywbem.CIMError(pywbem.CIM_ERR_ALREADY_EXISTS)
    # Create db for namespace
    conn = _createdb(_makedbname(namespace))
    conn.close(True)

##############################################################################
def Namespaces():
    for fname in os.listdir(_REPDIR):
        if fname.endswith('.db'):
            fname = fname[0:-3]
            name = '/'.join(fname.split('~'))
            if _namespace_exists(name):
                yield name

##############################################################################
def GetQualifier(QualifierName, namespace, Connection=None):
    conn = Connection or _getdbconnection(namespace)
    cqt = None
    try:
        cursor = conn.cursor()
        cursor.execute('select data from QualifierTypes where name=?',
                (QualifierName,))
        try:
            data, = cursor.next()
        except StopIteration:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)
        cursor.close(True)
        cqt = pickle.loads(str(data))
        Connection or conn.close(True)
    except:
        Connection or conn.close(True)
        raise
    return cqt

##############################################################################
def SetQualifier(QualifierDeclaration, namespace):
    conn = _getdbconnection(namespace)
    try:
        cursor = conn.cursor()
        pargq = pickle.dumps(QualifierDeclaration, pickle.HIGHEST_PROTOCOL)
        try:
            cqt = GetQualifier(QualifierDeclaration.name, namespace, conn)
        except pywbem.CIMError: 
            cqt = None

        if cqt:
            cursor.execute('update QualifierTypes set data=? where name=?',
                (buffer(pargq), QualifierDeclaration.name))
        else:
            cursor.execute('insert into QualifierTypes values(?,?)',
                (QualifierDeclaration.name, buffer(pargq)))
        conn.close(True)
    except:
        conn.close(True)
        raise

##############################################################################
def DeleteQualifier(QualifierName, namespace):
    conn = _getdbconnection(namespace)
    try:
        cursor = conn.cursor()
        if not GetQualifier(QualifierName, namespace, conn):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)
        cursor.execute(
            'delete from QualifierTypes where name=?', (QualifierName,))
        conn.close(True)
    except:
        conn.close(True)
        raise

##############################################################################
def EnumerateQualifiers(namespace):
    conn = _get_generator_connection(namespace)
    try:
        cursor = conn.get_cursor()
        for data, in cursor.execute('select data from QualifierTypes'):
            yield pickle.loads(str(data))
        conn.close()
    except:
        conn.close()
        raise

##############################################################################
def _valid_qualifier(conn, qualname):
    cc = False 
    cursor = conn.cursor()
    cursor.execute('select name from QualifierTypes where name=?',
            (qualname,))
    try:
        cursor.next()
        cc = True
    except StopIteration:
        pass
    cursor.close(True)
    return cc

##############################################################################
def _verify_qualifier_set(conn, qualset):
    for qualname,qual in qualset.iteritems():
        if not _valid_qualifier(conn, qualname):
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                'Qualifier %s is invalid' % qualname)
        # Set flavors to defaults if not specified
        if qual.overridable is None:
            qual.overridable = True
        if qual.tosubclass is None:
            qual.tosubclass = True
        if qual.translatable is None:
            qual.translatable = False
        if qual.toinstance is None:
            qual.toinstance = False

##############################################################################
def _verify_qualifiers(conn, theclass):
    # Verify class qualifiers
    _verify_qualifier_set(conn, theclass.qualifiers)

    # Verify property qualifiers
    for prop in theclass.properties.itervalues():
        _verify_qualifier_set(conn, prop.qualifiers)

    # Verify method qualifiers
    for meth in theclass.methods.itervalues():
        _verify_qualifier_set(conn, meth.qualifiers)

##############################################################################
def _adjust_root_class(theclass):
    for qual in theclass.qualifiers.itervalues():
        qual.propagated = False
    for prop in theclass.properties.itervalues():
        prop.propagated = False
        prop.class_origin = theclass.classname
    for meth in theclass.methods.itervalues():
        meth.propagated = False
        meth.class_origin = theclass.classname
    return theclass

##############################################################################
# Assumption: parent_class has already been resolved
def _adjust_child_class(child_class, parent_class):
    # Sync quals
    quals = pywbem.NocaseDict()

    # Make sure 
    if 'association' in child_class.qualifiers and \
            'association' not in parent_class.qualifiers:
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
            'Association class %s is derived from not Association class %s' % \
                (child_class.classname, parent_class.classname))
    is_association = 'association' in parent_class.qualifiers

    for child_qual_name, child_qual in child_class.qualifiers.iteritems():
        # Is the child qualifier in the parent class
        if child_qual_name in parent_class.qualifiers:
            parent_qual = parent_class.qualifiers[child_qual_name]
            # If the value of the qual is not the same, we save it if the
            # qual is overridable
            if parent_qual.value != child_qual.value:
                if not parent_qual.overridable:
                    # Child can change this qualifier because it is not
                    # overridable by subclasses
                    raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        'Parent class qualifier %s does not have OVERRIDABLE '
                        'flavor. Child cannot override it' % child_qual_name)
                quals[child_qual_name] = child_qual
        else:
            quals[child_qual_name] = child_qual
    child_class.qualifiers = quals

    # Sync properties
    parent_has_keys = None
    props = pywbem.NocaseDict()
    for child_prop_name, child_prop in child_class.properties.iteritems():
        if child_prop_name not in parent_class.properties:
            # This property was introduced by the child class.

            # If ref and this is not an association, raise and exception
            if not is_association and child_prop.type == 'reference':
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    'Reference property an only be defined in an Association '
                    'class')

            # If it is a key property, make sure no keys have been defined
            # in any superclass
            if 'key' in child_prop.qualifiers:
                if parent_has_keys is None:
                    parent_has_keys = False
                    for p in parent_class.properties.itervalues():
                        if 'key' in p.qualifiers:
                            parent_has_keys = True
                            break
                if parent_has_keys:
                    raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        'Parent class has keys. Child cannot define '
                        'additional key properties. Child class: %s '
                        'property name: %s' % \
                        (child_class.classname, child_prop.name))
            child_prop.class_origin = child_class.classname
            child_prop.propagated = False
            props[child_prop_name] = child_prop
            continue

        # This property is in the parent and child class
        parent_prop = parent_class.properties[child_prop_name]

        # If child did not override this property, then don't
        # save it unless it has a different default value
        if 'override' not in child_prop.qualifiers:
            if child_prop.value:
                if parent_prop.value and child_prop.value != parent_prop.value:
                    child_prop.propagated = True
                    child_prop.class_origin = parent_prop.class_origin
                    props[child_prop_name] = parent_prop
                    props[child_prop_name].value = child_prop.value
            continue

        # Child as specified 'override' on this property

        # Turn off 'tosubclass' for the override qual so children of
        # this class don't automatically get it (They have to
        # explicitly specify 'override'
        child_prop.qualifiers['override'].tosubclass = False
        if not child_prop.class_origin:
            child_prop.class_origin = child_class.classname
            child_prop.propagated = False
        else:
            child_prop.class_origin = parent_class.classname
            child_prop.propagated = True

        # Make sure the quals are set on the overridden property
        for parent_prop_qual_name, parent_prop_qual in \
                parent_prop.qualifiers.iteritems():
            if not parent_prop_qual.overridable:
                if parent_prop_qual_name not in child_prop.qualifiers:
                    child_prop.qualifiers[parent_prop_qual_name] = \
                        parent_prop_qual
                else:
                    # Qual is not overridable but it is on the child
                    # property. Probably need to tell the caller that
                    # this condition exists, but we're going to
                    # silently set it to the parent's qual
                    child_prop.qualifiers[parent_prop_qual_name] = \
                        parent_prop_qual
            # Parent does allow override of qualifier.
            # If the qual has tosubclass (not restricted), then only
            # propagate it down if it's not overridden in the subclass
            elif parent_prop_qual.tosubclass:
                if parent_prop_qual_name not in child_prop.qualifiers:
                    child_prop.qualifiers[parent_prop_qual_name] = \
                        parent_prop_qual

        props[child_prop_name] = child_prop
    child_class.properties = props

    # properties now sync'ed. Now sync methods
    # TODO. Should do more validation here
    meths = pywbem.NocaseDict()
    for child_meth_name, child_method in child_class.methods.iteritems():
        if child_meth_name not in parent_class.methods:
            child_method.propagated = False
            child_method.class_origin = child_class.classname
            meths[child_meth_name] = child_method
            continue
        if child_method.qualifiers.has_key('override'):
            child_method.propagated = True
            child_method.class_origin = parent_class.classname
    child_class.methods = meths
    return child_class

##############################################################################
def CreateClass(NewClass, namespace):
    conn = _getdbconnection(namespace)
    try: 
        cursor = conn.cursor()
        # Make sure the class doesn't already exist
        cursor.execute('select cid from Classes where name=?',
            (NewClass.classname,))
        try:
            cursor.next()
            cursor.close(True)
            conn.close(True)
            raise pywbem.CIMError(pywbem.CIM_ERR_ALREADY_EXISTS)
        except StopIteration:
            pass

        # Validate all quals in class
        _verify_qualifiers(conn, NewClass)

        # If there is a super class then synchronize the class
        # with the super class
        if NewClass.superclass:
            scid, scc = _get_class(conn, NewClass.superclass, namespace,
                LocalOnly=False, IncludeQualifiers=True,
                IncludeClassOrigin=True)
            NewClass = _adjust_child_class(NewClass, scc)
        else:
            # There is no super class
            NewClass = _adjust_root_class(NewClass)

        pcc = pickle.dumps(NewClass, pickle.HIGHEST_PROTOCOL)
        cursor.execute('insert into Classes values(NULL,?,?)',
                (NewClass.classname, buffer(pcc)))
        cid = conn.last_insert_rowid()
        if NewClass.superclass:
            # create a single SuperClasses row for this class and its immediate
            # parent class
            cursor.execute('insert into SuperClasses values(?,?,1);',
                    (cid, scid))
            # Now create all the SuperClasses rows for any super classes of the
            # given class's super class
            cursor.execute('insert into SuperClasses select ?,supercid,'
                    'depth+1 from SuperClasses where subcid=?', (cid, scid))
        conn.close(True)
    except:
        conn.close(True)
        raise

##############################################################################
def ModifyClass(ModifiedClass, namespace):
    conn = _getdbconnection(namespace)
    try: 
        # Ensure the class exists
        try:
            oldcid, oldcc = _get_bare_class(conn, thename=ModifiedClass.classname)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)

        # Make sure all the quals are valid
        _verify_qualifiers(conn, ModifiedClass)

        if ModifiedClass.superclass:
            if ModifiedClass.superclass.lower() != oldcc.superclass.lower():
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    'Cannot change superclass when modifying class %s' \
                    % (ModifiedClass.superclass))
            try:
                scid, scc = _get_class(conn, ModifiedClass.superclass, namespace,
                    LocalOnly=False, IncludeQualifiers=True,
                    IncludeClassOrigin=True)
            except pywbem.CIMError:
                # This shouldn't happen
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    'Invalid super class %s' % (ModifiedClass.superclass))
            ModifiedClass = _adjust_child_class(ModifiedClass, scc)
        else:
            ModifiedClass = _adjust_root_class(ModifiedClass)

        cursor = conn.cursor()
        pcc = pickle.dumps(ModifiedClass, pickle.HIGHEST_PROTOCOL)
        cursor.execute('update Classes set data=? where name=?',
            (buffer(pcc), ModifiedClass.classname))
        conn.close(True)
    except:
        conn.close(True)
        raise
    
##############################################################################
def _get_bare_class(conn, thename=None, thecid=None):
    cc = None
    try:
        cursor = conn.cursor()
        if thename is not None:
            cursor.execute('select cid,data from Classes where name=?',
                (thename,))
        else:
            cursor.execute('select cid,data from Classes where cid=?',
                (thecid,))
        try:
            cid,data = cursor.next()
            theclass = pickle.loads(str(data))
            cursor.close(True)
            cc = (cid,theclass)
        except StopIteration:
            pass
    except:
        pass
    return cc

##############################################################################
def _merge_classes(child_class, parent_class):
    parent_class.qualifiers.update(child_class.qualifiers)
    parent_class.properties.update(child_class.properties)
    parent_class.methods.update(child_class.methods)
    parent_class.superclass = parent_class.classname
    parent_class.classname = child_class.classname
    return parent_class

##############################################################################
def _filter_class(cim_class, IncludeQualifiers, IncludeClassOrigin,
    PropertyList):
    if not IncludeQualifiers:
        cim_class.qualifiers = pywbem.NocaseDict()
    rmprops = []
    for prop_name, prop in cim_class.properties.iteritems():
        if PropertyList is not None and prop_name not in PropertyList:
            rmprops.append(prop_name)
            continue
        if not IncludeQualifiers:
            prop.qualifiers = pywbem.NocaseDict()
        if not IncludeClassOrigin:
            prop.class_origin = None
    if rmprops:
        for pname in rmprops:
            del cim_class.properties[pname]

    for meth in cim_class.methods.itervalues():
        if not IncludeQualifiers:
            meth.qualifiers = pywbem.NocaseDict()
        if not IncludeClassOrigin:
            meth.class_origin = None

    return cim_class
        
##############################################################################
def _get_class(conn, name, namespace, LocalOnly=False, IncludeQualifiers=True,
        IncludeClassOrigin=True, PropertyList=None):
    try:
        thecid,thecc = _get_bare_class(conn, thename=name)
    except TypeError:
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)

    if not thecc.superclass or LocalOnly:
        return (thecid, _filter_class(thecc, IncludeQualifiers, IncludeClassOrigin,
                    PropertyList))

    cursor = conn.cursor()
    # Get the cid values for all super classes. order descending by depth
    # of inheritance
    supercids = [x for x, in cursor.execute('select supercid from superclasses '
            'where subcid=? order by depth DESC', (thecid,))]
    if not supercids:
        return (thecid, _filter_class(thecc, IncludeQualifiers, IncludeClassOrigin,
                    PropertyList))

    try:
        scid,supercc = _get_bare_class(conn, thecid=supercids[0])
    except TypeError:
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, 'Super class does '
            'not exist for class %s. super class cid: %d',
                (name, supercids[0]))
    supercids = supercids[1:]
    for scid in supercids:
        tp = _get_bare_class(conn, thecid=scid)
        if tp is None:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, 'Super class does '
                'not exist for class %s. super class cid: %d', (name, scid))
        subcc = tp[1]
        supercc = _merge_classes(subcc, supercc)
    thecc = _merge_classes(thecc, supercc)
    return (thecid, _filter_class(thecc, IncludeQualifiers, IncludeClassOrigin,
                    PropertyList))

##############################################################################
def GetClass(ClassName, namespace, LocalOnly=True, IncludeQualifiers=True,
        IncludeClassOrigin=False, PropertyList=None, Connection=None):
    conn = Connection or _getdbconnection(namespace)
    try:
        tp = _get_class(conn, ClassName, namespace, LocalOnly, IncludeQualifiers,
            IncludeClassOrigin, PropertyList)
        Connection or conn.close(True)
        return tp[1]
    except:
        Connection or conn.close(True)
        raise

##############################################################################
def EnumerateClasses(ClassName=None, namespace=None, DeepInheritance=False, LocalOnly=True,
        IncludeQualifiers=True, IncludeClassOrigin=False):
    conn = _get_generator_connection(namespace)
    cursor = conn.get_cursor()
    if not ClassName:
        try:
            if DeepInheritance:
                for cname, in cursor.execute('select name from Classes;'):
                    tp = _get_class(conn, cname, namespace, LocalOnly,
                            IncludeQualifiers, IncludeClassOrigin)
                    yield tp[1]
            else:
                for cname, in cursor.execute('select name from Classes where cid '
                        'not in (select subcid from SuperClasses where depth=1);'):
                    tp = _get_class(conn, cname, namespace, LocalOnly,
                            IncludeQualifiers, IncludeClassOrigin)
                    yield tp[1]
            conn.close()
        except:
            conn.close()
            raise
        return

    # Class name specified
    try:
        try:
            # Make sure the class exists
            thecid,thecc = _get_bare_class(conn, thename=ClassName)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                'class %s does not exist' % ClassName)

        if DeepInheritance:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=?);', (thecid,)):
                tp = _get_class(conn, cname, namespace, LocalOnly,
                        IncludeQualifiers, IncludeClassOrigin)
                yield tp[1]
        else:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=? and depth=1);', (thecid,)):
                tp = _get_class(conn, cname, namespace, LocalOnly,
                        IncludeQualifiers, IncludeClassOrigin)
                yield tp[1]
        conn.close()
    except:
        conn.close()
        raise

##############################################################################
def EnumerateClassNames(ClassName=None, namespace=None, DeepInheritance=False):
    conn = _get_generator_connection(namespace)
    cursor = conn.get_cursor()
    if not ClassName:
        try:
            if DeepInheritance:
                for cname, in cursor.execute('select name from Classes;'):
                    yield cname
            else:
                for cname, in cursor.execute('select name from Classes where cid '
                        'not in (select subcid from SuperClasses where depth=1);'):
                    yield cname
            conn.close()
        except:
            conn.close()
            raise
        return

    # Class name specified
    try:
        try:
            # Make sure the class exists
            thecid,thecc = _get_bare_class(conn, thename=ClassName)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                'class %s does not exist' % ClassName)
        if DeepInheritance:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=?);', (thecid,)):
                yield cname
        else:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=? and depth=1);', (thecid,)):
                yield cname
        conn.close()
    except:
        conn.close()
        raise

##############################################################################
def DeleteClass(ClassName, namespace):
    conn = _getdbconnection(namespace)
    try:
        # Make sure the class exists
        try:
            thecid, thecc = _get_bare_class(conn, thename=ClassName)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)

        cursor = conn.cursor()
        # Get the names of all the classes that will be deleted.
        # Given class + children
        rmclasses = [x for x in cursor.execute('select name from Classes '
                'where cid in (select subcid from SuperClasses where '
                'supercid=?);', (thecid,))]
        rmclasses.append((ClassName,))

        # Remove all instances of the classes that will be removed
        cursor.executemany('delete from Instances where classname=?;',
                rmclasses)

        # Delete all entries in the superclass table for class and children
        cursor.execute('delete from SuperClasses where supercid=? or '
            'subcid=?;', (thecid,thecid))

        # Delete all entries from the Classes table
        cursor.executemany('delete from Classes where name=?;', rmclasses)
        conn.close(True)
    except:
        conn.close(True)
        raise

##############################################################################
def _filter_instance(instance, cim_class, IncludeQualifiers,
    IncludeClassOrigin, PropertyList):
    if not IncludeQualifiers:
        instance.qualifiers = pywbem.NocaseDict()
    rmprops = []
    for prop_name, prop in instance.properties.iteritems():
        if PropertyList is not None and prop_name not in PropertyList:
            rmprops.append(prop_name)
            continue
        # Ensure the property is in the class
        if prop_name not in cim_class.properties:
            rmprops.append(prop_name)
            continue
        if IncludeQualifiers:
            prop.qualifiers = cim_class.properties[prop_name].qualifiers
        else:
            prop.qualifiers = pywbem.NocaseDict()
        if IncludeClassOrigin:
            prop.class_origin = cim_class.properties[prop_name].class_origin
        else:
            prop.class_origin = None

    if rmprops:
        for pname in rmprops:
            del instance.properties[pname]
    return instance

##############################################################################
def GetInstance(InstanceName, LocalOnly=True,
        IncludeQualifiers=False, IncludeClassOrigin=False,
        PropertyList=None, Connection=None):
    conn = Connection or _getdbconnection(InstanceName.namespace)
    try:
        theclass = GetClass(InstanceName.classname, InstanceName.namespace, 
                LocalOnly, IncludeQualifiers=True, 
                IncludeClassOrigin=True, Connection=conn)
    except pywbem.CIMError:
        Connection or conn.close(True)
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)

    try:
        # Convert instance name to string
        strkey = _make_key_string(InstanceName)
        cursor = conn.cursor()
        cursor.execute('select data from Instances where strkey=?',
                (strkey,))
        try:
            data, = cursor.next()
            cursor.close(True)
            Connection or conn.close(True)
            ci = pickle.loads(str(data))
            return _filter_instance(ci, theclass, IncludeQualifiers,
                IncludeClassOrigin, PropertyList)
        except StopIteration:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)
    except:
        Connection or conn.close(True)
        raise

##############################################################################
def EnumerateInstances(ClassName, namespace, LocalOnly=True,
        DeepInheritance=True, IncludeQualifiers=False, 
        IncludeClassOrigin=False, PropertyList=None):
    conn = _get_generator_connection(namespace)
    cursor = conn.get_cursor()
    try:
        try:
            # Make sure the class exists
            thecid,thecc = _get_bare_class(conn, thename=ClassName)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_CLASS)

        classnames = [ClassName]

        if DeepInheritance:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=?);', (thecid,)):
                classnames.append(cname)
        else:
            for cname, in cursor.execute('select name from Classes where '
                    'cid in (select subcid from SuperClasses where '
                    'supercid=? and depth=1);', (thecid,)):
                classnames.append(cname)

        for cname in classnames:
            try:
                theclass = GetClass(cname, namespace, 
                        LocalOnly, IncludeQualifiers=True, 
                        IncludeClassOrigin=True, Connection=conn)
            except:
                # Log Error. Ignore?
                continue

            for data, in cursor.execute('select data from Instances where '
                    'classname=?', (cname,)):
                ci = pickle.loads(str(data))
                yield _filter_instance(ci, theclass, IncludeQualifiers,
                    IncludeClassOrigin, PropertyList)
        conn.close()
    except:
        conn.close()
        raise

##############################################################################
def EnumerateInstanceNames(ClassName, namespace):
    conn = _get_generator_connection(namespace)
    cursor = conn.get_cursor()
    try:
        try:
            # Make sure the class exists
            thecid,thecc = _get_bare_class(conn, thename=ClassName)
        except TypeError:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_CLASS)

        classnames = [ClassName]
        for cname, in cursor.execute('select name from Classes where '
                'cid in (select subcid from SuperClasses where '
                'supercid=?);', (thecid,)):
            classnames.append(cname)

        for cname in classnames:
            for data, in cursor.execute('select data from Instances where '
                    'classname=?', (cname,)):
                ci = pickle.loads(str(data))
                yield ci.path

        conn.close()
    except:
        conn.close()
        raise

##############################################################################
def _make_key_string(iname):
    kl = []
    # convert all values in keybindings to string
    for k,v in iname.keybindings.iteritems():
        try:
            # If this is a reference type, convert it
            # to a string using this function
            if isinstance(v, pywbem.CIMInstanceName):
                tv = make_key_string(v)
            else:
                tv = str(v)
        except TypeError:
            tv = str(v)
        kl.append([k.lower(),tv])

    # Sort the list by the key names
    kl.sort(key=lambda x:x[0])
    # Combine key/value, flatten
    kl = [''.join(x) for x in kl]
    # Insert the namespace at the beginning of the list
    kl.insert(0, iname.namespace)
    # Create 1 string out of the list
    return ''.join(kl)

##############################################################################
def CreateInstance(NewInstance):
    ipath = NewInstance.path
    if not ipath or not ipath.keybindings:
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
            'No key values for instance')
    class_name = NewInstance.classname;
    namespace = ipath.namespace
    conn = _getdbconnection(namespace)
    try:
        theclass = GetClass(NewInstance.classname, namespace, 
                LocalOnly=False, IncludeQualifiers=True, 
                IncludeClassOrigin=True, Connection=conn)
    except pywbem.CIMError:
        conn.close(True)
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_CLASS,
            'Class %s does not exist in namespace %s' \
            % (NewInstance.classname, namespace))

    try:
        # Convert instance name to string
        strkey = _make_key_string(NewInstance.path)
        cursor = conn.cursor()
        cursor.execute('select classname from Instances where strkey=?',
                (strkey,))
        try:
            cursor.next()
            cursor.close(True)
            conn.close(True)
            raise pywbem.CIMError(pywbem.CIM_ERR_ALREADY_EXISTS)
        except StopIteration:
            pass

        NewInstance.qualifiers = pywbem.NocaseDict()
        for prop in NewInstance.properties.itervalues():
            prop.qualifiers = pywbem.NocaseDict()
            prop.class_origin = None

        pd = pickle.dumps(NewInstance, pickle.HIGHEST_PROTOCOL)
        cursor.execute('insert into Instances values(?,?,?);',
                (class_name, strkey, buffer(pd)))
        conn.close(True)
        return ipath
    except:
        conn.close(True)
        raise

##############################################################################
def DeleteInstance(InstanceName):
    conn = _getdbconnection(InstanceName.namespace)
    # Ensure the class exists
    try:
        oldcid, oldcc = _get_bare_class(conn, thename=ModifiedClass.classname)
    except TypeError:
        conn.close(True)
        raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_CLASS)

    try:
        # Convert instance name to string
        strkey = _make_key_string(InstanceName)
        cursor = conn.cursor()
        cursor.execute('select classname from Instances where strkey=?',
                (strkey,))
        try:
            cursor.next()
            cursor.close(True)
        except StopIteration:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND)
        
        cursor = conn.cursor()
        # TODO deal with associations
        cursor.execute(
            'delete from Instances where strkey=?', (strkey,))
        conn.close(True)
    except: 
        conn.close(True)
        raise

##############################################################################
def ModifyInstance(ModifiedInstance, PropertyList=None):
    conn = _getdbconnection(ModifiedInstance.path.namespace)
    ipath = ModifiedInstance.path
    try:
        oldci = GetInstance(ipath, LocalOnly=False,
                    IncludeQualifiers=True, IncludeClassOrigin=False,
                    PropertyList=None, Connection=conn)
        if oldci.classname.lower() != ModifiedInstance.classname.lower():
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                'Cannot change class of instance')

        if PropertyList:
            for propname in PropertyList:
                if propname not in ipath: # Only update if not key property
                    if propname in ModifiedInstance.properties:
                        oldci.properties[propname] = \
                            ModifiedInstance.properties[propname]
                    elif propname in oldci.properties:
                        del oldci.properties[propname]
        else:
            for propname,prop in ModifiedInstance.properties.iteritems():
                # Only use non-key properties
                if propname not in ipath:
                    oldci[propname] = prop

        strkey = _make_key_string(ipath)
        pci = pickle.dumps(oldci, pickle.HIGHEST_PROTOCOL)
        cursor = conn.cursor()
        cursor.execute('update Instances set data=? where strkey=?',
                (buffer(pci), strkey))
        conn.close(True)
    except:
        conn.close(True)
        raise

#if __name__ == '__main__':
#   Testing


