import os
import shutil
import filecmp

######################################################
# Utils
######################################################

def save_text(text, path):
  with open(path, 'w') as file:
    file.write(text)
    file.close()

def create_dir_path(path):
  if not os.path.isdir(path):
    os.mkdir(path)

def copy_file(filename_src, filename_dst, force):
  # as we check whether the files are the same or not, no need to force
  if (not os.path.isfile(filename_dst) or (not filecmp.cmp(filename_src, filename_dst))):
    print('  + ' + filename_src)
    try:
      shutil.copy2(filename_src, filename_dst)
    except:
      print('   === cannot copy ' + filename_src)


# copy all files in src into dst
def copy_dir(src, dst, recursive, force):
  print('Copy ' + src + ' into ' + dst)
  for filename in os.listdir(src):
    filename_src = src + '/' + filename
    filename_dst = dst + '/' + filename
    if not os.path.isfile(filename_src):
      # this is a dir
      if recursive:
        copy_dir(filename_src, filename_dst, recursive, force)
      continue
    else:
      copy_file(filename_src, filename_dst, force)
