import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque, defaultdict

# 시리얼 설정
SERIAL_PORT = '/dev/ttyUSB0'  # sudo usermod -a -G dialout $USER
                              # Replace /dev/ttyUSB0 with your actual serial device (use ls /dev/tty*)
BAUD_RATE = 115200

# 시각화용 설정
MAX_LEN = 100
DATA_KEYS = ['DATA1', 'DATA2', 'DATA3', 'DATA4']

# GASID 매핑 및 색상 지정
GASID_LABELS = {
    '0': 'air',
    '1': 'MES'
}
COLOR_MAP = {
    'air': 'green',
    'MES': 'red'
}

# 데이터 저장 구조: {label: {DATA1: deque, DATA2: deque, ...}}
data_by_label = defaultdict(lambda: {k: deque([0]*MAX_LEN, maxlen=MAX_LEN) for k in DATA_KEYS})

# 시리얼 포트 연결
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# matplotlib 설정
fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
lines_by_label = {key: {} for key in DATA_KEYS}

for i, key in enumerate(DATA_KEYS):
    axs[i].set_ylim(0, 100)
    axs[i].set_xlim(0, MAX_LEN)
    axs[i].set_ylabel(key)
    axs[i].grid(True)

axs[-1].set_xlabel("Time (latest →)")
fig.suptitle("Real-Time Sensor Data (air / MES)")
plt.tight_layout()

# 애니메이션 업데이트 함수
def update(frame):
    line = ser.readline().decode('utf-8').strip()
    if line.startswith("D:"):
        try:
            raw = line[2:]
            parts = raw.split(',')
            if len(parts) != 5:
                print(f"⚠️ Invalid format: {line}")
                return

            d1, d2, d3, d4, gasid_raw = parts

            # GASID 매핑
            if gasid_raw not in GASID_LABELS:
                print(f"⚠️ Unknown GASID: {gasid_raw}")
                return

            label = GASID_LABELS[gasid_raw]
            color = COLOR_MAP[label]

            values = [float(d1), float(d2), float(d3), float(d4)]

            # 데이터 저장
            for i, key in enumerate(DATA_KEYS):
                data_by_label[label][key].append(values[i])

            # 라인 생성 또는 갱신
            for i, key in enumerate(DATA_KEYS):
                if label not in lines_by_label[key]:
                    line_obj, = axs[i].plot([], [], label=label, color=color)
                    lines_by_label[key][label] = line_obj
                    axs[i].legend(loc='upper left')

                line_obj = lines_by_label[key][label]
                ydata = data_by_label[label][key]
                xdata = range(len(ydata))
                line_obj.set_data(xdata, ydata)

        except Exception as e:
            print(f"⚠️ Error parsing line: {line} → {e}")

    # Y축 자동 조정
    for i in range(4):
        axs[i].relim()
        axs[i].autoscale_view()

    return [line for group in lines_by_label.values() for line in group.values()]

ani = animation.FuncAnimation(fig, update, interval=200)
plt.show()

ser.close()

