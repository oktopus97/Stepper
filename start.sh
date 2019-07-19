if [ ! -d "venv" ]

then
python3 -m venv venv 
source venv/bin/activate
tar xf wxPython-4.0.1.tar.gz
sudo apt-get update
sudo apt-get install dpkg-dev build-essential libjpeg-dev libtiff-dev libsdl1.2-dev libgstreamer-plugins-base0.10-dev libnotify-dev freeglut3 freeglut3-dev libwebkitgtk-dev
pip3 install -r requirements.txt
python3 wxPython-4.0.1/build.py build bdist_wheel --jobs=1 --gtk2
pip3 install wxPython-4.0.1/dist/wxPython-4.0.1-cp36-cp36m-linux_armv7l.whl
fi

python3 Stepper/GUI/main.py
