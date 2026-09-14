#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
[학생 실습용] srobot 모터 드라이버 노드 (motor_driver.py)
================================================================================
- 역할: 노트북의 텔레옵 노드가 보낸 키 명령(/srobot/key_cmd)을 수신(Subscribe)하여
        로봇 바퀴 모터가 이해하는 속도 명령(/cmd_vel, Twist)으로 변환해 발행(Publish)합니다.
================================================================================
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

# 전역 변수 설정 (기본 속도 및 현재 목표 속도)
linear_speed = 0.15    # 기본 전진/후진 선속도 (단위: m/s)
angular_speed = 0.75   # 기본 회전 각속도 (단위: rad/s)

target_linear = 0.0    # 현재 바퀴로 보낼 선속도
target_angular = 0.0   # 현재 바퀴로 보낼 각속도

# ------------------------------------------------------------------------------
# 1. 키 명령을 수신했을 때 실행되는 콜백 함수
# ------------------------------------------------------------------------------
def key_callback(msg):
    global linear_speed, angular_speed, target_linear, target_angular
    cmd = msg.data.strip()

    # [속도 조절]
    if cmd == 'e':
        linear_speed = min(0.30, linear_speed + 0.02)
        rospy.loginfo(f"[속도 증가] 선속도: {linear_speed:.2f} m/s")
        # 현재 주행 중이라면 변경된 속도 즉시 반영
        if target_linear > 0:
            target_linear = linear_speed
        elif target_linear < 0:
            target_linear = -linear_speed
        return

    elif cmd == 'c':
        linear_speed = max(0.05, linear_speed - 0.02)
        rospy.loginfo(f"[속도 감소] 선속도: {linear_speed:.2f} m/s")
        if target_linear > 0:
            target_linear = linear_speed
        elif target_linear < 0:
            target_linear = -linear_speed
        return

    # [방향 제어]
    if cmd == 'w':
        target_linear = linear_speed
        target_angular = 0.0
        rospy.loginfo(f"▲ 전진 (선속도: {target_linear:.2f} m/s)")

    elif cmd == 'x':
        target_linear = -linear_speed
        target_angular = 0.0
        rospy.loginfo(f"▼ 후진 (선속도: {target_linear:.2f} m/s)")

    elif cmd == 'a':
        target_linear = 0.0
        target_angular = angular_speed
        rospy.loginfo(f"◀ 좌회전 (각속도: {target_angular:.2f} rad/s)")

    elif cmd == 'd':
        target_linear = 0.0
        target_angular = -angular_speed
        rospy.loginfo(f"▶ 우회전 (각속도: {target_angular:.2f} rad/s)")

    elif cmd == 's':
        target_linear = 0.0
        target_angular = 0.0
        rospy.loginfo("■ 정지")

# ------------------------------------------------------------------------------
# 2. 메인 실행 함수
# ------------------------------------------------------------------------------
def main():
    global target_linear, target_angular

    # 1. ROS 노드 초기화 ('srobot_motor_driver')
    rospy.init_node('srobot_motor_driver', anonymous=False)

    # 2. OpenCR 모터 제어 퍼블리셔 생성 (/cmd_vel 토픽)
    cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

    # 3. 노트북의 키 명령 서브스크라이버 생성 (/srobot/key_cmd 토픽)
    rospy.Subscriber('/srobot/key_cmd', String, key_callback)

    rospy.loginfo("==========================================")
    rospy.loginfo(" SRobot 모터 드라이버가 시작되었습니다. ")
    rospy.loginfo(f" * 기본 선속도: {linear_speed:.2f} m/s")
    rospy.loginfo(f" * 기본 각속도: {angular_speed:.2f} rad/s")
    rospy.loginfo("==========================================")

    # 4. OpenCR 보드로 주기적으로 속도 명령 전송 (초당 10회 = 10Hz)
    rate = rospy.Rate(10)

    while not rospy.is_shutdown():
        # Twist 메시지 생성 및 목표 속도 대입
        twist = Twist()
        twist.linear.x = target_linear
        twist.angular.z = target_angular

        # 모터 토픽으로 발행
        cmd_pub.publish(twist)
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
