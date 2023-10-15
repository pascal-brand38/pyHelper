import sys
import getopt
from pyHelper import utilsHelper
import os
import shutil, subprocess

# python -m pip install --upgrade pillow
from PIL import Image, ExifTags

def main(argv):
  for orientation in ExifTags.TAGS.keys():
    if ExifTags.TAGS[orientation]=='Orientation':
        break

  # get_args(argv)
  modification_date = 0
  nb = 0
  utilsHelper.create_dir_path('tmp/new')
  root = "tmp"
  for root, dirs, files in os.walk(root):
    for jpg_filename in files:
      if jpg_filename.endswith('.jpg') or jpg_filename.endswith('.JPG'):
        nb = nb + 1
        if os.path.isfile('tmp/new/' + jpg_filename):
          modification_date = os.path.getmtime(root + "/" + jpg_filename)
          print('  - ' + str(nb) + ' ' + jpg_filename)
          continue

        ok = True

        # modification date not too close to previous one, except for Whatsapp images
        ok = ok and (abs(os.path.getmtime(root + "/" + jpg_filename) - modification_date) > 2  or  "WA" in jpg_filename)
        modification_date = os.path.getmtime(root + "/" + jpg_filename)

        if ok:
          try:
            image = Image.open(root + "/" + jpg_filename)
          except:
            continue

          # width larger than height
          ok = ok and (image.width > image.height)
          this_orientation = 0

          if ok:
            # look at exif orientation at https://sirv.com/help/articles/rotate-photos-to-be-upright/
            # and https://stackoverflow.com/questions/13872331/rotating-an-image-with-orientation-specified-in-exif-using-python-without-pil-in
            # The 8 EXIF orientation values are numbered 1 to 8.
            #   1/ = 0 degrees: the correct orientation, no adjustment is required.
            #   2/ = 0 degrees, mirrored: image has been flipped back-to-front.
            #   3/ = 180 degrees: image is upside down.
            #   4/ = 180 degrees, mirrored: image has been flipped back-to-front and is upside down.
            #   5/ = 90 degrees: image has been flipped back-to-front and is on its side.
            #   6/ = 90 degrees, mirrored: image is on its side.
            #   7/ = 270 degrees: image has been flipped back-to-front and is on its far side.
            #   8/ = 270 degrees, mirrored: image is on its far side
            try:
              exif = image._getexif()
              this_orientation = exif[orientation]
            except:
              this_orientation = 1      # no exif orientation is provided ==> is in the correct orientation

          ok = ok and ((this_orientation == 1) or (this_orientation == 3))
          if ok:
            print('  + ' + str(nb) + ' ' + jpg_filename)
            # shutil.copy2(root + "/" + jpg_filename, 'tmp/new/' + jpg_filename)
            # shutil.copystat(root + "/" + jpg_filename, 'tmp/new/' + jpg_filename)
            f = 256 / image.width
            noexif = False
            try:
              exifstr = image.info['exif']
            except:
              noexif = True
            image = image.resize((int(image.width * f), int(image.height * f)))
            if (this_orientation == 3):    # image is upside down
              image = image.rotate(180)

            try:
              if noexif:
                image.save('tmp/new/' + jpg_filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0')
              else:
                try:
                  image.save('tmp/new/' + jpg_filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0', exif=exifstr)
                except:
                  image.save('tmp/new/' + jpg_filename, quality=80, progressive=True, optimize=True, subsampling='4:2:0')
              shutil.copystat('tmp/' + jpg_filename, 'tmp/new/' + jpg_filename)
            except:
              print('    --> FAILED ')




if __name__ == "__main__":
  main(sys.argv[1:])
