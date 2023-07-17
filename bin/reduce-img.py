import sys
import getopt
import os
import shutil, subprocess
from datetime import datetime
import json
from pyHelper import utilsHelper

# python -m pip install --upgrade pillow
from PIL import Image, ImageOps, ExifTags

_dirimg = 'C:/tmp/toreduce'
_dirresized = 'C:/tmp/reduced'

# https://www.tutorialspoint.com/python/python_command_line_arguments.htm
def usage():
  print('# width using')
  print('   cmd --width=1024')
  print('# or height using')
  print('   cmd --height 256')
  print('# or whole using')
  print('   cmd --googlephoto --rotate --no-rafale=1')
  sys.exit(2)

def get_args(argv):
  global _width, _height, _googlephoto, _rotate, _norafale

  _width = 0
  _height = 0
  _googlephoto = False
  _rotate = False
  _norafale = 0

  try:
    opts, args = getopt.getopt(argv,"h",["width=","height=","googlephoto","rotate","no-rafale="])
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
    elif opt == '--no-rafale':
      _norafale = int(arg)

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

def printExifTags(exif):
  info = None
  for key, val in exif.items():
    if key in ExifTags.TAGS:
      print(f'{key}:{ExifTags.TAGS[key]}:{val}')
      if ExifTags.TAGS[key] == "ExifOffset":   # from https://github.com/python-pillow/Pillow/issues/5863
        info = exif.get_ifd(key)
  if info:
    for key, val in info.items():
      if key in ExifTags.TAGS:
        print(f'{key}:{ExifTags.TAGS[key]}:{val}')

def main(argv):
  get_args(argv)
  if not os.path.isdir(_dirresized):
    os.mkdir(_dirresized)

  nb = 0
  last_epoch = 0
  for filename in os.listdir(_dirimg):
    isJpg = (filename.endswith('.jpg') or filename.endswith('.JPG') or filename.endswith('.jpeg') or filename.endswith('.JPEG'))
    isPng = (filename.endswith('.png') or filename.endswith('.PNG'))
    isGif = (filename.endswith('.gif') or filename.endswith('.GIF'))
    if isGif:
      nb = nb + 1
      if os.path.isfile(_dirresized + '/' + filename):
        print('  - ' + str(nb) + ' ' + filename)
        continue
      print('  + ' + str(nb) + ' ' + filename)
      utilsHelper.copy_file(_dirimg + '/' + filename, _dirresized + '/' + filename, False)
    elif isPng or isJpg:
        nb = nb + 1
        if os.path.isfile(_dirresized + '/' + filename):
          print('  - ' + str(nb) + ' ' + filename)
          continue
        print('  + ' + str(nb) + ' ' + filename)
        try:
          image = Image.open(_dirimg + '/' + filename)
          if (isPng):
            image.load()      # https://stackoverflow.com/questions/48631908/python-extract-metadata-from-png
        except:
          print('NO WAY to open ' + filename)
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
          noexif = False
          exif = image.getexif()
          # printExifTags(exif)
          # 34665===ExifOffset  and  36867===DateTimeOriginal
          info = exif.get_ifd(34665)
          dateTimeOriginal = None
          if (info):
            dateTimeOriginal = info.get(36867)
          if not dateTimeOriginal and isPng:
            dateTimeOriginal = image.info.get('Creation Time')
          
          if not dateTimeOriginal:
            # no acquisition date in exif nor png metadata
            # check if a json file exist (from a google photo for example)
            try:
              with open(_dirimg + '/' + filename + '.json') as json_file:
                jsonData = json.load(json_file)
                epoch = int(jsonData['photoTakenTime']['timestamp'])
                dateTimeOriginal = datetime.fromtimestamp(epoch).strftime('%Y:%m:%d %H:%M:%S')
            except:
              pass

          

          if dateTimeOriginal:
            # set in exif + png metadata
            if info:
              info[36867] = dateTimeOriginal
            epoch = datetime.strptime(dateTimeOriginal, '%Y:%m:%d %H:%M:%S').timestamp()
          else:
            epoch = 0

        except:
          print('  no exif in ' + filename)
          noexif = True
          epoch = 0
        
        if (_norafale!=0) and (epoch!=0) and (epoch-last_epoch < _norafale) and (epoch>=last_epoch):
          print('Skip as date acquisition too close')
          last_epoch = epoch
          continue
        
        last_epoch = epoch

        if (f < 1):
          try:
            image = image.resize((int(width * f), int(height * f)))
          except:
            print('NO WAY for resizing ' + filename)
            continue

        # from https://stackoverflow.com/questions/13872331/rotating-an-image-with-orientation-specified-in-exif-using-python-without-pil-in
        if (_rotate):
          image = ImageOps.exif_transpose(image)

        if (noexif):
          if (isPng):
            image.save(_dirresized + '/' + filename, optimize=True)
          if (isJpg):
            image.save(_dirresized + '/' + filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0')
        else:
          if (isPng):
            image.save(_dirresized + '/' + filename, optimize=True, exif=exif)
          if (isJpg):
            image.save(_dirresized + '/' + filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0', exif=exif)

        # update timestamp
        shutil.copystat(_dirimg + '/' + filename, _dirresized + '/' + filename)
        #os.stat(_dirresized + '/' + filename).st_ctime(dateTimeOriginal)
        if (epoch != 0):
          os.utime(_dirresized + '/' + filename, (epoch, epoch))



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
