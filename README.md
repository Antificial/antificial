Antificial
======
**Antificial** is a real-time swarm simulation framework with real-time user interaction.

#### Screenshot
![Demo Screenshot](https://github.com/Antificial/antificial/blob/master/demo.png "Demo Screenshot")

## Download
* [Master Version](https://github.com/Antificial/antificial/archive/master.zip)

## Usage
It is recommended to use [virtualenv](https://pypi.python.org/pypi/virtualenv) with this project.
```
$ git clone https://github.com/Antificial/antificial.git
$ cd antificial
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ cd antificial/
$ python main.py
```

### Known Errors
##### `Cython is missing, it's required for compiling kivy!`:  
This likely occurs after trying to install the requirements through `pip`. Please `pip install Cython` and then try again.

##### `No module named 'cv2'`:  
Likely occurs after trying to start the program for the first time. Sometimes when creating a virtual environment, python does not copy the link to OpenCV, so it has to be done manually afterwards. The original link can be found in the `site-packages` of the respective original python installation, e.g. `/usr/local/lib/python3.6/site-packages/cv2.so`.  
To re-establish the link in the virtual environment, simply copy the link into it like this, then run the program again:  
`cp /usr/local/lib/python3.6/site-packages/cv2.so venv/lib/python3.6/site-packages/cv2.so`.

## Contributors

### Contributors on GitHub
* [Contributors](https://github.com/Antificial/antificial/graphs/contributors)

### Third party libraries
* [Kivy](https://kivy.org) Graphics Framework
* [OpenCV](http://opencv.org) Computer Vision Library

### Credit
* Antificial Logo - Dave Keller [[Website]](http://www.davedesignsstuff.com) / [[Dribble]](https://dribbble.com/dabious)
* Inspiration - Alex Belezjaks [[Website]](http://alexbelezjaks.com/works/ant-colony-simulation)

## License
* see [LICENSE](https://github.com/Antificial/antificial/blob/master/LICENSE) file

## Version
* Version 1.0

## How to use this code
* see [USAGE](https://github.com/Antificial/antificial/blob/master/USAGE.md) file
