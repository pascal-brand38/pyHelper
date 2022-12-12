# to run this installation from your bash:
#    curl -L https://raw.githubusercontent.com/pascal-brand38/pyHelper/main/install.sh > /tmp/install.sh
#    source /tmp/install.sh

# Install library dependencies
# Must be run before install of pyHelper, as 'pip install imagehash' fails on msys2/mingw
# due to complex compilation
export MYSYSTEM=mingw-w64-x86_64-
for lib in tidy python-numpy python-pywavelets python-scipy ffmpeg
do
  echo install ${MYSYSTEM}${lib}
  pacman -S --noconfirm ${MYSYSTEM}${lib}
done

# Install pytho package
python3 -m pip install git+https://github.com/pascal-brand38/pyHelper.git
