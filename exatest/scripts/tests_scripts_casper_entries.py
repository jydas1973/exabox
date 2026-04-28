#!/usr/bin/env python3
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import json
import os
import subprocess
import tempfile
import textwrap
import unittest

try:
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
except ImportError:
    class ebTestClucontrol(unittest.TestCase):
        pass


VIEW_ROOT = os.environ.get("ADE_VIEW_ROOT", "/ade/joysjose_voxioissue2")
SCRIPTS_ROOT = os.path.join(VIEW_ROOT, "ecs", "exacloud", "scripts")


class ebTestScriptsCasperEntries(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        pass

    def test_mlistobjects_returns_data_objects_without_json_reparse(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            oci_stub = os.path.join(temp_dir, "oci.py")
            with open(oci_stub, "w") as handle:
                handle.write("\n")

            script = textwrap.dedent("""
                import json
                import sys
                sys.path.insert(0, {scripts_root!r})
                import casper_entries

                class Data(object):
                    def __init__(self, objects):
                        self.objects = objects

                class Response(object):
                    def __init__(self, objects):
                        self.data = Data(objects)

                class ObjectStorage(object):
                    def list_objects(self, namespace, bucket_name):
                        return Response(["entry-a", "entry-b"])

                instance = casper_entries.ebKmsObjectStore.__new__(casper_entries.ebKmsObjectStore)
                instance._ebKmsObjectStore__object_storage = ObjectStorage()
                instance._ebKmsObjectStore__namespace = "namespace"
                instance._ebKmsObjectStore__bucketName = "bucket"
                rc, response = instance.mListObjects()
                print(json.dumps({{"rc": rc, "response": response}}))
            """.format(scripts_root=SCRIPTS_ROOT))

            env = dict(os.environ)
            env["PYTHONPATH"] = temp_dir
            result = subprocess.run(
                ["python2", "-c", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                env=env
            )

        payload = json.loads(result.stdout.decode("utf-8").strip())
        self.assertEqual(payload, {"rc": 0, "response": ["entry-a", "entry-b"]})


if __name__ == "__main__":
    unittest.main()
