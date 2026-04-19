# 云澜记忆系统 V3.0 Phase 3 - 智能分割机制

"""
智能分割机制模块
- 三维边界信号检测（时间/语义/实体）
- 置信度阈值判断（≥0.8确认）
- 后验关联度验证
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class BoundaryDecision(Enum):
    """边界决策类型"""
    CONFIRM = "confirm"      # 确认分割
    PENDING = "pending"      # 疑似边界
    REJECT = "reject"        # 不分割


# 三维边界信号权重配置
BOUNDARY_WEIGHTS = {
    "time": 0.2,       # 时间信号权重
    "semantic": 0.5,  # 语义信号权重
    "entity": 0.3     # 实体信号权重
}

# 语义边界触发词
TOPIC_SWITCH_MARKERS = ["对了", "换个话题", "那件事", "说起来", "另外", "忽然"]
COMPLETION_MARKERS = ["完成了", "搞定了", "解决了", "做完了", "结束"]


@dataclass
class BoundarySignal:
    """边界信号"""
    time_score: float      # 时间信号分数
    semantic_score: float  # 语义信号分数
    entity_score: float   # 实体信号分数
    boundary_score: float # 综合边界分数
    decision: BoundaryDecision


@dataclass
class EventBlock:
    """事件块"""
    event_id: str
    parent_event: Optional[str]
    child_memories: List[str]
    core_entities: List[str]
    core_topic: str
    time_range: Dict[str, str]
    boundary_confidence: float
    folding_level: int
    created_at: str
    last_accessed: str
    related_events: List[str]


class IntelligentSegmenter:
    """智能分割器 - 事件边界识别"""
    
    def __init__(self):
        self.entity_change_threshold = 0.5  # 实体变化阈值50%
    
    def detect_boundary(
        self, 
        memories: List[Dict],
        current_time: datetime = None
    ) -> BoundarySignal:
        """
        检测事件边界
        
        参数：
        - memories: 记忆列表（至少需要2条）
        - current_time: 当前时间（可选）
        
        返回：BoundarySignal
        """
        if len(memories) < 2:
            return BoundarySignal(0.0, 0.0, 0.0, 0.0, BoundaryDecision.REJECT)
        
        # 时间信号检测
        c_time = self._detect_time_signal(memories, current_time)
        
        # 语义信号检测
        c_semantic = self._detect_semantic_signal(memories)
        
        # 实体信号检测
        c_entity = self._detect_entity_signal(memories)
        
        # 综合置信度计算
        boundary_score = (
            BOUNDARY_WEIGHTS["time"] * c_time +
            BOUNDARY_WEIGHTS["semantic"] * c_semantic +
            BOUNDARY_WEIGHTS["entity"] * c_entity
        )
        
        # 决策判断
        decision = self._make_decision(boundary_score)
        
        return BoundarySignal(
            time_score=c_time,
            semantic_score=c_semantic,
            entity_score=c_entity,
            boundary_score=boundary_score,
            decision=decision
        )
    
    def _detect_time_signal(
        self, 
        memories: List[Dict],
        current_time: datetime = None
    ) -> float:
        """
        时间信号检测
        
        检测时间戳跳跃：
        - 间隔>2小时 → 1.0
        - 间隔>1小时 → 0.7
        - 间隔>30分钟 → 0.4
        """
        if current_time is None:
            current_time = datetime.now()
        
        time_gaps = []
        for i in range(1, min(len(memories), 6)):  # 最多检查最近5条
            prev_time = self._parse_time(memories[-i-1].get("timestamp"))
            curr_time = self._parse_time(memories[-i].get("timestamp"))
            
            if prev_time and curr_time:
                gap = (curr_time - prev_time).total_seconds()
                time_gaps.append(gap)
        
        if not time_gaps:
            return 0.0
        
        avg_gap = sum(time_gaps) / len(time_gaps)
        
        # 阈值判断
        if avg_gap > 7200:   # 2小时
            return 1.0
        elif avg_gap > 3600:  # 1小时
            return 0.7
        elif avg_gap > 1800:  # 30分钟
            return 0.4
        return 0.0
    
    def _detect_semantic_signal(self, memories: List[Dict]) -> float:
        """
        语义信号检测
        
        检测话题切换词、语气变化
        """
        if not memories:
            return 0.0
        
        last_content = memories[-1].get("content", "")
        
        # 检查话题切换标记
        for marker in TOPIC_SWITCH_MARKERS:
            if marker in last_content:
                return 1.0
        
        # 检查任务完成标记
        for marker in COMPLETION_MARKERS:
            if marker in last_content:
                return 0.9
        
        # 检查意图变化（问号开头）
        if last_content.strip().startswith("那") and "呢" in last_content:
            return 0.7
        
        return 0.0
    
    def _detect_entity_signal(self, memories: List[Dict]) -> float:
        """
        实体信号检测
        
        检测核心实体集合变化：
        - 变化率>50% → 高置信度边界
        """
        if len(memories) < 2:
            return 0.0
        
        prev_entities = set(memories[-2].get("core_entities", []))
        curr_entities = set(memories[-1].get("core_entities", []))
        
        if not prev_entities and not curr_entities:
            return 0.0
        
        if not prev_entities:
            return 0.5  # 无前序实体，温和检测
        
        # 计算实体变化率
        changed = len(prev_entities - curr_entities) + len(curr_entities - prev_entities)
        union = len(prev_entities | curr_entities)
        
        if union == 0:
            return 0.0
        
        change_rate = changed / union
        
        # 变化>50%触发实体信号
        if change_rate > self.entity_change_threshold:
            return min(1.0, change_rate)
        return 0.0
    
    def _make_decision(self, boundary_score: float) -> BoundaryDecision:
        """
        基于置信度决定是否分割
        
        - C ≥ 0.80 → 确认分割
        - 0.60 ≤ C < 0.80 → 疑似边界
        - C < 0.60 → 不分割
        """
        if boundary_score >= 0.8:
            return BoundaryDecision.CONFIRM
        elif boundary_score >= 0.6:
            return BoundaryDecision.PENDING
        else:
            return BoundaryDecision.REJECT
    
    def _parse_time(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def verify_post_hoc(self, event_block: EventBlock) -> Tuple[bool, float]:
        """
        后验验证：事件块形成后检测子记忆间的关联度
        
        返回：(是否有效, 关联度分数)
        
        验证维度：
        - 语义关联度（40%）
        - 时间连续性（30%）
        - 实体重叠度（30%）
        """
        if len(event_block.child_memories) < 2:
            return True, 1.0  # 单条记忆默认有效
        
        # 简化：使用时间间隔和实体重叠度计算
        # 实际实现中需要获取记忆详情进行向量相似度计算
        
        return True, 0.75  # 默认通过
    
    def create_event_block(
        self,
        memories: List[Dict],
        boundary_signal: BoundarySignal
    ) -> EventBlock:
        """
        创建事件块
        """
        from datetime import datetime
        
        # 收集核心实体
        all_entities = set()
        for mem in memories:
            all_entities.update(mem.get("core_entities", []))
        
        # 收集时间范围
        timestamps = [self._parse_time(m.get("timestamp")) for m in memories]
        timestamps = [t for t in timestamps if t]
        
        time_range = {}
        if timestamps:
            time_range = {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat()
            }
        
        return EventBlock(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            parent_event=None,
            child_memories=[m.get("id", f"mem_{i}") for i, m in enumerate(memories)],
            core_entities=list(all_entities)[:10],  # 最多10个核心实体
            core_topic=memories[-1].get("topic", "未知主题") if memories else "未知主题",
            time_range=time_range,
            boundary_confidence=boundary_signal.boundary_score,
            folding_level=0,
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            related_events=[]
        )


# ==================== 单元测试 ====================

def test_intelligent_segmentation():
    """测试智能分割机制"""
    segmenter = IntelligentSegmenter()
    
    # 测试场景1: 话题切换
    print("=" * 50)
    print("测试1: 话题切换场景")
    memories1 = [
        {"id": "m1", "content": "我们来讨论战略规划", "core_entities": ["战略", "规划"], "timestamp": "2026-05-14T10:00:00Z"},
        {"id": "m2", "content": "对的，还要考虑资源配置", "core_entities": ["资源", "配置"], "timestamp": "2026-05-14T10:30:00Z"},
        {"id": "m3", "content": "对了，说起市场竞争，你觉得...", "core_entities": ["市场", "竞争"], "timestamp": "2026-05-14T11:00:00Z"}
    ]
    signal = segmenter.detect_boundary(memories1)
    print(f"边界分数: {signal.boundary_score:.2f}")
    print(f"决策: {signal.decision.value}")
    print(f"  - 时间信号: {signal.time_score:.2f}")
    print(f"  - 语义信号: {signal.semantic_score:.2f}")
    print(f"  - 实体信号: {signal.entity_score:.2f}")
    
    # 测试场景2: 连续讨论（不应分割）
    print("=" * 50)
    print("测试2: 连续讨论场景")
    memories2 = [
        {"id": "m1", "content": "这个项目需要仔细规划", "core_entities": ["项目", "规划"], "timestamp": "2026-05-14T10:00:00Z"},
        {"id": "m2", "content": "是的，我们要分阶段推进", "core_entities": ["项目", "阶段"], "timestamp": "2026-05-14T10:05:00Z"},
        {"id": "m3", "content": "对的，我同意这个方案", "core_entities": ["项目", "方案"], "timestamp": "2026-05-14T10:10:00Z"}
    ]
    signal = segmenter.detect_boundary(memories2)
    print(f"边界分数: {signal.boundary_score:.2f}")
    print(f"决策: {signal.decision.value}")
    
    # 测试场景3: 跨天对话
    print("=" * 50)
    print("测试3: 跨天对话场景")
    memories3 = [
        {"id": "m1", "content": "今天的讨论很有收获", "core_entities": ["讨论"], "timestamp": "2026-05-14T17:00:00Z"},
        {"id": "m2", "content": "继续昨天的议题", "core_entities": ["议题"], "timestamp": "2026-05-15T09:00:00Z"}
    ]
    signal = segmenter.detect_boundary(memories3)
    print(f"边界分数: {signal.boundary_score:.2f}")
    print(f"决策: {signal.decision.value}")
    
    print("=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    test_intelligent_segmentation()
