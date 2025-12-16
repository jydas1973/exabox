
"""
This prototype does not use any model framework or data class.

REFERENCES:

    http://libvirt.org/remote.html#Remote_URI_reference

    http://libvirt.org/remote.html

    https://libvirt.org/docs/libvirt-appdev-guide-python/en-US/html/index.html

    https://libvirt.org/docs/libvirt-appdev-guide-python/en-US/html/libvirt_application_development_guide_using_python-Connections.html

    XML format: https://libvirt.org/formatdomain.html
"""
from __future__ import print_function

import os
import re
import socket
import string
import sys
import defusedxml.ElementTree as ET

try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict

from functools import partial

import libvirt # pylint: disable=import-error
import paramiko

paramiko.transport.Transport.preferred_pubkeys = (
    "ssh-ed25519",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "ssh-rsa",
    "rsa-sha2-512",
    "rsa-sha2-256",
    "ssh-dss"
)

# TODO make a sub class or metaclass of ET.Element
class XmlConfig(object):
    """
    XML config builder and parser prototype.

    The purpose of this class is to provide simple interface to xml domain configuration.

    Libvirt Domain XML format
    https://libvirt.org/formatdomain.html

    property getter for read-only

    property setter for read-write
    """
    def __init__(self, xmldata):
        if isinstance(str, xmldata):
            self.__root = ET.fromstring(xmldata)
        else:
            self.__root = xmldata

    @property
    def xml(self):
        return ET.tostring(self.__root)

    def find(self, key):
        """
        Finds element in xml by the key

        :rtype: ET
        :param key: key to look for
        :return: element of xml
        """
        return self.__root.find(key)

    def findtext(self, key):
        return self.__root.findtext(key)

    def dump(self, fname):
        with open(fname, 'w') as f:
            f.write(self.xml)

    @property
    def root(self):
        return self.__root

    def iter(self, key):
        return self.__root.iter(key)

    def __str__(self):
        return self.xml


class XmlPoolConfig(XmlConfig):
    def __init__(self, xmldata):
        super(XmlPoolConfig, self).__init__(xmldata)


VOLUME_XML_TEMPLATE = """
<volume>
  <name>NOT SET</name>
  <allocation>0</allocation>
  <capacity unit="G">2</capacity>
  <target>
    <path>NOT SET</path>
    <format type='qcow2'/>
    <permissions>
      <owner>107</owner>
      <group>107</group>
      <mode>0744</mode>
      <label>virt_image_t</label>
    </permissions>
  </target>
</volume>"""


class XmlVolumeConfig(XmlConfig):
    def __init__(self, xmldata):
        super(XmlVolumeConfig, self).__init__(xmldata)


# type must be raw/qcow2/auto
DISK_XML_TEMPLATE = """
<disk device="disk" type="file">
  <driver name="qemu" type="auto" />
  <source file="NOT SET" />
  <target bus="ide" dev="NOT SET" />
  <address bus="NOT SET" controller="0" target="0" type="drive" unit="NOT SET" />
</disk>
"""


class XmlDiskConfig(XmlConfig):
    def __init__(self, xmldata):
        if xmldata is None:
            # can't use xmldata or DISK_XML_TEMPLATE
            # because of FutureWarning: The behavior of this method will change in future versions.
            # Use specific 'len(elem)' or 'elem is not None' test instead.
            xmldata = DISK_XML_TEMPLATE
        super(XmlDiskConfig, self).__init__(xmldata)

    @property
    def address(self):
        return self.root.find('address')

    @property
    def bus(self):
        return int(self.address.get('bus'))

    @bus.setter
    def bus(self, value):
        self.address.set('bus', str(value))

    @property
    def unit(self):
        return int(self.address.get('unit'))

    @unit.setter
    def unit(self, value):
        self.address.set('unit', str(value))

    @property
    def target(self):
        return self.root.find('source').get('file')

    @property
    def target_dev(self):
        return self.root.find('target').get('dev')

    @target_dev.setter
    def target_dev(self, value):
        self.root.find('target').set('dev', value)

    @target.setter
    def target(self, value):
        self.root.find('source').set('file', value)

    @property
    def driver_type(self):
        return self.root.find('driver').get('type')

    @driver_type.setter
    def driver_type(self, value):
        self.root.find('driver').set('type', value)


class XmlDomainConfig(XmlConfig):
    NAME_FIELD = 'name'
    UUID_FIELD = 'uuid'
    MEMORY_FIELD = 'memory'
    CURRENT_MEMORY_FIELD = 'currentMemory'
    HUGE_PAGES = 'memoryBacking/hugepages/page'
    VCPU = 'vcpu'
    KNOWN_FIELDS = (NAME_FIELD, UUID_FIELD,
                    MEMORY_FIELD, CURRENT_MEMORY_FIELD, HUGE_PAGES,
                    VCPU)

    """
    XML config builder and parser prototype.

    The purpose of this class is to provide simple interface to xml domain configuration.

    Libvirt Domain XML format
    https://libvirt.org/formatdomain.html

    property getter for read-only

    property setter for read-write
    """
    def __init__(self, xmldata):
        """Initialize builder/parser from existing domain xml
        configuration or pass template xml to create new configuration
        """
        super(XmlDomainConfig, self).__init__(xmldata)

        self.dump('%s.xml' % self.name)
        self.print_unknown_field_names()

    def print_unknown_field_names(self):
        print([child.tag for child in self.root if child.tag not in self.KNOWN_FIELDS])
        # for child in self.__root:
        #     if child.tag not in self.KNOWN_FIELDS:
        #         # assert isinstance(child, ET)
        #         print(ET.tostring(child))

    def print_xml_unknown_fields(self):
        for key in self.KNOWN_FIELDS:
            if '/' in key:
                elem = self.find(key)
                if elem is not None:
                    parent = self.find(key[:key.rfind('/')])
                    print('-' * 60)
                    print(elem, parent)
                    print(ET.tostring(parent))
                    print('=' * 60)
                    parent.remove(elem)
            else:
                elem = self.find(key)
                self.root.remove(elem)

        print(ET.tostring(self.root))

    @property
    def name(self):
        """A short name for the virtual machine.

        This name should consist only of alpha-numeric characters
        and is required to be unique within the scope of a single host.
        """
        return self.findtext(self.NAME_FIELD)

    @name.setter
    def name(self, value):
        """A short name for the virtual machine.

        This name should consist only of alpha-numeric characters
        and is required to be unique within the scope of a single host.
        """
        self.find(self.NAME_FIELD).text = value

    @property
    def uuid(self):
        return self.findtext(self.UUID_FIELD)

    @uuid.setter
    def uuid(self, value):
        self.find(self.UUID_FIELD).text = value

    def get_elem_value_and_unit(self, key, value_in=None):
        if key not in self.KNOWN_FIELDS:
            raise KeyError('Unknown key %s' % key)

        elem = self.find(key)
        if elem is not None:
            return '%s %s' % (elem.get(value_in) if value_in else elem.text, elem.get('unit'))
        else:
            return ''

    @property
    def memory(self):
        """The maximum allocation of memory for the guest at boot time"""
        return self.get_elem_value_and_unit(self.MEMORY_FIELD)

    @property
    def maxMemory(self):
        raise NotImplementedError('Method is not used')
        """The run time maximum memory allocation of the guest"""
        return self.get_elem_value_and_unit('maxMemory')

    @property
    def currentMemory(self):
        """The actual allocation of memory for the guest"""
        return self.get_elem_value_and_unit(self.CURRENT_MEMORY_FIELD)

    @property
    def memoryBacking(self):
        """memoryBacking/huge pages support"""
        return self.get_elem_value_and_unit(self.HUGE_PAGES, value_in='size')

    def memory_config(self):
        return {'memory': self.memory,
                'currentMemory': self.currentMemory,
                'memoryBacking': self.memoryBacking,
                }

    def cpu_config(self):
        elem = self.find(self.VCPU)
        return {'maxCpu': elem.text,
                'current': elem.get('current'),
                'placement': elem.get('placement')
                }

    def as_dict(self):
        """Return domain configuration as dict/JSON serializable"""
        ret = OrderedDict()
        ret['name'] = self.name
        ret['uuid'] = self.uuid

        ret['memory'] = self.memory_config()
        ret['cpu'] = self.cpu_config()

        self.print_xml_unknown_fields()

        return ret


"""
How missing SSH keys are handled
--------------------------------

ssh command adds both host and ip one line to the known_hosts file,
but in the following code adds:

when key is missing: host,key added automatically by paramiko in get_virt()
when key is missing: ip,key added automatically by libvirt in __init__()

TODO may be there is a way to add both host and ip by paramiko

How bad SSH keys are handled
----------------------------

when bad key is present for ip: no updates to the known_hosts file will be made.
Connection will be established if key no_verify set

paramiko will add good key resulting in two identical records of good keys.
This behaviour observed on paramiko 2.1.1
"""


class AbstractVirt(object):
    """Abstract class to show methods needed to be implemented"""
    def __init__(self, conn_string):
        self._c_string = conn_string
        self.__conn = None  # type: libvirt.virConnect

    @property
    def conn(self):
        assert isinstance(self.__conn, libvirt.virConnect)
        return self.__conn

    @conn.setter
    def conn(self, value):
        if value:
            assert isinstance(value, libvirt.virConnect)
        self.__conn = value

    @property
    def uri(self):
        """
        Get connection string
        :return: connection string
        """
        return self._c_string

    # domain info commands

    def get_list_domains_ids(self):
        """
        Get list of domain ids
        """
        raise NotImplementedError

    def get_brief_domain_info(self, domain):
        """
        Get brief information about domain.
        schema: DomainInfo
        """
        raise NotImplementedError

    def get_all_domains_info(self):
        """
        Get brief information about all domains in the system
        schema: AllDomainsInfo
        """
        raise NotImplementedError

    def list_domains(self):
        """Get list of domain names"""
        #FIXME should this list all domains or only active
        raise NotImplementedError

    # domain state management

    def start_domain(self, domain_name):
        raise NotImplementedError

    def stop_domain(self, domain_name):
        raise NotImplementedError

    def reboot_domain(self, domain_name):
        raise NotImplementedError

    def set_domain_state(self, domain_name, target_state):
        if target_state == 'start':
            self.start_domain(domain_name)
        elif target_state in ['stop', 'shutdown']:
            self.stop_domain(domain_name)
        elif target_state == 'reboot':
            self.reboot_domain(domain_name)
        else:
            raise NotImplementedError

    # domain configuration
    def get_domain_configuration(self, domain_name):
        raise NotImplementedError

    # domain configuration management

    def delete_domain(self, domain_name, data):
        raise NotImplementedError

    def create_domain(self, domain_name, data):
        raise NotImplementedError

    def modify_domain(self, domain_name, data):
        raise NotImplementedError

    def modify_domain_cpu(self, domain_name, data):
        raise NotImplementedError

    def attach_disk(self, domain_name, disk_name):
        raise NotImplementedError

    def modify_domain_memory(self, domain_name, data):
        raise NotImplementedError

    # methods to convert domain configuration between JSON and XML format

    def xml_to_json(self, xmldata):
        return XmlDomainConfig(xmldata).as_dict()

    def json_to_xml(self, jsondata):
        raise NotImplementedError

    # Below methods only to demo functionality

    def capabilities(self):
        raise NotImplementedError

    def get_max_vcpu(self):
        raise NotImplementedError

    def get_info(self, *args):
        raise NotImplementedError

    def get_cells_free_memory(self):
        raise NotImplementedError

    def list_interfaces(self):
        raise NotImplementedError

    def list_down_interfaces(self):
        raise NotImplementedError

    def list_roce_interfaces(self):
        return [x for x in self.list_interfaces() if x.startswith('re')]


# TODO check if this ever used
SASL_USER = 'root'
SASL_PASS = 'welcome1'


# TODO check if this ever used
def request_cred(credentials, user_data):
    """Not really used"""
    print(credentials)
    print(user_data)
    for credential in credentials:
        print(credential)
        if credential[0] == libvirt.VIR_CRED_AUTHNAME:
            credential[4] = SASL_USER
        elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
            credential[4] = SASL_PASS
    return 0


class LibVirt(AbstractVirt):
    """Implementation class with libvirt as backend

    libvirt can be used for both KVM and XEN
    TODO add prof to the latter: libvirt with XEN
    """
    NODE_INFO_FMT_STR = '''Model {n[0]}
Memory size: {n[1]} MB
Number of CPUs: {n[2]}
MHz of CPUs: {n[3]}
Number of NUMA nodes: {n[4]}
Number of CPU sockets: {n[5]}
Number of CPU cores per socket: {n[6]}
Number of CPU threads per core: {n[7]}'''
    NO_VERIFY_SSH = True

    def __init__(self, conn_string):
        super(LibVirt, self).__init__(conn_string)
        self.readonly = False

        auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE],
                request_cred, None]

        flags = libvirt.VIR_CONNECT_RO if self.readonly else 0
        conns = [partial(libvirt.openAuth, self._c_string, auth, flags),
                 # partial(libvirt.openReadOnly, self.uri),
                 # partial(libvirt.open, self.uri)
                 ]

        for each in conns:
            try:
                conn = each()
            except libvirt.libvirtError:
                conn = None

            if conn:
                self.conn = conn
                break

        if self.conn is None:
            print('Failed to open connection to the hypervisor')
            raise ValueError

        # self.print_details()

    @staticmethod
    def make_conn_string(protocol, transport=None, user=None, host=None, **kwargs):
        """
        kwargs possible (key, value) pairs:
            no_verify: If set to a non-zero value, this disables client's strict
                       host key checking making it auto-accept new host keys.
                       Existing host keys will still be validated.
                       default: LibVirt.NO_VERIFY_SSH

        :param protocol:
        :param transport:
        :param user:
        :param host:
        :param kwargs:
        :return:
        """
        if transport == 'ssh' and 'socket' not in kwargs:
            kwargs['socket'] = SOCKET_FILE

        endpoint = 'system' if protocol == 'qemu' else ''

        if transport is None:
            user = ''
        elif transport in ['ssh', 'tls'] and user:
            h = socket.gethostname()
            # fall back to simple protocol when connecting to local host
            if host in {h, h.split('.')[0], socket.getfqdn()}:
                protocol = transport
                user = ''
                host = ''
            else:
                protocol = '%s+%s' % (protocol, transport)
                user = '%s@' % user

                # This is to prevent ssh password prompt
                if transport == 'ssh':
                    kwargs['no_tty'] = '1'
                    if 'no_verify' not in kwargs and LibVirt.NO_VERIFY_SSH:
                        kwargs['no_verify'] = '1'

        else:
            raise ValueError('Invalid protocol')

        conn_str = '{protocol}://{user}{host}/{endpoint}?{extra}'.format(
            protocol=protocol,
            user=user,
            host=host,
            endpoint=endpoint,
            extra='&'.join(['%s=%s' % (k, v) for k, v
                            in kwargs.items() if v is not None])
        )

        print(conn_str)
        return conn_str

    @staticmethod
    def get_virt(user, host, keyfile, **kwargs):
        client = paramiko.SSHClient()
        hosts_file = os.path.join(os.environ.get('HOME'), '.ssh/known_hosts')
        if os.path.isfile(hosts_file):
            client.load_host_keys(hosts_file)
        else:
            raise NotImplementedError
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _done = False
        while not _done:
            try:
                client.connect(hostname=host, username=user,
                               pkey=paramiko.RSAKey.from_private_key_file(keyfile),
                               )
            except paramiko.ssh_exception.BadHostKeyException:
                hkeys = client.get_host_keys()
                """
paramiko==2.1.1 has bad hostkey implementation of __del__(item):
It does not actually delete key
223     def __delitem__(self, key):
224         k = self[key]
                """
                if host in hkeys:
                    # soft delete
                    del hkeys[host]
                if host in hkeys:
                    # hard delete
                    hkeys.clear()
                if host in hkeys:
                    # fail
                    raise
            else:
                _done = True

        stdin, stdout, stderr = client.exec_command('uname -r')
        # print(any(['el6' in _ for _ in stdout.readlines()]))
        lines = stdout.readlines()
        if any(['el6' in _ for _ in lines]):
            stdin, stdout, stderr = client.exec_command('service libvirtd status')
            # libvirtd (pid  170244) is running...
            pattern = re.compile('^libvirtd')
            libvirtd_running = any([pattern.match(_) for _ in stdout.readlines()])

            stdin, stdout, stderr = client.exec_command('service xend status')
            # xend daemon (pid 256302) is running...
            pattern = re.compile('^xend daemon')
            xend_running = any([pattern.match(_) for _ in stdout.readlines()])
        elif any(['el7' in _ for _ in lines]):
            stdin, stdout, stderr = client.exec_command('systemctl is-active libvirtd')
            # systemctl is-active libvirtd
            # active
            pattern = re.compile('^active')
            libvirtd_running = any([pattern.match(_) for _ in stdout.readlines()])

            stdin, stdout, stderr = client.exec_command('systemctl is-active xend')
            xend_running = any([pattern.match(_) for _ in stdout.readlines()])
        else:
            raise NotImplementedError

        print(libvirtd_running, xend_running)

        if libvirtd_running:
            if xend_running:
                return XenVirt
            else:
                # must check for kvm
                return KVMVirt
        else:
            # need to fallback to ssh
            return None

    def print_details(self):
        root = ET.fromstring(self.capabilities())
        # child.tag, child.attrib
        print('Capabilities: %s' % set([child.tag for child in root]))

        host = self.conn.getHostname()
        print('Hostname:' + host)

        print('Maximum support virtual CPUs: ' + str(self.get_max_vcpu()))

        nodeinfo = self.get_info()

        print(self.NODE_INFO_FMT_STR.format(n=nodeinfo))

        free_memory_mb = 0
        for indx, value in enumerate(self.get_cells_free_memory()):
            _mb = value/1024**2
            print('Node ' + str(indx) + ': ' + str(_mb) + ' MB free memory')
            free_memory_mb += _mb
        print('Free memory %.2f' % (float(free_memory_mb)/nodeinfo[1]))

        mem = self.conn.getFreeMemory()
        print("Free memory on the node (host) is " + str(mem/1024**2) + " MB.")

        print('Virtualization type: ' + self.conn.getType())
        print('Version: ' + str(self.conn.getVersion()))
        print('Libvirt Version: ' + str(self.conn.getLibVersion()))
        print('Canonical URI: ' + self.conn.getURI())
        print('Connection is encrypted: ' + str(self.conn.isEncrypted()))
        print('Connection is secure: ' + str(self.conn.isSecure()))
        print("Connection is alive = " + str(self.conn.isAlive()))

        # Compare cpu to reference cpu
        xml = '<cpu mode="custom" match="exact">' + \
              '<model fallback="forbid">kvm64</model>' + \
              '</cpu>'

        retc = self.conn.compareCPU(xml)

        if retc == libvirt.VIR_CPU_COMPARE_ERROR:
            print("CPUs are not the same or there was error.")
        elif retc == libvirt.VIR_CPU_COMPARE_INCOMPATIBLE:
            print("CPUs are incompatible.")
        elif retc == libvirt.VIR_CPU_COMPARE_IDENTICAL:
            print("CPUs are identical.")
        elif retc == libvirt.VIR_CPU_COMPARE_SUPERSET:
            print("The host CPU is better than the one specified.")
        else:
            print("An Unknown return code was emitted.")

        # This method returns all the available memory parameters as strings.
        print(self.conn.getMemoryParameters().keys())

        map = self.conn.getCPUMap()

        print("CPUs: " + str(map[0]))
        print("Available: " + str(map[1]))

    def __del__(self):
        print('Closing connection')
        if self.conn:
            self.conn.close()

    def capabilities(self):
        return self.conn.getCapabilities()  # caps will be a string of XML

    def get_list_domains_ids(self):
        """
        https://libvirt.org/docs/libvirt-appdev-guide-python/en-US/html/libvirt_application_development_guide_using_python-Guest_Domains-Listing_Domains.html
        """
        return self.conn.listDomainsID() or []

    def list_domains(self):
        """Returns list of all domains including those not running"""
        return [dom.name() for dom in self.conn.listAllDomains(0)]

    def get_brief_domain_info(self, domain):
        assert isinstance(domain, libvirt.virDomain)
        _name = domain.name()
        # try:
        #     hname = domain.hostname()
        # except libvirt.libvirtError as ex:
        #     hname = str(ex)
        return _name, {'domain_name': _name,
                       'uptime': 'unknown',
                       'state': 'running' if domain.isActive() else 'inactive',
                       'ID': domain.ID(),
                       'Mem': domain.maxMemory() / 1024 if domain.isActive() else None,
                       'VCPUs': domain.maxVcpus() if domain.isActive() else None,
                       # 'snapshot': domain.hasCurrentSnapshot(),
                       # 'hostname': hname,
                      }

    def get_all_domains_info(self, *args):
        return {'domains': dict([self.get_brief_domain_info(each)
                                 for each in self.conn.listAllDomains(0)])}

    def get_domain_configuration(self, domain_name):
        assert isinstance(self.conn, libvirt.virConnect)
        try:
            domain = self.conn.lookupByName(domain_name)
        except libvirt.libvirtError:
            return None
        else:
            return domain.XMLDesc()

    def get_domain_by_name(self, domain_name):
        try:
            dom = self.conn.lookupByName(domain_name)
            assert isinstance(dom, libvirt.virDomain)
            return dom
        except libvirt.libvirtError:
            return None

    def create_domain(self, domain_name, data, persistent=True):
        """
        There are up to three methods involved in provisioning guests.
        The createXML method will create and immediately boot a new
        transient guest domain. When this guest domain shuts down,
        all trace of it will disappear. The defineXML method will
        store the configuration for a persistent guest domain.
        The create method will boot a previously defined guest
        domain from its persistent configuration. One important
        thing to note, is that the defineXML command can be used
        to turn a previously booted transient guest domain, into a
        persistent domain. This can be useful for some provisioning
        scenarios that will be illustrated later.

        :param persistent:
        :param domain_name:
        :param data:
        :return:
        """
        with open(os.path.join(os.path.dirname(__file__), 'template.xml')) as f:
            dom_config = XmlDomainConfig(f.read())

        # create system disk
        pool = self.print_storage_pool('default')
        sys_disk, sys_disk_path = self.create_disk(pool, domain_name)

        # assign system disk to domain
        elem = dom_config.find('devices')
        sys_disk_xml_elem = elem.findall('disk')[0]
        elem = sys_disk_xml_elem.find('source')
        elem.set('file', sys_disk_path)

        # set domain required parameters
        dom_config.name = domain_name
        dom_config.uuid = None

        if persistent:
            dom = self.conn.defineXML(dom_config.xml)
            self.start_domain(domain_name)
        else:
            dom = self.conn.createXML(dom_config.xml, 0)
        if dom is None:
            print('Failed to create a domain from an XML definition.', file=sys.stderr)
        else:
            print('Guest ' + dom.name() + ' has booted', file=sys.stderr)

    def modify_domain_cpu(self, domain_name, data):
        """
        Modify domain cpu configuration

        EXAMPLE data:
            {"current": "3",
             "placement": "static",
             "maxCpu": "5"
            }

        :param domain_name:
        :param data:
        """
        dom = self.get_domain_by_name(domain_name)
        if dom and 'current' in data:
            dom.setVcpus(int(data['current']))
            # dom.setVcpusFlags

    def attach_disk(self, domain_name, disk_name):
        dom = self.get_domain_by_name(domain_name)
        if dom:
            dom_config = XmlDomainConfig(dom.XMLDesc())
            len_before = len(dom_config.find('devices'))

            attach_to_bus, attach_as_unit = 1, 0

            # list hda, hdb ....
            hdd_names_in_use = set([])
            # TOD may be also track file names in use

            for each in dom_config.iter('disk'):
                _disk = XmlDiskConfig(each)
                curr_bus, curr_unit = _disk.bus, _disk.unit
                hdd_names_in_use.add(_disk.target_dev)

                if curr_bus > attach_to_bus:
                    attach_to_bus = curr_bus
                    attach_as_unit = 0
                if curr_bus == attach_to_bus and curr_unit >= attach_as_unit:
                    attach_as_unit = curr_unit + 1

            new_disk = XmlDiskConfig(None)
            new_disk.bus = attach_to_bus
            new_disk.unit = attach_as_unit
            new_disk.target = disk_name
            new_disk.driver_type = 'raw'
            hdd_name = None
            for letter in string.ascii_lowercase:
                hdd = 'hd' + letter
                if hdd not in hdd_names_in_use:
                    hdd_name = hdd
                    break

            assert hdd_name is not None, 'Failed to find free hdd name'
            new_disk.target_dev = hdd_name

            # we need xml root to insert
            new_disk = new_disk.root
            assert len(dom_config.find('devices')) == len_before

            insert_at = None
            count = 0
            for each in dom_config.find('devices'):
                count += 1
                if each.tag == 'disk':
                    insert_at = count
                elif insert_at is not None:
                    dom_config.find('devices').insert(insert_at, new_disk)
                    break

            assert len(dom_config.find('devices')) == len_before + 1
            self.conn.defineXML(str(dom_config))

            return hdd_name
        else:
            print('Domain %s does not exist' % domain_name)

        return None

    def create_disk(self, pool, disk_name):
        assert isinstance(pool, libvirt.virStoragePool)
        poolxml = XmlPoolConfig(pool.XMLDesc())
        path = poolxml.findtext('target/path')
        volume_xml = XmlVolumeConfig(VOLUME_XML_TEMPLATE)
        img_name = '%s.img' % disk_name

        elem = volume_xml.find('name')
        elem.text = os.path.join(img_name)

        elem = volume_xml.find('target/path')
        disk_path = os.path.join(path, img_name)
        elem.text = disk_path

        stgvol = pool.createXML(volume_xml.xml, libvirt.VIR_STORAGE_VOL_CREATE_PREALLOC_METADATA)

        if stgvol is None:
            print('Failed to create a  StorageVol objects.', file=sys.stderr)
            exit(1)
        # remove the storage volume
        # physically remove the storage volume from the underlying disk media
        # stgvol.wipe(0)
        # logically remove the storage volume from the storage pool
        # stgvol.delete(0)

        return stgvol, disk_path

    # Below methods only to demo functionality

    def print_storage_pool(self, pool_name):
        pool = self.conn.storagePoolLookupByName(pool_name)
        info = pool.info()
        print('Pool: ' + pool.name())
        print('  UUID: ' + pool.UUIDString())
        print('  Autostart: ' + str(pool.autostart()))
        print('  Is active: ' + str(pool.isActive()))
        print('  Is persistent: ' + str(pool.isPersistent()))
        print('  Num volumes: ' + str(pool.numOfVolumes()))
        print('  Pool state: ' + str(info[0]))
        print('  Capacity: ' + str(info[1]))
        print('  Allocation: ' + str(info[2]))
        print('  Available: ' + str(info[3]))

        return pool

    def print_storage_pools(self):
        pools = self.conn.listAllStoragePools(0)
        if pools is None:
            print('Failed to locate any StoragePool objects.', file=sys.stderr)
        else:
            for pool in pools:
                print('Pool: ' + pool.name())

    def print_domain_info(self, domId):
        assert isinstance(self.conn, libvirt.virConnect)
        try:
            domain = self.conn.lookupByID(domId)
        except:
            print('Failed to find the main domain %d' + domId)
        else:
            assert isinstance(domain, libvirt.virDomain)
            print("Domain: id %d running %s" % (domain.ID(), domain.OSType()))
            print(domain.info())
            try:
                """
                the following need to be added to xml
<channel type='unix'>
   <source mode='bind' path='/var/lib/libvirt/qemu/f16x86_64.agent'/>
   <target type='virtio' name='org.qemu.guest_agent.0'/>
</channel>
                """
                print('-' * 60)
                print(domain.getTime())
                print('-' * 60)
            except libvirt.libvirtError:
                pass

    def get_max_vcpu(self):
        """
        The getMaxVcpus method can be used to obtain the maximum number
        of virtual CPUs per-guest the underlying virtualization technology supports.
        It takes a virtualization "type" as input (which can be None),
        and if successful, returns the number of virtual CPUs supported.
        If an error occurred, -1 is returned instead.
        The following code demonstrates the use of getMaxVcpus:
        :return:
        """
        return self.conn.getMaxVcpus(None)

    def get_info(self):
        """
        The getInfo method can be used to obtain various information about the virtualization host.
        The method returns a Python list if successful and None if and error occurred.
        The Python list contains the following members:

        Member	Description
        list[0]	string indicating the CPU model
        list[1]	memory size in megabytes
        list[2]	the number of active CPUs
        list[3]	expected CPU frequency (mhz)
        list[4]	the number of NUMA nodes, 1 for uniform memory access
        list[5]	number of CPU sockets per node
        list[6]	number of cores per socket
        list[7]	number of threads per core
        Table 3.5. virNodeInfo structure members

        The following code demonstrates the use of virNodeGetInfo:
        :return:
        """
        return self.conn.getInfo()

    def get_cells_free_memory(self):
        """
        The getCellsFreeMemory method can be used to obtain the amount of
        free memory (in kilobytes) in some or all of the NUMA nodes in the system.
        It takes as input the starting cell and the maximum number of cells to
        retrieve data from. If successful, Python list is returned with
        the amount of free memory in each node. On failure None is returned.
        The following code demonstrates the use of getCellsFreeMemory:
        :return:
        """
        return self.conn.getCellsFreeMemory(0, self.get_info()[4])

    def start_domain(self, domain_name):
        domain = self.get_domain_by_name(domain_name)
        ret = domain.create() if domain else -1
        return ret

    def stop_domain(self, domain_name):
        dom = self.get_domain_by_name(domain_name)
        return dom.shutdown() if dom else -1

    def reboot_domain(self, domain_name):
        dom = self.get_domain_by_name(domain_name)
        return dom.reboot() if dom else -1

    def destroy_domain(self, domain_name):
        """
        Terminate domain immediately

        :param domain_name:
        :return:
        """
        domain = self.get_domain_by_name(domain_name)
        return domain.destroy() if domain else -1

    def undefine_domain(self, domain_name):
        """
        Terminate domain immediately

        :param domain_name:
        :return:
        """
        dom = self.get_domain_by_name(domain_name)
        if dom:
            if dom.isActive():
                dom.destroy()
            ret = dom.undefineFlags(flags=libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
            print(ret)
        else:
            print('No such domain %s' % domain_name)

    def list_interfaces(self):
        """Getting a list of active ("up") interfaces on a host"""
        return self.conn.listInterfaces()

    def list_down_interfaces(self):
        """Getting a list of inactive ("down") interfaces on a host"""
        return self.conn.listDefinedInterfaces()

    def get_iface_xml(self, iface_name):
        iface = self.conn.interfaceLookupByName(iface_name)
        return iface.XMLDesc()


SOCKET_FILE = '/var/run/libvirt/libvirt-sock'


class KVMVirt(LibVirt):
    """KVM specific implementation on top of libvirt"""
    def __init__(self, transport=None, user=None, host=None, **kwargs):
        """
        Extra parameters for ssh:

        no_tty  disables interactive password prompt
        keyfile ssh key file

        If set to a non-zero value, this stops ssh from asking for a password
        if it cannot log in to the remote machine automatically (eg. using ssh-agent etc.).
        Use this when you don't have access to a terminal - for example in graphical
        programs which use libvirt.

        Example: no_tty=1

        :param driver:
        :param transport:
        :param user:
        :param host:
        """

        conn_str = self.make_conn_string('qemu', transport, user, host, **kwargs)
        super(KVMVirt, self).__init__(conn_str)

    def modify_domain(self, domain_name, data):
        if 'state' in data:
            d = {'start': self.start_domain,
                 'stop': self.stop_domain
                 }
            f = d.get(data['state'], None)
            if f:
                f(domain_name)

    # Mapping for xm commands found in clucontrol/vmcontrol
    # Some methods listed in here just call super method and listed with
    # the only purpose of being listed under this comment

    def get_domain_id(self, domain_name):
        dom = self.get_domain_by_name(domain_name)
        return dom.ID() if dom else None

    def destroy_domain(self, domain_name):
        """Terminate a domain immediately."""
        return super(KVMVirt, self).destroy_domain(domain_name)

    def shutdown_domain(self, domain_name):
        """Shutdown a domain."""
        return super(KVMVirt, self).stop_domain(domain_name)

    def reboot_domain(self, domain_name):
        """Reboot a domain."""
        return super(KVMVirt, self).reboot_domain(domain_name)

    def get_info(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return super(KVMVirt, self).get_info()

    def get_nr_cpus(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return super(KVMVirt, self).get_info()[2]

    def get_free_memory(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return self.conn.getFreeMemory() / 1024 ** 2


class XenVirt(LibVirt):
    """Xen specific implementation on top of libvirt"""
    def __init__(self, transport=None, user=None, host=None, **kwargs):
        """
        Extra parameters for ssh:

        no_tty  disables interactive password prompt
        keyfile ssh key file

        If set to a non-zero value, this stops ssh from asking for a password
        if it cannot log in to the remote machine automatically (eg. using ssh-agent etc.).
        Use this when you don't have access to a terminal - for example in graphical
        programs which use libvirt.

        Example: no_tty=1

        :param driver:
        :param transport:
        :param user:
        :param host:
        """

        conn_str = self.make_conn_string('xen', transport, user, host, **kwargs)
        super(XenVirt, self).__init__(conn_str)

    def modify_domain(self, domain_name, data):
        if 'state' in data:
            d = {'start': self.start_domain,
                 'stop': self.stop_domain
                 }
            f = d.get(data['state'], None)
            if f:
                f(domain_name)

    def get_all_domains_info(self, *args):
        return {'domains': dict([self.get_brief_domain_info(self.conn.lookupByID(each))
                                 for each in self.conn.listDomainsID()
                                 if each > 0
                                 ])}

    # Mapping for xm commands found in clucontrol/vmcontrol
    # Some methods listed in here just call super method and listed with
    # the only purpose of being listed under this comment

    def get_domain_id(self, domain_name):
        dom = self.get_domain_by_name(domain_name)
        return dom.ID() if dom else None

    def destroy_domain(self, domain_name):
        """Terminate a domain immediately."""
        return super(XenVirt, self).destroy_domain(domain_name)

    def shutdown_domain(self, domain_name):
        """Shutdown a domain."""
        return super(XenVirt, self).stop_domain(domain_name)

    def reboot_domain(self, domain_name):
        """Reboot a domain."""
        return super(XenVirt, self).reboot_domain(domain_name)

    def get_info(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return super(XenVirt, self).get_info()

    def get_nr_cpus(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return super(XenVirt, self).get_info()[2]

    def get_free_memory(self, *args):
        """Get information about the host."""
        # FIXME *args is only needed because demo always passes extra argument
        return self.conn.getFreeMemory() / 1024 ** 2

    def xm_start(self, fname):
        """xm create vm.cfg"""
        print('/EXAVMIMAGES/GuestImages/%s/vm.cfg' % fname)
        raise NotImplementedError('Not implemented xm create vm.cfg')

"""
xm commands (grouped) found in clucontrol.py
--------------------------------------------
+ xm destroy

+ xm info
+ xm info | grep free_memory
+ xm info | grep nr_cpus

+ xm list
xm list | grep
xm li %s -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'
xm li %s -l | grep '(vcpu' | tr -d ')' | awk '{ print $2 }'
xm li %s | grep %s | awk '{ print $2 }'
xm li %s | grep %s | awk '{ print $3 }'
xm li %s | grep %s | awk '{ print $4 }'
xm li | awk '{ print $4 }'
xm li | grep %s | awk '{ print $4 }'
xm li | grep Domain-0 | awk '{ print $4 }'

xm network-list
xm network-list %s | grep vif | awk 'BEGIN { FS = "/" } ; { print $7$8"."$9 }'
xm vcpu-list
xm vcpu-list | awk '{ print $1 \" \"  $7 }' | uniq | awk 'NR>1'
xm vcpu-pin ' + _domU + ' all ' + _range_str
xm vcpu-set ' + _domU + ' ' + str(_cores)

xm commands found in vmcontrol.py
---------------------------------

xm list

xm info
xm list -l
xm destroy
xm shutdown -w
xm reboot -w
xm create /EXAVMIMAGES/GuestImages/'+_vmid+'/vm.cfg'
xm uptime
xm vcpu-set ' + _vmid + ' ' +_vcpu
"""

"""
Example:

# host is XEN/KVM host running libvirtd
# keyfile is ssh private key to connect to host
# Note: public key must be in auth_ file on the host
CONFIG = dict(driver='qemu', transport='ssh', user='root',
              host='roce-x6-3, keyfile='./roce-x6-3.key')
lv = KVMVirt(**CONFIG)

lv.method(domain_name)
# where method is one if the values from xm_map below
"""

xm_map = {'xm list | grep for domain': 'get_domain_id',
          'xm destroy': 'destroy_domain',
          'xm shutdown -w': 'shutdown_domain',
          'xm reboot -w': 'reboot_domain',
          'xm info': 'get_info',
          'xm info | grep nr_cpus': 'get_nr_cpus',
          'xm info | grep free_memory': 'get_free_memory',
          'xm start': 'xm_start'
          }
