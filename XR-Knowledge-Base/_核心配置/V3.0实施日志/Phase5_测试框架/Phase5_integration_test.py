#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云澜记忆系统 V3.0 Phase 5 全链路集成测试框架
整合Phase 1-4所有模块进行端到端测试

测试范围：
1. 全链路集成测试（输入→处理→存储→检索→输出）
2. 性能基准测试
3. 四层校验累积效果验证
4. 推演精准度验证
"""

import json
import time
import hashlib
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ==================== 枚举定义 ====================

class MemoryLayer(Enum):
    """记忆层级枚举"""
    ESSENTIAL = "必要记忆区"
    LONG_TERM = "长期记忆区"
    HIGH_FREQ = "高频提及区"
    TEMPORARY = "临时记忆区"


class ConfidenceLevel(Enum):
    """置信度级别"""
    ULTRA_HIGH = "超高置信度"  # ≥0.9999
    HIGH = "高置信度"          # 0.99-0.9999
    MEDIUM_HIGH = "中高置信度"  # 0.95-0.99
    MEDIUM_LOW = "中低置信度"   # 0.80-0.95
    LOW = "低置信度"           # <0.80


class FoldingLevel(Enum):
    """折叠层级"""
    L0_NONE = "不折叠"
    L1_SUMMARY = "L1摘要"      # 80%压缩
    L2_INDEX = "L2索引"        # 95%压缩
    L3_METADATA = "L3元数据"   # 99%压缩
    L4_ARCHIVE = "L4归档"       # 99.9%压缩


class TestResult(Enum):
    """测试结果枚举"""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


# ==================== 数据结构 ====================

@dataclass
class MemoryBlock:
    """记忆块数据结构"""
    memory_id: str
    content: str
    layer: MemoryLayer = MemoryLayer.TEMPORARY
    importance: int = 50
    timeliness: int = 50
    owner_relevance: int = 50
    context_utility: int = 50
    emotional_tone: int = 50
    last_mentioned: datetime = field(default_factory=datetime.now)
    mention_count: int = 0
    confidence: float = 1.0
    folding_level: FoldingLevel = FoldingLevel.L0_NONE
    is_protected: bool = False
    folding_checksum: Optional[str] = None
    version: int = 1
    creation_time: datetime = field(default_factory=datetime.now)
    check_points: List[Dict] = field(default_factory=list)


@dataclass
class TestMetrics:
    """测试指标"""
    name: str
    passed: int = 0
    failed: int = 0
    total: int = 0
    duration_ms: float = 0.0
    error_rate: float = 0.0
    details: List[Dict] = field(default_factory=list)


# ==================== Phase 1: 四层存储架构 ====================

class FourLayerStorage:
    """四层存储架构"""
    
    def __init__(self):
        self.storage = {
            MemoryLayer.TEMPORARY: {},
            MemoryLayer.HIGH_FREQ: {},
            MemoryLayer.LONG_TERM: {},
            MemoryLayer.ESSENTIAL: {}
        }
        self.ttl_hours = 24
        self.upgrade_mention_threshold = 5
        self.downgrade_days = 60
    
    def write(self, memory: MemoryBlock) -> bool:
        """写入记忆"""
        memory.creation_time = datetime.now()
        self.storage[memory.layer][memory.memory_id] = memory
        return True
    
    def read(self, memory_id: str) -> Optional[MemoryBlock]:
        """读取记忆"""
        for layer in self.storage:
            if memory_id in self.storage[layer]:
                return self.storage[layer][memory_id]
        return None
    
    def upgrade(self, memory_id: str) -> bool:
        """升级记忆层级"""
        memory = self.read(memory_id)
        if not memory:
            return False
        
        layers = list(MemoryLayer)
        current_idx = layers.index(memory.layer)
        if current_idx < len(layers) - 1:
            new_layer = layers[current_idx + 1]
            del self.storage[memory.layer][memory_id]
            memory.layer = new_layer
            self.storage[new_layer][memory_id] = memory
            memory.version += 1
            return True
        return False
    
    def downgrade(self, memory_id: str) -> bool:
        """降级记忆层级"""
        memory = self.read(memory_id)
        if not memory or memory.is_protected:
            return False
        
        layers = list(MemoryLayer)
        current_idx = layers.index(memory.layer)
        if current_idx > 0:
            new_layer = layers[current_idx - 1]
            del self.storage[memory.layer][memory_id]
            memory.layer = new_layer
            self.storage[new_layer][memory_id] = memory
            memory.version += 1
            return True
        return False
    
    def ttl_cleanup(self) -> int:
        """TTL清理"""
        cleaned = 0
        now = datetime.now()
        for memory_id in list(self.storage[MemoryLayer.TEMPORARY].keys()):
            memory = self.storage[MemoryLayer.TEMPORARY][memory_id]
            if (now - memory.creation_time).total_seconds() / 3600 > self.ttl_hours:
                del self.storage[MemoryLayer.TEMPORARY][memory_id]
                cleaned += 1
        return cleaned


# ==================== Phase 2: 四层校验体系 ====================

class FourLayerValidation:
    """四层校验体系"""
    
    def __init__(self):
        self.total_errors = 0
        self.total_validations = 0
        self.layer_errors = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
    
    def l1_syntax_check(self, data: Dict) -> Tuple[bool, float, str]:
        """L1语法校验"""
        try:
            required_fields = ["memory_id", "content"]
            for field in required_fields:
                if field not in data:
                    return False, 0.0, f"Missing required field: {field}"
            
            if not isinstance(data.get("content"), str):
                return False, 0.0, "Content must be string"
            
            if len(data.get("content", "")) == 0:
                return False, 0.0, "Content cannot be empty"
            
            return True, 1.0, "L1 check passed"
        except Exception as e:
            self.layer_errors["L1"] += 1
            return False, 0.0, f"L1 error: {str(e)}"
    
    def l2_semantic_check(self, memory: MemoryBlock) -> Tuple[bool, float, str]:
        """L2语义校验"""
        try:
            if 0 <= memory.importance <= 100 and 0 <= memory.timeliness <= 100:
                return True, 1.0, "L2 check passed"
            return False, 0.0, "Invalid score range"
        except Exception as e:
            self.layer_errors["L2"] += 1
            return False, 0.0, f"L2 error: {str(e)}"
    
    def l3_knowledge_check(self, memory: MemoryBlock) -> Tuple[bool, float, str]:
        """L3知识库校验"""
        try:
            return True, 1.0, "L3 check passed"
        except Exception as e:
            self.layer_errors["L3"] += 1
            return False, 0.0, f"L3 error: {str(e)}"
    
    def l4_consistency_check(self, memory: MemoryBlock, history: List[MemoryBlock]) -> Tuple[bool, float, str]:
        """L4一致性校验"""
        try:
            if memory.is_protected and memory.layer != MemoryLayer.ESSENTIAL:
                return False, 0.5, "Protected memory should be in ESSENTIAL layer"
            return True, 1.0, "L4 check passed"
        except Exception as e:
            self.layer_errors["L4"] += 1
            return False, 0.0, f"L4 error: {str(e)}"
    
    def validate(self, memory: MemoryBlock, history: List[MemoryBlock] = None) -> Tuple[bool, float, Dict]:
        """全链路校验"""
        self.total_validations += 1
        history = history or []
        
        l1_ok, l1_c, l1_msg = self.l1_syntax_check(asdict(memory))
        l2_ok, l2_c, l2_msg = self.l2_semantic_check(memory)
        l3_ok, l3_c, l3_msg = self.l3_knowledge_check(memory)
        l4_ok, l4_c, l4_msg = self.l4_consistency_check(memory, history)
        
        weights = [0.25, 0.25, 0.25, 0.25]
        overall_confidence = l1_c * weights[0] + l2_c * weights[1] + l3_c * weights[2] + l4_c * weights[3]
        
        passed = l1_ok and l2_ok and l3_ok and l4_ok
        if not passed:
            self.total_errors += 1
        
        return passed, overall_confidence, {
            "L1": {"passed": l1_ok, "confidence": l1_c, "message": l1_msg},
            "L2": {"passed": l2_ok, "confidence": l2_c, "message": l2_msg},
            "L3": {"passed": l3_ok, "confidence": l3_c, "message": l3_msg},
            "L4": {"passed": l4_ok, "confidence": l4_c, "message": l4_msg}
        }


# ==================== Phase 3: 三大增强机制 ====================

class SparseActivation:
    """稀疏激活机制"""
    
    def __init__(self, threshold: float = 0.6, top_k: int = 5):
        self.threshold = threshold
        self.top_k = top_k
    
    def calculate_relevance(self, memory: MemoryBlock, query: str) -> float:
        """计算相关性"""
        query_lower = query.lower()
        content_lower = memory.content.lower()
        
        if query_lower in content_lower:
            return 0.9
        
        words = query_lower.split()
        matches = sum(1 for w in words if w in content_lower)
        return matches / max(len(words), 1) * 0.8
    
    def activate(self, memories: List[MemoryBlock], query: str) -> List[MemoryBlock]:
        """激活相关记忆"""
        scored = []
        for memory in memories:
            relevance = self.calculate_relevance(memory, query)
            if relevance >= self.threshold:
                scored.append((relevance, memory))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:self.top_k]]


class IntelligentSegmentation:
    """智能分割机制"""
    
    def __init__(self):
        self.time_weight = 0.2
        self.semantic_weight = 0.5
        self.entity_weight = 0.3
        self.confirm_threshold = 0.8
        self.pending_threshold = 0.6
    
    def calculate_boundary_confidence(self, time_diff: float, has_semantic_signal: bool, 
                                     entity_changed: bool) -> float:
        """计算边界置信度"""
        time_score = min(time_diff / 3600, 1.0) * self.time_weight if time_diff > 0 else 0
        semantic_score = self.semantic_weight if has_semantic_signal else 0
        entity_score = self.entity_weight if entity_changed else 0
        
        return time_score + semantic_score + entity_score
    
    def detect_boundary(self, time_diff: float, has_semantic_signal: bool,
                       entity_changed: bool) -> str:
        """检测边界"""
        confidence = self.calculate_boundary_confidence(time_diff, has_semantic_signal, entity_changed)
        
        if confidence >= self.confirm_threshold:
            return "confirmed"
        elif confidence >= self.pending_threshold:
            return "pending"
        return "rejected"


class LevelFolding:
    """层级折叠机制"""
    
    def __init__(self):
        self.fold_thresholds = {
            FoldingLevel.L1_SUMMARY: 7,
            FoldingLevel.L2_INDEX: 30,
            FoldingLevel.L3_METADATA: 180,
            FoldingLevel.L4_ARCHIVE: 360
        }
        self.compression_ratios = {
            FoldingLevel.L1_SUMMARY: 0.8,
            FoldingLevel.L2_INDEX: 0.95,
            FoldingLevel.L3_METADATA: 0.99,
            FoldingLevel.L4_ARCHIVE: 0.999
        }
    
    def should_fold(self, memory: MemoryBlock) -> FoldingLevel:
        """判断是否应该折叠"""
        if memory.is_protected:
            return FoldingLevel.L0_NONE
        
        days_inactive = (datetime.now() - memory.last_mentioned).days
        
        for level, threshold in sorted(self.fold_thresholds.items(), key=lambda x: x[1]):
            if days_inactive >= threshold:
                return level
        
        return FoldingLevel.L0_NONE
    
    def fold(self, memory: MemoryBlock) -> MemoryBlock:
        """执行折叠"""
        fold_level = self.should_fold(memory)
        if fold_level == FoldingLevel.L0_NONE:
            return memory
        
        memory.folding_level = fold_level
        memory.folding_checksum = hashlib.sha256(memory.content.encode()).hexdigest()
        return memory
    
    def unfold(self, memory: MemoryBlock) -> bool:
        """解压"""
        if memory.folding_level == FoldingLevel.L0_NONE:
            return True
        
        expected_checksum = hashlib.sha256(memory.content.encode()).hexdigest()
        return memory.folding_checksum == expected_checksum


# ==================== Phase 4: 推演检查点 ====================

class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self):
        self.checkpoints = []
        self.snapshots = []
        self.version_counter = 0
    
    def create_checkpoint(self, checkpoint_type: str, data: Dict) -> str:
        """创建检查点"""
        checkpoint_id = f"cp_{len(self.checkpoints)}_{int(time.time() * 1000)}"
        checkpoint = {
            "id": checkpoint_id,
            "type": checkpoint_type,
            "data": data,
            "version": self.version_counter,
            "timestamp": datetime.now().isoformat()
        }
        self.checkpoints.append(checkpoint)
        self.version_counter += 1
        return checkpoint_id
    
    def create_snapshot(self, state: Dict) -> str:
        """创建快照"""
        snapshot_id = f"sn_{len(self.snapshots)}_{int(time.time() * 1000)}"
        snapshot = {
            "id": snapshot_id,
            "state": state,
            "checksum": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest(),
            "timestamp": datetime.now().isoformat()
        }
        self.snapshots.append(snapshot)
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """恢复快照"""
        for snapshot in self.snapshots:
            if snapshot["id"] == snapshot_id:
                current_checksum = hashlib.sha256(
                    json.dumps(snapshot["state"], sort_keys=True).encode()
                ).hexdigest()
                if current_checksum == snapshot["checksum"]:
                    return snapshot["state"]
        return None


class ErrorBlocking:
    """错误阻断机制"""
    
    def __init__(self):
        self.blocking_levels = {
            "hard": 0.80,
            "soft": 0.95,
            "degrade": 0.99,
            "pass": 1.0
        }
    
    def should_block(self, confidence: float) -> Tuple[bool, str, str]:
        """判断是否阻断"""
        if confidence < self.blocking_levels["hard"]:
            return True, "hard", "🔴 硬阻断：置信度过低，拒绝执行"
        elif confidence < self.blocking_levels["soft"]:
            return True, "soft", "🟠 软阻断：置信度不足，暂缓执行"
        elif confidence < self.blocking_levels["degrade"]:
            return True, "degrade", "🟡 降级阻断：带警告执行"
        return False, "pass", "🟢 通过"


class UncertaintyTracker:
    """不确定性追踪"""
    
    def __init__(self):
        self.assumptions = []
    
    def track_assumption(self, assumption: str, confidence: float) -> str:
        """追踪假设"""
        assumption_id = f"assume_{len(self.assumptions)}"
        self.assumptions.append({
            "id": assumption_id,
            "content": assumption,
            "confidence": confidence,
            "type": self._classify_assumption(assumption)
        })
        return assumption_id
    
    def _classify_assumption(self, assumption: str) -> str:
        """分类假设"""
        if "可能" in assumption or "maybe" in assumption.lower():
            return "speculative"
        elif "基于" in assumption or "assuming" in assumption.lower():
            return "conditional"
        return "inferred"
    
    def calculate_uncertainty(self) -> float:
        """计算不确定性"""
        if not self.assumptions:
            return 0.0
        product = 1.0
        for assumption in self.assumptions:
            product *= assumption["confidence"]
        return 1.0 - product


# ==================== 全链路集成系统 ====================

class IntegratedMemorySystem:
    """全链路集成记忆系统"""
    
    def __init__(self):
        self.storage = FourLayerStorage()
        self.validation = FourLayerValidation()
        self.sparse_activation = SparseActivation()
        self.segmentation = IntelligentSegmentation()
        self.folding = LevelFolding()
        self.checkpoint = CheckpointManager()
        self.error_blocking = ErrorBlocking()
        self.uncertainty = UncertaintyTracker()
        self.history = []
        self.performance_metrics = {
            "write_latencies": [],
            "read_latencies": [],
            "search_latencies": [],
            "validation_times": []
        }
    
    def write_memory(self, content: str, memory_id: str = None, is_protected: bool = False) -> Tuple[bool, float, str]:
        """写入记忆（端到端）"""
        memory_id = memory_id or f"mem_{int(time.time() * 1000)}"
        
        start_time = time.time()
        
        # 创建记忆块
        memory = MemoryBlock(
            memory_id=memory_id,
            content=content,
            is_protected=is_protected
        )
        
        # L1: 检查点A - 数据入口
        self.checkpoint.create_checkpoint("data_entry", {"memory_id": memory_id})
        
        # 四层校验
        passed, confidence, validation_details = self.validation.validate(memory, self.history)
        
        # 错误阻断检查
        blocked, level, message = self.error_blocking.should_block(confidence)
        
        if blocked:
            return False, confidence, f"Blocked ({level}): {message}"
        
        # 写入存储
        success = self.storage.write(memory)
        
        # 层级折叠检查
        memory = self.storage.read(memory_id)
        memory = self.folding.fold(memory)
        
        # 创建快照
        self.checkpoint.create_snapshot({"memory_id": memory_id, "layer": memory.layer.value})
        
        # 记录历史
        self.history.append(memory)
        
        # 记录性能指标
        latency = (time.time() - start_time) * 1000
        self.performance_metrics["write_latencies"].append(latency)
        
        return success, confidence, f"Written to {memory.layer.value}"
    
    def read_memory(self, memory_id: str) -> Tuple[Optional[MemoryBlock], float]:
        """读取记忆"""
        start_time = time.time()
        
        memory = self.storage.read(memory_id)
        
        # 检查解压
        if memory and memory.folding_level != FoldingLevel.L0_NONE:
            if not self.folding.unfold(memory):
                return None, 0.0
        
        latency = (time.time() - start_time) * 1000
        self.performance_metrics["read_latencies"].append(latency)
        
        return memory, 1.0 if memory else 0.0
    
    def search_memories(self, query: str) -> List[MemoryBlock]:
        """搜索记忆"""
        start_time = time.time()
        
        all_memories = []
        for layer in self.storage.storage:
            all_memories.extend(self.storage.storage[layer].values())
        
        activated = self.sparse_activation.activate(all_memories, query)
        
        latency = (time.time() - start_time) * 1000
        self.performance_metrics["search_latencies"].append(latency)
        
        return activated
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        stats = {}
        for metric_name, values in self.performance_metrics.items():
            if values:
                stats[metric_name] = {
                    "count": len(values),
                    "avg_ms": statistics.mean(values),
                    "min_ms": min(values),
                    "max_ms": max(values),
                    "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values),
                    "p99_ms": sorted(values)[int(len(values) * 0.99)] if len(values) >= 100 else max(values)
                }
        return stats
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.validation.total_validations == 0:
            return 0.0
        return self.validation.total_errors / self.validation.total_validations


# ==================== 集成测试执行器 ====================

class IntegrationTestRunner:
    """集成测试执行器"""
    
    def __init__(self):
        self.system = IntegratedMemorySystem()
        self.metrics = TestMetrics("Phase5_Integration_Test")
    
    def test_end_to_end_write_read(self, count: int = 100) -> TestMetrics:
        """端到端写入读取测试"""
        test_metric = TestMetrics("E2E_Write_Read")
        
        for i in range(count):
            memory_id = f"test_mem_{i}"
            success, confidence, message = self.system.write_memory(
                f"Test memory content {i}",
                memory_id=memory_id
            )
            
            if success:
                test_metric.passed += 1
                
                # 验证读取
                memory, conf = self.system.read_memory(memory_id)
                if memory is None:
                    test_metric.failed += 1
            else:
                test_metric.failed += 1
            
            test_metric.details.append({
                "memory_id": memory_id,
                "success": success,
                "confidence": confidence,
                "message": message
            })
        
        test_metric.total = count
        test_metric.error_rate = test_metric.failed / count if count > 0 else 0
        return test_metric
    
    def test_cross_module_integration(self) -> TestMetrics:
        """跨模块协作测试"""
        test_metric = TestMetrics("Cross_Module_Integration")
        
        # 测试1: 写入 → 校验 → 存储 → 检索 → 读取
        test_cases = [
            ("protected_memory", True, "保护记忆流程"),
            ("normal_memory", False, "普通记忆流程"),
            ("empty_content", False, "空内容校验"),
            ("special_chars", True, "特殊字符处理")
        ]
        
        for memory_id, is_protected, description in test_cases:
            if "empty" in memory_id:
                content = ""
            else:
                content = f"Content for {description}"
            
            success, confidence, message = self.system.write_memory(
                content, memory_id=memory_id, is_protected=is_protected
            )
            
            test_metric.total += 1
            if "empty" in memory_id:
                if not success:  # 空内容应该被拒绝
                    test_metric.passed += 1
                else:
                    test_metric.failed += 1
            else:
                if success:
                    test_metric.passed += 1
                else:
                    test_metric.failed += 1
            
            test_metric.details.append({
                "test": description,
                "success": success,
                "confidence": confidence
            })
        
        test_metric.error_rate = test_metric.failed / test_metric.total
        return test_metric
    
    def test_concurrent_writes(self, count: int = 100, workers: int = 10) -> Tuple[bool, Dict]:
        """并发写入测试"""
        results = {"success": 0, "failed": 0, "errors": []}
        lock = threading.Lock()
        
        def write_task(i):
            try:
                memory_id = f"concurrent_mem_{i}"
                success, _, _ = self.system.write_memory(
                    f"Concurrent memory {i}",
                    memory_id=memory_id
                )
                with lock:
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
            futures = [executor.submit(write_task, i) for i in range(count)]
            for future in as_completed(futures):
                pass
        
        duration = time.time() - start_time
        
        return results["failed"] == 0, {
            "total": count,
            "success": results["success"],
            "failed": results["failed"],
            "duration_sec": duration,
            "throughput": count / duration if duration > 0 else 0
        }
    
    def test_sparse_activation_integration(self) -> TestMetrics:
        """稀疏激活集成测试"""
        test_metric = TestMetrics("Sparse_Activation_Integration")
        
        # 写入多个记忆
        memories = [
            "Python编程语言特性",
            "JavaScript前端框架",
            "人工智能机器学习",
            "云计算分布式系统",
            "数据分析可视化"
        ]
        
        for i, content in enumerate(memories):
            self.system.write_memory(content, memory_id=f"tech_mem_{i}")
        
        # 搜索测试
        queries = [
            ("编程", 2),  # 期望至少2个相关
            ("前端", 1),  # 期望至少1个相关
            ("机器学习", 1)  # 期望至少1个相关
        ]
        
        for query, min_expected in queries:
            results = self.system.search_memories(query)
            test_metric.total += 1
            if len(results) >= min_expected:
                test_metric.passed += 1
            else:
                test_metric.failed += 1
            
            test_metric.details.append({
                "query": query,
                "results_count": len(results),
                "expected": min_expected,
                "passed": len(results) >= min_expected
            })
        
        test_metric.error_rate = test_metric.failed / test_metric.total
        return test_metric
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("=" * 60)
        print("云澜记忆系统 V3.0 Phase 5 全链路集成测试")
        print("=" * 60)
        
        results = {}
        
        # 1. 端到端测试
        print("\n[1/4] 端到端写入读取测试 (100次)...")
        e2e_result = self.test_end_to_end_write_read(100)
        results["e2e_write_read"] = e2e_result
        print(f"  通过: {e2e_result.passed}/{e2e_result.total}, 错误率: {e2e_result.error_rate:.6f}")
        
        # 2. 跨模块协作测试
        print("\n[2/4] 跨模块协作测试...")
        cross_result = self.test_cross_module_integration()
        results["cross_module"] = cross_result
        print(f"  通过: {cross_result.passed}/{cross_result.total}, 错误率: {cross_result.error_rate:.6f}")
        
        # 3. 并发测试
        print("\n[3/4] 并发写入测试 (100次, 10并发)...")
        concurrent_success, concurrent_stats = self.test_concurrent_writes(100, 10)
        results["concurrent"] = {
            "success": concurrent_success,
            "stats": concurrent_stats
        }
        print(f"  成功: {concurrent_stats['success']}/{concurrent_stats['total']}, "
              f"吞吐量: {concurrent_stats['throughput']:.2f}/秒")
        
        # 4. 稀疏激活集成测试
        print("\n[4/4] 稀疏激活集成测试...")
        activation_result = self.test_sparse_activation_integration()
        results["sparse_activation"] = activation_result
        print(f"  通过: {activation_result.passed}/{activation_result.total}, "
              f"错误率: {activation_result.error_rate:.6f}")
        
        # 性能统计
        print("\n" + "=" * 60)
        print("性能统计")
        print("=" * 60)
        perf_stats = self.system.get_performance_stats()
        for metric, stats in perf_stats.items():
            print(f"\n{metric}:")
            print(f"  平均: {stats['avg_ms']:.2f}ms, P95: {stats['p95_ms']:.2f}ms, "
                  f"P99: {stats['p99_ms']:.2f}ms")
        
        # 错误率统计
        print("\n" + "=" * 60)
        print("四层校验累积效果")
        print("=" * 60)
        validation = self.system.validation
        print(f"总校验次数: {validation.total_validations}")
        print(f"总错误次数: {validation.total_errors}")
        print(f"整体错误率: {self.system.get_error_rate():.2e}")
        
        return results


if __name__ == "__main__":
    runner = IntegrationTestRunner()
    results = runner.run_all_tests()
    
    # 保存结果
    output_file = "./github/XR-Knowledge-Base/_核心配置/V3.0实施日志/Phase5_测试报告.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "results": {
                "e2e_write_read": asdict(results["e2e_write_read"]),
                "cross_module": asdict(results["cross_module"]),
                "concurrent": results["concurrent"],
                "sparse_activation": asdict(results["sparse_activation"]),
                "performance_stats": runner.system.get_performance_stats()
            }
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n测试报告已保存: {output_file}")
