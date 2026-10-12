import time
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw

# 4MHz, mode=3, 物理ピン: DC=GPIO24 (Pin 18), RST=GPIO25 (Pin 22)
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, mode=3, bus_speed_hz=4000000)

# st7789クラスで480x320として初期化
device = st7789(serial, width=480, height=320, rotate=1)

# 画面バッファ作成 (青背景に白文字・黄枠)
img = Image.new("RGB", (device.width, device.height), color="blue")
draw = ImageDraw.Draw(img)

# 外枠
draw.rectangle((10, 10, device.width - 10, device.height - 10), outline="yellow", width=5)
# 中央の白い四角形
draw.rectangle((100, 80, 380, 240), fill="white")
# 文字
draw.text((120, 140), "STANDARD LUMA OK!", fill="black")

print("Sending display buffer via standard luma.lcd...")
device.display(img)
print("Done! Check display.")
time.sleep(10)
