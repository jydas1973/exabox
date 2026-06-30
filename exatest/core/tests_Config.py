#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_Config.py /main/1 2024/03/11 15:24:49 jfsaldan Exp $
#
# tests_Config.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_Config.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    abysebas    04/16/26 - ER 38915551 - SUPPORT FOR EXACLOUD IN BUTTERFLY
#                           REGIONS
#    jfsaldan    03/08/24 - Bug 36350252 - EXACC GEN2 | INFRA PATCHING | DOMU
#                           OS PRECHECK/PATCHING FAILING ON ADBD VMS DUE TO
#                           MISSING KEYS
#    jfsaldan    03/08/24 - Creation
#

import unittest
import json
import os
import tempfile
from types import SimpleNamespace
from unittest import mock

import exabox.config.Config as config_module
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.config.Config import (
    _load_cfgfile,
    ebLoadProgramArguments,
    get_value_from_exabox_config,
)


class _DummyContext(object):

    def __init__(self, reg_entries=None, config_options=None):
        self._reg_entries = reg_entries or {}
        self._config_options = config_options or {}


    def mCheckRegEntry(self, key):
        return key in self._reg_entries


    def mGetRegEntry(self, key):
        return self._reg_entries.get(key)


    def mGetConfigOptions(self):
        return self._config_options


class ebTestConfig(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None


    def test_diffkeys_patching_program_args(self):
        """
        Make sure infrapatching has diffkeys argument
        """
        PROGRAM_ARGUMENTS, CLU_CMDS_OPTIONS, VM_CMDS_OPTIONS, CS_SUBSTEPS_CMDS_OPTIONS = ebLoadProgramArguments()
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('patch'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('patch_prereq_check'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('postcheck'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('rollback'))
        self.assertTrue('diffsync_keys' in CLU_CMDS_OPTIONS.get('rollback_prereq_check'))


    def _write_temp_config(self, aConfig):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as cfgfile:
            json.dump(aConfig, cfgfile)

        self.addCleanup(os.unlink, cfgfile.name)
        return cfgfile.name


    def test_load_cfgfile_applies_low_profile_overlay(self):
        """
        Make sure low profile overlay updates the top-level config when enabled.
        """
        cfgpath = self._write_temp_config({
            'region_name': 'region1',
            'shape': 'dense',
            'low_profile_region': True,
            'low_profile_config': {
                'region_name': 'region1-butterfly',
                'shape': 'base'
            }
        })

        dictConfig = _load_cfgfile(cfgpath, {'exatest': True})

        self.assertEqual('region1-butterfly', dictConfig['region_name'])
        self.assertEqual('base', dictConfig['shape'])


    def test_load_cfgfile_skips_low_profile_overlay_when_disabled(self):
        """
        Make sure low profile values are ignored when the region flag is disabled.
        """
        cfgpath = self._write_temp_config({
            'region_name': 'region1',
            'shape': 'dense',
            'low_profile_region': False,
            'low_profile_config': {
                'region_name': 'region1-butterfly',
                'shape': 'base'
            }
        })

        dictConfig = _load_cfgfile(cfgpath, {'exatest': True})

        self.assertEqual('region1', dictConfig['region_name'])
        self.assertEqual('dense', dictConfig['shape'])


    def test_get_value_from_exabox_config_returns_overlaid_value(self):
        """
        Make sure value lookups return the overlaid low profile config values.
        """
        cfgpath = self._write_temp_config({
            'region_name': 'region1',
            'low_profile_region': 'TRUE',
            'low_profile_config': {
                'region_name': 'region1-butterfly'
            }
        })

        self.assertEqual(
            'region1-butterfly',
            get_value_from_exabox_config('region_name', cfgpath)
        )

    # Auto-generated test for _load_cfgfile
    def test_load_cfgfile_skips_overlay_when_low_profile_config_not_dict(self):
        cfgpath = self._write_temp_config({
            'region_name': 'region1',
            'low_profile_region': 'TRUE',
            'low_profile_config': ['not', 'a', 'dict']
        })

        dictConfig = _load_cfgfile(cfgpath, {'exatest': True})

        self.assertEqual('region1', dictConfig['region_name'])


    # Auto-generated test for _load_cfgfile
    def test_load_cfgfile_masks_sensitive_values_and_updates_file(self):
        cfgpath = self._write_temp_config({
            'proxy_port': 443,
            'ec_agent_port': 8443,
            'default_pwd': 'encoded-secret'
        })

        with mock.patch.object(config_module, 'checkifsaltedandb64encoded', return_value=False), \
             mock.patch.object(config_module, 'umask', side_effect=lambda value: 'decoded-' + value), \
             mock.patch.object(config_module, 'mask', side_effect=lambda value: 'masked-' + value), \
             mock.patch.object(config_module, 'mBackupFile') as backup_file, \
             mock.patch.object(config_module.os, 'access', return_value=True):
            dictConfig = _load_cfgfile(cfgpath, config_module.argparse.Namespace(exatest=False))

        self.assertEqual(8443, dictConfig['agent_port'])
        self.assertEqual('decoded-encoded-secret', dictConfig['default_pwd'])
        backup_file.assert_called_once_with(cfgpath, True)

        with open(cfgpath) as cfgfile:
            stored_config = json.load(cfgfile)

        self.assertEqual('masked-decoded-encoded-secret', stored_config['default_pwd'])


    # Auto-generated test for _load_cfgfile
    def test_load_cfgfile_skips_write_when_masked_values_change_but_file_is_not_writable(self):
        cfgpath = self._write_temp_config({
            'default_pwd': 'encoded-secret'
        })

        with mock.patch.object(config_module, 'checkifsaltedandb64encoded', return_value=False), \
             mock.patch.object(config_module, 'umask', side_effect=lambda value: 'decoded-' + value), \
             mock.patch.object(config_module, 'mask', side_effect=lambda value: 'masked-' + value), \
             mock.patch.object(config_module, 'mBackupFile') as backup_file, \
             mock.patch.object(config_module.os, 'access', return_value=False):
            dictConfig = _load_cfgfile(cfgpath, {'exatest': False})

        self.assertEqual('decoded-encoded-secret', dictConfig['default_pwd'])
        backup_file.assert_called_once_with(cfgpath, True)

        with open(cfgpath) as cfgfile:
            stored_config = json.load(cfgfile)

        self.assertEqual('encoded-secret', stored_config['default_pwd'])


    # Auto-generated test for get_value_from_exabox_config
    def test_get_value_from_exabox_config_logs_and_reraises_on_error(self):
        with mock.patch.object(config_module, '_load_cfgfile', side_effect=RuntimeError('boom')), \
             mock.patch.object(config_module, 'ebLogError') as log_error:
            with self.assertRaises(RuntimeError):
                get_value_from_exabox_config('region_name', '/tmp/missing.conf')

        self.assertIn('/tmp/missing.conf', log_error.call_args[0][0])
        self.assertIn('boom', log_error.call_args[0][0])


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_exits_when_base_path_cannot_be_built(self):
        options = SimpleNamespace(exaconf=None)

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/run.py'), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=False), \
             mock.patch('builtins.print') as print_mock:
            with self.assertRaises(SystemExit):
                config_module.exaBoxConfigFileReader(options)

        self.assertIn('Could not build base path', print_mock.call_args[0][0])


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_uses_absolute_config_path(self):
        options = SimpleNamespace(exaconf='/tmp/custom.conf')

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, '_load_cfgfile', return_value={'loaded': True}) as load_cfgfile:
            self.assertEqual({'loaded': True}, config_module.exaBoxConfigFileReader(options))

        load_cfgfile.assert_called_once_with('/tmp/custom.conf', options)


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_warns_when_relative_config_path_is_missing(self):
        options = SimpleNamespace(exaconf='config/custom.conf')

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=True), \
             mock.patch.object(config_module, 'ebLogWarn') as log_warn:
            self.assertIsNone(config_module.exaBoxConfigFileReader(options))

        log_warn.assert_called_once_with('ExaBox Config file not found: /tmp/config/custom.conf')


    # Auto-generated test for ebJsonConfigFileReader
    def test_ebJsonConfigFileReader_reads_existing_local_file(self):
        cfgpath = self._write_temp_config({'shape': 'dense'})

        self.assertEqual({'shape': 'dense'}, config_module.ebJsonConfigFileReader(cfgpath))


    # Auto-generated test for ebJsonConfigFileReader
    def test_ebJsonConfigFileReader_reads_db_file_when_db_version_is_two(self):
        fake_db = SimpleNamespace(mReadFile=mock.Mock(return_value='{"shape": "base"}'))
        fake_module = SimpleNamespace(ebGetDefaultDB=mock.Mock(return_value=fake_db))

        with mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'get_gcontext', return_value=_DummyContext(config_options={'db_version': '2'})), \
             mock.patch.dict('sys.modules', {'exabox.core.DBStore': fake_module}, clear=False):
            self.assertEqual({'shape': 'base'}, config_module.ebJsonConfigFileReader('/tmp/db.json'))

        fake_module.ebGetDefaultDB.assert_called_once_with()
        fake_db.mReadFile.assert_called_once_with('/tmp/db.json', 'ecra_files')


    # Auto-generated test for ebJsonConfigFileReader
    def test_ebJsonConfigFileReader_prints_when_db_version_is_two_but_db_file_is_empty(self):
        fake_db = SimpleNamespace(mReadFile=mock.Mock(return_value=''))
        fake_module = SimpleNamespace(ebGetDefaultDB=mock.Mock(return_value=fake_db))

        with mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'get_gcontext', return_value=_DummyContext(config_options={'db_version': '2'})), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=False), \
             mock.patch.dict('sys.modules', {'exabox.core.DBStore': fake_module}, clear=False), \
             mock.patch('builtins.print') as print_mock:
            self.assertIsNone(config_module.ebJsonConfigFileReader('/tmp/db-miss.json'))

        fake_module.ebGetDefaultDB.assert_called_once_with()
        fake_db.mReadFile.assert_called_once_with('/tmp/db-miss.json', 'ecra_files')
        self.assertIn('/tmp/db-miss.json', print_mock.call_args[0][0])


    # Auto-generated test for ebJsonConfigFileReader
    def test_ebJsonConfigFileReader_returns_none_and_prints_when_missing_without_logger(self):
        with mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'get_gcontext', return_value=_DummyContext(config_options={'db_version': '1'})), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=False), \
             mock.patch('builtins.print') as print_mock:
            self.assertIsNone(config_module.ebJsonConfigFileReader('/tmp/missing.json'))

        self.assertIn('/tmp/missing.json', print_mock.call_args[0][0])


    # Auto-generated test for ebJsonConfigFileReader
    def test_ebJsonConfigFileReader_warns_when_missing_with_initialized_logger(self):
        with mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'get_gcontext', return_value=_DummyContext(config_options={'db_version': '1'})), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=True), \
             mock.patch.object(config_module, 'ebLogWarn') as log_warn:
            self.assertIsNone(config_module.ebJsonConfigFileReader('/tmp/missing.json'))

        log_warn.assert_called_once_with('ExaBox Config file not found: /tmp/missing.json')


    # Auto-generated test for ebCluCmdCheckOptions
    def test_ebCluCmdCheckOptions_rejects_unknown_command(self):
        self.assertFalse(config_module.ebCluCmdCheckOptions('unknown', ['opt']))


    # Auto-generated test for ebCluCmdCheckOptions
    def test_ebCluCmdCheckOptions_filters_prefixed_options_by_environment(self):
        clu_cmds = {
            'patch': set(['always', 'exadbxs:dbx-only', 'exacc:acc-only'])
        }

        with mock.patch.object(config_module, 'CLU_CMDS_OPTIONS', clu_cmds), \
             mock.patch.object(config_module, 'get_gcontext', return_value=_DummyContext()):
            self.assertTrue(config_module.ebCluCmdCheckOptions('patch', ['always']))
            self.assertFalse(config_module.ebCluCmdCheckOptions('patch', ['dbx-only']))

        env_context = _DummyContext(reg_entries={'ENV_EXADBXS': True, 'ENV_EXACC': True})
        with mock.patch.object(config_module, 'CLU_CMDS_OPTIONS', clu_cmds), \
             mock.patch.object(config_module, 'get_gcontext', return_value=env_context):
            self.assertTrue(config_module.ebCluCmdCheckOptions('patch', ['dbx-only', 'acc-only']))


    # Auto-generated test for ebVmCmdCheckOptions
    def test_ebVmCmdCheckOptions_checks_known_and_unknown_commands(self):
        with mock.patch.object(config_module, 'VM_CMDS_OPTIONS', {'vmcmd': set(['opt1', 'opt2'])}):
            self.assertTrue(config_module.ebVmCmdCheckOptions('vmcmd', ['opt1']))
            self.assertFalse(config_module.ebVmCmdCheckOptions('missing', ['opt1']))


    # Auto-generated test for ebCsSubCmdCheckOptions
    def test_ebCsSubCmdCheckOptions_checks_known_and_unknown_commands(self):
        with mock.patch.object(config_module, 'CS_SUBSTEPS_CMDS_OPTIONS', {'step': set(['phase1'])}):
            self.assertTrue(config_module.ebCsSubCmdCheckOptions('step', ['phase1']))
            self.assertFalse(config_module.ebCsSubCmdCheckOptions('missing', ['phase1']))


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_uses_parser_args_and_sets_agent_from_proxy(self):
        program_args = {
            'proxy': {'choices': ['asproxy', 'agent'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        parsed = SimpleNamespace(proxy='agent', agent=None, standbyloc=None)
        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.argparse.ArgumentParser, 'parse_args', return_value=parsed) as parse_args:
            options = config_module.exaBoxProcessArgs(None)

        parse_args.assert_called_once_with()
        self.assertEqual('agent', options.agent)


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_keeps_agent_empty_for_asproxy(self):
        program_args = {
            'proxy': {'choices': ['asproxy'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        parsed = SimpleNamespace(proxy='asproxy', agent=None, standbyloc=None)
        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.argparse.ArgumentParser, 'parse_args', return_value=parsed) as parse_args:
            options = config_module.exaBoxProcessArgs(None)

        parse_args.assert_called_once_with()
        self.assertIsNone(options.agent)


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_requires_standbyloc_for_switchover(self):
        program_args = {
            'proxy': {'choices': ['switchover'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args):
            with self.assertRaises(SystemExit):
                config_module.exaBoxProcessArgs(None, ['--proxy', 'switchover'])


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_logs_when_switchover_location_is_invalid(self):
        program_args = {
            'proxy': {'choices': ['switchover'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'ebLogError') as log_error:
            options = config_module.exaBoxProcessArgs(
                None,
                ['--proxy', 'switchover', '--standbyloc', '/tmp/missing']
            )

        self.assertEqual('switchover', options.proxy)
        log_error.assert_called_once_with('Standby proxy location invalid: /tmp/missing')


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_accepts_existing_standbyloc_for_switchover(self):
        program_args = {
            'proxy': {'choices': ['switchover'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, 'ebLogError') as log_error:
            options = config_module.exaBoxProcessArgs(
                None,
                ['--proxy', 'switchover', '--standbyloc', '/tmp/existing']
            )

        self.assertEqual('switchover', options.proxy)
        self.assertEqual('switchover', options.agent)
        self.assertEqual('/tmp/existing', options.standbyloc)
        log_error.assert_not_called()


    # Auto-generated test for import fallback
    def test_config_import_fallback_raises_when_ordereddict_is_missing(self):
        with open(config_module.__file__) as config_file:
            source_lines = config_file.readlines()

        import_block = ('\n' * 66) + ''.join(source_lines[66:70])
        real_import = __import__

        def _import_without_ordereddict(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'collections' and fromlist and 'OrderedDict' in fromlist:
                raise ImportError('forced OrderedDict import failure')
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch('builtins.__import__', side_effect=_import_without_ordereddict):
            with self.assertRaises(ImportError) as ctx:
                exec(compile(import_block, config_module.__file__, 'exec'), {})

        self.assertIn('OrderedDict', str(ctx.exception))


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_logs_when_base_path_cannot_be_built_with_logger(self):
        options = SimpleNamespace(exaconf=None)

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/run.py'), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=True), \
             mock.patch.object(config_module, 'ebLogError') as log_error:
            with self.assertRaises(SystemExit):
                config_module.exaBoxConfigFileReader(options)

        log_error.assert_called_once_with('Could not build base path : /tmp/run.py')


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_prints_when_default_config_is_missing_without_logger(self):
        options = SimpleNamespace(exaconf=None)

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=False), \
             mock.patch.object(config_module, 'ebLogInitialized', return_value=False), \
             mock.patch('builtins.print') as print_mock:
            self.assertIsNone(config_module.exaBoxConfigFileReader(options))

        print_mock.assert_called_once_with('*** ERROR *** ExaBox Config file not found: /tmp/config/exabox.conf')


    # Auto-generated test for _load_cfgfile
    def test_load_cfgfile_skips_backup_when_exatest_is_true(self):
        cfgpath = self._write_temp_config({
            'default_pwd': 'encoded-secret'
        })

        with mock.patch.object(config_module, 'checkifsaltedandb64encoded', return_value=False), \
             mock.patch.object(config_module, 'umask', side_effect=lambda value: 'decoded-' + value), \
             mock.patch.object(config_module, 'mask', side_effect=lambda value: 'masked-' + value), \
             mock.patch.object(config_module, 'mBackupFile') as backup_file:
            dictConfig = _load_cfgfile(cfgpath, {'exatest': True})

        self.assertEqual('decoded-encoded-secret', dictConfig['default_pwd'])
        backup_file.assert_not_called()

        with open(cfgpath) as cfgfile:
            stored_config = json.load(cfgfile)

        self.assertEqual('encoded-secret', stored_config['default_pwd'])


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_uses_default_config_path_when_present(self):
        options = SimpleNamespace(exaconf=None)

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, '_load_cfgfile', return_value={'loaded': 'default'}) as load_cfgfile:
            self.assertEqual({'loaded': 'default'}, config_module.exaBoxConfigFileReader(options))

        load_cfgfile.assert_called_once_with('/tmp/config/exabox.conf', options)


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_uses_relative_config_path_when_present(self):
        options = SimpleNamespace(exaconf='config/custom.conf')

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, '_load_cfgfile', return_value={'loaded': 'relative'}) as load_cfgfile:
            self.assertEqual({'loaded': 'relative'}, config_module.exaBoxConfigFileReader(options))

        load_cfgfile.assert_called_once_with('/tmp/config/custom.conf', options)


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_preserves_existing_agent_value(self):
        program_args = {
            'proxy': {'choices': ['agent'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        parsed = SimpleNamespace(proxy='agent', agent='custom-agent', standbyloc=None)
        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.argparse.ArgumentParser, 'parse_args', return_value=parsed) as parse_args:
            options = config_module.exaBoxProcessArgs(None)

        parse_args.assert_called_once_with()
        self.assertEqual('custom-agent', options.agent)


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_accepts_shortname_arguments(self):
        program_args = {
            'proxy': {
                'choices': ['agent', 'asproxy'],
                'required': True,
                'shortname': 'p',
            },
            'agent': {
                'required': False,
                'shortname': 'a',
            },
            'standbyloc': {'required': False},
        }

        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args):
            options = config_module.exaBoxProcessArgs(
                None,
                ['-p', 'agent', '-a', 'explicit-agent']
            )

        self.assertEqual('agent', options.proxy)
        self.assertEqual('explicit-agent', options.agent)

    # Auto-generated test for _apply_low_profile_overlay
    def test_apply_low_profile_overlay_skips_logging_when_flag_is_disabled(self):
        config = {
            'shape': 'dense'
        }

        with mock.patch.object(config_module, 'ebLogInfo') as log_info, \
             mock.patch.object(config_module, 'ebLogDebug') as log_debug:
            result = config_module._apply_low_profile_overlay(config)

        self.assertIs(config, result)
        self.assertEqual('dense', result['shape'])
        log_info.assert_not_called()
        log_debug.assert_not_called()


    # Auto-generated test for _apply_low_profile_overlay
    def test_apply_low_profile_overlay_logs_and_updates_values_when_enabled(self):
        config = {
            'shape': 'dense',
            'low_profile_region': 'true',
            'low_profile_config': {
                'shape': 'base',
                'region_name': 'region1-butterfly'
            }
        }

        with mock.patch.object(config_module, 'ebLogInfo') as log_info, \
             mock.patch.object(config_module, 'ebLogDebug') as log_debug:
            result = config_module._apply_low_profile_overlay(config)

        self.assertIs(config, result)
        self.assertEqual('base', result['shape'])
        self.assertEqual('region1-butterfly', result['region_name'])
        log_info.assert_called_once_with('Applying low profile region config overlay')
        self.assertEqual(2, log_debug.call_count)
        log_debug.assert_any_call('low_profile_config[shape]=base')
        log_debug.assert_any_call('low_profile_config[region_name]=region1-butterfly')


    # Auto-generated test for ebVmCmdCheckOptions
    def test_ebVmCmdCheckOptions_rejects_invalid_option_for_known_command(self):
        with mock.patch.object(config_module, 'VM_CMDS_OPTIONS', {'vmcmd': set(['opt1', 'opt2'])}):
            self.assertFalse(config_module.ebVmCmdCheckOptions('vmcmd', ['opt3']))


    # Auto-generated test for ebCsSubCmdCheckOptions
    def test_ebCsSubCmdCheckOptions_rejects_invalid_option_for_known_command(self):
        with mock.patch.object(config_module, 'CS_SUBSTEPS_CMDS_OPTIONS', {'step': set(['phase1'])}):
            self.assertFalse(config_module.ebCsSubCmdCheckOptions('step', ['phase2']))


    # Auto-generated test for _load_cfgfile
    def test_load_cfgfile_skips_backup_when_sensitive_values_are_already_salted(self):
        cfgpath = self._write_temp_config({
            'default_pwd': 'encoded-secret'
        })

        with mock.patch.object(config_module, 'checkifsaltedandb64encoded', return_value=True), \
             mock.patch.object(config_module, 'umask', side_effect=lambda value: 'decoded-' + value), \
             mock.patch.object(config_module, 'mask', side_effect=lambda value: 'masked-' + value), \
             mock.patch.object(config_module, 'mBackupFile') as backup_file, \
             mock.patch.object(config_module.os, 'access') as os_access:
            dictConfig = _load_cfgfile(cfgpath, {'exatest': False})

        self.assertEqual('decoded-encoded-secret', dictConfig['default_pwd'])
        backup_file.assert_not_called()
        os_access.assert_not_called()


    # Auto-generated test for exaBoxConfigFileReader
    def test_exaBoxConfigFileReader_uses_default_config_path_when_exaconf_missing(self):
        options = SimpleNamespace(exaconf=None)

        with mock.patch.object(config_module.sys, 'argv', ['/tmp/exabox/run.py']), \
             mock.patch.object(config_module.os.path, 'abspath', return_value='/tmp/exabox/run.py'), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, '_load_cfgfile', return_value={'loaded': True}) as load_cfgfile:
            self.assertEqual({'loaded': True}, config_module.exaBoxConfigFileReader(options))

        load_cfgfile.assert_called_once_with('/tmp/config/exabox.conf', options)


    # Auto-generated test for exaBoxProcessArgs
    def test_exaBoxProcessArgs_accepts_existing_standbyloc_for_switchover(self):
        program_args = {
            'proxy': {'choices': ['switchover'], 'required': True},
            'agent': {'required': False},
            'standbyloc': {'required': False},
        }

        with mock.patch.object(config_module, 'PROGRAM_ARGUMENTS', program_args), \
             mock.patch.object(config_module.os.path, 'exists', return_value=True), \
             mock.patch.object(config_module, 'ebLogError') as log_error:
            options = config_module.exaBoxProcessArgs(
                None,
                ['--proxy', 'switchover', '--standbyloc', '/tmp/present']
            )

        self.assertEqual('switchover', options.proxy)
        self.assertEqual('switchover', options.agent)
        self.assertEqual('/tmp/present', options.standbyloc)
        log_error.assert_not_called()


    # Auto-generated test for ebLoadProgramArguments
    def test_ebLoadProgramArguments_normalizes_choice_collections(self):
        payload = {
            'clusterctrl': {'choices': {'patch': ['opt1', 'opt2']}},
            'vmcmd': {'choices': {'start': ['vmopt']}},
            'steplist': {'tags': {'phase1': ['tag1', 'tag2']}},
        }

        with mock.patch.object(config_module.json, 'load', return_value=payload), \
             mock.patch('builtins.open', mock.mock_open(read_data='{}')) as open_mock:
            program_args, clu_cmds, vm_cmds, cs_substeps = ebLoadProgramArguments()

        open_mock.assert_called_once_with('config/program_arguments.conf', 'r')
        self.assertEqual(['patch'], program_args['clusterctrl']['choices'])
        self.assertEqual(['start'], program_args['vmcmd']['choices'])
        self.assertNotIn('tags', program_args['steplist'])
        self.assertEqual(set(['opt1', 'opt2']), clu_cmds['patch'])
        self.assertEqual(set(['vmopt']), vm_cmds['start'])
        self.assertEqual(set(['tag1', 'tag2']), cs_substeps['phase1'])


    # Auto-generated test for import fallback
    def test_config_import_fallback_uses_collections_abc_ordereddict_when_available(self):
        with open(config_module.__file__) as config_file:
            source_lines = config_file.readlines()

        import_block = ('\n' * 66) + ''.join(source_lines[66:70])
        real_import = __import__
        fallback_ordereddict = object()

        def _import_with_fallback(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'collections' and fromlist and 'OrderedDict' in fromlist:
                raise ImportError('forced OrderedDict import failure')
            if name == 'collections.abc' and fromlist and 'OrderedDict' in fromlist:
                return SimpleNamespace(OrderedDict=fallback_ordereddict)
            return real_import(name, globals, locals, fromlist, level)

        namespace = {}
        with mock.patch('builtins.__import__', side_effect=_import_with_fallback):
            exec(compile(import_block, config_module.__file__, 'exec'), namespace)

        self.assertIs(fallback_ordereddict, namespace['OrderedDict'])


if __name__ == '__main__':
    unittest.main()
