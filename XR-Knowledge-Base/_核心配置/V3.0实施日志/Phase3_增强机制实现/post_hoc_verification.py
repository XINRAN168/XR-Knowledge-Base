# 云澜记忆系统 V3.0 Phase 3 - 后验验证机制

"""
后验验证机制模块
- 事件块合并机制
- Timeline视图构建
- 事件链追溯
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


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


@dataclass
class TimelineView:
    """Timeline视图"""
    timeline: List[EventBlock]
    events_by_date: Dict[str, List[str]]
    events_by_topic: Dict[str, List[str]]
    event_chains: List[List[str]]
    total_events: int


@dataclass
class EventChain:
    """事件链"""
    chain_id: str
    events: List[EventBlock]
    total_duration: str  # 时间跨度
    topic_progression: List[str]  # 话题演进


class EventBlockMerger:
    """事件块合并器 - 解决事件块膨胀问题"""
    
    def __init__(self):
        self.merge_threshold = 0.6  # 合并阈值
        self.time_gap_threshold = 1800  # 30分钟时间间隔阈值
        self.entity_overlap_threshold = 0.6  # 60%实体重叠阈值
    
    def evaluate_and_merge(self, event_blocks: List[EventBlock]) -> List[EventBlock]:
        """
        评估并执行事件块合并
        
        合并条件：
        1. 语义关联度高（相似主题）
        2. 时间连续（间隔<30分钟）
        3. 实体重叠多（>60%重叠）
        """
        if len(event_blocks) <= 1:
            return event_blocks
        
        # 按时间排序
        sorted_blocks = sorted(
            event_blocks, 
            key=lambda x: x.time_range.get("start", "")
        )
        
        merged = []
        current = sorted_blocks[0]
        
        for next_block in sorted_blocks[1:]:
            if self._should_merge(current, next_block):
                current = self._merge_blocks(current, next_block)
            else:
                merged.append(current)
                current = next_block
        
        merged.append(current)
        return merged
    
    def _should_merge(self, block1: EventBlock, block2: EventBlock) -> bool:
        """判断两个事件块是否应该合并"""
        # 语义关联度
        semantic_score = self._calculate_semantic_similarity(
            block1.core_topic,
            block2.core_topic
        )
        
        # 时间连续性
        time_gap = self._calculate_time_gap(block1, block2)
        time_score = 1.0 if time_gap < self.time_gap_threshold else 0.0
        
        # 实体重叠度
        entity_overlap = self._calculate_entity_overlap(block1, block2)
        
        # 综合判断
        merge_score = semantic_score * 0.5 + time_score * 0.2 + entity_overlap * 0.3
        
        return merge_score >= self.merge_threshold
    
    def _merge_blocks(self, block1: EventBlock, block2: EventBlock) -> EventBlock:
        """合并两个事件块"""
        # 合并时间范围
        start_times = [block1.time_range.get("start", ""), block2.time_range.get("start", "")]
        end_times = [block1.time_range.get("end", ""), block2.time_range.get("end", "")]
        
        merged_time_range = {
            "start": min([t for t in start_times if t]) if any(start_times) else "",
            "end": max([t for t in end_times if t]) if any(end_times) else ""
        }
        
        # 合并子记忆
        merged_memories = list(set(block1.child_memories + block2.child_memories))
        
        # 合并核心实体
        merged_entities = list(set(block1.core_entities + block2.core_entities))
        
        # 合并关联事件
        merged_related = list(set(block1.related_events + [block2.event_id]))
        
        return EventBlock(
            event_id=block1.event_id,
            parent_event=block1.parent_event,
            child_memories=merged_memories,
            core_entities=merged_entities,
            core_topic=block1.core_topic if semantic := True else f"{block1.core_topic}|{block2.core_topic}",
            time_range=merged_time_range,
            boundary_confidence=(block1.boundary_confidence + block2.boundary_confidence) / 2,
            folding_level=min(block1.folding_level, block2.folding_level),
            created_at=block1.created_at,
            last_accessed=datetime.now().isoformat(),
            related_events=merged_related
        )
    
    def _calculate_semantic_similarity(self, topic1: str, topic2: str) -> float:
        """计算语义相似度（简化实现）"""
        if not topic1 or not topic2:
            return 0.0
        
        # 简单关键词匹配
        words1 = set(topic1.split())
        words2 = set(topic2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_time_gap(self, block1: EventBlock, block2: EventBlock) -> float:
        """计算时间间隔（秒）"""
        from datetime import datetime
        
        end1 = block1.time_range.get("end", "")
        start2 = block2.time_range.get("start", "")
        
        if not end1 or not start2:
            return float('inf')
        
        try:
            t1 = datetime.fromisoformat(end1.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(start2.replace('Z', '+00:00'))
            return abs((t2 - t1).total_seconds())
        except:
            return float('inf')
    
    def _calculate_entity_overlap(self, block1: EventBlock, block2: EventBlock) -> float:
        """计算实体重叠度"""
        entities1 = set(block1.core_entities)
        entities2 = set(block2.core_entities)
        
        if not entities1 or not entities2:
            return 0.0
        
        intersection = len(entities1 & entities2)
        union = len(entities1 | entities2)
        
        return intersection / union if union > 0 else 0.0


class TimelineBuilder:
    """Timeline视图构建器"""
    
    def build_timeline(self, event_blocks: List[EventBlock]) -> TimelineView:
        """
        构建Timeline视图
        
        返回：
        - timeline: 按时间排序的事件列表
        - events_by_date: 按日期分组
        - events_by_topic: 按主题分组
        - event_chains: 事件链追溯
        """
        # 按时间排序
        sorted_blocks = sorted(
            event_blocks,
            key=lambda x: x.time_range.get("start", "")
        )
        
        # 按日期分组
        events_by_date = self._group_by_date(sorted_blocks)
        
        # 按主题分组
        events_by_topic = self._group_by_topic(sorted_blocks)
        
        # 事件链追溯
        event_chains = self._build_event_chains(sorted_blocks)
        
        return TimelineView(
            timeline=sorted_blocks,
            events_by_date=events_by_date,
            events_by_topic=events_by_topic,
            event_chains=event_chains,
            total_events=len(sorted_blocks)
        )
    
    def _group_by_date(self, event_blocks: List[EventBlock]) -> Dict[str, List[str]]:
        """按日期分组"""
        by_date = defaultdict(list)
        
        for block in event_blocks:
            start_time = block.time_range.get("start", "")
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    date_key = dt.strftime("%Y-%m-%d")
                    by_date[date_key].append(block.event_id)
                except:
                    pass
        
        return dict(by_date)
    
    def _group_by_topic(self, event_blocks: List[EventBlock]) -> Dict[str, List[str]]:
        """按主题分组"""
        by_topic = defaultdict(list)
        
        for block in event_blocks:
            topic = block.core_topic or "未分类"
            by_topic[topic].append(block.event_id)
        
        return dict(by_topic)
    
    def _build_event_chains(self, event_blocks: List[EventBlock]) -> List[List[str]]:
        """
        构建事件链追溯
        
        返回事件ID链列表
        """
        chains = []
        visited = set()
        
        # 按时间排序后构建链
        for block in event_blocks:
            if block.event_id in visited:
                continue
            
            # 检查是否有后续关联
            related = block.related_events
            if related:
                chain = [block.event_id]
                visited.add(block.event_id)
                
                # 追溯后续事件
                for rel_id in related:
                    if rel_id not in visited:
                        chain.append(rel_id)
                        visited.add(rel_id)
                
                if len(chain) > 1:  # 只保留长度>1的链
                    chains.append(chain)
        
        return chains


class EventChainTracer:
    """事件链追溯器"""
    
    def __init__(self):
        self.max_chain_length = 10  # 最多追溯10个事件
    
    def trace_chain(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock],
        direction: str = "both"
    ) -> EventChain:
        """
        追溯事件关联链
        
        参数：
        - event_id: 起始事件ID
        - all_blocks: 所有事件块
        - direction: 追溯方向（before/after/both）
        
        返回：EventChain
        """
        # 找到起始事件
        start_event = self._find_block_by_id(event_id, all_blocks)
        if not start_event:
            raise ValueError(f"Event not found: {event_id}")
        
        chain_events = [start_event]
        visited = {event_id}
        
        # 向前追溯
        if direction in ["before", "both"]:
            before_events = self._trace_before(event_id, all_blocks, visited)
            chain_events = before_events + chain_events
        
        # 向后追溯
        if direction in ["after", "both"]:
            after_events = self._trace_after(event_id, all_blocks, visited)
            chain_events = chain_events + after_events
        
        # 计算总时长
        total_duration = self._calculate_duration(chain_events)
        
        # 提取话题演进
        topic_progression = [e.core_topic for e in chain_events]
        
        return EventChain(
            chain_id=f"chain_{event_id}",
            events=chain_events,
            total_duration=total_duration,
            topic_progression=topic_progression
        )
    
    def _trace_before(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock],
        visited: set
    ) -> List[EventBlock]:
        """向前追溯"""
        before_events = []
        current_id = event_id
        
        for _ in range(self.max_chain_length):
            prev_id = self._find_previous_event_id(current_id, all_blocks)
            if prev_id and prev_id not in visited:
                prev_event = self._find_block_by_id(prev_id, all_blocks)
                if prev_event:
                    before_events.append(prev_event)
                    visited.add(prev_id)
                    current_id = prev_id
            else:
                break
        
        # 反转，保持时间顺序
        return list(reversed(before_events))
    
    def _trace_after(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock],
        visited: set
    ) -> List[EventBlock]:
        """向后追溯"""
        after_events = []
        current_id = event_id
        
        for _ in range(self.max_chain_length):
            next_id = self._find_next_event_id(current_id, all_blocks)
            if next_id and next_id not in visited:
                next_event = self._find_block_by_id(next_id, all_blocks)
                if next_event:
                    after_events.append(next_event)
                    visited.add(next_id)
                    current_id = next_id
            else:
                break
        
        return after_events
    
    def _find_block_by_id(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock]
    ) -> Optional[EventBlock]:
        """根据ID查找事件块"""
        for block in all_blocks:
            if block.event_id == event_id:
                return block
        return None
    
    def _find_previous_event_id(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock]
    ) -> Optional[str]:
        """查找前一个关联事件"""
        block = self._find_block_by_id(event_id, all_blocks)
        if block and block.related_events:
            # 返回时间上最近的前置事件
            return block.related_events[0] if block.related_events else None
        return None
    
    def _find_next_event_id(
        self, 
        event_id: str, 
        all_blocks: List[EventBlock]
    ) -> Optional[str]:
        """查找下一个关联事件"""
        for block in all_blocks:
            if block.event_id == event_id:
                # 通过related_events被其他事件引用来找到下一个
                for other in all_blocks:
                    if event_id in other.related_events:
                        return other.event_id
        return None
    
    def _calculate_duration(self, events: List[EventBlock]) -> str:
        """计算事件链总时长"""
        if not events:
            return "0分钟"
        
        start_times = [e.time_range.get("start", "") for e in events if e.time_range.get("start")]
        end_times = [e.time_range.get("end", "") for e in events if e.time_range.get("end")]
        
        if not start_times or not end_times:
            return "未知"
        
        try:
            first = datetime.fromisoformat(start_times[0].replace('Z', '+00:00'))
            last = datetime.fromisoformat(end_times[-1].replace('Z', '+00:00'))
            duration = last - first
            
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            if hours > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{minutes}分钟"
        except:
            return "未知"


# ==================== 单元测试 ====================

def test_post_hoc_verification():
    """测试后验验证机制"""
    from datetime import datetime, timedelta
    
    # 创建测试事件块
    now = datetime.now()
    
    events = [
        EventBlock(
            event_id="evt_001",
            parent_event=None,
            child_memories=["m1", "m2"],
            core_entities=["战略", "规划"],
            core_topic="战略规划讨论",
            time_range={"start": (now - timedelta(hours=3)).isoformat(), "end": (now - timedelta(hours=2)).isoformat()},
            boundary_confidence=0.9,
            folding_level=0,
            created_at=(now - timedelta(hours=3)).isoformat(),
            last_accessed=now.isoformat(),
            related_events=["evt_002"]
        ),
        EventBlock(
            event_id="evt_002",
            parent_event="evt_001",
            child_memories=["m3", "m4"],
            core_entities=["战略", "执行"],
            core_topic="战略执行讨论",
            time_range={"start": (now - timedelta(hours=2)).isoformat(), "end": (now - timedelta(hours=1)).isoformat()},
            boundary_confidence=0.85,
            folding_level=0,
            created_at=(now - timedelta(hours=2)).isoformat(),
            last_accessed=now.isoformat(),
            related_events=["evt_003"]
        ),
        EventBlock(
            event_id="evt_003",
            parent_event="evt_002",
            child_memories=["m5"],
            core_entities=["资源", "配置"],
            core_topic="资源配置讨论",
            time_range={"start": (now - timedelta(hours=1)).isoformat(), "end": now.isoformat()},
            boundary_confidence=0.8,
            folding_level=0,
            created_at=(now - timedelta(hours=1)).isoformat(),
            last_accessed=now.isoformat(),
            related_events=[]
        )
    ]
    
    print("=" * 50)
    print("测试1: Timeline视图构建")
    builder = TimelineBuilder()
    timeline = builder.build_timeline(events)
    print(f"总事件数: {timeline.total_events}")
    print(f"按日期分组: {list(timeline.events_by_date.keys())}")
    print(f"事件链: {timeline.event_chains}")
    
    print("=" * 50)
    print("测试2: 事件链追溯")
    tracer = EventChainTracer()
    chain = tracer.trace_chain("evt_002", events, "both")
    print(f"链ID: {chain.chain_id}")
    print(f"链长度: {len(chain.events)}")
    print(f"总时长: {chain.total_duration}")
    print(f"话题演进: {' -> '.join(chain.topic_progression)}")
    
    print("=" * 50)
    print("测试3: 事件块合并")
    merger = EventBlockMerger()
    
    # 创建一个应合并的场景（时间间隔短，主题相似）
    merge_test = [
        EventBlock(
            event_id="merge_1",
            parent_event=None,
            child_memories=["a"],
            core_entities=["话题A"],
            core_topic="话题A讨论",
            time_range={"start": now.isoformat(), "end": now.isoformat()},
            boundary_confidence=0.5,
            folding_level=0,
            created_at=now.isoformat(),
            last_accessed=now.isoformat(),
            related_events=[]
        ),
        EventBlock(
            event_id="merge_2",
            parent_event=None,
            child_memories=["b"],
            core_entities=["话题A"],
            core_topic="话题A继续",
            time_range={"start": (now + timedelta(minutes=10)).isoformat(), "end": (now + timedelta(minutes=20)).isoformat()},
            boundary_confidence=0.3,
            folding_level=0,
            created_at=(now + timedelta(minutes=10)).isoformat(),
            last_accessed=(now + timedelta(minutes=20)).isoformat(),
            related_events=[]
        )
    ]
    
    merged = merger.evaluate_and_merge(merge_test)
    print(f"合并前: {len(merge_test)} 个事件块")
    print(f"合并后: {len(merged)} 个事件块")
    
    print("=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    test_post_hoc_verification()
