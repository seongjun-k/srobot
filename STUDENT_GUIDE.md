# ROS 1 로봇 원격 조종 패키지(srobot) 만들기 실습 가이드

> 수업 목표:
> ROS(Robot Operating System)의 기본 원리인 퍼블리셔(Publisher)와 서브스크라이버(Subscriber), 그리고 로봇 바퀴 제어용 Twist 메시지를 이해하고, 노트북 키보드로 로봇을 직접 조종하는 패키지를 완성합니다.

---

## 목차
1. 프로젝트 개요 및 시스템 구조
2. 사전 준비 (필수 패키지 설치)
3. 1단계: 패키지 준비하기 (Git Clone 또는 직접 생성)
4. 2단계: 노트북 조종 노드 작성 (teleop_key.py)
5. 3단계: 로봇 모터 드라이버 노드 작성 (motor_driver.py)
6. 4단계: 런치(Launch) 파일 만들기
7. 5단계: 네트워크 환경 설정 (노트북과 로봇 연결)
8. 6단계: 로봇 조종 실습하기

---

## 1. 프로젝트 개요 및 시스템 구조

### 1.1 이번 시간에 무엇을 만드나요?
- 노트북에서 w, a, s, d, x 키를 누르면
- Wi-Fi 무선 통신을 통해 로봇에 명령이 전달되어
- 로봇 바퀴 모터가 회전하여 로봇이 움직입니다.

### 1.2 시스템 통신 구조
- 노트북 (teleop_key.py)
  -> /srobot/key_cmd 토픽 발행 (String 메시지)
  -> Wi-Fi 네트워크
  -> 로봇 (motor_driver.py)
  -> /cmd_vel 토픽 발행 (Twist 메시지)
  -> OpenCR 보드 (rosserial)
  -> 바퀴 모터 구동

---

## 2. 사전 준비 (필수 패키지 설치)

로봇(라즈베리파이)에서 OpenCR 보드와 통신하기 위해 설치합니다.

```bash
# 로봇 터미널에서 실행
sudo apt update
sudo apt install -y ros-noetic-rosserial-python ros-noetic-rosserial-msgs

# 시리얼 포트 접근 권한 설정
sudo usermod -aG dialout $USER
```

---

## 3. 1단계: 패키지 준비하기 (Git Clone 또는 직접 생성)

### 방법 A. 깃허브에서 바로 다운로드하기 (Git Clone)
이미 완성된 패키지를 내려받아 빠르게 실습하려면 워크스페이스의 src 폴더에서 클론합니다:

```bash
cd ~/turtle_ws/src
git clone https://github.com/seongjun-k/srobot.git
```

### 방법 B. 처음부터 내 손으로 직접 만들기
패키지를 직접 하나씩 생성하며 배우고 싶다면 아래 명령어로 생성합니다:

```bash
cd ~/turtle_ws/src
catkin_create_pkg srobot rospy std_msgs geometry_msgs
cd srobot
mkdir scripts launch
```

---

## 4. 2단계: 노트북 조종 노드 작성 (scripts/teleop_key.py)

노트북에서 실행할 키보드 입력 프로그램입니다.
아래 코드를 직접 입력하여 저장합니다.

```bash
nano scripts/teleop_key.py
```

### 소스 코드 (teleop_key.py)

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
        key = get_key()

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

### 실행 권한 부여 (필수)
```bash
chmod +x scripts/teleop_key.py
```

---

## 5. 3단계: 로봇 모터 드라이버 노드 작성 (scripts/motor_driver.py)

로봇에서 키 입력을 받아 실제 모터 속도(Twist)로 변환하는 노드입니다.

```bash
nano scripts/motor_driver.py
```

### 소스 코드 (motor_driver.py)

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

### 실행 권한 부여 (필수)
```bash
chmod +x scripts/motor_driver.py
```

---

## 6. 4단계: 런치(Launch) 파일 만들기

### 6.1 로봇용 런치 (launch/robot.launch)

```xml
<launch>
  <node pkg="rosserial_python" type="serial_node.py" name="opencr_core" output="screen" respawn="true">
    <param name="port" value="/dev/ttyACM0"/>
    <param name="baud" value="115200"/>
  </node>

  <node pkg="srobot" type="motor_driver.py" name="srobot_motor_driver" output="screen" respawn="true"/>
</launch>
```

### 6.2 노트북 조종용 런치 (launch/teleop.launch)

```xml
<launch>
  <node pkg="srobot" type="teleop_key.py" name="srobot_teleop" output="screen"/>
</launch>
```

---

## 7. 5단계: 네트워크 환경 설정 (노트북과 로봇 연결)

### 7.1 내 IP 확인하기
터미널에서 아래 명령어로 IP를 확인합니다:
```bash
hostname -I
```

### 7.2 환경변수 설정
- ROS_MASTER_URI: roscore가 켜져 있는 로봇의 IP를 양쪽 컴퓨터에 똑같이 적어줍니다.
- ROS_IP: 지금 명령어를 치고 있는 내 컴퓨터의 IP를 적어줍니다.

**로봇 터미널:**
```bash
export ROS_MASTER_URI=http://<로봇IP>:11311
export ROS_IP=<로봇IP>
```

**노트북 터미널:**
```bash
export ROS_MASTER_URI=http://<로봇IP>:11311
export ROS_IP=<노트북IP>
```

---

## 8. 6단계: 로봇 조종 실습하기

### [1] 빌드하기
```bash
cd ~/turtle_ws
catkin_make
source devel/setup.bash
```

### [2] 로봇에서 모터 노드 실행
```bash
roslaunch srobot robot.launch
```

### [3] 노트북에서 조종 콘솔 실행
```bash
roslaunch srobot teleop.launch
```

### [4] 키보드로 조종하기
- w: 전진
- x: 후진
- a: 좌회전
- d: 우회전
- s: 정지
- e: 속도 증가
- c: 속도 감소
- q: 종료
