from ST7735 import TFT,TFTColor
from machine import SPI, Pin, Timer
from micropython import const, 
from random import random, choice
from mandelbrot import mandelbrot
import gc

spi1_sck=const(10)
spi1_mosi=const(11)
spi1_miso=const(8)     #not used
st7789_res=const(12)
st7789_dc=const(13)
st7789_cs=const(14)
disp_width=const(80)
disp_height=const(160)

spitft = SPI(1, baudrate=40000000, polarity=1)
tft = TFT(spitft,st7789_dc,st7789_res,st7789_cs)
tft.initr()
tft.rgb(True)
tft.invertcolor(True)
tft.fill(TFT.BLACK)
tft.update()

colour_palets = ("r", "g", "b")

@micropython.native
def get_colour(colour, colour_base):
    if colour_base == "r":
        return TFTColor(colour,0, 0)
    if colour_base == "g":
        return TFTColor(0, colour, 0)
    return TFTColor(0, 0, colour)


@micropython.native
def draw_mandelbrot():
    global tft
    
    RealStart = -2 * random()
    RealEnd= 1 * random() 
    ImaginaryStart = -1 * random() 
    ImaginaryEnd = 1 * random()
    colour_base = choice(colour_palets)
    
    buff = mandelbrot((disp_width, disp_height), colour_base, (RealStart, RealEnd, ImaginaryStart, ImaginaryEnd))
    
    tft.image(0, 0, disp_width - 0, disp_height - 0, buff)
    tft.update()

    gc.collect()


if __name__ == "__main__":
    draw_mandelbrot()
