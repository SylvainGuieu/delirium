from .supports import Supports
from .delirium import Delirium, DataError, DataUtils
from .rail import Rail
from .sensors import Sensors, Fogale, Inclinometer
from .carriage import Carriage    
from .parameters import parameters
from .dl import DelayLineState, DelayLineSates, DelayLineHysteresis
from .log import Log, ERROR, WARNING, NOTICE, INFO, DATA
import plots

def open_dl(num, date=None, directory=None, reverse=False, file_index=-1):
    """ Return the delay line object of the last delirium found for the given date and delay line number

    If date is not given,  take the date of today.
    Parameters
    ----------
    num : int
        delay line number 
    date : string, optional
        date in the format 'yyyy-mm-dd'. If None take the today date.
    directory : string, optional
        the root directory containing the deliriums. default is 
            'ftp://utcomm@odyssey3.pl.eso.org/DELIRIUM'
    reverse : bool, optional
        If True, look for the reverse file
    file_index : int, optional
        in case of several file found gives the list index, default is -1 
        Files are ordoned in increasing date
    
    Outputs
    -------
    dl : DelayLineState object
                        
    """
    from . import io
    if directory is None:
        directory = "ftp://utcomm:Bnice2me@odyssey3.pl.eso.org/DELIRIUM"
    dldir = io.DeliriumDirectory(directory)
    files = dldir.deliriumfiles(date, "reverse" if reverse else "direct")
    if not len(files):
        raise IOError("Cannot find %s file for DL %d and  date '%s'  "%("reverse" if reverse else "", num, date))
    files = files[num]
    return DelayLineState(deliriumfile=files[file_index])


def open_histeresis(num, date=None, directory=None, file_index=-1):
    dld = open_dl(num, date=date, directory=directory, file_index=file_index)

    try:
        dlr = open_dl(num, date, directory=directory, reverse=True, file_index=file_index)
    except IOError:
        raise IOError("Cannot find the reverse file for that date %s"%date)    

    return DelayLineHysteresis(dld, dlr)

def set_verbose_type(msgtypes):
    """ Set the verbose filter type 
    
    Parameters
    ----------
    msgtypes : 4-bites int
          1 1 1 1
          | | | |
       DATA | | |
       NOTICE | |
        WARNING |
            ERROR
    
    Examples
    --------
        set_verbose_type(1+2) will verbose only ERROR and WARNING
        set_verbose_type(4) will verbose only the notices
    """
    global Log

    if isinstance(msgtypes, basestring):
        msgtypes = sum( (s in msgtypes)*bit for s,bit in [('E',ERROR),('W',WARNING),('N',NOTICE),('D',DATA)] )
    if not isinstance(msgtypes, int):
        raise ValueError("expecting int got %s"%msgtypes)    
    Log.msgtypes = msgtypes

