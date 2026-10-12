import time
from luma.core.interface.serial import spi

# SPI接続: DC=GPIO24, RST=GPIO25, CS=GPIO8(CE0)
# 安定のためクロックは8MHzで初期化
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, bus_speed_hz=8000000)

# 1. ハードウェアリセット
serial._gpio.output(25, 0) # RST LOW
time.sleep(0.1)
serial._gpio.output(25, 1) # RST HIGH
time.sleep(0.12)

# 2. ST7796S コマンド初期化シーケンス
# コマンド送信関数
def cmd(c, data=None):
    serial.command(c)
    if data:
        serial.data(data)

print("Initializing ST7796S registers...")
cmd(0x01) # SWRESET
time.sleep(0.15)

cmd(0x11) # Sleep Out
time.sleep(0.12)

cmd(0xF0, [0xC3]) # Command Set Control
cmd(0xF0, [0x96])

cmd(0x36, [0x48]) # Memory Data Access Control (RGB/BGR, 向き)
cmd(0x3A, [0x55]) # 16-bit color (RGB565)

cmd(0xB4, [0x01]) # Display Inversion Control
cmd(0xB7, [0xC6]) # Entry Mode

cmd(0x29) # Display ON
time.sleep(0.05)

# 3. 画面全体（480x320）を青色で塗りつぶし
print("Sending BLUE fill data...")
# カラム範囲: 0〜479
cmd(0x2A, [0x00, 0x00, 0x01, 0xDF])
# ページ範囲: 0〜319
cmd(0x2B, [0x00, 0x00, 0x01, 0x3F])
cmd(0x2C) # RAMWR (メモリ書き込み開始)

# 青色 (0x001F) のピクセルデータを送信
# 1行分 (480ピクセル = 960バイト)
blue_line = [0x00, 0x1F] * 480
for _ in range(320):
    serial.data(blue_line)

print("Draw complete! Screen should be BLUE.")
time.sleep(5)
