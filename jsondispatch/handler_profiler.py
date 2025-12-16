#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_profiler.py /main/1 2024/01/12 09:01:07 jesandov Exp $
#
# handler_profiler.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_profiler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/08/24 - Creation
#

import datetime
import time
import json
import os

from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler


class ProfilerHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetEmptyPayloadAllowed(False)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/profiler.json"))

    def mExecute(self):

        _profilerData = self.mGetDB().mGetProfilerData(
            self.mGetOptions().jsonconf.get("workflowId"),
            self.mGetOptions().jsonconf.get("exaunitId")
        )

        _parsedData = {
            "EXACLOUD": {
                "steps": {}
            },
            "OEDA": {
                "steps": {}
            },
            "EXTRA": {
                "cmds": {
                    "steps": {}
                },
                "files": {
                    "steps": {}
                }
            }
        }

        _stepId = {}
        _substepId = {}
        _generalStats = {}

        for _row in _profilerData:

            if _row["step"] not in _stepId:
                _stepId[_row["step"]] = f"{str(len(_stepId)).zfill(2)}_{_row['step']}"

            if _row["profiler_type"] == "step":

                if _stepId[_row["step"]] not in _parsedData[_row["component"]]["steps"]:
                    _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]] = {}

                if _row["component"] not in _generalStats:
                    _generalStats[_row["component"]] = {
                        "StartTime": _row["start_time"],
                        "EndTime": _row["end_time"]
                    }

                if _row["start_time"] < _generalStats[_row["component"]]["StartTime"]:
                    _generalStats[_row["component"]]["StartTime"] = _row["start_time"]

                if _row["end_time"] > _generalStats[_row["component"]]["EndTime"]:
                    _generalStats[_row["component"]]["EndTime"] = _row["end_time"]

                _start = datetime.datetime.strptime(_generalStats[_row["component"]]["StartTime"], "%Y-%m-%d %H:%M:%S")
                _end = datetime.datetime.strptime(_generalStats[_row["component"]]["EndTime"] , "%Y-%m-%d %H:%M:%S")
                _generalStats[_row["component"]]["Elapsed"] = str(_end - _start)

                _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]["StartTime"] = _row["start_time"]
                _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]["EndTime"] = _row["end_time"]
                _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]["Elapsed"] = _row["elapsed"]
 
            elif _row["profiler_type"] == "substeps":

                if _stepId[_row["step"]] not in _parsedData[_row["component"]]["steps"]:
                    _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]] = {}

                if "substeps" not in _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]:
                    _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]["substeps"] = {}

                _details = json.loads(_row["details"])
            
                if _details["substep"] not in _substepId:
                    _substepId[_details["substep"]] = f"{str(len(_substepId)).zfill(4)}_{_details['substep']}"

                _parsedData[_row["component"]]["steps"][_stepId[_row["step"]]]["substeps"][_substepId[_details["substep"]]] = {
                    "StartTime": _row["start_time"],
                    "EndTime": _row["end_time"],
                    "Elapsed": _row["elapsed"]
                }

            elif _row["profiler_type"] in ["cmds", "files"]:

                if _stepId[_row["step"]] not in _parsedData["EXTRA"][_row["profiler_type"]]["steps"]:
                    _parsedData["EXTRA"][_row["profiler_type"]]["steps"][_stepId[_row["step"]]] = []

                _details = json.loads(_row["details"])
                _parsedData["EXTRA"][_row["profiler_type"]]["steps"][_stepId[_row["step"]]].append({
                    "Details": _details,
                    "StartTime": _row["start_time"],
                    "EndTime": _row["end_time"],
                    "Elapsed": _row["elapsed"]
                })


        for _component, _stats in _generalStats.items():
            for _statK, _statV in _stats.items():
                _parsedData[_component][_statK] = _statV

        return (0, _parsedData)


# end of file
