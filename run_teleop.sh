#!/bin/bash

# ==============================================================================
# SRobot Teleop One-Click Runner with Auto IP Detection
# ==============================================================================
# 이 스크립트는 노트북의 현재 IP를 자동으로 감지하여 ROS_IP를 설정하므로,
# 다른 사용자가 .bashrc를 일일이 수정하지 않아도 바로 로봇과 연결됩니다.
#
# 사용법:
#   ./run_teleop.sh                 # 대화형으로 IP 입력 또는 ROS_MASTER_URI 사용
#   ./run_teleop.sh <ROBOT_IP>      # 특정 로봇 IP 지정 (예: ./run_teleop.sh 192.168.0.50)
# ==============================================================================

# 1. 로봇 IP 설정
if [ -n "$1" ]; then
    TARGET_ROBOT_IP="$1"
elif [ -n "$ROS_MASTER_URI" ] && [ "$ROS_MASTER_URI" != "http://localhost:11311" ] && [ "$ROS_MASTER_URI" != "http://127.0.0.1:11311" ]; then
    TARGET_ROBOT_IP="$ROS_MASTER_URI"
else
    echo "======================================================"
    echo "  SRobot Teleop Launcher"
    echo "======================================================"
    echo "사용법: $0 <로봇_IP>"
    echo "  예시: $0 192.168.0.50"
    echo ""
    echo "또는 환경변수 ROS_MASTER_URI가 설정되어 있어야 합니다."
    echo "======================================================"
    read -r -p "연결할 로봇의 IP 주소를 입력하세요 (기본값: localhost): " INPUT_IP
    if [ -n "$INPUT_IP" ]; then
        TARGET_ROBOT_IP="$INPUT_IP"
    else
        TARGET_ROBOT_IP="127.0.0.1"
    fi
fi

# http:// 및 포트 번호 제거하여 순수 IP만 추출
TARGET_ROBOT_IP=$(echo "$TARGET_ROBOT_IP" | sed -e 's|^[^/]*//||' -e 's|:.*$||')

# 2. 내 노트북 IP 자동 감지 (첫 번째 유효한 IPv4 주소)
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

if [ -z "$MY_IP" ]; then
    echo "[경고] 유효한 네트워크 IP를 찾을 수 없어 127.0.0.1로 설정합니다."
    MY_IP="127.0.0.1"
fi

echo "======================================================"
echo "          SRobot Teleop Launcher (Auto Network)       "
echo "======================================================"
echo "[*] 로봇 IP (Master) : $TARGET_ROBOT_IP"
echo "[*] 내 노트북 IP     : $MY_IP (자동 감지됨)"
echo "======================================================"

# 3. ROS 환경변수 설정
export ROS_MASTER_URI="http://${TARGET_ROBOT_IP}:11311"
export ROS_IP="${MY_IP}"

# 4. 워크스페이스 setup.bash 로드 (현재 위치 기준 또는 기본 경로)
if [ -f "$(dirname "$0")/../../devel/setup.bash" ]; then
    source "$(dirname "$0")/../../devel/setup.bash"
elif [ -f "$HOME/turtle_ws/devel/setup.bash" ]; then
    source "$HOME/turtle_ws/devel/setup.bash"
elif [ -f "$HOME/catkin_ws/devel/setup.bash" ]; then
    source "$HOME/catkin_ws/devel/setup.bash"
else
    source /opt/ros/noetic/setup.bash
fi

# 5. 텔레옵 콘솔 실행
roslaunch srobot teleop.launch
