import os
import sys, getopt
from collections import namedtuple
from pathlib import Path
from PIL import Image
import imagehash        # python -m pip install imagehash
import subprocess

_filterdir = 'C:/tmp/ToFilter'
_refdir = 'E:/pictures'
_remove = False
_verbose = False
_paintexe = 'C:/Program Files/paint-net/paintdotnet'

fields = ('full_names')
Entry = namedtuple('Entry', fields)

def usage():
    print('python bin/remove-similar [-h] [--remove] [--verbose]')
    print('   dryrun by default. use --remove to remove similar images')
    sys.exit(2)

def get_args(argv):
    global _remove, _verbose

    try:
        opts, args = getopt.getopt(argv,"h",["remove", "verbose"])
    except:
        usage()

    # get arguments
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt == '--remove':
            print('OK')
            _remove = True
        elif opt == '--verbose':
            _verbose = True


def file_ext_is_img(filename):
    list_ext = [ 'jpg', 'JPG', 'png', 'PNG']
    for ext in list_ext:
        if filename.endswith(ext):
            return True
    return False

def remove_img(tofilter_name, ref_name):
    if (_remove):
        print("Remove ", tofilter_name, " -- Found in", ref_name)
        try:
            os.remove(tofilter_name)
        except:
            pass
    else:
        print("[dryrun] Remove ? ", tofilter_name, " -- Found in", ref_name)
        subprocess.call([
            _paintexe,
            tofilter_name,
            ref_name])
        answer = 'do at least a loop'
        while answer not in [ 'y', 'n', 'quit' ]:
            answer = input("Remove similar image (y/n)?")
            answer = answer.lower()
            if answer == 'y':
                print('... removing')
                try:
                    os.remove(tofilter_name)
                except:
                    pass
            if answer == 'n':
                print('... skipping')
            if answer == 'quit':
                print('Quitting...')
                sys.exit(-1)


def add_to_list(list, root, file, remove_same):
    filename = root + "/" + file
    try:
        thishash = imagehash.phash(Image.open(filename))
    except:
        return
    if list.get(thishash) == None:
        list[thishash] = filename
    else:
        remove_img(filename, list[thishash])
    if _verbose:
        print("-- ", filename, " ", thishash)

def add_to_list_dir(list, root_dir, remove_same):
    print("Scan", root_dir)
    nb = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file_ext_is_img(file):
                nb = nb + 1
                if nb % 100 == 0:
                    print('-- ', nb, ' processed')

                add_to_list(list, root, file, remove_same)

def remove_similar(root_dir_ref, root_dir_tofilter):
    list_hashes_tofilter = {}
    add_to_list_dir(list_hashes_tofilter, root_dir_tofilter, _remove)

    print("Process References", root_dir_ref)
    nb = 0
    for root, dirs, filesref in os.walk(root_dir_ref):
        for fileref in filesref:
            if file_ext_is_img(fileref):
                nb = nb + 1
                if nb % 100 == 0:
                    print('-- ', nb, ' processed')
                filerefname = root + "/" + fileref
                try:
                    hashref = imagehash.phash(Image.open(filerefname))
                except:
                    continue
                if _verbose:
                    print("-- ", filerefname, " ", hashref)
                if (list_hashes_tofilter.get(hashref) is not None):
                    remove_img(list_hashes_tofilter.get(hashref), filerefname)

def main(argv):
    get_args(argv)

    print('Options are:')
    print('--verbose = ', _verbose)
    print('--remove  = ', _remove)
    print('Reference:  ', _refdir)
    print('Tofilter:   ', _filterdir)
    print()
    remove_similar(_refdir, _filterdir)

if __name__ == "__main__":
  main(sys.argv[1:])
