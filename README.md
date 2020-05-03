# NESTrisOCR-CJL

Reimplementation & Simplification & Slight improvements on [original NESTrisOCR](https://github.com/alex-ong/NESTrisOCR) for [CTWC Japan Lite](https://sites.google.com/view/classic-tetris-japan/).

See also [NESTrisSystem-CJL](https://github.com/NESTetrisJP/NESTrisSystem-CJL).

## Contents

* `assets/`: Image files for OCR/GUI.
* `captureWorker.py`: A thread capturing a window region and performs OCR.
* `config.py`: Saves/loads configurations.
* `main.py`: Entry point.
* `main.spec`: Configuration for PyInstaller (which makes an .exe executable).
* `mainWindow.py`: Automatically generated from `pyuic5 -o mainWindow.py mainWindow.ui`. **Do not edit manually**.
* `mainWindow.ui`: Qt Designer file of the main window.
* `networkWorker.py`: A thread connecting and sending data to NESTrisSystem-CJL Server.
* `win32.py`: Win32 helper functions.

## Setup

1. Install [Python 3](https://www.python.org/downloads/).
2. Run `pip3 install numba numpy Pillow pyqt5 pywin32`

## Running

Run `python main.py`

## Deploying

Run `pyinstaller main.spec`, then `dist/NESTrisOCR/` is distributable.

## What's changed from original version

* All-in-one GUI for connecting/previewing/setting
* Fixed resolution (512x448) for processing OCR
* More balanced field detection (reads center 2x2 from 4x4 block)
* Added game detection feature

## What's missing compared to original version

**Contributions welcome!**

* macOS/Linux support
* Automatic calibration
* Different window capture methods (File, OpenCV, etc.)
* Different packet format

## What I wanted to implement but had no time

**Contributions welcome!**

* Automatic color calibration
* Faster capturing/OCR
* Porting to web app (by using `getUserMedia()`, `getDisplayMedia()`)

## License

MIT. See [LICENSE](LICENSE).