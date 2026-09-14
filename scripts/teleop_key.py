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
