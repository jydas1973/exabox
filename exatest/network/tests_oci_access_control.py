#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_oci_access_control.py /main/1 2026/05/04 00:00:00 codex Exp $
#
# tests_oci_access_control.py
#
import importlib.util
import os
import sys
import types
import unittest
from unittest import mock


class PortRange:
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __eq__(self, other):
        return isinstance(other, PortRange) and self.min == other.min and self.max == other.max


class TcpOptions:
    def __init__(self, destination_port_range=None, source_port_range=None):
        self.destination_port_range = destination_port_range
        self.source_port_range = source_port_range


class EgressSecurityRule:
    def __init__(self, description=None, destination=None, destination_type=None,
                 is_stateless=None, protocol=None, tcp_options=None):
        self.description = description
        self.destination = destination
        self.destination_type = destination_type
        self.is_stateless = is_stateless
        self.protocol = protocol
        self.tcp_options = tcp_options


class SecurityList:
    LIFECYCLE_STATE_AVAILABLE = 'AVAILABLE'

    def __init__(self, egress_security_rules=None, id='seclist'):
        self.egress_security_rules = egress_security_rules or []
        self.id = id


def _install_stub_modules():
    oci_module = types.ModuleType('oci')
    oci_core_module = types.ModuleType('oci.core')
    oci_models_module = types.ModuleType('oci.core.models')
    oci_exceptions_module = types.ModuleType('oci.exceptions')

    oci_core_module.VirtualNetworkClient = object
    oci_core_module.ComputeClient = object
    oci_core_module.VirtualNetworkClientCompositeOperations = lambda client: mock.Mock()

    for _name in (
        'CreateServiceGatewayDetails', 'CreateSecurityListDetails', 'UpdateServiceGatewayDetails',
        'UpdateRouteTableDetails', 'ServiceGateway', 'RouteTable', 'RouteRule', 'ServiceIdRequestDetails',
        'SecurityRule', 'Subnet', 'Vcn', 'Service', 'UpdateSecurityListDetails', 'UpdateSubnetDetails'
    ):
        setattr(oci_models_module, _name, type(_name, (), {}))
    oci_models_module.PortRange = PortRange
    oci_models_module.TcpOptions = TcpOptions
    oci_models_module.SecurityList = SecurityList
    oci_models_module.EgressSecurityRule = EgressSecurityRule
    oci_exceptions_module.ServiceError = Exception

    exabox_module = types.ModuleType('exabox')
    core_module = types.ModuleType('exabox.core')
    context_module = types.ModuleType('exabox.core.Context')
    exatest_module = types.ModuleType('exabox.exatest')
    common_module = types.ModuleType('exabox.exatest.common')
    util_module = types.ModuleType('exabox.exatest.common.ebExacloudUtil')
    exaoci_module = types.ModuleType('exabox.exaoci')
    factory_module = types.ModuleType('exabox.exaoci.ExaOCIFactory')

    context_module.get_gcontext = lambda: None
    util_module.ebExacloudUtil = mock.Mock()
    factory_module.ExaOCIFactory = mock.Mock()

    sys.modules.update({
        'oci': oci_module,
        'oci.core': oci_core_module,
        'oci.core.models': oci_models_module,
        'oci.exceptions': oci_exceptions_module,
        'exabox': exabox_module,
        'exabox.core': core_module,
        'exabox.core.Context': context_module,
        'exabox.exatest': exatest_module,
        'exabox.exatest.common': common_module,
        'exabox.exatest.common.ebExacloudUtil': util_module,
        'exabox.exaoci': exaoci_module,
        'exabox.exaoci.ExaOCIFactory': factory_module,
    })


def _load_oci_access_control():
    _install_stub_modules()
    _exacloudRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    _modulePath = os.path.join(_exacloudRoot, 'scripts', 'network', 'oci_access_control.py')
    _spec = importlib.util.spec_from_file_location('oci_access_control', _modulePath)
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    return _module


class TestOCIAccessControl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_oci_access_control()

    def _logged_messages(self, logger):
        return [call.args[0] for call in logger.call_args_list if call.args]

    def _make_rule(self, source_port_range):
        return EgressSecurityRule(
            destination='all-phx-services',
            destination_type='SERVICE_CIDR_BLOCK',
            is_stateless=False,
            protocol='6',
            tcp_options=TcpOptions(
                destination_port_range=PortRange(min=443, max=443),
                source_port_range=source_port_range
            )
        )

    def test_default_port_range_is_all(self):
        self.assertEqual('ALL', self.module.DEFAULT_PORT_RANGE)
        self.assertIsNone(self.module.ebUtil.mStrToPortRange(self.module.DEFAULT_PORT_RANGE))

    def test_explicit_port_range_still_supported(self):
        _portRange = self.module.ebUtil.mStrToPortRange('9000-65500')
        self.assertEqual(9000, _portRange.min)
        self.assertEqual(65500, _portRange.max)

    def test_create_rule_defaults_source_port_range_to_all(self):
        _manager = self.module.ebSecurityListManager(mock.Mock())
        with mock.patch.object(self.module.ebVCNManager, 'mSearchServiceByCIDR',
                               return_value=types.SimpleNamespace(cidr_block='all-phx-services')), \
             mock.patch.object(self.module.ebLogger, 'mLog') as _logger:
            _rule = _manager.mCreateOCIAccessRule(self.module.DEFAULT_PORT_RANGE)
        self.assertEqual(443, _rule.tcp_options.destination_port_range.min)
        self.assertEqual(443, _rule.tcp_options.destination_port_range.max)
        self.assertIsNone(_rule.tcp_options.source_port_range)
        self.assertTrue(any(
            'OCI access desired egress rule: destination=all-phx-services' in message and
            'dest_port=443-443' in message and
            'requested_source_port_range=ALL' in message and
            'normalized_source_port_range=ALL' in message
            for message in self._logged_messages(_logger)
        ))

    def test_create_rule_logs_explicit_source_port_range(self):
        _manager = self.module.ebSecurityListManager(mock.Mock())
        with mock.patch.object(self.module.ebVCNManager, 'mSearchServiceByCIDR',
                               return_value=types.SimpleNamespace(cidr_block='all-phx-services')), \
             mock.patch.object(self.module.ebLogger, 'mLog') as _logger:
            _rule = _manager.mCreateOCIAccessRule('9000-65500')
        self.assertEqual(9000, _rule.tcp_options.source_port_range.min)
        self.assertEqual(65500, _rule.tcp_options.source_port_range.max)
        self.assertTrue(any(
            'requested_source_port_range=9000-65500' in message and
            'normalized_source_port_range=9000-65500' in message
            for message in self._logged_messages(_logger)
        ))

    def test_ensure_rule_replaces_restricted_source_port_rule(self):
        _oldRule = self._make_rule(PortRange(min=9000, max=65500))
        _newRule = self._make_rule(None)
        _secList = SecurityList(egress_security_rules=[_oldRule])
        _manager = self.module.ebSecurityListManager(mock.Mock())

        with mock.patch.object(_manager, 'mFindOCIAccessEgressRules', return_value=[_oldRule]), \
             mock.patch.object(_manager, 'mRemoveOCIAccessSecurityListRules', return_value=SecurityList()) as _remove, \
             mock.patch.object(_manager, 'mAddSecurityListRule', return_value=SecurityList()) as _add, \
             mock.patch.object(self.module.ebLogger, 'mLog') as _logger:
            _manager.mEnsureOCIAccessSecurityListRule(_secList, _newRule)

        _remove.assert_called_once_with(_secList, aKeepRule=None)
        _add.assert_called_once()
        self.assertIs(_newRule, _add.call_args[0][1])
        self.assertTrue(any(
            'existing rule source_port_range=9000-65500 differs from desired source_port_range=ALL' in message and
            'replacing existing OCI access rules' in message
            for message in self._logged_messages(_logger)
        ))

    def test_ensure_rule_keeps_existing_all_source_port_rule(self):
        _existingRule = self._make_rule(None)
        _newRule = self._make_rule(None)
        _secList = SecurityList(egress_security_rules=[_existingRule])
        _manager = self.module.ebSecurityListManager(mock.Mock())

        with mock.patch.object(_manager, 'mFindOCIAccessEgressRules', return_value=[_existingRule]), \
             mock.patch.object(_manager, 'mRemoveOCIAccessSecurityListRules', return_value=SecurityList()) as _remove, \
             mock.patch.object(_manager, 'mAddSecurityListRule') as _add, \
             mock.patch.object(self.module.ebLogger, 'mLog') as _logger:
            _manager.mEnsureOCIAccessSecurityListRule(_secList, _newRule)

        _remove.assert_called_once_with(_secList, aKeepRule=_existingRule)
        _add.assert_not_called()
        self.assertTrue(any(
            'matching source_port_range=ALL already exists' in message and
            'keeping one rule and removing duplicates' in message
            for message in self._logged_messages(_logger)
        ))


if __name__ == '__main__':
    unittest.main()
