import time
from luma.core.interface.serial import spi
from PIL import Image, ImageDraw, ImageFont

# 4MHz, mode=3
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, mode=3, bus_speed_hz=4000000)

def cmd(c, data=None):
    serial.command(c)
    if data:
        serial.data(data)

# 1. ハードウェアリセット
serial._gpio.output(25, 0)
time.sleep(0.1)
serial._gpio.output(25, 1)
time.sleep(0.15)

# 2. ST7796S 初期化
cmd(0x01); time.sleep(0.15)
cmd(0x11); time.sleep(0.15)
cmd(0xF0, [0xC3])
cmd(0xF0, [0x96])
cmd(0x36, [0x48]) # 横向き
cmd(0x3A, [0x55]) # 16-bit RGB565
cmd(0xB4, [0x01])
cmd(0x29)         # Display ON
time.sleep(0.05)

# 3. Pillowで画像を作成（480x320）
width, height = 480, 320
img = Image.new("RGB", (width, height), color=(0, 0, 0)) # 黒背景
draw = ImageDraw.Draw(img)

# 目立つテストパターンを描画
# 外枠（赤）
draw.rectangle((10, 10, width - 10, height - 10), outline=(255, 0, 0), width=4)
# 中心の四角（緑）
draw.rectangle((50, 50, 150, 150), fill=(0, 255, 0))
# 文字（白）
draw.text((180, 80), "ST7796S DISPLAY TEST", fill=(255, 255, 255))
draw.text((180, 110), "MEKOU GROOVEBOX", fill=(0, 255, 255))
draw.text((180, 140), "SPI Mode 3 / 4MHz OK", fill=(255, 255, 0))

# 4. RGB888 -> RGB565 バイト列へ変換
pixels = img.load()
raw_bytes = bytearray(width * height * 2)
idx = 0
for y in range(height):
    for x in range(width):
        r, g, b = pixels[x, y]
        # RGB565フォーマット (R:5bit, G:6bit, B:5bit)
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        raw_bytes[idx] = (rgb565 >> 8) & 0xFF
        raw_bytes[idx + 1] = rgb565 & 0xFF
        idx += 2

# 5. 液晶へ描画領域を設定して送信
print("Sending frame buffer...")
cmd(0x2A, [0x00, 0x00, 0x01, 0xDF]) # カラム 0〜479
cmd(0x2B, [0x00, 0x00, 0x01, 0x3F]) # 行 0〜319
cmd(0x2C)                            # RAM書き込み開始

# ★ここが最重要: 4096バイトずつ分割して送信（SPIバッファ溢れ防止）
CHUNK_SIZE = 4096
raw_bytes_list = list(raw_bytes)
for i in range(0, len(raw_bytes_list), CHUNK_SIZE):
    serial.data(raw_bytes_list[i : i + CHUNK_SIZE])

print("Draw complete! Check display.")
