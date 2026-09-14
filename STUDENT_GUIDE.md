# [교육용 교재] ROS 1 로봇 원격 조종 패키지(srobot) 만들기

> **수업 목표:**  
> ROS(Robot Operating System)의 기본 원리인 **퍼블리셔(Publisher)**와 **서브스크라이버(Subscriber)**, 그리고 로봇 바퀴 제어용 **Twist 메시지**를 이해하고, 노트북 키보드로 로봇을 직접 조종하는 패키지를 내 손으로 완성합니다.  
> *(구글 문서(Google Docs)로 그대로 복사하여 학생 배포용 유인물/교재로 활용하실 수 있습니다)*

---

## 목차
1. [프로젝트 개요 및 시스템 구조](#1-프로젝트-개요-및-시스템-구조)
2. [사전 준비 (필수 패키지 설치)](#2-사전-준비-필수-패키지-설치)
3. [1단계: ROS 패키지 생성하기](#3-1단계-ros-패키지-생성하기)
4. [2단계: 노트북 조종 노드 작성 (teleop_key.py)](#4-2단계-노트북-조종-노드-작성-scripts-teleop_keypy)
5. [3단계: 로봇 모터 드라이버 노드 작성 (motor_driver.py)](#5-3단계-로봇-모터-드라이버-노드-작성-scripts-motor_driverpy)
6. [4단계: 원터치 실행 런치(Launch) 파일 만들기](#6-4단계-원터치-실행-런치launch-파일-만들기)
7. [5단계: 네트워크 환경 설정 (노트북 ↔ 로봇 연결)](#7-5단계-네트워크-환경-설정-노트북--로봇-연결)
8. [6단계: 로봇 조종 실습하기](#8-6단계-로봇-조종-실습하기)
9. [도전 과제 및 퀴즈 (스스로 해보기)](#9-도전-과제-및-퀴즈-스스로-해보기)

---

## 1. 프로젝트 개요 및 시스템 구조

### 1.1 이번 시간에 무엇을 만드나요?
- **노트북**에서 `w`, `a`, `s`, `d`, `x` 키를 누르면,
- Wi-Fi 무선 통신을 통해 **로봇**에 명령이 전달되어,
- 로봇의 바퀴 모터(다이나믹셀)가 즉시 회전하여 로봇이 주행합니다.

### 1.2 시스템 통신 구조

```
[노트북 (Laptop)]
     │
     ▼  teleop_key.py (Publisher)
     │  - 키보드 w, a, s, d, x 입력 감지
     │
     ├─▶ 토픽: /srobot/key_cmd (String 메시지) ─── [Wi-Fi 무선 네트워크] ───┐
                                                                           │
┌──────────────────────────────────────────────────────────────────────────┘
│
▼ [로봇 (Robot / Raspberry Pi)]
│
├─▶ motor_driver.py (Subscriber & Publisher)
│   - /srobot/key_cmd 수신
│   - 키를 속도(선속도, 각속도)로 변환
│
├─▶ 토픽: /cmd_vel (Twist 메시지)
│
├─▶ opencr_core (rosserial_python)
│   - OpenCR 제어 보드로 속도 전달
│
▼
[다이나믹셀 모터 (좌/우 바퀴 주행)]
```

---

## 2. 사전 준비 (필수 패키지 설치)

로봇(라즈베리파이)에서 OpenCR과 통신하기 위해 `rosserial` 패키지가 필요합니다.

```bash
# 로봇 터미널에서 실행
sudo apt update
sudo apt install -y ros-noetic-rosserial-python ros-noetic-rosserial-msgs

# 시리얼 포트 접근 권한 설정
sudo usermod -aG dialout $USER
```

---

## 3. 1단계: ROS 패키지 생성하기

터미널을 열고 catkin 워크스페이스의 `src` 폴더로 이동하여 패키지를 생성합니다.

```bash
# 1. src 폴더로 이동 (turtle_ws 또는 catkin_ws)
cd ~/turtle_ws/src

# 2. srobot 패키지 생성 (의존성: rospy, std_msgs, geometry_msgs)
catkin_create_pkg srobot rospy std_msgs geometry_msgs

# 3. 파이썬 스크립트와 런치 파일을 담을 폴더 생성
cd srobot
mkdir scripts launch
```

---

## 4. 2단계: 노트북 조종 노드 작성 (`scripts/teleop_key.py`)

노트북에서 실행될 키보드 입력 프로그램입니다.  
`scripts/teleop_key.py` 파일을 생성하고 아래 코드를 복사하여 저장합니다.

```bash
nano scripts/teleop_key.py
# (또는 gedit scripts/teleop_key.py)
```

### 소스 코드 (`teleop_key.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import tty
import termios
import rospy
from std_msgs.msg import String

# 키보드 입력을 엔터 없이 즉시 1글자 읽어오는 함수
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
    # 1. 노드 초기화
    rospy.init_node('srobot_teleop', anonymous=False)

    # 2. 퍼블리셔 생성 (/srobot/key_cmd 토픽으로 전송)
    key_pub = rospy.Publisher('/srobot/key_cmd', String, queue_size=10)

    # 3. 조종 안내 화면 출력
    print("=" * 50)
    print("           로봇 키보드 조종 콘솔 (SROBOT)         ")
    print("=" * 50)
    print("       [ w ] : 전진")
    print("  [ a ] : 좌회전      [ d ] : 우회전")
    print("       [ s ] : 정지")
    print("       [ x ] : 후진")
    print("")
    print("  [Space] : 비상 정지")
    print("  [ e / c ] : 속도 증가 / 감소")
    print("  [ q ]     : 프로그램 종료")
    print("=" * 50)
    print("▶ 키보드를 누르면 로봇이 즉시 움직입니다 (종료: q)\n")

    # 4. 반복해서 키를 읽고 토픽으로 발행
    while not rospy.is_shutdown():
        key = get_key()

        # q를 누르면 정지 명령 보내고 프로그램 종료
        if key == 'q' or key == '\x03':
            key_pub.publish('s')
            print("\n[안내] 조종 콘솔을 종료합니다.")
            break

        # 스페이스바는 정지('s')로 변환
        if key == ' ':
            key = 's'

        # 유효한 키인 경우 토픽 발행
        if key in ['w', 'a', 's', 'd', 'x', 'e', 'c']:
            key_pub.publish(key)
            print(f">> 입력 명령 전송: {key}")

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
```

### 실행 권한 부여 (필수)
파이썬 파일이 프로그램처럼 단독 실행될 수 있도록 실행 권한을 줍니다.

```bash
chmod +x scripts/teleop_key.py
```

---

## 5. 3단계: 로봇 모터 드라이버 노드 작성 (`scripts/motor_driver.py`)

로봇 측에서 키 입력을 받아 실제 모터 속도(`Twist`)로 변환해주는 노드입니다.  
`scripts/motor_driver.py` 파일을 생성하고 아래 코드를 저장합니다.

```bash
nano scripts/motor_driver.py
# (또는 gedit scripts/motor_driver.py)
```

### 소스 코드 (`motor_driver.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

# 기본 속도 설정
linear_speed = 0.15    # 기본 전진/후진 선속도 (m/s)
angular_speed = 0.75   # 기본 회전 각속도 (rad/s)

target_linear = 0.0    # 현재 바퀴로 보낼 선속도
target_angular = 0.0   # 현재 바퀴로 보낼 각속도

# 키 명령을 수신했을 때 호출되는 콜백 함수
def key_callback(msg):
    global linear_speed, angular_speed, target_linear, target_angular
    cmd = msg.data.strip()

    # 속도 증감 조절
    if cmd == 'e':
        linear_speed = min(0.30, linear_speed + 0.02)
        rospy.loginfo(f"[속도 증가] {linear_speed:.2f} m/s")
        if target_linear > 0: target_linear = linear_speed
        elif target_linear < 0: target_linear = -linear_speed
        return

    elif cmd == 'c':
        linear_speed = max(0.05, linear_speed - 0.02)
        rospy.loginfo(f"[속도 감소] {linear_speed:.2f} m/s")
        if target_linear > 0: target_linear = linear_speed
        elif target_linear < 0: target_linear = -linear_speed
        return

    # 방향 제어
    if cmd == 'w':
        target_linear = linear_speed
        target_angular = 0.0
        rospy.loginfo(f"▲ 전진 (속도: {target_linear:.2f})")

    elif cmd == 'x':
        target_linear = -linear_speed
        target_angular = 0.0
        rospy.loginfo(f"▼ 후진 (속도: {target_linear:.2f})")

    elif cmd == 'a':
        target_linear = 0.0
        target_angular = angular_speed
        rospy.loginfo(f"◀ 좌회전 (속도: {target_angular:.2f})")

    elif cmd == 'd':
        target_linear = 0.0
        target_angular = -angular_speed
        rospy.loginfo(f"▶ 우회전 (속도: {target_angular:.2f})")

    elif cmd == 's':
        target_linear = 0.0
        target_angular = 0.0
        rospy.loginfo("■ 정지")

def main():
    global target_linear, target_angular

    # 1. 노드 초기화
    rospy.init_node('srobot_motor_driver', anonymous=False)

    # 2. 퍼블리셔 (/cmd_vel) 및 서브스크라이버 (/srobot/key_cmd) 생성
    cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    rospy.Subscriber('/srobot/key_cmd', String, key_callback)

    rospy.loginfo("srobot 모터 드라이버 노드가 준비되었습니다.")

    # 3. 1초에 10번(10Hz) 주기적으로 로봇 모터에 속도 명령 전송
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

## 6. 4단계: 원터치 실행 런치(Launch) 파일 만들기

여러 노드를 일일이 터미널을 열어 켤 필요 없이, `roslaunch` 한 줄로 동시에 실행하도록 런치 파일을 만듭니다.

### 6.1 로봇용 런치 (`launch/robot.launch`)

```xml
<launch>
  <!-- 1. OpenCR 시리얼 통신 노드 -->
  <node pkg="rosserial_python" type="serial_node.py" name="opencr_core" output="screen" respawn="true">
    <param name="port" value="/dev/ttyACM0"/>
    <param name="baud" value="115200"/>
  </node>

  <!-- 2. 모터 드라이버 노드 -->
  <node pkg="srobot" type="motor_driver.py" name="srobot_motor_driver" output="screen" respawn="true"/>
</launch>
```

### 6.2 노트북 조종용 런치 (`launch/teleop.launch`)

```xml
<launch>
  <!-- 노트북 키보드 조종 노드 -->
  <node pkg="srobot" type="teleop_key.py" name="srobot_teleop" output="screen"/>
</launch>
```

---

## 7. 5단계: 네트워크 환경 설정 (노트북 ↔ 로봇 연결)

### 7.1 내 IP 확인하기
노트북과 로봇 각각 터미널에서 아래 명령을 입력하여 IP를 확인합니다.

```bash
hostname -I
```
- 예시: 로봇 IP가 `192.168.0.20`, 노트북 IP가 `192.168.0.30`인 경우

### 7.2 환경변수 설정 원리
* `ROS_MASTER_URI`: 마스터(`roscore`)가 켜져 있는 로봇의 주소 (양쪽 다 동일하게 로봇 IP 입력)
* `ROS_IP`: **지금 명령어를 입력하고 있는 내 컴퓨터의 IP**

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

### [1] 워크스페이스 빌드하기
노트북과 로봇에서 각각 빌드를 완료합니다:
```bash
cd ~/turtle_ws
catkin_make
source devel/setup.bash
```

### [2] 로봇에서 모터 노드 실행
로봇에 SSH로 접속하거나 로봇 본체 터미널에서 실행합니다:
```bash
roslaunch srobot robot.launch
```
*(OpenCR과 모터 드라이버가 연결되고 주행 대기 상태가 됩니다)*

### [3] 노트북에서 조종 콘솔 실행
노트북의 새 터미널에서 실행합니다:
```bash
roslaunch srobot teleop.launch
```

### [4] 키보드로 조종하기
- `w`: 전진
- `x`: 후진
- `a`: 좌회전 (제자리 회전)
- `d`: 우회전 (제자리 회전)
- `s` 또는 `Space`: 정지
- `e` / `c`: 주행 중 선속도 증가 / 감소
- `q`: 조종 종료

---

## 9. 도전 과제 및 퀴즈 (스스로 해보기)

### 퀴즈 1. 로봇의 기본 전진 속도를 더 빠르게 바꾸려면?
`scripts/motor_driver.py` 파일에서 어떤 변수를 수정해야 할까요?
> **힌트:** `linear_speed = 0.15` 값을 `0.20` 또는 `0.25`로 변경해보세요!

### 퀴즈 2. 후진할 때 선속도(`linear.x`)는 왜 음수(`-`)일까요?
> **해설:** ROS 좌표계(REP-103) 표준에서 x축의 양(+)의 방향은 로봇 앞쪽(전진), 음(-)의 방향은 로봇 뒤쪽(후진)을 의미합니다.

### 도전 과제. 대각선 주행 키(`q`, `e`) 만들어보기!
앞으로 가면서 동시에 좌회전하거나 우회전하는 곡선 주행을 추가하려면 `teleop_key.py`와 `motor_driver.py`에 어떤 코드를 추가해야 할까요?
> **힌트:** `twist.linear.x`와 `twist.angular.z`에 동시에 0이 아닌 값을 넣어주면 곡선으로 부드럽게 회전합니다!
