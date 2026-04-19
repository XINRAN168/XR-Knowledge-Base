#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云澜记忆系统 V3.0 Phase 5 性能基准测试框架
验证性能指标是否达到设计目标

性能目标：
- 记忆写入延迟：<100ms
- 检索响应时间：<500ms
- 并发处理能力：1000+请求
- 存储容量弹性扩展验证
"""

import json
import time
import statistics
import threading
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# 导入Phase 5集成测试框架
import sys
sys.path.append('./github/XR-Knowledge-Base/_核心配置/V3.0实施日志/Phase5_测试框架')
from Phase5_integration_test import IntegratedMemorySystem, MemoryBlock, MemoryLayer


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.system = IntegratedMemorySystem()
        self.results = {}
    
    def benchmark_write_latency(self, sample_size: int = 1000) -> Dict:
        """记忆写入延迟基准测试（目标：<100ms）"""
        print(f"\n[基准测试1] 写入延迟测试 (样本数: {sample_size})")
        
        latencies = []
        successes = 0
        failures = 0
        
        for i in range(sample_size):
            start = time.time()
            success, _, _ = self.system.write_memory(
                f"Performance test memory {i} with some random content to simulate real usage",
                memory_id=f"perf_mem_{i}"
            )
            latency = (time.time() - start) * 1000
            
            latencies.append(latency)
            if success:
                successes += 1
            else:
                failures += 1
        
        sorted_latencies = sorted(latencies)
        avg_latency = statistics.mean(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        target = 100  # ms
        meets_target = avg_latency < target
        
        result = {
            "test_name": "Write Latency",
            "target_ms": target,
            "actual_avg_ms": round(avg_latency, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "min_ms": round(min_latency, 2),
            "max_ms": round(max_latency, 2),
            "success_count": successes,
            "failure_count": failures,
            "success_rate": successes / (successes + failures) if (successes + failures) > 0 else 0,
            "meets_target": meets_target,
            "status": "✅ PASS" if meets_target else "❌ FAIL"
        }
        
        print(f"  目标: <{target}ms")
        print(f"  实际: 平均{avg_latency:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")
        print(f"  结果: {result['status']}")
        
        return result
    
    def benchmark_search_latency(self, sample_size: int = 500, queries: List[str] = None) -> Dict:
        """检索响应时间基准测试（目标：<500ms）"""
        print(f"\n[基准测试2] 检索延迟测试 (样本数: {sample_size})")
        
        # 准备测试数据
        if queries is None:
            queries = [
                "Python", "JavaScript", "人工智能", "机器学习", "云计算",
                "数据分析", "前端开发", "后端服务", "数据库", "缓存系统"
            ]
        
        # 写入测试数据
        for i in range(100):
            self.system.write_memory(
                f"Memory about {random.choice(queries)} topic {i}",
                memory_id=f"search_mem_{i}"
            )
        
        latencies = []
        successes = 0
        
        for i in range(sample_size):
            query = random.choice(queries)
            start = time.time()
            results = self.system.search_memories(query)
            latency = (time.time() - start) * 1000
            
            latencies.append(latency)
            successes += 1
        
        sorted_latencies = sorted(latencies)
        avg_latency = statistics.mean(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        target = 500  # ms
        meets_target = avg_latency < target
        
        result = {
            "test_name": "Search Latency",
            "target_ms": target,
            "actual_avg_ms": round(avg_latency, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "success_count": successes,
            "failure_count": 0,
            "success_rate": 1.0,
            "meets_target": meets_target,
            "status": "✅ PASS" if meets_target else "❌ FAIL"
        }
        
        print(f"  目标: <{target}ms")
        print(f"  实际: 平均{avg_latency:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")
        print(f"  结果: {result['status']}")
        
        return result
    
    def benchmark_concurrent_capacity(self, total_requests: int = 1000, workers: int = 50) -> Dict:
        """并发处理能力基准测试（目标：1000+请求）"""
        print(f"\n[基准测试3] 并发处理能力测试 (总请求: {total_requests}, 并发数: {workers})")
        
        results = {"success": 0, "failed": 0, "errors": []}
        latencies = []
        lock = threading.Lock()
        
        def write_task(i):
            try:
                start = time.time()
                success, _, _ = self.system.write_memory(
                    f"Concurrent test memory {i}",
                    memory_id=f"concurrent_mem_{i}"
                )
                latency = (time.time() - start) * 1000
                
                with lock:
                    latencies.append(latency)
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
            except Exception as e:
                with lock:
                    results["failed"] += 1
                    results["errors"].append(str(e))
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(write_task, i) for i in range(total_requests)]
            for future in as_completed(futures):
                pass
        
        total_time = time.time() - start_time
        
        target_requests = 1000
        target_throughput = 100  # requests/second
        actual_throughput = total_requests / total_time if total_time > 0 else 0
        meets_target = results["success"] >= target_requests and actual_throughput >= target_throughput
        
        result = {
            "test_name": "Concurrent Capacity",
            "target_requests": target_requests,
            "target_throughput": target_throughput,
            "total_requests": total_requests,
            "successful_requests": results["success"],
            "failed_requests": results["failed"],
            "success_rate": results["success"] / total_requests,
            "total_duration_sec": round(total_time, 2),
            "actual_throughput": round(actual_throughput, 2),
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0,
            "meets_target": meets_target,
            "status": "✅ PASS" if meets_target else "❌ FAIL"
        }
        
        print(f"  目标: >={target_requests}请求, >={target_throughput}请求/秒")
        print(f"  实际: {results['success']}请求成功, {actual_throughput:.2f}请求/秒")
        print(f"  结果: {result['status']}")
        
        return result
    
    def benchmark_storage_scalability(self, max_memories: int = 10000) -> Dict:
        """存储容量弹性扩展验证"""
        print(f"\n[基准测试4] 存储容量扩展测试 (目标: {max_memories}条记忆)")
        
        latencies = []
        
        for i in range(max_memories):
            start = time.time()
            success, _, _ = self.system.write_memory(
                f"Scalability test memory {i} with content for testing storage capacity",
                memory_id=f"scale_mem_{i}"
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            # 每1000条记录性能统计
            if (i + 1) % 1000 == 0:
                avg = statistics.mean(latencies[-1000:])
                print(f"    [{i+1}/{max_memories}] 平均延迟: {avg:.2f}ms")
        
        # 性能稳定性分析
        segments = 10
        segment_size = len(latencies) // segments
        segment_avgs = []
        for i in range(segments):
            start_idx = i * segment_size
            end_idx = start_idx + segment_size
            segment_avgs.append(statistics.mean(latencies[start_idx:end_idx]))
        
        # 检查性能是否随数据量增加而显著下降
        early_avg = statistics.mean(segment_avgs[:3])
        late_avg = statistics.mean(segment_avgs[-3:])
        performance_degradation = (late_avg - early_avg) / early_avg if early_avg > 0 else 0
        
        # 存储了多少记忆
        total_memories = len(self.system.history)
        
        result = {
            "test_name": "Storage Scalability",
            "target_memories": max_memories,
            "actual_memories": total_memories,
            "early_performance_ms": round(early_avg, 2),
            "late_performance_ms": round(late_avg, 2),
            "performance_degradation": round(performance_degradation * 100, 2),
            "segment_performance": [round(s, 2) for s in segment_avgs],
            "meets_target": total_memories >= max_memories and performance_degradation < 0.5,
            "status": "✅ PASS" if total_memories >= max_memories and performance_degradation < 0.5 else "❌ FAIL"
        }
        
        print(f"  目标: {max_memories}条记忆")
        print(f"  实际: {total_memories}条记忆")
        print(f"  早期性能: {early_avg:.2f}ms → 后期性能: {late_avg:.2f}ms")
        print(f"  性能衰减: {performance_degradation*100:.2f}%")
        print(f"  结果: {result['status']}")
        
        return result
    
    def run_all_benchmarks(self) -> Dict:
        """运行所有基准测试"""
        print("=" * 70)
        print("云澜记忆系统 V3.0 Phase 5 性能基准测试")
        print("=" * 70)
        
        results = {
            "test_date": datetime.now().isoformat(),
            "benchmarks": {}
        }
        
        # 1. 写入延迟测试
        results["benchmarks"]["write_latency"] = self.benchmark_write_latency(1000)
        
        # 2. 检索延迟测试
        results["benchmarks"]["search_latency"] = self.benchmark_search_latency(500)
        
        # 3. 并发处理能力测试
        results["benchmarks"]["concurrent_capacity"] = self.benchmark_concurrent_capacity(1000, 50)
        
        # 4. 存储容量扩展测试
        results["benchmarks"]["storage_scalability"] = self.benchmark_storage_scalability(10000)
        
        # 汇总
        print("\n" + "=" * 70)
        print("性能基准测试汇总")
        print("=" * 70)
        
        all_passed = True
        for name, result in results["benchmarks"].items():
            status = "✅ PASS" if result["meets_target"] else "❌ FAIL"
            if not result["meets_target"]:
                all_passed = False
            print(f"  {result['test_name']}: {status}")
        
        results["overall_result"] = "✅ 所有性能指标达标" if all_passed else "❌ 部分性能指标未达标"
        
        return results


if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # 保存结果
    output_file = "./github/XR-Knowledge-Base/_核心配置/V3.0实施日志/Phase5_性能基准测试报告.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n性能基准测试报告已保存: {output_file}")
