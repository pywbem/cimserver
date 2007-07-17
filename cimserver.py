#
# (C) Copyright 2007 Novell, Inc. 
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

# Author: Bart Whiteley <bwhiteley suse.de>

import pywbem
import sys
from pywbem import tupleparse
import cimdb
from socket import getfqdn
import internal_providers

class Logger(object):
    def __init__(self, fobj):
        self.file = fobj

    def log_debug(self, str):
        print >> self.file, str

    def log_info(self, str):
        print >> self.file, str

class ProviderEnvironment(object):

    def __init__(self, logger, cimom_handle):
        self.logger = logger
        self.cimom_handle = cimom_handle

    def get_logger(self):
        return self.logger

    def get_cimom_handle(self):
        return self.cimom_handle

    def get_user_name(self):
        # TODO
        return 'root'

class CIMServer(object):
    PROVIDERTYPE_INSTANCE = 1
    PROVIDERTYPE_ASSOCIATION = 3
    PROVIDERTYPE_LIFECYCLE_INDICATION = 4
    PROVIDERTYPE_ALERT_INDICATION = 5
    PROVIDERTYPE_METHOD = 6
    PROVIDERTYPE_INDICATION_HANDLER = 7
    PROVIDERTYPE_POLLED = 8
    PROVIDERTYPE_QUERY = 9

    def __init__(self):
        self.env = ProviderEnvironment(Logger(sys.stdout), self)
        self.provregs = {}
        for inst in cimdb.EnumerateInstances('OpenWBEM_PyProviderRegistration', namespace='Interop'):
            cname = inst['classname']
            mp = inst['modulepath']
            pts = inst['providertypes']
            nss = inst['namespacenames']
            methods = inst['methodnames']
            if not nss:
                nss = [""]
            for ns in nss:
                key = ns
                if key:
                    key+= ':'
                key+= cname.lower() 
                self.provregs[key] = (mp, pts, methods)
        for cname in ['cim_namespace']:
            self.provregs[cname] = (internal_providers, 
                                    [self.PROVIDERTYPE_INSTANCE], [])
        print 'provregs: ', `self.provregs`

    def _get_provider(self, ns, class_name, type, method_name=None):
        lcname = class_name.lower()
        key = '%s:%s' % (ns, lcname)
        provreg = None
        for kn in [key, lcname]:
            try:
                provreg = self.provregs[kn]
                if type in provreg[1]:
                    break
                provreg = None
            except KeyError:
                pass
        if not provreg: 
            return None
        return pywbem.cim_provider.ProviderProxy(self.env, provreg[0])

    def AssociatorNames(self, *args, **kwargs):
        # TODO
        return None
    def Associators(self, *args, **kwargs):
        # TODO
        return None
    def CreateClass(self, *args, **kwargs):
        # TODO
        return None
    def CreateInstance(self, *args, **kwargs):
        del kwargs['namespace']
        cimdb.CreateInstance(*args, **kwargs)
    def DeleteClass(self, *args, **kwargs):
        # TODO
        return None
    def DeleteInstance(self, *args, **kwargs):
        # TODO
        return None
    def DeleteQualifier(self, *args, **kwargs):
        # TODO
        return None
    def GetClass(self, ClassName, namespace=None,
                 LocalOnly=True, IncludeQualifiers=True, 
                 IncludeClassOrigin=False, PropertyList=None):
        return cimdb.GetClass(ClassName, namespace, 
                               LocalOnly=LocalOnly,
                               IncludeQualifiers=IncludeQualifiers,
                               IncludeClassOrigin=IncludeClassOrigin,
                               PropertyList=PropertyList)
    def EnumerateClassNames(self, ClassName=None, namespace=None, 
                            DeepInheritance=False):
        for cn in cimdb.EnumerateClassNames(className, namespace=None, 
                                         DeepInheritance=DeepInheritance):
            yield cn
    def EnumerateClasses(self, ClassName=None, namespace=None, 
                         DeepInheritance=False, 
                         LocalOnly=True, IncludeQualifiers=True, 
                         IncludeClassOrigin=False):
        for cc in cimdb.EnumerateClasses(ClassName, namespace, 
                                     DeepInheritance=DeepInheritance,
                                     LocalOnly=LocalOnly,
                                     IncludeQualifiers=IncludeQualifiers,
                                     IncludeClassOrigin=IncludeClassOrigin):
            yield cc
    def _classtree(self, ClassName, namespace):
        """Return the specified CIMClass, all its subclasses"""
        cc = cimdb.GetClass(ClassName, namespace=namespace, 
                LocalOnly=False, IncludeQualifiers=True, 
                IncludeClassOrigin=True)
        yield cc
        for cc in cimdb.EnumerateClasses(ClassName, namespace=namespace, 
                LocalOnly=False, IncludeQualifiers=True, 
                IncludeClassOrigin=True, DeepInheritance=True):
            yield cc

    def EnumerateInstanceNames(self, ClassName, namespace):
        for cc in self._classtree(ClassName, namespace):
            print 'cc:', cc
            provider = self._get_provider(namespace, cc.classname, 
                                          self.PROVIDERTYPE_INSTANCE)
            if provider is not None:
                gen = provider.MI_enumInstanceNames(self.env, namespace, cc)
                for i in gen:
                    yield i

    def EnumerateInstances(self, namespace, ClassName, LocalOnly=True, 
            DeepInheritance=True, IncludeQualifiers=False, 
            IncludeClassOrigin=False, PropertyList=None):
        for cc in self._classtree(ClassName, namespace):
            provider = self._get_provider(namespace, cc.classname, 
                                          self.PROVIDERTYPE_INSTANCE)
            if provider is not None:
                gen = provider.MI_enumInstances(self.env, namespace, 
                        propertyList=PropertyList, 
                        requestedCimClass=None, 
                        cimClass=cc)
                for i in gen:
                    yield i
        
    def EnumerateQualifiers(self, *args, **kwargs):
        # TODO
        return None
    def ExecQuery(self, *args, **kwargs):
        # TODO
        return None
    def GetInstance(self, namespace, InstanceName, 
                    LocalOnly=True, IncludeQualifiers=False, 
                    IncludeClassOrigin=False, PropertyList=None):
        cname = InstanceName.classname
        provider = self._get_provider(namespace, cname, 
                                      self.PROVIDERTYPE_INSTANCE)
        cc = cimdb.GetClass(cname, namespace=namespace, LocalOnly=False, 
                                IncludeQualifiers=True)
        return provider.MI_getInstance(self.env, InstanceName, PropertyList, cc)

    def GetQualifier(self, *args, **kwargs):
        return cimdb.GetQualifier(*args, **kwargs)
    def InvokeMethod(self, method_name, object_name, in_params):
        cc = cimdb.GetClass(object_name.classname, 
                                namespace=object_name.namespace,
                                LocalOnly=False, IncludeQualifiers=True)
        provider = self._get_provider(object_name.namespace, 
                                      object_name.classname, 
                                      self.PROVIDERTYPE_METHOD, method_name)
        return provider.MI_invokeMethod(self.env, object_name, 
                cc.methods[method_name], in_params)

    def ModifyClass(self, *args, **kwargs):
        return cimdb.ModifyClass(*args, **kwargs)
    def ModifyInstance(self, *args, **kwargs):
        # TODO providers...
        return cimdb.ModifyInstance(*args, **kwargs)
    def ReferenceNames(self, *args, **kwargs):
        # TODO
        return None
    def References(self, *args, **kwargs):
        # TODO
        return None
    def SetQualifier(self, *args, **kwargs):
        return cimdb.SetQualifier(*args, **kwargs)

cs = CIMServer()

class CIMXMLDispatch(object):
    def enumerateinstancenames(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        ipvs['ClassName'] = ipvs['ClassName'].classname
        for iname in cs.EnumerateInstanceNames(namespace=ns, **ipvs):
            iname.host = None
            iname.namespace = None
            output.write(iname.tocimxml().toxml().encode('utf8'))

    def enumerateinstances(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        ipvs['ClassName'] = ipvs['ClassName'].classname
        for inst in cs.EnumerateInstances(namespace=ns, **ipvs):
            inst.path.host = None
            inst.path.namespace = None
            output.write(inst.tocimxml().toxml().encode('utf8'))

    def enumerateclassnames(self, tt, output):
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        print 'ipvs:', `ipvs`
        for name in cs.EnumerateClassNames(namespace=ns, **ipvs):
            cn = pywbem.CIMClassName(classname=name)
            output.write(cn.tocimxml().toxml().encode('utf8'))

    def enumerateclasses(self, tt, output):
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        print 'ipvs:', `ipvs`
        for cc in cs.EnumerateClasses(namespace=ns, **ipvs):
            output.write(cc.tocimxml().toxml().encode('utf8'))

    def getclass(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        ipvs['ClassName'] = ipvs['ClassName'].classname
        print 'ipvs:', `ipvs`
        cc = cs.GetClass(namespace=ns, **ipvs)
        output.write(cc.tocimxml().toxml().encode('utf8'))

    def getqualifier(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        qual = cs.GetQualifier(namespace=ns, **ipvs)
        output.write(cc.tocimxml().toxml().encode('utf8'))

    def createclass(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        cs.CreateClass(namespace=ns, **ipvs)

    def createinstance(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        print 'ipvs:', `ipvs`
        iname = cs.CreateInstance(namespace=ns, **ipvs)
        output.write(iname.tocimxml().toxml().encode('utf8'))

    def getinstance(self, tt, output):
        print 'tt[0]', tt[0]
        ns = tt[2]
        print 'ns:', `ns`
        ipvs = dict([(str(k), v) for k, v in tt[3]])
        inst = cs.GetInstance(namespace=ns, **ipvs)
        inst.path = None
        output.write(inst.tocimxml().toxml().encode('utf8'))

    def invokemethod(self, tt, output):
        path = tt[2]
        method_name = tt[1]['NAME']
        in_params = {}
        for p in tt[3]:
            if p[1] == 'reference':
                in_params[p[0].encode('utf8')] = p[2]
            else:
                in_params[p[0].encode('utf8')] = pywbem.tocimobj(p[1], p[2])

        print 'in_params:', in_params
        rval, out_params = cs.InvokeMethod(method_name, path, 
                in_params)
        print 'rval:', rval
        print 'out_params', out_params

        def paramtype(obj):
            """Return a string to be used as the CIMTYPE for a parameter."""
            if isinstance(obj, pywbem.CIMType):
                return obj.cimtype
            elif type(obj) == bool:
                return 'boolean'
            elif isinstance(obj, StringTypes):
                return 'string'
            elif isinstance(obj, (datetime, timedelta)):
                return 'datetime'
            elif isinstance(obj, (pywbem.CIMClassName, pywbem.CIMInstanceName)):
                return 'reference'
            elif isinstance(obj, (pywbem.CIMClass, pywbem.CIMInstance)):
                return 'string'
            elif isinstance(obj, list):
                return paramtype(obj[0])
            raise TypeError('Unsupported parameter type "%s"' % type(obj))

        def paramvalue(obj):
            """Return a cim_xml node to be used as the value for a
            parameter."""
            if isinstance(obj, (pywbem.CIMType, bool, basestring)):
                return pywbem.VALUE(pywbem.atomic_to_cim_xml(obj))
            if isinstance(obj, (pywbem.CIMClassName, pywbem.CIMInstanceName)):
                return pywbem.VALUE_REFERENCE(obj.tocimxml())
            if isinstance(obj, (pywbem.CIMClass, pywbem.CIMInstance)):
                return pywbem.VALUE(obj.tocimxml().toxml())
            if isinstance(obj, list):
                if isinstance(obj[0], (pywbem.CIMClassName, 
                                       pywbem.CIMInstanceName)):
                    return pywbem.VALUE_REFARRAY([paramvalue(x) for x in obj])
                return pywbem.VALUE_ARRAY([paramvalue(x) for x in obj])
            raise TypeError('Unsupported parameter type "%s"' % type(obj))

        def is_embedded(obj):
            """Determine if an object requires an EmbeddedObject attribute"""
            if isinstance(obj,list) and obj:
                return is_embedded(obj[0])
            elif isinstance(obj, pywbem.CIMClass):
                return 'object'
            elif isinstance(obj, pywbem.CIMInstance):
                return 'instance'
            return None

        plist = [pywbem.PARAMVALUE(x[0], 
                                    paramvalue(x[1]), 
                                    paramtype(x[1]),
                                    embedded_object=is_embedded(x[1]))
                 for x in out_params.items()]
        if rval is not None:
            rxml = pywbem.RETURNVALUE(paramvalue(rval[1]), rval[0])
            output.write(rxml.toxml())
        for p in plist:
            output.write(p.toxml())


