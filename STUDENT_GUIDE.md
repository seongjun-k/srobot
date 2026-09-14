# ROS 1 Noetic 터틀봇 원격 조종 패키지 제작 실습

## 1. 프로젝트 개요

### 1) 실습 목적
- ROS의 기본 통신 원리인 퍼블리셔(Publisher)와 서브스크라이버(Subscriber) 구조를 이해합니다.
- 터틀봇 바퀴 모터 제어 표준 메시지인 geometry_msgs/Twist의 구조와 동작 방식을 이해합니다.
- 노트북 키보드 입력을 통해 원격 터틀봇을 실시간 조종하는 srobot 패키지를 완성합니다.

### 2) 시스템 통신 구조
- 노트북 (teleop_key.py) : 키보드 입력을 감지하여 /srobot/key_cmd 토픽(String) 발행
- 무선 네트워크 (Wi-Fi) : 노트북과 터틀봇 간 ROS 멀티 마신 무선 통신 연결
- 터틀봇 (motor_driver.py) : /srobot/key_cmd 토픽 수신 후 /cmd_vel 토픽(Twist) 발행
- OpenCR 보드 (rosserial) : /cmd_vel 속도 지휘값을 받아 터틀봇 좌/우 다이나믹셀 모터 구동

---

## 2. 패키지 구성 및 준비

### 1) 패키지 이름 : srobot
### 2) 대상 로봇 : 터틀봇 (TurtleBot3 Burger 호환, OpenCR + 다이나믹셀 XL430)
### 3) 의존성 패키지 : rospy, std_msgs, geometry_msgs, rosserial_python

### 4) 터틀봇 측 필수 패키지 설치 및 권한 설정
터틀봇(라즈베리파이) 터미널에서 OpenCR 시리얼 통신 패키지를 설치하고 권한을 부여합니다:

```bash
sudo apt update
sudo apt install -y ros-noetic-rosserial-python ros-noetic-rosserial-msgs
sudo usermod -aG dialout $USER
```

### 5) 깃허브에서 패키지 다운로드 (Git Clone)
이미 완성된 패키지를 깃허브에서 내려받아 바로 실습할 경우 워크스페이스에서 실행합니다:

```bash
cd ~/turtle_ws/src
git clone https://github.com/seongjun-k/srobot.git
```

### 6) 직접 패키지 생성하기 (처음부터 직접 만들 경우)
패키지를 기초부터 직접 만들어볼 경우 아래 명령어로 패키지와 폴더를 생성합니다:

```bash
cd ~/turtle_ws/src
catkin_create_pkg srobot rospy std_msgs geometry_msgs
cd srobot
mkdir scripts launch
```

---

## 3. 노트북 조종 노드 작성 (teleop_key.py)

### 1) 소스 파일 경로 : scripts/teleop_key.py
### 2) 소스 코드 작성
노트북에서 엔터(Enter) 없이 키보드 입력을 즉시 감지하여 터틀봇으로 전송하는 노드입니다:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# srobot - teleop_key.py
# 노트북 키보드로 로봇을 원격 조종하는 노드

import sys
import tty
import termios
import rospy
from std_msgs.msg import String

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

def main():
    rospy.init_node('srobot_teleop', anonymous=False)
    key_pub = rospy.Publisher('/srobot/key_cmd', String, queue_size=10)

    print("========================================")
    print("        로봇 키보드 조종 프로그램")
    print("========================================")
    print("  w: 전진,  x: 후진,  a: 좌회전,  d: 우회전")
    print("  s: 정지,  q: 종료")
    print("  e: 속도 증가,  c: 속도 감소")
    print("========================================")
    print("키를 누르면 로봇이 움직입니다 (종료: q)")

    while not rospy.is_shutdown():
        key = get_key().lower()

        if key == 'q':
            key_pub.publish('s')
            print("프로그램을 종료합니다.")
            break

        if key == ' ':
            key = 's'

        if key in ['w', 'a', 's', 'd', 'x', 'e', 'c']:
            key_pub.publish(key)
            print("전송 명령: " + key)

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
```

### 3) 실행 권한 부여 (필수)
작성한 파이썬 스크립트에 실행 권한(+x)을 부여합니다:

```bash
chmod +x scripts/teleop_key.py
```

---

## 4. 터틀봇 모터 드라이버 노드 작성 (motor_driver.py)

### 1) 소스 파일 경로 : scripts/motor_driver.py
### 2) 소스 코드 작성
키 입력을 수신하여 터틀봇 다이나믹셀 모터 구동용 Twist 속도로 변환해 /cmd_vel로 발행하는 노드입니다:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# srobot - motor_driver.py
# 키보드 명령을 받아 바퀴 모터 속도로 변환하는 노드

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

linear_speed = 0.15
angular_speed = 0.75

target_linear = 0.0
target_angular = 0.0

def key_callback(msg):
    global linear_speed, angular_speed, target_linear, target_angular
    cmd = msg.data.strip()

    if cmd == 'e':
        linear_speed = min(0.30, linear_speed + 0.02)
        rospy.loginfo("속도 증가: %f", linear_speed)
        if target_linear > 0:
            target_linear = linear_speed
        elif target_linear < 0:
            target_linear = -linear_speed
        return

    elif cmd == 'c':
        linear_speed = max(0.05, linear_speed - 0.02)
        rospy.loginfo("속도 감소: %f", linear_speed)
        if target_linear > 0:
            target_linear = linear_speed
        elif target_linear < 0:
            target_linear = -linear_speed
        return

    if cmd == 'w':
        target_linear = linear_speed
        target_angular = 0.0
        rospy.loginfo("전진")
    elif cmd == 'x':
        target_linear = -linear_speed
        target_angular = 0.0
        rospy.loginfo("후진")
    elif cmd == 'a':
        target_linear = 0.0
        target_angular = angular_speed
        rospy.loginfo("좌회전")
    elif cmd == 'd':
        target_linear = 0.0
        target_angular = -angular_speed
        rospy.loginfo("우회전")
    elif cmd == 's':
        target_linear = 0.0
        target_angular = 0.0
        rospy.loginfo("정지")

def main():
    global target_linear, target_angular

    rospy.init_node('srobot_motor_driver', anonymous=False)

    cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    rospy.Subscriber('/srobot/key_cmd', String, key_callback)

    rospy.loginfo("모터 드라이버 노드가 준비되었습니다.")

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        twist = Twist()
        twist.linear.x = target_linear
        twist.angular.z = target_angular
        cmd_pub.publish(twist)
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
```

### 3) 실행 권한 부여 (필수)
작성한 파이썬 스크립트에 실행 권한(+x)을 부여합니다:

```bash
chmod +x scripts/motor_driver.py
```

---

## 5. 런치(Launch) 파일 작성

### 1) 터틀봇용 런치 파일 : launch/robot.launch
OpenCR 통신 노드와 모터 드라이버 노드를 하나의 프로세스로 함께 실행합니다:

```xml
<launch>
  <node pkg="rosserial_python" type="serial_node.py" name="opencr_core" output="screen" respawn="true">
    <param name="port" value="/dev/ttyACM0"/>
    <param name="baud" value="115200"/>
  </node>

  <node pkg="srobot" type="motor_driver.py" name="srobot_motor_driver" output="screen" respawn="true"/>
</launch>
```

### 2) 노트북 조종용 런치 파일 : launch/teleop.launch
노트북에서 키보드 텔레옵 콘솔 노드를 실행합니다:

```xml
<launch>
  <node pkg="srobot" type="teleop_key.py" name="srobot_teleop" output="screen"/>
</launch>
```

---

## 6. 패키지 빌드 및 환경변수 등록 (Build)

### 1) 워크스페이스로 이동하여 빌드 수행 (catkin_make)
노드와 런치 파일 작성이 완료되면 catkin 워크스페이스 루트에서 빌드를 수행해야 ROS 시스템이 패키지를 인식합니다:

```bash
cd ~/turtle_ws
catkin_make
```

### 2) 빌드 환경변수 적용 (source)
빌드 후 생성된 실행 환경을 현재 터미널에 반영합니다:

```bash
source devel/setup.bash
```

### 3) 패키지 인식 확인 (rospack)
ROS 패키지 시스템에 srobot 패키지가 정상적으로 등록되었는지 확인합니다:

```bash
rospack find srobot
```
- 출력 결과로 `/home/.../turtle_ws/src/srobot` 경로가 나타나면 정상적으로 빌드 및 등록이 완료된 것입니다.

---

## 7. 네트워크 환경 설정 (노트북과 터틀봇 무선 연결)

### 1) 내 IP 확인하기
노트북과 터틀봇 각각 터미널에서 자신의 Wi-Fi IP 주소를 확인합니다:

```bash
hostname -I
```

### 2) 환경변수 설정 원리
- ROS_MASTER_URI : roscore가 실행 중인 터틀봇의 IP 주소 (양쪽 모두 동일하게 입력)
- ROS_IP : 현재 명령어를 입력하고 있는 컴퓨터 본인의 IP 주소

### 3) 터틀봇 환경변수 등록

```bash
export ROS_MASTER_URI=http://<터틀봇IP>:11311
export ROS_IP=<터틀봇IP>
```

### 4) 노트북 환경변수 등록

```bash
export ROS_MASTER_URI=http://<터틀봇IP>:11311
export ROS_IP=<노트북IP>
```

---

## 8. 터틀봇 주행 실습

### 1) 터틀봇에서 모터 노드 실행
터틀봇에 SSH 접속하거나 본체 터미널에서 아래 명령을 실행합니다:

```bash
roslaunch srobot robot.launch
```

### 2) 노트북에서 조종 콘솔 실행
노트북 터미널에서 키보드 텔레옵 콘솔을 실행합니다:

```bash
roslaunch srobot teleop.launch
```

### 3) 키보드 조종 가이드
콘솔 창에 키를 누르면 터틀봇이 엔터 없이 즉각 반응하여 주행합니다:

| 키 (Key) | 동작 (Action) | 상세 설명 |
|:---|:---|:---|
| **w** | 전진 | 현재 설정된 선속도로 앞쪽 주행 |
| **x** | 후진 | 현재 설정된 선속도로 뒤쪽 주행 |
| **a** | 좌회전 | 제자리 반시계방향 회전 |
| **d** | 우회전 | 제자리 시계방향 회전 |
| **s 또는 Space** | 정지 | 바퀴 모터 즉각 정지 |
| **e** | 속도 증가 | 선속도 0.02 m/s 실시간 증가 |
| **c** | 속도 감소 | 선속도 0.02 m/s 실시간 감소 |
| **q** | 종료 | 로봇 정지 후 콘솔 프로그램 종료 |
