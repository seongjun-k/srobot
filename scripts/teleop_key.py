#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
[학생 실습용] srobot 키보드 원격 조종 노드 (teleop_key.py)
================================================================================
- 역할: 노트북에서 w, a, s, d, x 키를 누르면 엔터(Enter) 없이 즉시 감지하여
        /srobot/key_cmd 토픽(String 메시지)으로 전송하는 퍼블리셔(Publisher) 노드입니다.
- 키 매핑:
    * w : 전진 (Forward)
    * x : 후진 (Backward)
    * a : 좌회전 (Turn Left)
    * d : 우회전 (Turn Right)
    * s : 정지 (Stop)
    * Space : 비상 정지
    * e / c : 속도 증가 / 감소
    * q : 프로그램 종료
================================================================================
"""

import sys
import tty
import termios
import rospy
from std_msgs.msg import String

# ------------------------------------------------------------------------------
# 1. 키보드 입력을 엔터 없이 한 글자 즉시 읽어오는 함수
# ------------------------------------------------------------------------------
def get_key():
    """
    터미널의 기본 설정을 임시로 변경하여(Raw 모드)
    엔터 키를 누르지 않아도 키를 누르는 즉시 1글자를 읽어옵니다.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        # 키를 읽은 후 원래 터미널 설정으로 복원
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

# ------------------------------------------------------------------------------
# 2. 메인 실행 함수
# ------------------------------------------------------------------------------
def main():
    # ROS 노드 초기화 ('srobot_teleop'이라는 이름으로 등록)
    rospy.init_node('srobot_teleop', anonymous=False)

    # 퍼블리셔 생성: '/srobot/key_cmd' 토픽으로 String 타입 메시지 발행
    key_pub = rospy.Publisher('/srobot/key_cmd', String, queue_size=10)

    # 화면에 조종 안내문 출력
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

    # 키보드 입력 및 전송 반복 루프
    while not rospy.is_shutdown():
        # 키보드에서 1글자 입력받기
        key = get_key()

        # 'q' 또는 Ctrl+C(\x03)를 누르면 정지 명령 보내고 종료
        if key == 'q' or key == '\x03':
            key_pub.publish('s')
            print("\n[안내] 조종 콘솔을 종료합니다. 로봇을 정지했습니다.")
            break

        # 스페이스바(Space)는 정지('s')로 변환
        if key == ' ':
            key = 's'

        # 유효한 조종 키인 경우 로봇으로 전송
        if key in ['w', 'a', 's', 'd', 'x', 'e', 'c']:
            key_pub.publish(key)

            # 터미널에 현재 누른 키 상태 출력
            key_names = {
                'w': '전진 (Forward)',
                'x': '후진 (Backward)',
                'a': '좌회전 (Left)',
                'd': '우회전 (Right)',
                's': '정지 (Stop)',
                'e': '속도 증가 (+)',
                'c': '속도 감소 (-)'
            }
            print(f">> 전송 명령: {key} [{key_names.get(key, '')}]")

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
