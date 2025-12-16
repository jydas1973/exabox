#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/atp/tests_atpfeatures.py /main/3 2024/01/23 19:09:43 ririgoye Exp $
#
# tests_atpfeatures.py
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_atpfeatures.py - Tests for ebAtpUtils features handling.
#
#    DESCRIPTION
#      Tests mainly areATPFeatureDependenciesSatisfied because it's an impure
#      function that depends on the global context.
#      We generate a set of combinations of ATP features and dependencies,
#      then we check if the pure version matches with the impure version.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/01/23 - Bug 35769896 - PROTECT YIELD KEYWORDS WITH
#                           TRY-EXCEPT BLOCKS
#    scoral      11/30/20 - Creation
#

import unittest
from typing import TypeVar, Sequence, List, Callable, Generator, Dict, Set, Tuple
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Context import get_gcontext
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.ovm.atp import ATP_FEATUREKEY_CLASSNAME_MAP, areATPFeatureDependenciesSatisfied

A, B = map(TypeVar, ['A', 'B'])


def getBits(x: int, numBits: int) -> Generator[bool, None, bool]:
    """
    Converts an integer to a sequence of booleans representing their
    binary states starting from the least significative bit.

    e.g.:
    getbits(12, 4) == [False, False, True, True]
    """
    for _ in range(numBits):
        try:
            yield bool(x & 1)
            x >>= 1
        except StopIteration:
            return

def buildAtpFeaturesDict(numFeatures: int, stateFeatures: int) -> Dict[str, bool]:
    """
    Builds an atp dictionary like the one contained in exabox.conf
    given the number of features and their states.

    e.g.:
    buildAtpFeaturesDict(4, 12) == {
        "feature_0": "False",
        "feature_1": "False",
        "feature_2": "True",
        "feature_3": "True"
    }
    """
    return dict(zip(
        map(lambda n: f'feature_{n}', range(numFeatures)),
        map(str, getBits(stateFeatures, numFeatures))
    ))

def buildAtpDependenciesDict(numFeatures: int, stateEnabled: int, stateDisabled: int) -> Dict[str, Tuple[Set[str], Set[str]]]:
    """
    Builds an ATP_FEATUREKEY_CLASSNAME_MAP like dictionary with classnames
    as feature names and sets the enabled and disabled dependencies for
    the first feature only.

    e.g.:
    buildAtpDependenciesDict(4, 12, 3) == {
        "feature_0": ({"feature_2", "feature_3"}, {"feature_0", "feature_1"}),
        "feature_1": ({}, {}),
        "feature_2": ({}, {}),
        "feature_3": ({}, {})
    }
    """
    if numFeatures == 0:
        return {}
    
    _build_set = lambda state: {
        f'feature_{n}'
        for n, bit
        in zip(range(2**numFeatures), getBits(state, numFeatures))
        if bit
    }
    _result = dict(map(lambda n: (f'feature_{n}', ({}, {})), range(numFeatures)))
    _result['feature_0'] = (_build_set(stateEnabled), _build_set(stateDisabled))
    return _result

def getExpectedResult(features: Dict[str, bool], dependencies: Dict[str, Tuple[Set[str], Set[str]]]) -> bool:
    """
    "Pure" version of areATPFeatureDependenciesSatisfied. It's supposed to be
    implemented the same, but this one doesn't read the context, so it's
    expected to behave the same.
    """
    _enabledFeatures, _disabledFeatures = dependencies['feature_0']
    _isFeatureEnabled = lambda feature: features.get(feature) == str(True)
    return all(map(_isFeatureEnabled, _enabledFeatures)) and \
        not any(map(_isFeatureEnabled, _disabledFeatures))


class ebTestAtpFeatures(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_atpfeatures(self):
        # Test ALL possible combinations
        # O(2^(3n))
        n = 1
        for features in [ buildAtpFeaturesDict(n, state) for state in range(2**n) ]:
            get_gcontext().mSetConfigOption('atp', features)
            for dependencies in [
                    buildAtpDependenciesDict(n, enabled, disabled)
                    for enabled in range(2**n)
                    for disabled in range(2**n)
                ]:
                
                self.assertEqual(
                    getExpectedResult(features, dependencies),
                    areATPFeatureDependenciesSatisfied('feature_0', dependencies)
                )


if __name__ == '__main__':
    unittest.main()
