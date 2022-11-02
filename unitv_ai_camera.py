#refer to http://blog.sipeed.com/p/675.html
import sensor
import KPU as kpu
import json

from machine import UART
from fpioa_manager import fm
from modules import ws2812

class_ws2812 = ws2812(8, 1)

# シリアル通信の設定
fm.register(34, fm.fpioa.UART1_TX, force=True)
fm.register(35, fm.fpioa.UART1_RX, force=True)
uart = UART(UART.UART1, 115200,8,0,0, timeout=1000, read_buf_len=4096)

# カメラモジュールの準備
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True) # 上下反転
# sensor.set_hmirror(True) # 左右反転
sensor.run(1)

# 画像保存の準備
folder_counter = 0

while True:
   try:
       os.mkdir("/sd/" + str(folder_counter)) # フォルダ名を0から順につけていく
       break
   except Exception as e:
       folder_counter += 1
       pass


# YOLOの準備
task = kpu.load(0x300000) # you need put model(face.kfpkg) in flash at address 0x300000
anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
a = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

# 画面解像度 320x240

target_face_position_x = 160 #
target_face_position_y = 120 # 中心:120、顔の位置を高くしたいときは小さくする

focus_counter = 0
picture_counter = 0

while(True):

   img = sensor.snapshot()
   code = kpu.run_yolo2(task, img)
   if code:
       for i in code:
           data = json.loads(json.dumps(i))
           face_center_x = round(data['x'] + data['w'] / 2)
           face_center_y = round(data['y'] + data['h'] / 2)
           # print(face_center_x, m',', face_center_y)
           uart.write(str(face_center_x) + ',' + str(face_center_y)+ '\n') # 座標データをシリアルで送信
           if abs(face_center_x - target_face_position_x) >= 20:
               focus_counter = 0
               if face_center_x > target_face_position_x:
                   # uart.write('L'+'\n')
                   b = class_ws2812.set_led(0,(10,0,0)) # 赤 追従中
                   b = class_ws2812.display()
               elif face_center_x < target_face_position_x:
                   # uart.write('R'+'\n')
                   b = class_ws2812.set_led(0,(10,0,0)) # 赤 追従中
                   b = class_ws2812.display()
           elif abs(face_center_y - target_face_position_y) >= 20:
               if face_center_y > target_face_position_y:
                   # uart.write('D'+'\n')
                   b = class_ws2812.set_led(0,(10,10,0)) # 黄 追従中
                   b = class_ws2812.display()
               elif face_center_y < target_face_position_y:
                   # uart.write('U'+'\n')
                   b = class_ws2812.set_led(0,(10,10,0)) # 黄 追従中
                   b = class_ws2812.display()
           else:
               # uart.write('S'+'\n')
               b = class_ws2812.set_led(0,(0,10,0)) #緑  フォーカス時
               b = class_ws2812.display()

               focus_counter += 1
               if focus_counter > 10:
                   focus_counter = 0
                   b = class_ws2812.set_led(0,(255,255,255)) #白  撮影
                   b = class_ws2812.display()
                   img.save("/sd/" + str(folder_counter) + "/"+ str(picture_counter) + ".jpg", quality=95)
                   picture_counter += 1
                   b = class_ws2812.set_led(0,(0,10,0))
                   b = class_ws2812.display()

           a = img.draw_rectangle(i.rect())
           a = img.draw_circle(target_face_position_x, target_face_position_y, 10)

a = kpu.deinit(task)
