# to run this installation from your bash:
#    curl -L https://raw.githubusercontent.com/pascal-brand38/pyHelper/main/install.sh > /tmp/install.sh
#    source /tmp/install.sh

# Install pytho package
python3 -m pip install git+https://github.com/pascal-brand38/pyHelper.git

# Install library dependencies
export MYSYSTEM=mingw-w64-x86_64-
for lib in tidy
do
  echo install ${MYSYSTEM}${lib}
  pacman -S --noconfirm ${MYSYSTEM}${lib}
done

