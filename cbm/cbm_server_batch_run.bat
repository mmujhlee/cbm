start ZTDRServer/ZTDR_Server.exe
TIMEOUT /T 10
start python ztdr_tcp_server_v01.py
start python daq_tcp_server_v01.py
start python rgbt_camera_tcp_server_v01.py
