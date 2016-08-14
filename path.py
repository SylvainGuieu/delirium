from __future__ import print_function
from ftplib import FTP, error_perm, error_temp, all_errors
from shutil import copyfile
from urlparse import urlsplit, urlparse

import time
import glob
import os
import StringIO

VERBOSE = True
FORCE = True
tempdirectory = "/tmp"

__all__ = ["fpath", "dpath", "open", "ls"]

class PathTypeError(TypeError):
    pass

class log:
    @staticmethod
    def error(*args, **kwargs):
        pass
    @staticmethod            
    def notice(*args,**kwargs):
        pass
    @staticmethod    
    def warning(*args,**kwargs):
        pass

ftp_connections = {}
def get_ftp_connection(host, login, new=False):
    global ftp_connections    
    #return FTP(host)
    if ((host,login) not in ftp_connections) or new:   
        ftp_connections[(host,login)] = FTP(host)          
    return ftp_connections[(host,login)]   


#################################################
#
#  API function
#
#################################################

def set_log(*args):
    global log
    if len(args)==1:
        l = args[0]
        for a in ["error", "warning", "notice"]:
            if not hasattr(l, a):
                raise ValueError("log must have a callable '%s' attribute"%a)
        log = l
    elif len(args)==3:
        d = dict((a,staticmethod(f)) for a,f in zip(["error", "warning", "notice"], args))
        log = type("log", tuple(), d)()

    else:        
        raise ValueError("set_log must have exactly one or three arguments")
        
def put(file, *insides):
    return fpath(file).put(*insides)


def ls(glb):
    if isinstance(glb, fpath):
        return [glb]
    if isinstance(glb, dpath):
        return [glb]
    return glob.glob(glb)    
        
def write(file, strin):
    if isinstance(file, path):
        file.write(strin)
    else:
        with open(file, "w") as f:
            f.write(strin)

def writelines(file, lines):
    if isinstance(file, path):
        file.writelines(lines)
    else:
        with open(file, "w") as f:
            f.writelines(lines)                    

def read(file):
    if isinstance(file, path):
        return file.read()
    else:
        with open(file, "r") as f:
            out = f.read()    
        return out

def readlines(file):
    if isinstance(file, path):
        return file.readlines()
    else:
        with open(file, "r") as f:
            out = f.readlines()    
        return out
try:
    _open
except:    
    _open = open    
def open(path, mode='r'):
    return fpath(path).open(mode)
  

def getctime(filename):
    """Return the metadata change time of a file"""
    return filename.getctime() if isinstance(filename, fpath) else os.path.getctime(filename)

def getatime(filename):
    """Return the last access time of a file"""
    return filename.getactime() if isinstance(filename, fpath) else os.path.getactime(filename)

def getmtime(filename):
    """Return the last modification time of a file"""
    return filename.getmctime() if isinstance(filename, fpath) else os.path.getmctime(filename)

def djoin(*args):
    path = ""
    connection = ('', None)    
    for a in args:
        if isinstance(a, (dpath, LocalDirectory)):
            if a.isroot():
                path = unicode(a)
                connection = a.connection
            elif a=="..":
                path, _ = os.path.split(path)
            else:                
                path = os.path.join(path, a)
        else:
            if a[:1] == "/":
                path = a
                connection = ("", None)
            elif a=="..":
                path, _ = os.path.split(path)    
            else:    
                path = os.path.join(path, a)

    if connection[0]:
        d = dpath(path, **dict([connection]))
    else:    
        d= dpath(path)    
    return d    

def join(*args):
    if len(args)<1:
        raise ValueError("join needs at least one argument")
    return fpath(*args)    

class dpath(unicode):
    def __new__(cl, *tpath, **kwargs):
        scheme_lookup = {"":LocalDirectory,"ftp": FtpDirectory}

        if not len(tpath):
            raise ValueError("dpath need at leas one positional argument")
        

        if len(tpath)>1:
            path = djoin(*tpath)
        else:
            path = tpath[0]
        
        if isinstance(path, tuple(scheme_lookup.values())):
            d = path
        elif isinstance(path, dpath):
            d = path.d  
        else:    
            
            bridge = None
            for scheme in scheme_lookup:
                if scheme in kwargs:
                    bridge = kwargs.pop(scheme)
                    DirClass = scheme_lookup[scheme]
                    break

            if len(kwargs):
                raise KeyError("only one keyword is accepted")        

            if not bridge:
                scheme = urlsplit(path).scheme
                if not scheme:
                    bridge   = None
                    DirClass = LocalDirectory
                else:
                    if not scheme in scheme_lookup:
                        raise ValueError("'%s' is an unknown scheme"%scheme)
                    DirClass = scheme_lookup.get(scheme)  

            d = DirClass(path, bridge)       

        new = unicode.__new__(cl, d)
        new.d = d         
        return new
    def __repr__(self):
        return "d'%s'"%self    
    

    def write(self, file, strin):
        """ write string in the given file 

        If exists previous content is erased
        """
        self.d.write(file, strin)    
    def writelines(self, file, lines):
        """ write list of string in the given file

        If exists previous content is erased
        """
        self.d.writelines(file, lines)
    def read(self, file):
        """ read the file content and return it in string """
        return self.d.read(file)
    def open(self, file, mode='r'):
        """ open en a file inside directory """
        return self.d.open(file, mode)        
    def readlines(self, file):
        """ read the file content and return is in a list of string """
        return self.d.readlines(file)
    def put(self, file):
        """ put files in the directory 

        files can be a string glob as e.g. "*.txt" or a list of file path
        """
        return self.d.put(file)
    
    def rmtree(self, path):
        """ remove the subdirectory defined in path and all its content
        """
        return self.d.rmtree(path)

    def get(self, glb='*', inside=None, child=None):
        """ get files inside a new directory """
        return self.d.get(glb, inside, child=child)                
    def ls(self, glb='*'):
        return self.d.ls(glb)
    def isroot(self):
        return self.d.isroot()   
    def als(self, glb='*', child=None, key=None, reverse=False):
        return self.d.als(glb, child, key, reverse)                
    def cleanup(self, file=None):
        return self.d.cleanup(file)    
    def makedirs(self, d):
        return self.d.makedirs(d)

    def getmtime(self, file):
        return self.d.getmtime(file)

    def getctime(self, file):
        return self.d.getctime(file)

    def getatime(self, file):
        return self.d.getatime(file)              
    
    def build(self):
        return self.d.build() 
    def path(self, p):
        return self.d.path(p)
    def dpath(self, *p):
        return self.d.dpath(*p)
    def fpath(self, *p):
        return self.d.fpath(*p)   
    def isdir(self, dirname):
        return self.d.isdir(dirname)
    def isfile(self, filename):
        return self.d.isfile(filename)             
    def exists(self):
        return self.d.exists()                                             
    def path_exists(self, path):
        return self.d.path_exists(path)
    
    def dbreak(self, *args):
        for d in args:
            yield self.dpath(d)

    def fbreak(self, *args):
        for f in args:
            yield self.fpath(f)        
    
    def prepare(self):
        """ If the directory does not exists create it 

        Always return self for quick access : 
            d = dpath("/a/b/c").prepare() 
        """
        if not self.exists():
            r  = self.dpath("..").prepare()
            _, d = os.path.split(self.dirname)
            r.makedirs(d)
            
            #dpath(r).prepare().makedirs(d)
        return self

        
    @property
    def connection(self):
        return self.d.connection

    @property
    def isremote(self):
        return self.d.isremote

    @property
    def dirname(self):
        return self.d.directory

    @property
    def pathname(self):
        return self.dirname
        
class LocalDirectory(unicode):

    def __new__(cl, directory, dummy=None):
        new = unicode.__new__(cl, directory)
        #if os.path.isfile(directory):
        #   raise PathTypeError("'%s' is a regular file"%directory)
        new.directory = directory
        return new


    @property
    def isremote(self):
        return False

    @property
    def connection(self):
        return ('', None)
            
    def put(self, files):        
        if isinstance(files, basestring):
            files = ls(files)            

        for file in files:
            d, filename = os.path.split(file)
            filepath = self.fpath(filename)             
            if filepath != file:
                with open(file,"r") as f:                    
                    filepath.write(f.read())
                    log.notice("file '%s' copied to '%s' "%(file, filepath))

    def rmtree(self, path):
        """ remove the subrirectory in path """        
        return local_rmtree(os.path.join(self.directory, path))
                
                
    def get(self, files='*', inside=None, child=None):
        child = (lambda x:x) if child is None else child #self.fpath

        files = self.ls(files)
        if inside is None or inside==self:    
            return [child( fpath(self, file) ) for file in files]

        inside = dpath(inside)
        inside.build()
                                    
        out =[] 
        for file in files:
            orig = os.path.join(self, file)
            dest = os.path.join(inside, file)
            inside.put([file])
            out.append(child(fpath(inside, self)))

        return out

    def ls(self, glb='*'):
        """ list file in directory from glob. e.g. '*.txt' 

        The returned path are relative 
        """
        if isinstance(glb, basestring):                                
            return remove_roots(ls(os.path.join(self, glb)), self)            
        return [s if os.path.exists(os.path.join(self, s)) else None for s in glb]

    def als(self, glb='*', child=None, key=None, reverse=False):
        child = (lambda x:x) if child is None else child

        l = [child( fpath(self,f) ) for f in self.ls(glb)]
        if key:
            l.sort(key=key, reverse=reverse)
        elif reverse:
            l = l[::-1]
        return l

    def path_exists(self, path):
        """ true if the relative path exists inside the directory """
        return path in self.ls(path)

    def exists(self):
        """ true if the directory exists """
        return os.path.exists(self)
        #return len(self.ls("."))>0

    def getmtime(self, file):
        return os.path.getmtime(os.path.join(self,file))    

    def getctime(self, file):
        return os.path.getctime(os.path.join(self,file))  

    def getatime(self, file):
        return os.path.getatime(os.path.join(self,file))                  

    def open(self, file, mode='r'):
        """ open a file inside directory """
        return pathfile(fpath(self,file), mode)

    def read(self, file):
        """ read the file content and return it in string """
        return self.open(file).read()

    def readlines(self, file):
        """ read the file content and return is in a list of string """
        return self.open(file).readlines()

    def write(self, file, strin):
        """ write string in the given file 

        If exists previous content is erased
        """
        with self.open(file, "w") as f:
            f.write(strin)

    def writelines(self, file, lines):
        """ write list of string in the given file

        If exists previous content is erased
        """
        with self.open(file, "w") as f:
            f.writelines(lines)        
            
    def append(self, file, strin):
        with self.open(file, "a") as f:
            f.write(strin)    

    def appendlines(self, file, lines):
        with self.open(file, "a") as f:
            f.writelines(lines)          

    def isfile(self, filename):
        return os.path.isfile(os.path.join(self, filename))

    def isdir(self, dirname):
        return os.path.isdir(dirname)                    

    def fpath(self, *args):
        return fpath(self, *args)
        
    def dpath(self, *args):
        return dpath(self, *args)

    def isroot(self):
        return self[:1] == "/"    

    def path(self, *path):    
        if self.isfile(os.join(*path)):
            return self.fpath(*path)
        else:
            return self.dpath(*path)   

    def cleanup(self, glb=None):
        pass    

    def makedirs(self, d):
        os.makedirs(os.path.join(self, d))    

    def build(self):
        try:
            os.makedirs(self)
        except OSError:
            pass                    

class FtpDirectory(LocalDirectory):
    """ A object used to copy file to a ftp directory """
    ftp = None

    def __new__(cl,  url, ftp=None):
        """ a path to a ftp directory """
        url = urlsplit(url)  
                    
        if url.scheme:
            if url.scheme not in ["ftp","sftp"]:
                raise ValueError("scheme must be 'ftp'")
            if ftp is None:
                ftp = FTP(url.hostname, url.username, url.password)

                ftp.connect(url.hostname, url.port)
                ftp.login(url.username, url.password)
                ## store the username in the ftp
                ftp.username = url.username
                username = url.username              
            else:
                username = getattr(ftp, "username", url.username)
                #ftp.connect(url.hostname)
                #ftp.login(url.username, url.password)    

            directory = url.path[1:] # remove the first '/' so the path 
                                     # is relative to the connection point 
            
            ## do not use the url.geturl() method in order to 
            ## remove the password from the url representation 
            path = '%s://'%url.scheme
            if username:
                path += username + "@"
            path += url.hostname + "/" + directory
        
        else:
            if ftp is None:
                raise ValueError("if no explicite sceme is present in url, a valid ftp class must be present")
            username = getattr(ftp, "username", url.username)      
            directory = url.path
            path = "ftp://%s%s/%s"%("@"+username if username else "", ftp.host, directory)

        #new = "ftp://{u}{uh}{h}{hd}{d}".format(
        #        u = user or '',
        #        up = ":" if pwd else "",
        #        p = pwd or '',
        #        uh = "@" if user else "",
        #        h = host, 
        #        hd = ":" if host else "",
        #        d = directory
        #    )
        new = LocalDirectory.__new__(cl, path)    

        new.directory = directory
        new.localdir  = tempdirectory
        new.ftp = ftp

        #ftp = get_ftp_connection(new.host, new.user, new.directory)
        #print( "isfile", new.directory, ftp_isfile(ftp, new.directory))
        #if not getattr(ftp, "_right_directory", False) and ftp_isfile(ftp, new.directory):
        #    raise PathTypeError("'%s' is a regular file"%new.directory)

        return new


    @property
    def isremote(self):
        """ True if the directory is in remote access """
        return True            

    @property
    def connection(self):
        return ('ftp', self._get_ftp())

    def _get_ftp(self):
        return self.ftp

    def put(self, files):
        """ put files in the directory 

        files can be a string glob as e.g. "*.txt" or a list of file path
        """
        ftp = self._get_ftp()
        if isinstance(files, basestring):
            files = ls(files)            

        for file in files:
            with open(file,'rb') as f:
                d, filename = os.path.split(file)              
                ftp.storbinary('STOR %s'%os.path.join(self.directory,filename), f)     # send the file
                log.notice("file '%s' transfered in '%s' "%(file, self))
    

    def rmtree(self, path):
        """ remove the subrirectory in path """
        ftp = self._get_ftp()
        return ftp_rmtree(ftp, os.path.join(self.directory, path))

    def ls(self, glob='*'):
        """ list file in directory from glob. e.g. '*.txt' 

        The returned path are relative 
        """
        ftp = self._get_ftp()        
        return remove_roots(ftp_ls(ftp, os.path.join(self.directory,glob)), self.directory)        

    def get(self, files, inside=None, child=None):
        """ 
        Parameters
        ----------
        files : string
            file glob 
        """
        child = child or self.fpath

        ftp = self._get_ftp()
        if inside is None:
            if self.localdir:
                inside = self.localdir
            else:    
                inside = os.path.join(tempdirectory, str(id(self)))
        #inside = inside or self.localdir
        inside = dpath(inside)
        inside.build()
        return [child(f) for f in ftp_mget(ftp, os.path.join(self.directory, files), inside)]

    def open(self, file, mode='r'):    
        """ open a file inside directory """    
        return remotepathfile(fpath(self, file), mode)

    def _open(self, file):    
        ftp = self._get_ftp()
        strout = StringIO.StringIO()
        ftp.retrbinary("RETR %s"%(os.path.join(self.directory, file)), strout.write)
        strout.seek(0)
        return strout

    def getmtime(self,file):
        ftp = self._get_ftp()        
        t = ftp.sendcmd("MDTM %s"%(os.path.join(self.directory, file)))
        t = time.strptime(t[4:], "%Y%m%d%H%M%S")
        return time.mktime(t)

    def getatime(self, file):
        raise RuntimeError("Cannot get access time from ftp connection. Modification date only")    

    def getctime(self, file):
        raise RuntimeError("Cannot get creation time from ftp connection. Modification date only")            

    def read(self, file):
        """ read the file content and return it in string """
        return self._open(file).read()    

    def readlines(self, file):
        """ read the file content and return is in a list of string """
        return self._open(file).readlines()         

    def write(self, file, strin):
        """ write string in the given file 

        If exists previous content is erased
        """
        f = StringIO.StringIO(strin)
        ftp = self._get_ftp()
        ftp.storbinary('STOR %s'%os.path.join(self.directory,file), f)

    def writelines(self, file, lines):
        """ write list of string in the given file 

        If exists previous content is erased
        """
        f = StringIO.StringIO(lines)
        ftp = self._get_ftp()
        ftp.storlines('STOR %s'%os.path.join(self.directory,file), lines)        
    
    def exists(self):
        _, d = os.path.split(self)
        return d in self.dpath("..").ls() 

    def append(self, file, strin):
        f = self.open(file)
        f.seek(0,2)
        f.write(strin)
        f.seek(0)
        ftp = self._get_ftp()
        ftp.storbinary('STOR %s'%os.path.join(self.directory,file), f)

    def appendlines(self, file, lines):
        f = self.open(file)
        f.seek(0,2)
        f.writelines(lines)
        f.seek(0)
        ftp = self._get_ftp()
        ftp.storlines('STOR %s'%os.path.join(self.directory,file), f)

    def isfile(self, filename):
        return ftp_isfile(ftp, os.path.join(self.directory, filename))    

    def isdir(self, dirname):
        return not ftp_isfile(ftp, os.path.join(self.directory, dirname))   
        
    def path(self, *relpath):
        ftp = self._get_ftp()
        return self._path(relpath, ftp)
    

    def _path(self, relpath, ftp):
        ftppath  = os.path.join(self.directory, relpath)
        path = (self,)+relpath

        if ftp_isfile(ftp, os.path.join(ftppath)):            
            return fpath(*path)

        return dpath(*path)
        #return path(os.path.join(self.localdir, file), outputdirs=[self])

    def dpath(self, *relpath):
        return dpath(self, *relpath)
        #return dpath(os.path.join(self.directory,relpath), ftp=self._get_ftp())
        
    def makedirs(self, d):
        ftp = self._get_ftp()
        ftp_makedirs(ftp, os.path.join(self.directory,d))

    def build(self):
        ftp = self._get_ftp()
        ftp_makedirs(ftp, self.directory)

    def isroot(self):
        return True

class fpath(unicode):
    header = None
    def __new__(cl, *tpath):
        if not len(tpath):
            raise ValueError("fpath needs at least one argument")

        outputdirs = []    
        if len(tpath)>1:
            _directory = djoin(*tpath[:-1])
        else:
            _directory = None
        path = tpath[-1]     

        if isinstance(path, fpath):
            _directory = _directory or path.directory
            outputdirs = outputdirs or path.outputdirs
            path = path.filename 

        if not _directory:
            path_dir, file = os.path.split(path)
            path_dir = dpath(path_dir)
        else:
            path_dir, file = os.path.split(path)
            
            if path_dir:
                path_dir = _directory.dpath(path_dir)
            else:
                path_dir = _directory    
              
        

        new = unicode.__new__(cl, os.path.join(unicode(path_dir), file))
        new._directory = path_dir
        new._filename = file
        new.outputdirs = [dpath(d) for d in outputdirs]
        return new

    def __repr__(self):
        return "f'%s'"%self 

    def open(self, mode='r'):  
        return self.directory.open(self.filename, mode)      

    def read(self):
        return self.directory.read(self.filename)    
        
    def readlines(self):
        return self.directory.readlines(self.filename) 

    def write(self, strin):
        self.directory.write(self.filename, strin)
        for d in self.outputdirs:
            d.write(self.filename, strin)                           

    def writelines(self, lines):
        self.directory.writelines(self.filename, lines)
        for d in self.outputdirs:
            d.writelines(self.filename, lines)                           
    
    def append(self, strin):
        self.directory.append(self.filename, strin)
        for d in self.outputdirs:
            d.append(self.filename, strin)                           

    def appendlines(self, lines):
        self.directory.appendlines(self.filename, lines)
        for d in self.outputdirs:
            d.appendlines(self.filename, lines)       

    def getmtime(self):
        return self.directory.getmtime(self.filename)        

    def getatime(self):
        return self.directory.getatime(self.filename)   
    
    def getctime(self):
        return self.directory.getctime(self.filename)           

    def put(self, *insides):
        strin = self.read()        
        for d in insides:
            dpath(d).write(self.filename, strin)  

    def copy(self, *tos):
        strin = self.read()
        for to in tos:  
            fpath(to).write(strin)

    def replace_ext(self, newext):
        body, ext = os.path.splitext(self.filename)
        return self.__class__(self.directory,  body + newext)
    
    def exists(self):
        return self.directory.path_exists(self.filename)    

    
    def prepare(self, header=None):
        """ If the file does not exists create it with all tree structure
        
        Always return self for quick access : 
            f = fpath("/a/b/c").prepare() 

        A file header can be specified and will be writen in the file if 
        this one does not exists. 
        The fpath object can also have a header attribute taken by default
        """
        if not self.exists():
            self.create(header)
        return self

    def create(self, header=None):
        """ create the file with all the directory tree if necessary 
        
        !! Twhis will erase file contant !!
        
        A file header can be specified and will be writen in the file if 
        this one does not exists. 
        The fpath object can also have a header attribute taken by default        
        
        Header can also callable method which return a string.
        example : 
            header = fpath("/a/b/header.txt")
            newfile = fpath("/a/b/data.txt")
            newfile.create(header.read)
        """
        self.directory.prepare()
        header = self.header if header is None else header
        if isinstance(header, basestring):
            self.write(header)
        elif hasattr(header, "__call__"):
            self.write(header())            
        elif header is not None:
            raise ValueError("header must be a string or a callable method got a %s object"%type(header))
        else:    
            self.write("")       

    @property
    def filename(self):
        return self._filename
    
    @property
    def directory(self):
        return self._directory
        
    @property
    def ext(self):
        return os.path.splitext(self.filename)[1]

    @property
    def body(self):
        return os.path.splitext(self.filename)[0]    
    
    @property
    def dirname(self):
        return self.directory.d.directory

    @property
    def pathname(self):
        return os.path.join(self.dirname,self.filename)
        

class pathfile(file):
    def __new__(cl, pth, mode='r'):
        pth = fpath(pth)
        new = file.__new__(cl, pth)
        new.path = pth
        return new

    def close(self):
        mode = self.mode
        file.close(self)
        if not 'r' in mode:
            put(self.path)

class remotepathfile(StringIO.StringIO):
    
    def __init__(self, pth, mode='r'):
        if not isinstance(pth, fpath):
            pth = fpath(pth)

        if 'r' in mode or 'a' in mode:
            buf = pth.read()
        if 'w' in mode:
            buf = ''          
        StringIO.StringIO.__init__(self, buf)            
        if 'a' in mode:
            self.seek(0,2)

        self._path = pth
        self.mode = mode

    def close(self):
        mode = self.mode
        if not 'r' in mode:
            self.seek(0)            
            self._path.write(self.read())        
        StringIO.StringIO.close(self)

    @property
    def name(self):
        return self._path
                
    def __exit__(self, *args):
        self.close()  
    def __enter__(self):
        return self                  
#####################################################################
#
#  FTP stuff 
#
#####################################################################
def remove_roots(lst, root):
    root = os.path.normpath(root)+"/"
    n = len(root)
    return [l[n:] if l[:n]==root else l for l in (os.path.normpath(l) for l in lst)]



def _ftp_exists(ftp, path):
    r, d = os.path.split(path)
    return os.path.join(r,d) in ftp.nlst(r)

def _ftp_dir(ftp, pathes, pref, output):
    
    if not len(pathes):
        try:
            lst = [pref] if pref and (len(ftp.nlst(pref)) or _ftp_exists(ftp, pref))  else []
            ## if belowe line uncomment it will end up with a one depth more 
            #lst = ftp.nlst(pref) if pref else ftp.nlst() 
        except error_temp as e:
            code = str(e).split(" ")[0]
            if code!='450':
                raise e
        else:       
        #output.append(pref)
        
            output.extend(lst)
        return 0

    glb = pathes[0]
    pathes.pop(0)

    if not glob.has_magic(glb):
        
        return _ftp_dir(ftp, pathes, os.path.join(pref,glb), output)  

    try:
        lst = ftp.nlst(pref) if pref else ftp.nlst()
    except error_temp as e:
        code = str(e).split(" ")[0]
        if code!='450':
            raise e
        
        return len(pathes)
    else:
        if len(lst)==1 and lst[0]==pref: # this is a file not a directory
            
            return len(pathes) 
        for item in lst:            
            _, f = os.path.split(item)
            if glob.fnmatch.fnmatch(f, glb):
                _ftp_dir(ftp, list(pathes), item, output)
    return len(pathes)

def ftp_ls(ftp, glb):
    output = []
    pathes = glb.split("/")
    pref = ""
    if pathes and glb[0]=="/":
        pathes[0] = "/"+pathes[0]
    _ftp_dir(ftp, pathes, pref, output)
    return output


def ftp_isfile(ftp, path):
    try:
        lst = ftp.nlst(path)
    except error_perm:
        return False
    return len(lst)==1 and lst[0]==path


def _ftp_makedirs(ftp, pathes, pref):
    if not len(pathes):
        return 0
    d = pathes[0]
    pathes.pop(0)
    d = os.path.join(pref,d)
    try:
        ftp.mkd(d)
    except error_perm:
        if not len(pathes):
            raise error_perm("550 %s: File exists."%d)
    return _ftp_makedirs(ftp, pathes, d)       

def ftp_makedirs(ftp, dirs):
    pathes = dirs.split("/")
    if pathes and dirs[0]=="/":
        pathes[0] = "/"+pathes[0]

    _ftp_makedirs(ftp, pathes, "")


def ftp_dirlist(ftp, directory, verbose=VERBOSE):
    """
    Return a list of file of the directory in ftp connection
    the returned list does not contain the directory path
    """
    listfile = []
    log.notice("Changing distant directory to %s"%(directory))

    rtr = ftp.cwd(directory)
    log.notice( "%s"%(rtr))
    log.notice("Get file list ")

    rtr = ftp.retrlines('NLST', listfile.append)
    log.notice("%s"%(rtr), verbose)

    return listfile



def ftp_rmtree(ftp, path):
    """Recursively delete a directory tree on a remote server."""
    wd = ftp.pwd()

    try:
        names = ftp.nlst(path)
    except all_errors as e:
        # some FTP servers complain when you try and list non-existent paths
        return

    for name in names:
        if os.path.split(name)[1] in ('.', '..'): continue


        try:
            ftp.cwd(name)  # if we can cwd to it, it's a folder
            ftp.cwd(wd)  # don't try a nuke a folder we're in
            ftp_rmtree(ftp, name)
        except all_errors:
            ftp.delete(name)

    try:
        ftp.rmd(path)
    except all_errors as e:        
        return

def local_rmtree(path):
    import shutil
    shutil.rmtree(path)


def _ftp_glob_dirlist_rec(ftp, path_list, pref="", verbose=VERBOSE):
    # walk through the path_list to get a list of files
    # ftp NLST to not allows to list a path of directory with the * like /tmp/*/*.txt
    # so we need to split the path and goes directory by directory if needed

    if not len(path_list):
        return []

    directory_glob  = path_list.pop(0)
    if not glob.has_magic( directory_glob ):
        if not len(path_list):
            # end of the recursive call, just return the list
            file_list = []
            ftp.retrlines("NLST %s"%pref+directory_glob , file_list.append)
            return file_list
        else:
            # if no magic found just stick to the prefix and send the rest of
            # path_list as a copy: list(path_list)
            return _ftp_glob_dirlist_rec(ftp, list(path_list), pref=pref+directory_glob+"/", verbose=verbose)

    directory_found = []

    # the following line works only with * not with more complex glob [0-9] etc ...
    #rtr     = ftp.retrlines("NLST %s"%pref+directory_glob , directory_found.append)
    # So we need to list all the directory and then match the files
    ftp.retrlines("NLST %s"%pref, directory_found.append)
    #pref_len = len(pref)
    #directory_found = [l for l in directory_found if glob.fnmatch.fnmatch(l[pref_len:], directory_glob)]
    directory_found = [l for l in directory_found if glob.fnmatch.fnmatch(os.path.split(l)[1], directory_glob)]

    if not len(path_list):
        return directory_found

    output = []

    for d in directory_found:
        # list(path_list) to make a copy
        fls =  _ftp_glob_dirlist_rec(ftp, list(path_list), pref=d+"/", verbose=verbose)
        # extend the output with the new found
        output.extend(fls)
    return output




###############################################
# old stuf 

def ftp_put(ftp, local, remote):        
    with open(local, 'rb') as f:        
        ftp.storbinary('STOR %s'%remote, f)     # send the file
    return remote

def ftp_get(ftp, remote, local):
    with open(local, "wb") as f:
        ftp.retrbinary("RETR %s"%(remote),f.write)
    return local    

def ftp_mget(ftp, remotes, localdir):
    if isinstance(remotes, basestring):
        files = ftp_ls(ftp, remotes)
    else:
        files = list(remotes)

    lst = []    
    for remote in files:
        _, name = os.path.split(remote)
        lst.append(ftp_get(ftp, remote, os.path.join(localdir, name)))
    return lst    

def ftp_mput(ftp, flocals, remotedir):
    if isinstance(flocals, basestring):
        files = glob.glob(flocals)
    else:
        files = list(flocals)

    lst = []    
    for local in files:
        _, name = os.path.split(remote)
        lst.append(ftp_put(ftp, local, os.path.join(remotedir, name)))
    return lst   


def ftp_lsdir(ftp, strglob, verbose=VERBOSE):
    """
    ftp_lsdir(ftp, str)
    do the same thing than lsdir but for a ftp connection.
    """
    return ftp_glob_dirlist_rec(ftp, strglob, verbose=verbose)

def ftp_glob_dirlist_rec( ftp, path, verbose=VERBOSE):
    path_list =  path.split("/")
    pref = ""
    if len(path_list) and path_list[0] == "":
        path_list.pop(0)
        pref= "/"
    log.notice( "Looking for '%s:%s' in ftp connection ... "%(ftp.host,path) )
    files=  _ftp_glob_dirlist_rec(ftp, path_list, pref, verbose=verbose)
    log.notice( "found %d"%(len(files)) )
    return files





def ftp_transfer(ftp, strglob, localdir= "",distdir="",
                 verbose=VERBOSE, force=FORCE):
    """
    ftp_transfer(ftp, strglob, localdir= "",distdir="")
    Transfer file matching strglob from the ftp connection. The hierarchic path directory
    will be created from the localdir.
    distdir is the distant root ftp directory starting point, is equivalent
    to do a ftp.cwd( distdir) to change directory.

    """
    if distdir and len(distdir):
        ftp.cwd(distdir)
    files = ftp_lsdir(ftp, strglob, verbose=verbose)
    if not len(files):
        return []
    return ftp_transfer_files( ftp, files, localdir=localdir,
                               distdir=distdir,
                               verbose=verbose, force=force)



def ftp_transfer_files(ftp,  files, localdir= "", distdir="", verbose=VERBOSE, force=FORCE):
    """
    Transfer a list of files from the ftp connection. The hierarchic path directory
    will be created from the localdir.
    distdir is the distant root ftp directory starting point, is equivalent
    to do a ftp.cwd( distdir) to change directory.

    Return the list of local path to files
    """
    if os.path.exists(localdir):
        if not os.path.isdir(localdir):
            raise Exception("The local path '%s' is not a directory"%(localdir))
    else:
        os.makedirs(localdir)
    localdir = add_slash(localdir)
    if distdir and distdir!="":
        ftp.cwd(distdir)

    global _ftpfinished
    global _ftpwrfunc


    outlist = []
    for path in files:
        subdir, fl = os.path.split(path)
        if subdir[0:len(distdir)] == distdir:
            subdir = subdir[len(distdir):]
        create_dir(subdir, localdir, verbose=verbose)
        localpath = os.path.join(localdir, subdir, fl)
        #localpath = add_slash(localdir)+add_slash(subdir)+fl


        if not force and os.path.exists(localpath):
            log.notice("file %s already exists use force=True to force download"%(localpath))
        else:
            log.notice("FTP: Copying file %s:%s to %s "%(ftp.host, fl, localdir+subdir))

            try:
                ftp.retrbinary("RETR %s"%(path),open(localpath, "wb").write)
            except error_perm:
                log.warning("wrong permition for transfert %s"%path)    
        outlist.append( localpath )
    return outlist


def ftp_put_file(ftp, file, distdir=""):
    if distdir:
        ftp.cwd(distdir)
    d, filename = os.path.split(file)        
    file = open(file,'rb')                  # file to send
        
    ftp.storbinary('STOR %s'%filename, file)     # send the file
    log.notice("file '%s' transfered in '%s/%s' "%(filename,ftp.host, ftp.user()))
    file.close()

def add_slash(directory):
    """ Add slashes to str if not directory.endswith("/")"""
    if not directory or not len(directory): return directory
    return directory+"/"*(not directory.endswith("/") )   


def create_dir(directory,inside="", verbose=VERBOSE):
    """
    recreate is necessary a directory structure from a path string  "a/b/c" or a list ["a","b","c"]
    The second argument precise where the structure should be installed
    so create_dir( "data/set1", "/tmp")  is the same than create_dir( "tmp/data/set1")

    """

    if not os.path.isdir(inside):
        raise Exception( "'%s' is not a directory"%inside)
    if isinstance( directory, basestring):
        # save time exist if exists
        if os.path.isdir(add_slash(inside)+ directory):
            return None
        directories = directory.split("/")
    else:
        directories = directory
        if os.path.isdir(add_slash(inside)+"/".join(directories)):
            return None

    sub = inside
    while len(directories):
        sub += "/"+directories.pop(0)

        if os.path.exists(sub):
            if not os.path.isdir(sub):
                raise Exception("'%s' exists but is not a directory "%(sub))
        else:
            log.notice( verbose, "Creating directory %s"%sub)
            os.mkdir(sub)
    return None


