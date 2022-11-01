import sys
import getopt
import os
import shutil, subprocess
from datetime import datetime

# python -m pip install --upgrade pillow
from PIL import Image, ImageOps

_dirimg = 'C:/tmp/toreduce'
_dirresized = 'C:/tmp/reduced'

# https://www.tutorialspoint.com/python/python_command_line_arguments.htm
def usage():
  print('# width using')
  print('   cmd --width=1024')
  print('# or height using')
  print('   cmd --height 256')
  print('# or whole using')
  print('   cmd --googlephoto --rotate --norafale')
  sys.exit(2)

def get_args(argv):
  global _width, _height, _googlephoto, _rotate, _norafale

  _width = 0
  _height = 0
  _googlephoto = False
  _rotate = False
  _norafale = False

  try:
    opts, args = getopt.getopt(argv,"h",["width=","height=","googlephoto","rotate","norafale"])
  except:
    usage()

  # get arguments
  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt == '--width':
      _width = int(arg)
    elif opt == '--height':
      _height = int(arg)
    elif opt == '--googlephoto':
      _googlephoto = True
    elif opt == '--rotate':
      _rotate = True
    elif opt == '--norafale':
      _norafale = True

  # check 1 and only 1 option
  nb = 0
  if _width != 0:
    nb = nb+1
  if _height != 0:
    nb = nb+1
  if _googlephoto:
    nb = nb+1
  if nb != 1:
    usage()

def main(argv):
  get_args(argv)
  if not os.path.isdir(_dirresized):
    os.mkdir(_dirresized)

  nb = 0
  last_epoch = 0
  for jpg_filename in os.listdir(_dirimg):
    if jpg_filename.endswith('.jpg') or jpg_filename.endswith('.JPG'):
        nb = nb + 1
        if os.path.isfile(_dirresized + '/' + jpg_filename):
          print('  - ' + str(nb) + ' ' + jpg_filename)
          continue
        print('  + ' + str(nb) + ' ' + jpg_filename)
        try:
          image = Image.open(_dirimg + '/' + jpg_filename)
        except:
          print('NO WAY to open ' + jpg_filename)
          continue
        width = image.width
        height = image.height
        if _width != 0:
          if width > height:
            f = _width / width
          else:
            f = _width / height
        elif _height != 0:
          f = _height / height
        else:
          if width > height:
            f = 1920 / width
          else:
            f = 1920 / height

        try:
          exif = image.info['exif']
          noexif = False
          # 36867 comes from https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
          epoch = datetime.strptime(image._getexif()[36867], '%Y:%m:%d %H:%M:%S').timestamp()
        except:
          print('  no exif in ' + jpg_filename)
          noexif = True
          epoch = 0

        if (_norafale) and (epoch!=0) and (epoch-last_epoch < 2):
          print('Skip as date acquisition too close')
          last_epoch = epoch
          continue
        
        last_epoch = epoch

        if (f < 1):
          try:
            image = image.resize((int(width * f), int(height * f)))
          except:
            print('NO WAY for resizing ' + jpg_filename)
            continue

        # from https://stackoverflow.com/questions/13872331/rotating-an-image-with-orientation-specified-in-exif-using-python-without-pil-in
        if (_rotate):
          image = ImageOps.exif_transpose(image)

        if (noexif):
          image.save(_dirresized + '/' + jpg_filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0')
        else:
          image.save(_dirresized + '/' + jpg_filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0', exif=exif)
        # update timestamp
        shutil.copystat(_dirimg + '/' + jpg_filename, _dirresized + '/' + jpg_filename)

  if _googlephoto:
    # resize video too
    for mp4_filename in os.listdir(_dirimg):
      if mp4_filename.endswith('.mp4') or mp4_filename.endswith('.MP4'):
        nb = nb + 1
        if os.path.isfile(_dirresized + '/' + mp4_filename):
          print('  - ' + str(nb) + ' ' + mp4_filename)
          continue
        print('  + ' + str(nb) + ' ' + mp4_filename)
        subprocess.call([
          'ffmpeg',
          '-i', _dirimg + '/'+mp4_filename,
          '-map_metadata', '0',   # copy video media properties - keep this option right after the -i option
          '-vf', 'scale=640:-1',
          _dirresized + '/' + mp4_filename, 
          '-loglevel', 'quiet'
          ])
        # update timestamp
        # shutil.copystat(_dirimg + '/' + mp4_filename, _dirresized + '/' + mp4_filename)

if __name__ == "__main__":
  main(sys.argv[1:])
