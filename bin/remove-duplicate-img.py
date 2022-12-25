import os
import sys, getopt
import filecmp
from collections import namedtuple
from pathlib import Path

fields = ('full_names')
Entry = namedtuple('Entry', fields)

_dir_pictures = "C:/Users/pasca/Pictures"
_dir_tofilter = "C:/tmp/tofilter"

def usage():
	print('python bin/remove-duplicate-img.py [-h] [--remove] [--nameonly]')
	print('   dryrun by default. use --remove to remove duplicated files')
	print('   --nameonly to check filename only')
	print('   --recursive to only check in images directory')
	print('     --nameonly is forbidden in such a case')
	sys.exit(2)

def get_args(argv):
	global _remove, _nameonly, _recursive

	_remove = False
	_nameonly = False
	_recursive = False

	try:
		opts, args = getopt.getopt(argv,"h",["remove", "recursive", "nameonly"])
	except:
		usage()

	# get arguments
	for opt, arg in opts:
		if opt == '-h':
			usage()
		elif opt == '--remove':
			_remove = True
		elif opt == '--nameonly':
			_nameonly = True
		elif opt == '--recursive':
			_recursive = True
	if _recursive and _nameonly:
		usage()

def check_remove(list_this_name_file, full_name_to_remove):
	for previous_full_name in list_this_name_file:
		same = (_nameonly) or filecmp.cmp(full_name_to_remove, previous_full_name, True)
		if same:
			if (_remove):
				print("Remove", full_name_to_remove, " -- Found in", previous_full_name)
				os.remove(full_name_to_remove)
			else:
				print("[dryrun] Remove", full_name_to_remove, " -- Found in", previous_full_name)
			return True
	return False

def add_to_list(list, root, file):
	if list.get(file) is not None:
		if not _recursive or not check_remove(list[file].full_names, root+"/"+file):
			list[file].full_names.append(root+"/"+file)
	else:
		list[file] = Entry([ root+"/"+file ])

def add_to_list_dir(list, root_dir):
	print("Scan", root_dir)
	for root, dirs, files in os.walk(root_dir):
		for file in files:
			add_to_list(list, root, file)

def remove_duplicate(root_dir_full, root_dir_toadd=None):
	list_full_names = {}
	add_to_list_dir(list_full_names, root_dir_full)

	if not _recursive:
		print("Process", root_dir_toadd)
		for root, dirs, files in os.walk(root_dir_toadd):
				for file in files:
					if (list_full_names.get(file) is not None):
						check_remove(list_full_names[file].full_names, root+"/"+file)

def main(argv):
	get_args(argv)

	if _recursive:
		remove_duplicate(_dir_pictures)
	else:
		remove_duplicate(_dir_pictures, _dir_tofilter)

if __name__ == "__main__":
  main(sys.argv[1:])
