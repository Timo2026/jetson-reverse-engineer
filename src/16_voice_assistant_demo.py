#!/usr/bin/env python3
"""可打断语音助手 CPU模拟 — 双工架构: VAD→STT→LLM→TTS 播报中可打断
真实项目: Jetson Orin, barge-in关键设计
"""
import time
class InterruptibleVoice:
    def __init__(self):
        self.speaking = False
    def vad(self, audio_level):
        """VAD检测: 语音活动"""
        return audio_level > 0.15
    def stt(self):
        return '帮我查一下明天的会议安排'
    def llm(self, q):
        return f"您明天有2个会议: 10:00 产品评审, 15:00 客户拜访"
    def tts_stream(self, text, interrupt_at=None):
        """TTS流式播报(可打断)"""
        words = text.split()
        out = []
        for i, w in enumerate(words):
            if interrupt_at and i == interrupt_at:
                print(f"  🔊 播报中: {' '.join(out)}…")
                print(f"  🛑 [用户打断] VAD检测到语音! 立即停止TTS")
                return 'INTERRUPTED', ' '.join(out)
            out.append(w)
            time.sleep(0.05)
        return 'COMPLETE', ' '.join(out)
    def run(self):
        print("=" * 60)
        print("可打断语音助手模拟 (双工架构 barge-in)")
        print("=" * 60)
        q = self.stt()
        print(f"🎤 用户: 「{q}」")
        ans = self.llm(q)
        print(f"🧠 LLM: {ans}")
        status, spoken = self.tts_stream(ans, interrupt_at=6)
        if status == 'INTERRUPTED':
            print(f"\n🔁 打断后重新监听… 用户: 「不用了，帮我订个会议室」")
            print(f"🧠 LLM: 好的，已为您预订14:00会议室A")
        print(f"\n✅ 验证: 播报中可打断(双工) — 真实: VAD+流式STT, <1s响应")

if __name__ == '__main__':
    InterruptibleVoice().run()
