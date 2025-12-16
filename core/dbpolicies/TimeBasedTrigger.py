
import datetime
from exabox.core.dbpolicies.Base import ebDbTrigger


# --- Start of Triggers ---
class ebTimeBasedTrigger(ebDbTrigger):
    """ Trigger implementing a time based strategy """
    def __init__(self, wait_time=datetime.timedelta(hours=24)):
        self._wait_time = wait_time
        # Next backup is now
        self._next_backup = datetime.datetime.now()

    def mGetFilterData(self):
        """ Filter Data used in Where clause """
        return (datetime.datetime.now() - self._wait_time).strftime('%Y%m%d%H%M%S')

    def mEvaluate(self):
        if self._next_backup <= datetime.datetime.now():
            self.mRollover()
            return True
        else:
            return False
            
    def mRollover(self):
        self._next_backup = self._next_backup + self._wait_time