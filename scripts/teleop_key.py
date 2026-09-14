#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
srobot - teleop_key.py
────────────────────────────────────────────────────────────────────────
노트북용 실시간 키보드 텔레옵 퍼블리셔
- 키보드 입력을 엔터(Enter) 없이 즉각 감지하여 로봇으로 전송
- 키 매핑:
    w : 전진 (Forward)
    a : 좌회전 (Turn Left)
    s : 정지 (Stop)
    d : 우회전 (Turn Right)
    x : 후진 (Backward)
    space : 비상 정지 (Emergency Stop)
    e / c : 선속도 증가 / 감소 (+0.02 / -0.02 m/s)
    r / v : 각속도 증가 / 감소 (+0.1 / -0.1 rad/s)
    q : 종료 (Quit)
────────────────────────────────────────────────────────────────────────
"""

import sys
import select
import tty
import termios
import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

BANNER = """
======================================================
            SROBOT TELEOPERATION CONSOLE              
======================================================
                  [ w ] : 전진 (Forward)
   [ a ] : 좌회전               [ d ] : 우회전
                  [ s ] : 정지 (Stop)
                  [ x ] : 후진 (Backward)

   [Space] : 비상 정지 (Emergency Stop)
   [ e / c ] : 선속도 증가 / 감소 (+- 0.02 m/s)
   [ r / v ] : 각속도 증가 / 감소 (+- 0.10 rad/s)
   [ q ]     : 프로그램 종료 (Quit)
======================================================
"""

class KeyReader:
    def __init__(self):
        self.settings = termios.tcgetattr(sys.stdin)

    def get_key(self, timeout=0.1):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
            # Handle escape sequences for arrow keys if needed
            if key == '\x1b':
                extra = sys.stdin.read(2)
                if extra == '[A': key = 'w'
                elif extra == '[B': key = 'x'
                elif extra == '[C': key = 'd'
                elif extra == '[D': key = 'a'
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def restore(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)


def main():
    rospy.init_node('srobot_teleop', anonymous=False)

    key_topic = rospy.get_param('~key_topic', '/srobot/key_cmd')
    pub_key = rospy.Publisher(key_topic, String, queue_size=10)

    # 기본 속도 파라미터
    linear_speed = rospy.get_param('~linear_speed', 0.15)
    angular_speed = rospy.get_param('~angular_speed', 0.75)

    reader = KeyReader()
    print(BANNER)
    print(f"[*] 퍼블리시 토픽: {key_topic}")
    print(f"[*] 초기 설정 - 선속도: {linear_speed:.2f} m/s | 각속도: {angular_speed:.2f} rad/s\n")
    print("▶ 키를 누르면 로봇이 즉시 반응합니다...\n")

    current_state = "정지 (STOP)"

    try:
        while not rospy.is_shutdown():
            key = reader.get_key(timeout=0.05)

            if not key:
                continue

            # 종료
            if key == 'q' or key == '\x03': # q or Ctrl+C
                pub_key.publish("s")
                print("\n\n[!] 텔레옵 콘솔을 종료합니다. 로봇을 정지했습니다.")
                break

            # 이동 명령
            elif key in ['w', 'a', 's', 'd', 'x']:
                pub_key.publish(key)
                state_map = {
                    'w': "전진 ▲ (FORWARD)",
                    'a': "좌회전 ◀ (LEFT)",
                    's': "정지 ■ (STOP)",
                    'd': "우회전 ▶ (RIGHT)",
                    'x': "후진 ▼ (BACKWARD)"
                }
                current_state = state_map.get(key, "알 수 없음")
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s | 각속도: {angular_speed:.2f} rad/s   ")
                sys.stdout.flush()

            # 스페이스바: 비상 정지
            elif key == ' ':
                pub_key.publish("s")
                current_state = "비상 정지 ■■ (EMERGENCY STOP)"
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s | 각속도: {angular_speed:.2f} rad/s   ")
                sys.stdout.flush()

            # 속도 조절 (동작 중 실시간 가감속)
            elif key == 'e':
                linear_speed = min(0.30, linear_speed + 0.02)
                pub_key.publish(f"speed:{linear_speed:.2f}:{angular_speed:.2f}")
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s (+0.02) | 각속도: {angular_speed:.2f} rad/s   ")
                sys.stdout.flush()
            elif key == 'c':
                linear_speed = max(0.03, linear_speed - 0.02)
                pub_key.publish(f"speed:{linear_speed:.2f}:{angular_speed:.2f}")
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s (-0.02) | 각속도: {angular_speed:.2f} rad/s   ")
                sys.stdout.flush()
            elif key == 'r':
                angular_speed = min(2.0, angular_speed + 0.10)
                pub_key.publish(f"speed:{linear_speed:.2f}:{angular_speed:.2f}")
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s | 각속도: {angular_speed:.2f} rad/s (+0.10)   ")
                sys.stdout.flush()
            elif key == 'v':
                angular_speed = max(0.10, angular_speed - 0.10)
                pub_key.publish(f"speed:{linear_speed:.2f}:{angular_speed:.2f}")
                sys.stdout.write(f"\r[상태] {current_state:<20} | 선속도: {linear_speed:.2f} m/s | 각속도: {angular_speed:.2f} rad/s (-0.10)   ")
                sys.stdout.flush()

    except Exception as e:
        rospy.logerr(f"오류 발생: {e}")
    finally:
        reader.restore()
        # 종료 시 안전 정지
        try:
            pub_key.publish("s")
        except:
            pass


if __name__ == '__main__':
    main()
