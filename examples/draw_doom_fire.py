from ST7735 import TFT
from machine import SPI
from doom_fire import DoomFire

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

doom_fire = DoomFire(tft.buf, disp_height, disp_width)

def draw_doom_fire():
    doom_fire.update()
    tft.update()


def draw_doom_fire_loop():
    while True:
        draw_doom_fire()


if __name__ == "__main__":
    draw_doom_fire_loop()
