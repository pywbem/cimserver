"""Python Provider for CIM_Namespace

Instruments the CIM class CIM_Namespace

"""

import pywbem
from socket import getfqdn
import cimdb

class CIM_NamespaceProvider(pywbem.CIMProvider):
    """Instrument the CIM class CIM_Namespace 

    Namespace provides a domain (in other words, a container), in which the
    instances [of a class] are guaranteed to be unique per the KEY
    qualifier definitions. It is named relative to the CIM_ObjectManager
    implementation that provides such a domain.
    
    """

    def __init__ (self, env):
        logger = env.get_logger()
        logger.log_debug('Initializing provider %s from %s' \
                % (self.__class__.__name__, __file__))
        # If you will be filtering instances yourself according to 
        # property_list, role, result_role, and result_class_name 
        # parameters, set self.filter_results to False
        # self.filter_results = False

    def get_instance(self, env, model, cim_class):
        """Return an instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        model -- A template of the pywbem.CIMInstance to be returned.  The 
            key properties are set on this instance to correspond to the 
            instanceName that was requested.  The properties of the model
            are already filtered according to the PropertyList from the 
            request.  Only properties present in the model need to be
            given values.  If you prefer, you can set all of the 
            values, and the instance will be filtered for you. 
        cim_class -- The pywbem.CIMClass

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the CIM Class does exist, but the requested CIM 
            Instance does not exist in the specified namespace)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        
        logger = env.get_logger()
        logger.log_debug('Entering %s.get_instance()' \
                % self.__class__.__name__)
        
        #model['Caption'] = # TODO (type = unicode) 
        #model['ClassInfo'] = # TODO (type = pywbem.Uint16 self.Values.ClassInfo) (Required)
        #model['ClassType'] = # TODO (type = pywbem.Uint16 self.Values.ClassType) 
        #model['ClassTypeVersion'] = # TODO (type = unicode) 
        #model['Description'] = # TODO (type = unicode) 
        #model['DescriptionOfClassInfo'] = # TODO (type = unicode) 
        #model['DescriptionOfClassType'] = # TODO (type = unicode) 
        #model['ElementName'] = # TODO (type = unicode) 
        return model

    def enum_instances(self, env, model, cim_class, keys_only):
        """Enumerate instances.

        The WBEM operations EnumerateInstances and EnumerateInstanceNames
        are both mapped to this method. 
        This method is a python generator

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        model -- A template of the pywbem.CIMInstances to be generated.  
            The properties of the model are already filtered according to 
            the PropertyList from the request.  Only properties present in 
            the model need to be given values.  If you prefer, you can 
            always set all of the values, and the instance will be filtered 
            for you. 
        cim_class -- The pywbem.CIMClass
        keys_only -- A boolean.  True if only the key properties should be
            set on the generated instances.

        Possible Errors:
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        logger = env.get_logger()
        logger.log_debug('Entering %s.enum_instances()' \
                % self.__class__.__name__)

        # Key properties    
        model['ObjectManagerName'] = 'TODO'
        model['ObjectManagerCreationClassName'] = 'TODO'
        model['SystemName'] = getfqdn()
        model['CreationClassName'] = 'CIM_Namespace'    
        model['SystemCreationClassName'] = 'TODO'
        for ns in cimdb.Namespaces():
            model['Name'] = ns
            if keys_only:
                yield model.copy() #TODO remove copy when provifc is fixed. 
            else:
                try:
                    yield self.get_instance(env, model, cim_class)
                except pywbem.CIMError, (num, msg):
                    if num not in (pywbem.CIM_ERR_NOT_FOUND, 
                                   pywbem.CIM_ERR_ACCESS_DENIED):
                        raise

    def set_instance(self, env, instance, previous_instance, cim_class):
        """Return a newly created or modified instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance -- The new pywbem.CIMInstance.  If modifying an existing 
            instance, the properties on this instance have been filtered by 
            the PropertyList from the request.
        previous_instance -- The previous pywbem.CIMInstance if modifying 
            an existing instance.  None if creating a new instance. 
        cim_class -- The pywbem.CIMClass

        Return the new instance.  The keys must be set on the new instance. 

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_ALREADY_EXISTS (the CIM Instance already exists -- only 
            valid if previous_instance is None, indicating that the operation
            was CreateInstance)
        CIM_ERR_NOT_FOUND (the CIM Instance does not exist -- only valid 
            if previous_instance is not None, indicating that the operation
            was ModifyInstance)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        logger = env.get_logger()
        logger.log_debug('Entering %s.set_instance()' \
                % self.__class__.__name__)
        # TODO create or modify the instance
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED) # Remove to implement
        return instance

    def delete_instance(self, env, instance_name):
        """Delete an instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance_name -- A pywbem.CIMInstanceName specifying the instance 
            to delete.

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_NAMESPACE
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_INVALID_CLASS (the CIM Class does not exist in the specified 
            namespace)
        CIM_ERR_NOT_FOUND (the CIM Class does exist, but the requested CIM 
            Instance does not exist in the specified namespace)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """ 

        logger = env.get_logger()
        logger.log_debug('Entering %s.delete_instance()' \
                % self.__class__.__name__)

        # TODO delete the resource
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED) # Remove to implement
        
    class Values(object):
        class ClassType(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            CIM = pywbem.Uint16(2)
            DMI_Recast = pywbem.Uint16(200)
            SNMP_Recast = pywbem.Uint16(201)
            CMIP_Recast = pywbem.Uint16(202)

        class ClassInfo(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            CIM_1_0 = pywbem.Uint16(2)
            CIM_2_0 = pywbem.Uint16(3)
            CIM_2_1 = pywbem.Uint16(4)
            CIM_2_2 = pywbem.Uint16(5)
            CIM_2_3 = pywbem.Uint16(6)
            CIM_2_4 = pywbem.Uint16(7)
            CIM_2_5 = pywbem.Uint16(8)
            CIM_2_6 = pywbem.Uint16(9)
            CIM_2_7 = pywbem.Uint16(10)
            CIM_2_8 = pywbem.Uint16(11)
            DMI_Recast = pywbem.Uint16(200)
            SNMP_Recast = pywbem.Uint16(201)
            CMIP_Recast = pywbem.Uint16(202)

## end of class CIM_NamespaceProvider

def get_providers(env): 
    cim_namespace_prov = CIM_NamespaceProvider(env)  
    return {'CIM_Namespace': cim_namespace_prov} 
