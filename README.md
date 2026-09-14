# srobot (SRobot Teleop & Direct Motor Control)

> **경량 로봇 텔레옵 및 OpenCR 다이나믹셀 직접 제어 ROS 1 Noetic 패키지**  
> 복잡하고 무거운 전체 브링업(LiDAR, 카메라, 진단 노드 등)을 일일이 실행할 필요 없이, **단 하나의 런치 명령**으로 다이나믹셀 모터를 구동하고 노트북에서 실시간 키보드로 주행을 제어합니다.

---

## 주요 특징 (Key Features)

1. **원터치 브링업 & 모터 제어 통합 (`robot.launch`)**
   - 로봇 측에서 라이다나 카메라 등 불필요한 노드를 띄울 필요 없이, OpenCR 통신(`rosserial`)과 모터 서브스크라이버를 단일 프로세스로 구동합니다.
2. **엔터(Enter) 없는 즉각적인 실시간 키보드 입력 (`teleop.launch`)**
   - 표준 `input()` 기반 입력 방식의 불편함을 해결하고, Linux Raw Terminal(termios)을 통해 키를 누르는 즉시 로봇이 반응합니다.
3. **직관적인 WASDX 키 매핑 & 속도 미세 조절**
   - `w`(전진), `a`(좌회전), `s`(정지), `d`(우회전), `x`(후진)
   - `Space`(비상 정지)
   - `e`/`c`(선속도 증가/감소), `r`/`v`(각속도 증가/감소)
4. **안전 기능 (Fail-Safe)**
   - 통신 단절 시 자동 정지(타임아웃 설정 지원)
   - 노드 종료(Ctrl+C) 시 모터 즉각 정지 명령 전송으로 폭주 방지
5. **(선택 사항) 로봇 부팅 시 자동 시작 (systemd service)**
   - 서비스 등록 시 로봇에 SSH 접속조차 할 필요 없이 로봇 전원만 켜면 대기 상태로 진입합니다.

---

## 시스템 아키텍처 (Architecture)

```mermaid
flowchart LR
    subgraph Laptop ["노트북 (Laptop)"]
        Teleop["teleop_key.py\n(Keyboard Publisher)"]
    end

    subgraph Robot ["로봇 (Robot / Raspberry Pi)"]
        Driver["motor_driver.py\n(Motor Subscriber)"]
        OpenCR_Node["opencr_core\n(rosserial_python)"]
        OpenCR_Board["OpenCR 1.0\n(Firmware)"]
        Dxl1["Dynamixel ID 1\n(Left Wheel)"]
        Dxl2["Dynamixel ID 2\n(Right Wheel)"]
    end

    Teleop -->|/srobot/key_cmd (String)| Driver
    Driver -->|/cmd_vel (Twist)| OpenCR_Node
    OpenCR_Node -->|/dev/ttyACM0 (115200)| OpenCR_Board
    OpenCR_Board --> Dxl1
    OpenCR_Board --> Dxl2
```

---

## 키보드 조작 가이드 (Controls)

| 키 | 동작 (Action) | 설명 |
|:---:|:---|:---|
| **`w`** | 전진 (Forward) | 설정된 선속도로 전진 |
| **`x`** | 후진 (Backward) | 설정된 선속도로 후진 |
| **`a`** | 좌회전 (Turn Left) | 제자리 좌회전 |
| **`d`** | 우회전 (Turn Right) | 제자리 우회전 |
| **`s`** | 정지 (Stop) | 주행 즉시 정지 |
| **`Space`** | 비상 정지 (Emergency Stop) | 속도 0으로 강제 리셋 |
| **`e` / `c`** | 선속도 증가 / 감소 | ± 0.02 m/s (기본: 0.15 m/s) |
| **`r` / `v`** | 각속도 증가 / 감소 | ± 0.10 rad/s (기본: 0.75 rad/s) |
| **`q`** | 프로그램 종료 (Quit) | 로봇 정지 후 안전 종료 |

---

## 빠른 시작 (Quick Start)

### 1. 패키지 빌드 (Build)

노트북과 로봇의 catkin 워크스페이스에 각각 빌드합니다.

```bash
cd ~/turtle_ws/src     # 또는 ~/catkin_ws/src
git clone https://github.com/seongjun-k/srobot.git
cd ~/turtle_ws
catkin_make
source devel/setup.bash
```

### 2. ROS 네트워크 환경 설정 (Multi-Machine Network)

같은 네트워크에 연결된 상태에서 IP를 지정합니다.

**로봇 (Robot):**
```bash
export ROS_MASTER_URI=http://<ROBOT_IP>:11311
export ROS_IP=<ROBOT_IP>
```

**노트북 (Laptop):**
```bash
export ROS_MASTER_URI=http://<ROBOT_IP>:11311
export ROS_IP=<LAPTOP_IP>
```

> **참고:** Tailscale 또는 VPN 환경인 경우 각 노드의 가상 IP를 사용하셔도 동일하게 동작합니다.

---

### 3. 실행 방법 (Run)

#### [Step 1] 로봇에서 실행 (Robot)
SSH 접속 후 아래 단 한 줄만 실행합니다:
```bash
roslaunch srobot robot.launch
```
*(OpenCR 연결과 모터 서브스크라이버가 동시에 시작됩니다)*

#### [Step 2] 노트북에서 실행 (Laptop)

**방법 A. 간편 원클릭 실행 (내 IP 자동 감지):**
```bash
cd ~/turtle_ws/src/srobot
./run_teleop.sh [로봇IP]
```
> 노트북의 현재 IP를 자동으로 감지하여 `ROS_IP`를 설정하므로 `.bashrc`를 일일이 수정할 필요가 없습니다. (로봇 IP 생략 시 기본값 사용)

**방법 B. 일반 roslaunch 실행:**
```bash
roslaunch srobot teleop.launch
# 또는
rosrun srobot teleop_key.py
```
이제 터미널에서 `w`, `a`, `s`, `d`, `x`를 눌러 로봇을 자유롭게 조종할 수 있습니다.

---

## (고급) 로봇 부팅 시 완전 자동 실행 (Systemd Auto-Start)

로봇에 SSH로 접속하는 것조차 건너뛰고 싶다면, 로봇에서 서비스를 등록할 수 있습니다.

```bash
# 로봇에서 실행
sudo cp $(rospack find srobot)/service/srobot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable srobot.service
sudo systemctl start srobot.service
```
이제 로봇 전원만 켜면 백그라운드에서 자동으로 `srobot`이 구동되므로, **노트북에서 `roslaunch srobot teleop.launch`만 켜면 즉시 주행**이 가능합니다.

---

## 라이선스 (License)
MIT License - seongjun-k
