import Queue
import os
import datetime
import time

watch_dir = '/home/jlabarba/Desktop/'

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

def print_filename(f):
    print("Found new file: %s" % f)

def print_done():
    print("Closing stuff")

watch_directory(print_filename, watch_dir, 5)


