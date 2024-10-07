import subprocess
import json
import serial
import re

ser = serial.Serial('/dev/ttyUSB0', 115200)
reading_list = []

while(True):
    if len(reading_list) == 10:

        result = subprocess.run(
            ['./bcw', json.dumps(reading_list)],
            capture_output=True,
            text=True
        )
        print("Classification result:", result.stdout.strip())
        reading_list = []
        
    data = ser.readline()
    data = data.decode('utf-8')
    numbers = re.findall(r'\d+\.\d+',data)
    numbers_list = [float(num) for num in numbers]
    reading_list.append(numbers_list)
    if data:
        print(data)

    


# data = [[2764.81, 3599.88, 3359.83, 1451.4],
#  [2766.68, 3599.88, 3362.58, 1451.4],
#  [2765.91, 3599.88, 3361.26, 1450.74],
#  [2764.7, 3599.88, 3360.27, 1450.41],
#  [2765.58, 3599.88, 3358.29, 1449.97],
#  [2761.96, 3599.88, 3357.74, 1449.42],
#  [2760.64, 3599.88, 3355.99, 1449.31],
#  [2761.19, 3599.88, 3355.0, 1448.32],
#  [2762.18, 3599.88, 3355.11, 1448.21],
#  [2761.85, 3599.88, 3352.58, 1447.88]]

# # subprocess로 CIS_bcw 실행
# result = subprocess.run(
#     ['./bcw', json.dumps(data)],
#     capture_output=True,
#     text=True
# )

# # 결과 출력
# print("예측 결과:", result.stdout.strip())
