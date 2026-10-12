import time
from luma.core.interface.serial import spi

# 500kHzで確実に通信（mode=3を使用。もし反応がなければmode=0に変更してください）
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, mode=3, bus_speed_hz=500000)

def cmd(c, data=None):
    serial.command(c)
    if data:
        serial.data(data)

# 1. ハードウェアリセット
serial._gpio.output(25, 0)
time.sleep(0.1)
serial._gpio.output(25, 1)
time.sleep(0.15)

# 2. ST7796S 調整済初期化
cmd(0x01); time.sleep(0.15) # ソフトウェアリセット
cmd(0x11); time.sleep(0.15) # スリープ解除

# コマンドのロック解除
cmd(0xF0, [0xC3])
cmd(0xF0, [0x96])

# ★向きの設定を「0xE8」（横向き・RGB順）に調整
cmd(0x36, [0xE8]) 
cmd(0x3A, [0x55]) # 16ビットカラー (RGB565)
cmd(0xB4, [0x01]) # ディスプレイ反転制御（もし白黒が反転していたら0x02や0x00に変更）
cmd(0x29); time.sleep(0.1) # 表示ON

# 3. 画面全体を一度「黒」で塗りつぶす（残像を消す）
print("Clearing screen to BLACK...")
cmd(0x2A, [0x00, 0x00, 0x01, 0xDF]) # カラム 0〜479
cmd(0x2B, [0x00, 0x00, 0x01, 0x3F]) # ページ 0〜319
cmd(0x2C)

black_line = [0x00, 0x00] * 480
for _ in range(320):
    serial.data(black_line)

time.sleep(0.5)

# 4. 画面中央に「白い四角形」を描画 (X: 100〜380, Y: 80〜240)
print("Drawing WHITE box...")
cmd(0x2A, [0x00, 100, 0x01, 124]) # X: 100 (0x0064) 〜 379 (0x017B)
cmd(0x2B, [0x00, 80, 0x00, 239])  # Y: 80 (0x0050) 〜 239 (0x00EF)
cmd(0x2C)

# 280ピクセル × 160ライン の白色 (0xFFFF)
white_data = [0xFF, 0xFF] * 280
for _ in range(160):
    serial.data(white_data)

print("Finish! Screen should show a clear WHITE rectangle on BLACK background.")
