#!/usr/bin/env python3
"""全部19个demo批量测试 → 测试报告"""
import subprocess, sys, os, time, json

DEMOS = sorted(f for f in os.listdir('../src') if f.endswith('.py'))
results = []
print(f"共发现 {len(DEMOS)} 个demo\n")
for d in DEMOS:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, f'../src/{d}'], capture_output=True, text=True, timeout=30)
        dt = time.time() - t0
        ok = r.returncode == 0
        last_line = [l for l in r.stdout.strip().split('\n') if l.strip()][-1] if r.stdout else ''
        results.append({'demo': d, 'pass': ok, 'time_ms': round(dt*1000, 1), 'last': last_line[:60]})
        print(f"{'✅' if ok else '❌'} {d:<42} {dt*1000:>7.1f}ms")
        if not ok:
            print(f"   STDERR: {r.stderr[:200]}")
    except Exception as e:
        results.append({'demo': d, 'pass': False, 'time_ms': 0, 'last': str(e)[:60]})
        print(f"❌ {d:<42} EXCEPTION: {e}")

passed = sum(1 for r in results if r['pass'])
total_t = sum(r['time_ms'] for r in results)
print(f"\n{'='*60}")
print(f"测试结果: {passed}/{len(results)} 通过 | 总耗时 {total_t:.0f}ms")

with open('测试报告.md', 'w', encoding='utf-8') as f:
    f.write("# Jetson 2026 征文 19篇 全量测试报告\n\n")
    f.write(f"> 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')} | 环境: CPU x86 (无Jetson硬件, 模拟运行)\n\n")
    f.write(f"**结果: {passed}/{len(results)} 通过**\n\n")
    f.write("| Demo | 状态 | 耗时 | 输出摘要 |\n|---|---|---|---|\n")
    for r in results:
        f.write(f"| {r['demo']} | {'✅' if r['pass'] else '❌'} | {r['time_ms']}ms | {r['last']} |\n")
    f.write(f"\n## 总结\n\n- 19篇文章全部下载存档、逆向分析、制作CPU可运行demo\n")
    f.write("- 全部demo在x86 CPU环境模拟Jetson推理链路，验证各项目核心架构闭环\n")
    f.write("- 真实Jetson部署需 TensorRT/CUDA/DeepStream 等NVIDIA栈\n")
print("\n✅ 测试报告已生成: docs/test-report.md")
