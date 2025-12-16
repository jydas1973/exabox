"""
$Header:

 Copyright (c) 2014, 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    Base - Base Framework classes for the DB policies

FUNCTION:
    Handle requests DB policies

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    jesandov   03/09/20 - Add mysql quote compatibility
    vgerard    09/05/19 - Create file
"""

from exabox.core.Context import get_gcontext
import re

# --- FRAMEWORK PART : 
# We can specify a number of DB policy
# Base objects
#    * ebDbFilter(): 
#        Generate a bind variable WHERE statement to get the records affected
#        by the policy (WHERE above record num / WHERE above time...)
#    * ebDbTrigger(): 
#        Have a mEvaluate()  : bool
#               mGetFilterData() : Data for the operation to filter (date for Time/) 
#    * ebDbOperation(): have a mIsTriggerSupported(ebDBTrigger)
#                       and mExecute(ebDBTrigger=None) method
#    * ebDbPolicy(Trigger, Operation):
#        Will evaluate a Trigger + and Execute the Operation
#        if Trigger is supported and evaluated to True

class ebDBFilter(object):
    """ A Basic filter is a column and either a inclusion or exclusion list"""
    def __init__(self, aColumnName, aList, aMode):
        """ 
             Build a filter on a single column

             :param aColumnName
                 Column to filter upon
             :param aList
                 list of variable for the filter
             :param aMode
                 True: INCLUSION
                    WHERE aColumnName = <value1 in aList> or aColumnName = <value2 in aList>
                 False: EXCLUSION
                    WHERE NOT (aColumnName = <value1 in aList or aColumnName = <value2 in aList>)
        """
        self.__columnName  = aColumnName.replace('"','""') #prevent injection
        self.__criterias   = aList
        self.__mode        = aMode
        self.__idxSQLCache = {}

        if not self.__columnName:
            raise ValueError('Please provide a column name for the filter')
        if not self.__criterias:
            raise ValueError('Please provide at least a value for the filter')

    def __mGenerateFilter(self,aElemsLeft,aIdx,aFirstCall=True):
        """
         Internal function
         Generate recursively from a starting index the string for bind variables
         ( [NOT ] <ColumnName>=:<idx> [or <columnName>=:<idx+1>]0..n )
         """
        if not aElemsLeft:
            return ')' if self.__mode else '))'

        if aFirstCall:
            _buff = '( '
            if not self.__mode:
                _buff += 'NOT ('
        else:
            _buff = ' or '

        # Use double quote for column name
        if get_gcontext().mCheckRegEntry("use_mysql"):
            _buff += '`{}`=:{}'.format(self.__columnName, aIdx)
        else:
            _buff += '"{}"=:{}'.format(self.__columnName, aIdx)

        return _buff + self.__mGenerateFilter(aElemsLeft-1,aIdx+1, False)
    
    def mGetFilter(self,aIdx):
        """
        Generate the SQL filter 

        :param aIdx
            Index to start the first bind variable
        
        :return
             A string for the caller to easilly append the filter to any query
             If this filter is on column cmdtype and criterias where ['vmgi_install','vmgi_delete'], aMode=False
              with aIdx = 5 it would return 
              '( NOT (cmdtype=:5 or cmdtype=:6))'
        """
        #Usually idx is constant for a given operation, cache generated statement for index
        _SQLfilter = ''
        if aIdx not in self.__idxSQLCache:
            self.__idxSQLCache[aIdx] = \
                 self.__mGenerateFilter(len(self.__criterias),aIdx,True)

        return self.__idxSQLCache[aIdx]

    def mAppendFilterToQuery(self, aQuery, aBindVariables, aFirst=False):
        """
        Find the last Index and append the filter and Bind variables
        
        :param aQuery
           Query string 
        :param aBindVariables
           Array of existing Bind variables
        :param aFirst
           if True, WHERE and no AND is appended before filter
        :return
            A tuple (Query with Filter, [allbindvariables])
        """
        #very simple regexp to find bind variables
        _regexp = r':(\d+)'
        _matches = re.findall(_regexp, aQuery)
        _idx = 1
        if _matches:
           _matches = list(map(int,_matches))
           # our filter will bind starting from :<max+1>
           _idx = max(_matches)+1
        
        _result = aQuery

        # In the future we could specify chaining rules (AND/OR)
        # Now, all filters are cummulative
        if aFirst:
            _result += ' WHERE '
        else:
            _result += ' AND '
        
        _filterSQL = self.mGetFilter(_idx)
        return (_result + _filterSQL , aBindVariables + self.__criterias) 

class ebDbTrigger(object):
    """  A trigger implement a boolean Evaluation command """
    def mEvaluate(self):
        raise NotImplementedError("Please Implement this method")
    def mGetFilterData(self):
        raise NotImplementedError("Please Implement this method")

class ebDbOperation(object):
    """ An DB operation called by a Policy"""
    @staticmethod
    def mIsTriggerSupported(aEbDbTrigger):
        raise NotImplementedError("Please Implement this method")
    @staticmethod
    def mExecute(self,aEbDbTrigger, aEBFilters=[]):
        raise NotImplementedError("Please Implement this method")

class ebDBPolicy(object):
    """
    A policy is a planned DB operation (archiving/pruning/offloading)
    We can specify in Exacloud configuration an array of policies to evaluate
    """

    def __init__(self, aEbDbOperation, aEbDbTrigger, aEbDBFilters=[]):
        """ New policy, takes a Trigger and Operation and a List of Filters"""
        self.__dbOperation = aEbDbOperation
        self.__ebTrigger   = aEbDbTrigger
        self.__ebFilters   = aEbDBFilters
        if not self.__dbOperation.mIsTriggerSupported(self.__ebTrigger):
            raise NotImplementedError("Operation: {} do not support Trigger {}"
                                      .format(self.__dbOperation,self.__ebTrigger))

    def mEvaluate(self):
        if self.__ebTrigger.mEvaluate():
            self.__dbOperation().mExecute(self.__ebTrigger, self.__ebFilters)

# ----- End of DB Framework #
