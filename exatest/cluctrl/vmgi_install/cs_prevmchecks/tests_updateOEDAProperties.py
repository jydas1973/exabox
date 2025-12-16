#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_prevmchecks/tests_updateOEDAProperties.py /main/1 2021/08/20 08:23:59 ffrrodri Exp $
#
# tests_updateOEDAProperties.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_updateOEDAProperties.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    08/17/21 - Creation
#
import unittest
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError


def mOpenJSONFile(file_path):
    try:
        _f = open(file_path, 'r')
        _json_content = json.load(_f)
    except Exception as e:
        _msg = f"Failed to load {file_path} file: {e}"
        raise ExacloudRuntimeError(0x0750, 0xA, _msg) from e
    finally:
        _f.close()

    return _json_content


class OEDAProperties(ebTestClucontrol):
    _OEDA_properties_path = 'properties/OEDAProperties.json'
    _OEDA_properties_schema_path = 'properties/OEDAProperties-schema.json'

    # Open JSON file with OEDA properties
    _OEDA_properties = mOpenJSONFile(_OEDA_properties_path)

    # Open JSON file with OEDA properties schema
    _OEDA_properties_schema = mOpenJSONFile(_OEDA_properties_schema_path)

    def test_OEDA_properties_json_correct_structure(self):
        return self.assertEqual(validate(self._OEDA_properties, self._OEDA_properties_schema), None)

    def test_OEDA_properties_json_wrong_structure(self):
        _removed = self._OEDA_properties.pop("es.properties", False)
        if _removed:
            try:
                validate(self._OEDA_properties, self._OEDA_properties_schema)
            except ValidationError:
                self.assertTrue(True, "Catched wrong JSON structure")


if __name__ == '__main__':
    unittest.main()
