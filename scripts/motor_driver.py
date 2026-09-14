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
