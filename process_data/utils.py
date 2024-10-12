import os
import json
import glob
from typing import List, Dict


def init_folder(path, create=True, clean=True, verbose=True):
    if not os.path.exists(path) and create:
        if verbose:
            print('Creating folder '+ str(path))
        os.makedirs(path)
    if clean:
        if verbose:
            print('Cleanning all files recursively in ' + str(path))
        del_file(path)

def del_file(dir_addr, format = None):
    if format:
        del_files = glob.glob(dir_addr+'/'+ format, recursive=True)
    else:
        del_files = glob.glob(dir_addr+'/*', recursive=True)
    for df in del_files:
        try:
            os.remove(df)
        except:
            pass

            
def get_file_list(folder):

    files = []
    for _,_, filenames in os.walk(folder):
        files.extend(filenames)
        break

    if '.DS_Store' in files:
        files.remove('.DS_Store')

    return files


def read_file(path, readlines=True) -> str:
    with open(path, "r") as f:
        if readlines:
            ret = f.readlines()  # -> List[str]
        else:
            ret = f.read()  # -> str
    return ret


def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

        
def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def dump_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
