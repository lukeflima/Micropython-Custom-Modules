# Micropython Custom Modules

Custom modules created with MicroPython C API.


## Madelbrot

A Madelbrot interface to use to draw on display.

### madelbrot((width: int, height: int), colour: str, (real_start: float, real_end: float, imaginary_start: float, imaginary_end: float)) -> bytearray

It allocates a buffer with `width * height * 2` bytes (RGB565) of size and used to return calculated Madelbrot as bytearray.
Colour options are "r" for red, "g" for green, and "b" for blue. Defauts to blue if passed wrong value.


#### Usage

```py
import mandlebrot
buff = mandlelbrot.madlebrot((80, 160), "r", (-2, 1, -1, 1))
```

## How to Build

The Bouncing Balls example uses the custom draw circle functions of my fork of micropython. As is added as a submodule you can simply to get my fork.
```
git submodule update --init -- micropython
```

Build Micropython for desired port using `USER_C_MODULES` as the cmake file on the modules folder.

Example using Pico Board:
```shell
micropython$ git submodule update --init -- lib/pico-sdk lib/tinyusb
micropython$ make -C mpy-cross
micropython$ cd ports/rp2
micropython/ports/rp2$ make USER_C_MODULES=../../../modules/micropython.cmake 
```

Now just drag the .uf2 file to your board located on the build folder.
