import time
import subprocess
from luma.core.interface.serial import spi
from PIL import Image, ImageDraw, ImageFont

# 1. SPI初期化 (4MHz, mode=3, DC=24, RST=25)
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, mode=3, bus_speed_hz=4000000)

def cmd(c, data=None):
    serial.command(c)
    if data:
        serial.data(data)

# ハードウェアリセット
serial._gpio.output(25, 0)
time.sleep(0.1)
serial._gpio.output(25, 1)
time.sleep(0.15)

# ST7796S 初期化シーケンス
cmd(0x01); time.sleep(0.15)
cmd(0x11); time.sleep(0.15)
cmd(0xF0, [0xC3]); cmd(0xF0, [0x96])
cmd(0x36, [0x48])  # 向き設定 (横画面 480x320)
cmd(0x3A, [0x55])  # 16-bit RGB565
cmd(0xB4, [0x01])  # 反転制御
cmd(0x29); time.sleep(0.05)

# 描画ウィンドウ設定 (0〜479, 0〜319)
cmd(0x2A, [0x00, 0x00, 0x01, 0xDF])
cmd(0x2B, [0x00, 0x00, 0x01, 0x3F])

def flush_image(img):
    """PillowのRGB画像をST7796S(RGB565)形式に変換して一括転送"""
    cmd(0x2C)
    img_rgb = img.convert("RGB")
    pixels = list(img_rgb.getdata())
    
    # RGB888 -> RGB565 バイト列生成
    buf = bytearray(480 * 320 * 2)
    idx = 0
    for r, g, b in pixels:
        val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        buf[idx] = (val >> 8) & 0xFF
        buf[idx + 1] = val & 0xFF
        idx += 2
    serial.data(list(buf))

# 2. 状態管理クラス
class DisplayApp:
    def __init__(self):
        self.state = "SYNTH"  # "SYNTH" or "CLI"
        self.width = 480
        self.height = 320
        self.frequency = 440
        
    def get_system_info(self):
        """CLI画面用のシステム情報取得"""
        ip = subprocess.getoutput("hostname -I").split()[0] if subprocess.getoutput("hostname -I") else "No IP"
        temp = subprocess.getoutput("vcgencmd measure_temp").replace("temp=", "")
        load = subprocess.getoutput("cat /proc/loadavg").split()[:3]
        return ip, temp, " ".join(load)

    def draw_synth_view(self, draw):
        """シンセ・グルーヴボックス用UI"""
        # 背景
        draw.rectangle((0, 0, self.width, self.height), fill=(10, 15, 30))
        # ヘッダー
        draw.rectangle((0, 0, self.width, 30), fill=(30, 40, 70))
        draw.text((15, 8), "MEKOU GROOVEBOX [SYNTH MODE]", fill=(0, 255, 200))
        
        # パラメータ表示
        draw.rectangle((20, 60, 220, 180), outline=(80, 100, 150), width=2)
        draw.text((35, 75), "OSC 1 FREQ", fill=(150, 150, 150))
        draw.text((35, 110), f"{self.frequency} Hz", fill=(255, 255, 255))
        
        # 簡易波形モニタ枠
        draw.rectangle((240, 60, 460, 180), outline=(80, 100, 150), width=2)
        draw.text((255, 75), "WAVEFORM (SINE)", fill=(150, 150, 150))
        # ダミー波形ライン
        points = [(250 + i * 7, 130 + int(30 * ((i % 4) - 1.5))) for i in range(29)]
        draw.line(points, fill=(0, 255, 120), width=2)
        
        # フッター
        draw.text((20, 280), "Press SW to switch -> CLI MODE", fill=(200, 200, 50))

    def draw_cli_view(self, draw):
        """CLI / システムモニタ用UI"""
        ip, temp, load = self.get_system_info()
        
        # 背景（黒ターミナル）
        draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        # ヘッダー
        draw.text((10, 10), "root@zero2w:~# sysstat --live", fill=(0, 255, 0))
        draw.line([(0, 30), (self.width, 30)], fill=(50, 50, 50), width=1)
        
        # コンソールログ
        logs = [
            f"[NET] IP Address : {ip}",
            f"[SOC] CPU Temp   : {temp}",
            f"[CPU] Load Avg   : {load}",
            f"[SPI] Bus Speed  : 4.0 MHz (Mode 3)",
            "",
            "systemd[1]: Started Audio Synthesizer Engine.",
            "kernel: spi0.0: ST7796S panel connected."
        ]
        y = 45
        for line in logs:
            draw.text((15, y), line, fill=(200, 220, 200))
            y += 25
            
        draw.text((15, 280), "[Press SW to switch -> SYNTH MODE]", fill=(0, 255, 0))

    def render(self):
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        if self.state == "SYNTH":
            self.draw_synth_view(draw)
        elif self.state == "CLI":
            self.draw_cli_view(draw)
            
        flush_image(img)

# 3. 動作テスト（3秒ごとにSYNTHとCLIを自動切り替え）
app = DisplayApp()
print("Starting State Machine Demo...")

for _ in range(4):
    print(f"Current State: {app.state}")
    app.render()
    time.sleep(3)
    # 状態反転
    app.state = "CLI" if app.state == "SYNTH" else "SYNTH"

print("Demo finished.")
