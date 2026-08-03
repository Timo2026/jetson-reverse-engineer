#!/usr/bin/env python3
"""驾驶员行为监测 CPU模拟 — MediaPipe姿态→疲劳/分心判定→告警
真实项目: Orin Nano + MediaPipe Pose + YOLO
"""
class DriverMonitor:
    def __init__(self):
        self.ear_threshold = 0.25  # 眼睛纵横比阈值
        self.blink_count = 0
        self.fatigue = 0
    def pose_landmarks(self, frame_id):
        """MediaPipe姿态: 模拟眼睛EAR和头部角度"""
        ear = 0.30 - frame_id * 0.004  # 逐渐疲劳
        head_pitch = 5 + frame_id * 0.5  # 低头
        return {'ear': max(ear, 0.12), 'head_pitch': head_pitch, 'looking': '前方' if head_pitch < 25 else '低头/分心'}
    def detect(self, lm):
        """行为判定"""
        events = []
        if lm['ear'] < self.ear_threshold:
            self.blink_count += 1
            if self.blink_count > 15: events.append('⚠️ 眼睛闭合过长-疑似疲劳')
        if lm['head_pitch'] > 25: events.append('⚠️ 长时间低头-分心驾驶')
        if lm['looking'] == '前方' and not events: events.append('✅ 正常驾驶')
        return events
    def run(self):
        print("=" * 60)
        print("驾驶员行为监测模拟 (MediaPipe姿态→疲劳/分心判定)")
        print("=" * 60)
        for i in range(0, 40, 5):
            lm = self.pose_landmarks(i)
            ev = self.detect(lm)
            print(f"帧{i:<4} EAR={lm['ear']:.2f} 低头{lm['head_pitch']:.0f}° → {ev[0]}")
        print("\n✅ 验证: 关键点→行为规则→告警 闭环 (真实: MediaPipe轻量实时)")

if __name__ == '__main__':
    DriverMonitor().run()
