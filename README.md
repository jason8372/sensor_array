가. Serial data logger : data를 loging해서 CSV화일로 저장합니다. (화면이 필요없을 경우 저장만을 위해서 사용)
ROS Interface for the sensor. /visualization_marker -> marks the map with the red sphere where the contamination is detected.
Save the csv file containing timestamp/sensor data(4)/classification result/position
나. Serial visualization: data를 받아서 화면에 표시해 줍니다. (저장이 필요없고 monitoring만을 위해 사용)
다. Seriallogvisualizer: data를 저장하면서 실시간으로 보여줌 (저장을 하고 Monitoring도 가능함)
