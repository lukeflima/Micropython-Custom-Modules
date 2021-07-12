from ST7735 import TFT, TFTColor, TFTColor2RGB_hex
from machine import SPI
from micropython import const
import random

spi1_sck=const(10)
spi1_mosi=const(11)
spi1_miso=const(8)     #not used
st7789_res = const(12)
st7789_dc  = const(13)
st7789_cs = const(14)
disp_width = const(80)
disp_height = const(160)

spitft = SPI(1, baudrate=40000000, polarity=1)
print(spitft)
tft = TFT(spitft,st7789_dc,st7789_res,st7789_cs)
tft.initg()
tft.rgb(True)
tft.invertcolor(True)
tft.fill(TFT.BLACK)


class Ball:
    def __init__(self, x, y, r, dx, dy, pen):
        self.x = x
        self.y = y
        self.r = r
        self.dx = dx
        self.dy = dy
        self.pen = pen
    
    def __str__(self):
        return "Ball(" + "x="+ str(self.x) + ", y="+ str(self.y) + ", r="+ str(self.r) + ", dx="+ str(self.dx) + ", dy="+ str(self.dy) + ", pen="+ TFTColor2RGB_hex(self.pen) +")"
    
    def __repr__(self):
        return self.__str__()
  
  

def create_random_ball():
    rad = random.randint(0, 10) + 3
    dx = dy = (14 - rad) / 2
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return Ball(
                random.randint(rad, rad + (disp_width - 2 * rad)),
                random.randint(rad, rad + (disp_height - 2 * rad)),
                rad,
                dx,
                dy,
                TFTColor(r, g, b),
            )




@micropython.native
def draw_balls(num_balls = 100):
    balls = [create_random_ball() for _ in range(num_balls)]

    while True:
        tft.fill(TFT.BLACK)
        
        for ball in balls:
            ball.x += ball.dx
            ball.y += ball.dy

            xmax = disp_width - ball.r
            xmin = ball.r
            ymax = disp_height - ball.r
            ymin = ball.r

            if ball.x < xmin or ball.x > xmax:
                ball.dx *= -1

            if ball.y < ymin or ball.y > ymax:
                ball.dy *= -1

            tft.fill_circle((round(ball.x), round(ball.y)), ball.r, ball.pen)
        tft.update()



if __name__ == '__main__':
    draw_balls()
