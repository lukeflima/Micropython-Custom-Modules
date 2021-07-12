# Micropython Custom Modules

Custom modules created with MicroPython C API.


## [Mandelbrot](https://en.wikipedia.org/wiki/Mandelbrot_set)

A Mandelbrot interface to use to draw on display.

### mandelbrot((width: int, height: int), colour: str, (real_start: float, real_end: float, imaginary_start: float, imaginary_end: float) [, int iterations]) -> bytearray

It allocates a buffer with `width * height * 2` bytes (RGB565) of size and used to return calculated Madelbrot as bytearray.
Colour options are "r" for red, "g" for green, and "b" for blue. Defauts to blue if passed wrong value. Iterations have default value of 10.


### mandelbrot_into((width: int, height: int), colour: str, (real_start: float, real_end: float, imaginary_start: float, imaginary_end: float), buffer: bytearray [, int iterations]) -> int

Same behaviour mandelbrot but uses buffer passed as args. Avoids memory allocations. Returns the size of the buffer. Buffer must be size of `width * height * 2`.

#### Usage

```py
import mandlebrot
buff = mandlelbrot.mandlebrot((80, 160), "r", (-2, 1, -1, 1))
```

Using pre-allocated buffer
```py
import mandlebrot
buff = bytearray(80 * 160 * 2)
mandlelbrot.mandlebrot((80, 160), "r", (-2, 1, -1, 1), buff)
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
