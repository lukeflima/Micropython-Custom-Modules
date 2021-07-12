#driver for Sainsmart 1.8" TFT display ST7735
#Translated by Guy Carver from the ST7735 sample code.
#Modirfied for micropython-esp32 by boochow 

import machine
import time
from math import sqrt
from micropython import const
import framebuf
import gc


#TFTRotations and TFTRGB are bits to set
# on MADCTL to control display rotation/color layout
#Looking at display with pins on top.
#00 = upper left printing right
#10 = does nothing (MADCTL_ML)
#20 = upper left printing down (backwards) (Vertical flip)
#40 = upper right printing left (backwards) (X Flip)
#80 = lower left printing right (backwards) (Y Flip)
#04 = (MADCTL_MH)

#60 = 90 right rotation
#C0 = 180 right rotation
#A0 = 270 right rotation
TFTRotations = [const(0x00), const(0x60), const(0xC0), const(0xA0)]
TFTBGR = const(0x08) #When set color is bgr else rgb.
TFTRGB = const(0x00)

@micropython.native
def clamp( aValue, aMin, aMax ) :
  return max(aMin, min(aMax, aValue))


@micropython.native
def TFTColor( aR, aG, aB, endianness='big') :
  '''Create a 16 bit rgb value from the given R,G,B from 0-255.
     This assumes rgb 565 layout and will be incorrect for bgr.'''
  if endianness == 'little':
      return ((aR & 0xF8) << 8) | ((aG & 0xFC) << 3) | (aB >> 3)
  elif endianness == 'big':
      return ((aG & 0x07) << 13) | ((aR & 0x1F) << 8) | ((aB & 0x1F) << 3) | ((aG >> 3) & 0x07)
  raise ValueError('invalid endianness')


@micropython.native
def TFTColor2RGB( aColor, endianness='big' ):
  if endianness == 'little':
      r = ((aColor >> 11) & 0x1F)*255/31
      g = ((aColor >> 5) & 0x3F)*255/63
      b = (aColor & 0x1F)*255/31
      return (int(r), int(g), int(b))
  elif endianness == 'big':
      r = ((aColor >> 8) & 0x1F)*255/31
      b = (((aColor >> 3) & 0x1F))*255/31
      g = (((aColor & 0x07) << 3) | aColor >> 13)*255/63
      return (int(r), int(g), int(b))
  raise ValueError('invalid endianness')


@micropython.native
def TFTColor2RGB_hex( aColor, endianness='big' ) :
  r, g, b = TFTColor2RGB(aColor)
  return '#{:02X}{:02X}{:02X}'.format(r,g,b,endianness)


ScreenSize = (const(80), const(160))

AUTOUPDATE_ONGOING = False

def check_autoupdate(f):
    def wrapper(*args):
        global AUTOUPDATE_ONGOING
        
        autoupdate_ongoing_control = False
        if not AUTOUPDATE_ONGOING:
            AUTOUPDATE_ONGOING = True
            autoupdate_ongoing_control = True
        f(*args)
        if autoupdate_ongoing_control:
            AUTOUPDATE_ONGOING = False
            if args[0].autoupdate:
                args[0].update()
    return wrapper


class TFT(object) :
  """Sainsmart TFT 7735 display driver."""

  NOP = const(0x0)
  SWRESET = const(0x01)
  RDDID = const(0x04)
  RDDST = const(0x09)

  SLPIN  = const(0x10)
  SLPOUT  = const(0x11)
  PTLON  = const(0x12)
  NORON  = const(0x13)

  INVOFF = const(0x20)
  INVON = const(0x21)
  DISPOFF = const(0x28)
  DISPON = const(0x29)
  CASET = const(0x2A)
  RASET = const(0x2B)
  RAMWR = const(0x2C)
  RAMRD = const(0x2E)

  VSCRDEF = const(0x33)
  VSCSAD = const(0x37)

  COLMOD = const(0x3A)
  MADCTL = const(0x36)

  FRMCTR1 = const(0xB1)
  FRMCTR2 = const(0xB2)
  FRMCTR3 = const(0xB3)
  INVCTR = const(0xB4)
  DISSET5 = const(0xB6)

  PWCTR1 = const(0xC0)
  PWCTR2 = const(0xC1)
  PWCTR3 = const(0xC2)
  PWCTR4 = const(0xC3)
  PWCTR5 = const(0xC4)
  VMCTR1 = const(0xC5)

  RDID1 = const(0xDA)
  RDID2 = const(0xDB)
  RDID3 = const(0xDC)
  RDID4 = const(0xDD)

  PWCTR6 = const(0xFC)

  GMCTRP1 = const(0xE0)
  GMCTRN1 = const(0xE1)

  BLACK = const(0)
  RED = TFTColor(const(0xFF), const(0x00), const(0x00))
  MAROON = TFTColor(const(0x80), const(0x00), const(0x00))
  GREEN = TFTColor(const(0x00), const(0xFF), const(0x00))
  FOREST = TFTColor(const(0x00), const(0x80), const(0x80))
  BLUE = TFTColor(const(0x00), const(0x00), const(0xFF))
  NAVY = TFTColor(const(0x00), const(0x00), const(0x80))
  CYAN = TFTColor(const(0x00), const(0xFF), const(0xFF))
  YELLOW = TFTColor(const(0xFF), const(0xFF), const(0x00))
  PURPLE = TFTColor(const(0xFF), const(0x00), const(0xFF))
  WHITE = TFTColor(const(0xFF), const(0xFF), const(0xFF))
  GRAY = TFTColor(const(0x80), const(0x80), const(0x80))
  
  @staticmethod
  def color( aR, aG, aB ) :
    '''Create a 565 rgb TFTColor value'''
    return TFTColor(aR, aG, aB)

  def __init__( self, spi, aDC, aReset, aCS) :
    """aLoc SPI pin location is either 1 for 'X' or 2 for 'Y'.
       aDC is the DC pin and aReset is the reset pin."""
    self._size = ScreenSize
    self._offset = bytearray([26,1])
    self.rotate = 0                    #Vertical with top toward pins.
    self._rgb = True                   #color order of rgb.
    self.tfa = 0                       #top fixed area
    self.bfa = 0                       #bottom fixed area
    self.dc  = machine.Pin(aDC, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.reset = machine.Pin(aReset, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.cs = machine.Pin(aCS, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.cs(1)
    self.spi = spi
    self.colorData = bytearray(2)
    self.windowLocData = bytearray(4)
    self.buf = bytearray(self._size[0] * self._size[1] * 2)
    self.fbuf = framebuf.FrameBuffer(self.buf, self._size[0], self._size[1], framebuf.RGB565)
    self.fbuf.fill(self.BLACK)
    self.autoupdate = False
    
  def set_autoupdate(self, autoupdate=True):
      self.autoupdate = autoupdate
  
  def size( self ) :
    return self._size

  def update(self):
    self._setwindowloc((0,0),(self._size[0] - 1, self._size[1] - 1))
    self._writedata(self.fbuf)


  @micropython.native
  def on( self, aTF = True ) :
    '''Turn display on or off.'''
    self._writecommand(TFT.DISPON if aTF else TFT.DISPOFF)

  @micropython.native
  def invertcolor( self, aBool ) :
    '''Invert the color data IE: Black = White.'''
    self._writecommand(TFT.INVON if aBool else TFT.INVOFF)

  @micropython.native
  def rgb( self, aTF = True ) :
    '''True = rgb else bgr'''
    self._rgb = aTF
    self._setMADCTL()

  @micropython.native
  def rotation( self, aRot ) :
    '''0 - 3. Starts vertical with top toward pins and rotates 90 deg
       clockwise each step.'''
    if (0 <= aRot < 4):
      rotchange = self.rotate ^ aRot
      self.rotate = aRot
      #If switching from vertical to horizontal swap x,y
      # (indicated by bit 0 changing).
      if (rotchange & 1):
        self._size =(self._size[1], self._size[0])
      self._setMADCTL()

  @micropython.native
  @check_autoupdate
  def pixel( self, aPos, aColor ) :
    '''Draw a pixel at the given position'''
    self.fbuf.pixel(aPos[0], aPos[1], aColor)

  @micropython.native
  @check_autoupdate
  def text( self, aPos, aString, aColor, aFont=None, aSize = 1, nowrap = False ) :
    '''Draw a text at the given position.  If the string reaches the end of the
       display it is wrapped to aPos[0] on the next line.  aSize may be an integer
       which will size the font uniformly on w,h or a or any type that may be
       indexed with [0] or [1].'''

    self.fbuf.text(aString, aPos[0], aPos[1], aColor)


  @micropython.native
  @check_autoupdate
  def line( self, aStart, aEnd, aColor ) :
    '''Draws a line from aStart to aEnd in the given color.  Vertical or horizontal
       lines are forwarded to vline and hline.'''
    self.fbuf.line(aStart[0], aStart[1], aEnd[0], aEnd[1], aColor)

  @micropython.native
  @check_autoupdate
  def vline( self, aStart, aLen, aColor ) :
    self.fbuf.vline(aStart[0], aStart[1], aLen, aColor)

  @micropython.native
  @check_autoupdate
  def hline( self, aStart, aLen, aColor ) :
    self.fbuf.hline(aStart[0], aStart[1], aLen, aColor)

  @micropython.native
  @check_autoupdate
  def rect( self, aStart, aSize, aColor ) :
    '''Draw a hollow rectangle.  aStart is the smallest coordinate corner
       and aSize is a tuple indicating width, height.'''
    self.fbuf.rect(aStart[0], aStart[1], aSize[0], aSize[1], aColor)

  @micropython.native
  @check_autoupdate
  def fill_rect( self, aStart, aSize, aColor ) :
    '''Draw a filled rectangle.  aStart is the smallest coordinate corner
       and aSize is a tuple indicating width, height.'''
    self.fbuf.fill_rect(aStart[0], aStart[1], aSize[0], aSize[1], aColor)

  @micropython.native
  @check_autoupdate
  def circle( self, aPos, aRadius, aColor ) :
    '''Draw a hollow circle with the given radius and color with aPos as center.'''
    self.fbuf.circle(aPos[0], aPos[1], aRadius, aColor)
    
  @micropython.native
  @check_autoupdate
  def fill_circle( self, aPos, aRadius, aColor ) :
    '''Draw a filled circle with given radius and color with aPos as center'''
    self.fbuf.fill_circle(aPos[0], aPos[1], aRadius, aColor)
  
  @check_autoupdate
  def fill( self, aColor = BLACK ) :
    '''Fill screen with the given color.'''
    self.fbuf.fill(aColor)
  
  @check_autoupdate
  def image( self, x0, y0, x1, y1, data ) :
    img_buff = framebuf.FrameBuffer(data, x1-x0, y1-y0, framebuf.RGB565)
    self.fbuf.blit(img_buff, x0, y0)
    gc.collect()

  def setvscroll(self, tfa, bfa) :
    ''' set vertical scroll area '''
    self._writecommand(TFT.VSCRDEF)
    data2 = bytearray([0, tfa])
    self._writedata(data2)
    data2[1] = 162 - tfa - bfa
    self._writedata(data2)
    data2[1] = bfa
    self._writedata(data2)
    self.tfa = tfa
    self.bfa = bfa

  def vscroll(self, value) :
    a = value + self.tfa
    if (a + self.bfa > 162) :
      a = 162 - self.bfa
    self._vscrolladdr(a)

  def _vscrolladdr(self, addr) :
    self._writecommand(TFT.VSCSAD)
    data2 = bytearray([addr >> 8, addr & 0xff])
    self._writedata(data2)
    
  @micropython.native
  def _setColor( self, aColor ) :
    self.colorData[0] = aColor >> 8
    self.colorData[1] = aColor
    self.buf = bytes(self.colorData) * 32

  @micropython.native
  def _setwindowpoint( self, aPos ) :
    '''Set a single point for drawing a color to.'''
    x = self._offset[0] + int(aPos[0])
    y = self._offset[1] + int(aPos[1])
    self._writecommand(TFT.CASET)            #Column address set.
    self.windowLocData[0] = self._offset[0]
    self.windowLocData[1] = x
    self.windowLocData[2] = self._offset[0]
    self.windowLocData[3] = x
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)            #Row address set.
    self.windowLocData[0] = self._offset[1]
    self.windowLocData[1] = y
    self.windowLocData[2] = self._offset[1]
    self.windowLocData[3] = y
    self._writedata(self.windowLocData)
    self._writecommand(TFT.RAMWR)            #Write to RAM.

  @micropython.native
  def _setwindowloc( self, aPos0, aPos1 ) :
    '''Set a rectangular area for drawing a color to.'''
    self._writecommand(TFT.CASET)            #Column address set.
    self.windowLocData[0] = self._offset[0]
    self.windowLocData[1] = self._offset[0] + int(aPos0[0])
    self.windowLocData[2] = self._offset[0]
    self.windowLocData[3] = self._offset[0] + int(aPos1[0])
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)            #Row address set.
    self.windowLocData[0] = self._offset[1]
    self.windowLocData[1] = self._offset[1] + int(aPos0[1])
    self.windowLocData[2] = self._offset[1]
    self.windowLocData[3] = self._offset[1] + int(aPos1[1])
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RAMWR)            #Write to RAM.

  @micropython.native
  def _writecommand( self, aCommand ) :
    '''Write given command to the device.'''
    self.dc(0)
    self.cs(0)
    self.spi.write(bytearray([aCommand]))
    self.cs(1)

  @micropython.native
  def _writedata( self, aData ) :
    '''Write given data to the device.  This may be
       either a single int or a bytearray of values.'''
    self.dc(1)
    self.cs(0)
    self.spi.write(aData)
    self.cs(1)

  @micropython.native
  def _setMADCTL( self ) :
    '''Set screen rotation and RGB/BGR format.'''
    self._writecommand(TFT.MADCTL)
    rgb = TFTRGB if self._rgb else TFTBGR
    self._writedata(bytearray([TFTRotations[self.rotate] | rgb]))

  @micropython.native
  def _reset( self ) :
    '''Reset the device.'''
    self.dc(0)
    self.reset(1)
    time.sleep_us(500)
    self.reset(0)
    time.sleep_us(500)
    self.reset(1)
    time.sleep_us(500)

  def initb( self ) :
    '''Initialize blue tab version.'''
    self._size = (ScreenSize[0] + 2, ScreenSize[1] + 1)
    self._reset()
    self._writecommand(TFT.SWRESET)              #Software reset.
    time.sleep_us(50)
    self._writecommand(TFT.SLPOUT)               #out of sleep mode.
    time.sleep_us(500)

    data1 = bytearray(1)
    self._writecommand(TFT.COLMOD)               #Set color mode.
    data1[0] = 0x05                             #16 bit color.
    self._writedata(data1)
    time.sleep_us(10)

    data3 = bytearray([0x00, 0x06, 0x03])       #fastest refresh, 6 lines front, 3 lines back.
    self._writecommand(TFT.FRMCTR1)              #Frame rate control.
    self._writedata(data3)
    time.sleep_us(10)

    self._writecommand(TFT.MADCTL)
    data1[0] = 0x08                             #row address/col address, bottom to top refresh
    self._writedata(data1)

    data2 = bytearray(2)
    self._writecommand(TFT.DISSET5)              #Display settings
    data2[0] = 0x15                             #1 clock cycle nonoverlap, 2 cycle gate rise, 3 cycle oscil, equalize
    data2[1] = 0x02                             #fix on VTL
    self._writedata(data2)

    self._writecommand(TFT.INVCTR)               #Display inversion control
    data1[0] = 0x00                             #Line inversion.
    self._writedata(data1)

    self._writecommand(TFT.PWCTR1)               #Power control
    data2[0] = 0x02   #GVDD = 4.7V
    data2[1] = 0x70   #1.0uA
    self._writedata(data2)
    time.sleep_us(10)

    self._writecommand(TFT.PWCTR2)               #Power control
    data1[0] = 0x05                             #VGH = 14.7V, VGL = -7.35V
    self._writedata(data1)

    self._writecommand(TFT.PWCTR3)           #Power control
    data2[0] = 0x01   #Opamp current small
    data2[1] = 0x02   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.VMCTR1)               #Power control
    data2[0] = 0x3C   #VCOMH = 4V
    data2[1] = 0x38   #VCOML = -1.1V
    self._writedata(data2)
    time.sleep_us(10)

    self._writecommand(TFT.PWCTR6)               #Power control
    data2[0] = 0x11
    data2[1] = 0x15
    self._writedata(data2)

    #These different values don't seem to make a difference.
#     dataGMCTRP = bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
#                             0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
    dataGMCTRP = bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29,
                            0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10])
    self._writecommand(TFT.GMCTRP1)
    self._writedata(dataGMCTRP)

#     dataGMCTRN = bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
#                             0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])
    dataGMCTRN = bytearray([0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d, 0x2e,
                            0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10])
    self._writecommand(TFT.GMCTRN1)
    self._writedata(dataGMCTRN)
    time.sleep_us(10)

    self._writecommand(TFT.CASET)                #Column address set.
    self.windowLocData[0] = 0x00
    self.windowLocData[1] = 2                   #Start at column 2
    self.windowLocData[2] = 0x00
    self.windowLocData[3] = self._size[0] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)                #Row address set.
    self.windowLocData[1] = 1                   #Start at row 2.
    self.windowLocData[3] = self._size[1] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.NORON)                #Normal display on.
    time.sleep_us(10)

    self._writecommand(TFT.RAMWR)
    time.sleep_us(500)

    self._writecommand(TFT.DISPON)
    self.cs(1)
    time.sleep_us(500)

  def initr( self ) :
    '''Initialize a red tab version.'''
    self._reset()

    self._writecommand(TFT.SWRESET)              #Software reset.
    time.sleep_us(150)
    self._writecommand(TFT.SLPOUT)               #out of sleep mode.
    time.sleep_us(500)

    data3 = bytearray([0x01, 0x2C, 0x2D])       #fastest refresh, 6 lines front, 3 lines back.
    self._writecommand(TFT.FRMCTR1)              #Frame rate control.
    self._writedata(data3)

    self._writecommand(TFT.FRMCTR2)              #Frame rate control.
    self._writedata(data3)

    data6 = bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d])
    self._writecommand(TFT.FRMCTR3)              #Frame rate control.
    self._writedata(data6)
    time.sleep_us(10)

    data1 = bytearray(1)
    self._writecommand(TFT.INVCTR)               #Display inversion control
    data1[0] = 0x07                             #Line inversion.
    self._writedata(data1)

    self._writecommand(TFT.PWCTR1)               #Power control
    data3[0] = 0xA2
    data3[1] = 0x02
    data3[2] = 0x84
    self._writedata(data3)

    self._writecommand(TFT.PWCTR2)               #Power control
    data1[0] = 0xC5   #VGH = 14.7V, VGL = -7.35V
    self._writedata(data1)

    data2 = bytearray(2)
    self._writecommand(TFT.PWCTR3)               #Power control
    data2[0] = 0x0A   #Opamp current small
    data2[1] = 0x00   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.PWCTR4)               #Power control
    data2[0] = 0x8A   #Opamp current small
    data2[1] = 0x2A   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.PWCTR5)               #Power control
    data2[0] = 0x8A   #Opamp current small
    data2[1] = 0xEE   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.VMCTR1)               #Power control
    data1[0] = 0x0E
    self._writedata(data1)

    self._writecommand(TFT.INVOFF)

    self._writecommand(TFT.MADCTL)               #Power control
    data1[0] = 0xC8
    self._writedata(data1)

    self._writecommand(TFT.COLMOD)
    data1[0] = 0x05
    self._writedata(data1)

    self._writecommand(TFT.CASET)                #Column address set.
    self.windowLocData[0] = 0x00
    self.windowLocData[1] = 0x00
    self.windowLocData[2] = 0x00
    self.windowLocData[3] = self._size[0] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)                #Row address set.
    self.windowLocData[3] = self._size[1] - 1
    self._writedata(self.windowLocData)

    dataGMCTRP = bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
                            0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
    self._writecommand(TFT.GMCTRP1)
    self._writedata(dataGMCTRP)

    dataGMCTRN = bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
                            0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])
    self._writecommand(TFT.GMCTRN1)
    self._writedata(dataGMCTRN)
    time.sleep_us(10)

    self._writecommand(TFT.DISPON)
    time.sleep_us(100)

    self._writecommand(TFT.NORON)                #Normal display on.
    time.sleep_us(10)

    self.cs(1)
    
  def initb2( self ) :
    '''Initialize another blue tab version.'''
    self._size = (ScreenSize[0] + 2, ScreenSize[1] + 1)
    self._offset[0] = 2
    self._offset[1] = 1
    self._reset()
    self._writecommand(TFT.SWRESET)              #Software reset.
    time.sleep_us(50)
    self._writecommand(TFT.SLPOUT)               #out of sleep mode.
    time.sleep_us(500)

    data3 = bytearray([0x01, 0x2C, 0x2D])        #
    self._writecommand(TFT.FRMCTR1)              #Frame rate control.
    self._writedata(data3)
    time.sleep_us(10)

    self._writecommand(TFT.FRMCTR2)              #Frame rate control.
    self._writedata(data3)
    time.sleep_us(10)

    self._writecommand(TFT.FRMCTR3)              #Frame rate control.
    self._writedata(data3)
    time.sleep_us(10)

    self._writecommand(TFT.INVCTR)               #Display inversion control
    data1 = bytearray(1)                         #
    data1[0] = 0x07
    self._writedata(data1)

    self._writecommand(TFT.PWCTR1)               #Power control
    data3[0] = 0xA2   #
    data3[1] = 0x02   #
    data3[2] = 0x84   #
    self._writedata(data3)
    time.sleep_us(10)

    self._writecommand(TFT.PWCTR2)               #Power control
    data1[0] = 0xC5                              #
    self._writedata(data1)

    self._writecommand(TFT.PWCTR3)           #Power control
    data2 = bytearray(2)
    data2[0] = 0x0A   #
    data2[1] = 0x00   #
    self._writedata(data2)

    self._writecommand(TFT.PWCTR4)           #Power control
    data2[0] = 0x8A   #
    data2[1] = 0x2A   #
    self._writedata(data2)

    self._writecommand(TFT.PWCTR5)           #Power control
    data2[0] = 0x8A   #
    data2[1] = 0xEE   #
    self._writedata(data2)

    self._writecommand(TFT.VMCTR1)               #Power control
    data1[0] = 0x0E   #
    self._writedata(data1)
    time.sleep_us(10)

    self._writecommand(TFT.MADCTL)
    data1[0] = 0xC8                             #row address/col address, bottom to top refresh
    self._writedata(data1)

#These different values don't seem to make a difference.
#     dataGMCTRP = bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
#                             0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
    dataGMCTRP = bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29,
                            0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10])
    self._writecommand(TFT.GMCTRP1)
    self._writedata(dataGMCTRP)

#     dataGMCTRN = bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
#                             0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])
    dataGMCTRN = bytearray([0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d, 0x2e,
                            0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10])
    self._writecommand(TFT.GMCTRN1)
    self._writedata(dataGMCTRN)
    time.sleep_us(10)

    self._writecommand(TFT.CASET)                #Column address set.
    self.windowLocData[0] = 0x00
    self.windowLocData[1] = 0x02                   #Start at column 2
    self.windowLocData[2] = 0x00
    self.windowLocData[3] = self._size[0] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)                #Row address set.
    self.windowLocData[1] = 0x01                   #Start at row 2.
    self.windowLocData[3] = self._size[1] - 1
    self._writedata(self.windowLocData)

    data1 = bytearray(1)
    self._writecommand(TFT.COLMOD)               #Set color mode.
    data1[0] = 0x05                             #16 bit color.
    self._writedata(data1)
    time.sleep_us(10)

    self._writecommand(TFT.NORON)                #Normal display on.
    time.sleep_us(10)

    self._writecommand(TFT.RAMWR)
    time.sleep_us(500)

    self._writecommand(TFT.DISPON)
    self.cs(1)
    time.sleep_us(500)

  @micropython.native
  def initg( self ) :
    '''Initialize a green tab version.'''
    self._reset()

    self._writecommand(TFT.SWRESET)              #Software reset.
    time.sleep_us(150)
    self._writecommand(TFT.SLPOUT)               #out of sleep mode.
    time.sleep_us(255)

    data3 = bytearray([0x01, 0x2C, 0x2D])       #fastest refresh, 6 lines front, 3 lines back.
    self._writecommand(TFT.FRMCTR1)              #Frame rate control.
    self._writedata(data3)

    self._writecommand(TFT.FRMCTR2)              #Frame rate control.
    self._writedata(data3)

    data6 = bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d])
    self._writecommand(TFT.FRMCTR3)              #Frame rate control.
    self._writedata(data6)
    time.sleep_us(10)

    self._writecommand(TFT.INVCTR)               #Display inversion control
    self._writedata(bytearray([0x07]))
    self._writecommand(TFT.PWCTR1)               #Power control
    data3[0] = 0xA2
    data3[1] = 0x02
    data3[2] = 0x84
    self._writedata(data3)

    self._writecommand(TFT.PWCTR2)               #Power control
    self._writedata(bytearray([0xC5]))

    data2 = bytearray(2)
    self._writecommand(TFT.PWCTR3)               #Power control
    data2[0] = 0x0A   #Opamp current small
    data2[1] = 0x00   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.PWCTR4)               #Power control
    data2[0] = 0x8A   #Opamp current small
    data2[1] = 0x2A   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.PWCTR5)               #Power control
    data2[0] = 0x8A   #Opamp current small
    data2[1] = 0xEE   #Boost frequency
    self._writedata(data2)

    self._writecommand(TFT.VMCTR1)               #Power control
    self._writedata(bytearray([0x0E]))

    self._writecommand(TFT.INVOFF)

    self._setMADCTL()

    self._writecommand(TFT.COLMOD)
    self._writedata(bytearray([0x05]))

    self._writecommand(TFT.CASET)                #Column address set.
    self.windowLocData[0] = 0x00
    self.windowLocData[1] = 0x01                #Start at row/column 1.
    self.windowLocData[2] = 0x00
    self.windowLocData[3] = self._size[0] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)                #Row address set.
    self.windowLocData[3] = self._size[1] - 1
    self._writedata(self.windowLocData)

    dataGMCTRP = bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29,
                            0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10])
    self._writecommand(TFT.GMCTRP1)
    self._writedata(dataGMCTRP)

    dataGMCTRN = bytearray([0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d, 0x2e,
                            0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10])
    self._writecommand(TFT.GMCTRN1)
    self._writedata(dataGMCTRN)

    self._writecommand(TFT.NORON)                #Normal display on.
    time.sleep_us(10)

    self._writecommand(TFT.DISPON)
    time.sleep_us(100)

    self.cs(1)

def maker(  ) :
  t = TFT(1, "X1", "X2")
  print("Initializing")
  t.initr()
  t.fill(0)
  return t

def makeb(  ) :
  t = TFT(1, "X1", "X2")
  print("Initializing")
  t.initb()
  t.fill(0)
  return t

def makeg(  ) :
  t = TFT(1, "X1", "X2")
  print("Initializing")
  t.initg()
  t.fill(0)
  return t

