#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
srobot - motor_driver.py
────────────────────────────────────────────────────────────────────────
로봇용 모터 구동 서브스크라이버 노드
- /srobot/key_cmd (String) 토픽 수신
- 키 입력(w, a, s, d, x, s)에 대응하여 /cmd_vel (Twist)로 변환 발행
- OpenCR(rosserial)을 통해 좌/우 다이나믹셀(XL430) 구동
- 안전 기능:
    * 's' 수신 시 즉시 정지
    * 노드 종료(SIGINT / ROS shutdown) 시 안전 정지(/cmd_vel = 0)
    * 통신 두절 시 자동 안전 정지 (timeout fail-safe)
────────────────────────────────────────────────────────────────────────
"""

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class SrobotMotorDriver:
    def __init__(self):
        rospy.init_node('srobot_motor_driver', anonymous=False)

        # 파라미터 로드
        self.linear_speed = rospy.get_param('~linear_speed', 0.15)
        self.angular_speed = rospy.get_param('~angular_speed', 0.75)
        self.cmd_timeout = rospy.get_param('~cmd_timeout', 0.0) # 0.0: 무제한 지속, >0: N초 후 자동 정지
        self.publish_rate = rospy.get_param('~publish_rate', 20) # 20Hz 지속 발행

        # 현재 목표 속도
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.last_cmd_time = rospy.Time.now()

        # 퍼블리셔 & 서브스크라이버
        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.key_sub = rospy.Subscriber('/srobot/key_cmd', String, self.key_callback, queue_size=10)

        rospy.on_shutdown(self.shutdown_hook)

        rospy.loginfo("==============================================")
        rospy.loginfo("  [SRobot Motor Driver Node Started]         ")
        rospy.loginfo(f"  * 기본 선속도: {self.linear_speed:.2f} m/s")
        rospy.loginfo(f"  * 기본 각속도: {self.angular_speed:.2f} rad/s")
        rospy.loginfo(f"  * 명령 타임아웃: {self.cmd_timeout:.1f}s")
        rospy.loginfo("==============================================")

    def key_callback(self, msg: String):
        key = msg.data.strip()
        self.last_cmd_time = rospy.Time.now()

        # 속도 변경 프로토콜 (speed:0.15:0.75)
        if key.startswith("speed:"):
            try:
                parts = key.split(":")
                self.linear_speed = float(parts[1])
                self.angular_speed = float(parts[2])
                rospy.loginfo(f"[설정 변경] 선속도: {self.linear_speed:.2f} m/s, 각속도: {self.angular_speed:.2f} rad/s")
                return
            except Exception as e:
                rospy.logwarn(f"속도 파싱 실패: {e}")
                return

        # WASDX 매핑
        if key == 'w':
            self.target_linear = self.linear_speed
            self.target_angular = 0.0
            rospy.loginfo(f"[주행] 전진 ▲ (선속도: {self.target_linear:.2f})")

        elif key == 'x':
            self.target_linear = -self.linear_speed
            self.target_angular = 0.0
            rospy.loginfo(f"[주행] 후진 ▼ (선속도: {self.target_linear:.2f})")

        elif key == 'a':
            self.target_linear = 0.0
            self.target_angular = self.angular_speed
            rospy.loginfo(f"[주행] 좌회전 ◀ (각속도: {self.target_angular:.2f})")

        elif key == 'd':
            self.target_linear = 0.0
            self.target_angular = -self.angular_speed
            rospy.loginfo(f"[주행] 우회전 ▶ (각속도: {self.target_angular:.2f})")

        elif key == 's':
            self.target_linear = 0.0
            self.target_angular = 0.0
            rospy.loginfo("[주행] 정지 ■")

        else:
            rospy.logwarn(f"알 수 없는 키 입력: {key}")

    def run(self):
        rate = rospy.Rate(self.publish_rate)

        while not rospy.is_shutdown():
            now = rospy.Time.now()

            # 타임아웃 활성화 상태이고 시간이 초과된 경우 자동 정지
            if self.cmd_timeout > 0:
                if (now - self.last_cmd_time).to_sec() > self.cmd_timeout:
                    if self.target_linear != 0.0 or self.target_angular != 0.0:
                        rospy.logwarn("[Fail-safe] 통신 타임아웃으로 로봇을 정지합니다.")
                        self.target_linear = 0.0
                        self.target_angular = 0.0

            twist = Twist()
            twist.linear.x = self.target_linear
            twist.angular.z = self.target_angular

            self.cmd_pub.publish(twist)
            rate.sleep()

    def shutdown_hook(self):
        rospy.loginfo("[종료] 모터 안전 정지 중...")
        stop_twist = Twist()
        for _ in range(5):
            self.cmd_pub.publish(stop_twist)
            rospy.sleep(0.05)
        rospy.loginfo("[종료] 다이나믹셀 정지 완료.")


if __name__ == '__main__':
    try:
        driver = SrobotMotorDriver()
        driver.run()
    except rospy.ROSInterruptException:
        pass
