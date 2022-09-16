


 

#COPY ./requirements.txt ./requirements
#RUN 

#WORKDIR /cbm

FROM ubuntu:latest
FROM python:3.8

COPY . .
RUN \
    apt update && \
    apt install -y pcmanfm featherpad lxtask xterm
    
#ENV DISPLAY=host.docker.internal:0.0
#windows 환경일 경우 주석 해제할 것
RUN pip install --no-cache-dir -r ./requirements.txt
CMD pcmanfm

#CMD ["python3", "tcpclient_ams_gui_v01.py"]
