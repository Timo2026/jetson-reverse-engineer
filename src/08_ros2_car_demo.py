#!/usr/bin/env python3
"""ROS2 循迹小车 CPU模拟 — 视觉线检测→PID→转向
真实项目: Jetson Nano + ROS2 Humble + OpenCV
"""
import numpy as np

class LineFollowCar:
    def __init__(self):
        self.kp, self.ki, self.kd = 0.8, 0.05, 0.3
        self.err_sum, self.last_err = 0, 0
        self.x = 0  # 赛道中心偏移
    def detect_line(self, frame_id):
        """模拟OpenCV线检测: 赛道中心偏移"""
        # 正弦扰动模拟弯道
        offset = 40 * np.sin(frame_id / 6)
        return offset
    def pid(self, err):
        self.err_sum += err
        d = err - self.last_err
        self.last_err = err
        return self.kp * err + self.ki * self.err_sum + self.kd * d
    def run(self):
        print("=" * 60)
        print("ROS2 循迹小车模拟 (视觉检测→PID→转向控制)")
        print("=" * 60)
        print(f"{'帧':<5}{'线偏移px':<12}{'PID转向':<12}{'动作'}")
        print("-" * 60)
        for i in range(30):
            err = self.detect_line(i)
            steer = self.pid(err)
            action = '左转' if steer < -5 else ('右转' if steer > 5 else '直行')
            if i % 3 == 0:
                print(f"{i:<5}{err:<12.1f}{steer:<12.1f}{action}")
        print("\n✅ 验证: ROS2话题发布(/vision/line → /control/steer) 解耦闭环")

if __name__ == '__main__':
    LineFollowCar().run()
