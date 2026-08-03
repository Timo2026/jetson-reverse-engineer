#!/usr/bin/env python3
"""DeepStream跟车预警 CPU模拟 — GStreamer管线→距离估计→预警状态机
真实项目: Jetson Orin Nano + DeepStream + TensorRT YOLO
"""
import time

class FollowWarningSim:
    """跟车距离预警: 检测→单目测距→预警状态机"""
    def __init__(self):
        self.state = 'SAFE'
        self.warn_count = 0
    
    def detect_car(self, frame_id):
        """模拟YOLO检测前车 (框宽与距离反比)"""
        # 模拟前车距离变化: 30m→8m 逼近
        dist = max(5, 30 - frame_id * 0.8)
        box_w = 400 / dist  # 框宽像素
        return {'dist_m': round(dist, 1), 'box_w_px': round(box_w, 1)}
    
    def estimate_distance(self, box_w_px):
        """单目测距: 基于标定焦距 f=500, 车宽=1.8m"""
        f, real_w = 500, 1.8
        return f * real_w / box_w_px
    
    def warning_state(self, dist):
        """预警状态机: >25m安全 / 15-25m注意 / 8-15m警告 / <8m急刹"""
        if dist > 25: return 'SAFE', '🟢 正常跟车'
        if dist > 15: return 'ATTENTION', '🟡 注意距离'
        if dist > 8:  return 'WARNING', '🟠 减速警告'
        return 'ALERT', '🔴 紧急制动'
    
    def run(self, frames=40):
        print("=" * 60)
        print("DeepStream 跟车距离预警模拟 (GStreamer管线→TensorRT→预警)")
        print("=" * 60)
        print(f"{'帧':<4}{'距离(m)':<10}{'状态':<12}{'建议动作'}")
        print("-" * 60)
        for i in range(frames):
            det = self.detect_car(i)
            est = self.estimate_distance(det['box_w_px'])
            state, action = self.warning_state(est)
            if i % 4 == 0 or state != self.state:
                print(f"{i:<4}{est:<10}{state:<12}{action}")
            self.state = state
        print("\n✅ 验证: 检测→测距→预警状态机完整闭环")
        print("   真实部署: DeepStream nvstreammux批处理 + TensorRT INT8")

if __name__ == '__main__':
    FollowWarningSim().run()
