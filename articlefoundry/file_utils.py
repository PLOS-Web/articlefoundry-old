import os
import datetime
import time

import paramiko
watch_dir = '/home/jlabarba/Desktop/'

class TriggerError(Exception):
    '''
    base class for categorizing non-fatal trigger func errors
    '''
    pass

class SSHConnection:
    def __init__(self, server, port, user, password=''):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(server, port, user, password)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.client.close()
        
def get_mtime(file):
    return datetime.datetime.fromtimestamp(os.stat(file).st_mtime)

def get_filenames_in_dir(path):
    return [ os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]

def get_filenames_and_mtime_in_dir(path):
    return [ (os.path.join(path, f), get_mtime(os.path.join(path, f))) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]

def is_modified_after(file, cutoff_time):
    return get_mtime(file) > cutoff_time
        
def watch_directory(trigger_func, directory, polling_period, cutoff_seed=datetime.datetime.fromtimestamp(0), close=None):
    '''
    Polls specified directory for newly modified files.
    Upon finding one, it will execute trigger function on it.
    Runs until keyboard interrupt (or uncaught exception).
    Returns modify time of last file worked on
    '''
    cutoff_cursor = cutoff_seed
    greatest_m_time = cutoff_cursor
    try:
        while(True):
            print "Looking for new files . . ."
            files = get_filenames_and_mtime_in_dir(directory)
            files = sorted(files, key=lambda f: f[1])
            for f, m_time in files:
                if m_time > cutoff_cursor:
                    trigger_func(f)
                if m_time > greatest_m_time:
                    greatest_m_time = m_time
            cutoff_cursor = greatest_m_time
            time.sleep(polling_period)          
    except KeyboardInterrupt, e:
        print "Keyboard Interrupt!"
    finally:
        print "Cleaning up . . ."
        if close:
            close()
        print "Done!"
        return

def watch_remote_directory(ssh_conn, directory, trigger_func, untouched_filename_regex, touched_filename_marker, polling_period, close=None):
    """Watches a folder over SSH and does stuff to new files.
    
    :param ssh_conn: :class:`SSHConnection` object.
    :param director: string path location of watch dir on remote location relative to user's home
    :param trigger_func: the function to be executed on new files.
    :param untouched_filename_regex: regex string used for identifying new files.
    :param touched_filename_marker: string appended to end of touched file to denote toucheddom.
    :param polling_period: seconds per polling period.
    :param close: (optional) function to be run after poll loop is killed.

    Usage::
    
     >>>cnx = SSHConnection("plosutil04.plos.org", 22, "web")
     >>>watch_remote_directory(cnx, 'test/', 5, '.*/p[a-z]{3}\.[0-9]{7}\.zip', 'done', print_done)
    """

    try:
        while(True):
            print "Probing for new files . . ."
            cmd = "find %s -regextype posix-extended -regex '%s' -mtime -1" % (directory, untouched_filename_regex)
            print "executing cmd: %s" % cmd 
            stdin, stdout, stderr = ssh_conn.client.exec_command(cmd)
            
            files =[line.strip() for line in stdout]
            print files

            # do something with those new files
            for f in files:
                try:
                    still_there = trigger_func(ssh_conn, f)
                    if still_there:
                        cmd = 'mv %s %s\.%s' % (f, f, touched_filename_marker)
                        stdin, stdout, stderr = ssh_conn.client.exec_command(cmd)
                except TriggerError, e:
                    print e

            time.sleep(polling_period)

    except KeyboardInterrupt, e:
        print "Keyboard Interrupt!"
    except:
        e = sys.exc_info()[0]
        print "Fatal exception: %s" % e
    finally:
        print "Cleaning up . . ."
        if close:
            close(ssh_conn)
        print "Done!"
        return True
    
class TestError(TriggerError):
    def __str__(self):
        return "Test error"

def cp_file(ssh_conn, f, new_location):
    """Moves a remote file to a new location"""
    print "Am I working???"
    cmd = "mv %s %s" % (f, new_location)
    print "executing cmd: %s" % cmd 
    stdin, stdout, stderr = ssh_conn.client.exec_command(cmd)
    return True

def mv_file(ssh_conn, f, new_location):
    """Moves a remote file to a new location"""
    print "Am I working???"
    cmd = "mv %s %s" % (f, new_location)
    print "executing cmd: %s" % cmd 
    stdin, stdout, stderr = ssh_conn.client.exec_command(cmd)
    return False

def print_filename(f, ssh_conn):
    print("Found new file: %s" % f)
    raise TestError()

def print_done(ssh_conn):
    print("Closing stuff")



