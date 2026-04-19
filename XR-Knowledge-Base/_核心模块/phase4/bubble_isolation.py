# -*- coding: utf-8 -*-
"""
气泡隔离机制

概念：每个检查点形成一个"气泡"，气泡内错误不外传

┌─────────────────────────────────────────────────────────────┐
│  [气泡A: Step 1-3] ──→ [检查点] ──→ [气泡B: Step 4-6]     │
│                                                            │
│  气泡A内部错误 ──→ 气泡A内部处理 ──→ 不影响气泡B          │
│                                                            │
│  气泡A出口 ──→ 校验 ──→ 气泡B入口                        │
│  校验失败 ──→ 气泡A重新推演 ──→ 校验通过后进入气泡B     │
└─────────────────────────────────────────────────────────────┘

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid


class BubbleStatus(Enum):
    """气泡状态"""
    ACTIVE = "active"
    VALIDATING = "validating"
    VALIDATED = "validated"
    ERROR = "error"
    CLOSED = "closed"


class BoundaryType(Enum):
    """边界类型"""
    ENTRY = "entry"    # 入口边界
    EXIT = "exit"      # 出口边界
    INTERNAL = "internal"  # 内部边界


@dataclass
class BubbleBoundary:
    """气泡边界"""
    boundary_id: str
    boundary_type: BoundaryType
    data_signatures: Dict[str, str]  # 数据签名
    validation_rules: List[str] = field(default_factory=list)
    is_validated: bool = False
    
    def add_data_signature(self, key: str, signature: str) -> None:
        """添加数据签名"""
        self.data_signatures[key] = signature
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据是否匹配"""
        # 简化实现：检查关键数据是否存在
        for key in self.data_signatures:
            if key not in data:
                return False
        return True


@dataclass
class Bubble:
    """气泡"""
    bubble_id: str
    checkpoint_id: str
    status: BubbleStatus
    entry_boundary: BubbleBoundary
    exit_boundary: BubbleBoundary
    internal_boundaries: List[BubbleBoundary] = field(default_factory=list)
    contained_steps: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    version: int = 1
    parent_bubble_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """记录错误"""
        self.errors.append(error)
        if self.status == BubbleStatus.ACTIVE:
            self.status = BubbleStatus.ERROR
    
    def isolate_error(self, error: Dict[str, Any]) -> bool:
        """
        隔离错误
        
        Returns:
            bool: 是否成功隔离
        """
        if not self._is_error_internal(error):
            return False
        
        self.add_error(error)
        return True
    
    def _is_error_internal(self, error: Dict[str, Any]) -> bool:
        """检查错误是否属于气泡内部"""
        error_location = error.get('location', '')
        return any(step in error_location for step in self.contained_steps)
    
    def close(self) -> None:
        """关闭气泡"""
        self.status = BubbleStatus.CLOSED


@dataclass
class ErrorIsolationResult:
    """错误隔离结果"""
    success: bool
    bubble_id: str
    error_id: str
    isolated: bool
    propagated: bool
    recovery_action: Optional[str] = None
    message: str = ""


@dataclass
class CrossBubbleMessage:
    """跨气泡消息"""
    message_id: str
    source_bubble_id: str
    target_bubble_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    validated: bool = False
    validation_signature: Optional[str] = None


class BubbleIsolation:
    """
    气泡隔离机制
    
    为每个检查点形成独立的"气泡"区域，气泡内部的错误
    不会传导到气泡外部。
    """
    
    def __init__(self):
        self.bubbles: Dict[str, Bubble] = {}
        self.bubble_counter = 0
        self.cross_bubble_messages: List[CrossBubbleMessage] = []
        self.protocol_rules = self._init_protocol_rules()
    
    def create_bubble(self, checkpoint_id: str, steps: List[str]) -> Bubble:
        """
        创建新气泡
        
        Args:
            checkpoint_id: 检查点ID
            steps: 气泡包含的步骤
        
        Returns:
            Bubble: 创建的气泡
        """
        self.bubble_counter += 1
        bubble_id = f"bubble_{self.bubble_counter}"
        
        # 创建入口和出口边界
        entry_boundary = BubbleBoundary(
            boundary_id=f"{bubble_id}_entry",
            boundary_type=BoundaryType.ENTRY,
            data_signatures={}
        )
        
        exit_boundary = BubbleBoundary(
            boundary_id=f"{bubble_id}_exit",
            boundary_type=BoundaryType.EXIT,
            data_signatures={}
        )
        
        # 创建气泡
        bubble = Bubble(
            bubble_id=bubble_id,
            checkpoint_id=checkpoint_id,
            status=BubbleStatus.ACTIVE,
            entry_boundary=entry_boundary,
            exit_boundary=exit_boundary,
            contained_steps=steps,
            parent_bubble_id=self._get_active_bubble_id()
        )
        
        self.bubbles[bubble_id] = bubble
        return bubble
    
    def validate_entry_boundary(self, bubble_id: str, data: Dict[str, Any]) -> bool:
        """
        验证气泡入口边界
        
        Args:
            bubble_id: 气泡ID
            data: 入口数据
        
        Returns:
            bool: 验证是否通过
        """
        bubble = self.bubbles.get(bubble_id)
        if bubble is None:
            return False
        
        bubble.status = BubbleStatus.VALIDATING
        result = bubble.entry_boundary.validate(data)
        
        if result:
            bubble.status = BubbleStatus.VALIDATED
        
        return result
    
    def validate_exit_boundary(self, bubble_id: str, data: Dict[str, Any]) -> bool:
        """
        验证气泡出口边界
        
        Args:
            bubble_id: 气泡ID
            data: 出口数据
        
        Returns:
            bool: 验证是否通过
        """
        bubble = self.bubbles.get(bubble_id)
        if bubble is None:
            return False
        
        result = bubble.exit_boundary.validate(data)
        
        if result:
            bubble.exit_boundary.is_validated = True
        
        return result
    
    def isolate_error(self, bubble_id: str, error: Dict[str, Any]) -> ErrorIsolationResult:
        """
        隔离错误
        
        Args:
            bubble_id: 气泡ID
            error: 错误信息
        
        Returns:
            ErrorIsolationResult: 隔离结果
        """
        bubble = self.bubbles.get(bubble_id)
        if bubble is None:
            return ErrorIsolationResult(
                success=False,
                bubble_id=bubble_id,
                error_id=error.get('id', ''),
                isolated=False,
                propagated=True,
                message="气泡不存在"
            )
        
        # 检查错误是否在气泡内部
        is_internal = bubble._is_error_internal(error)
        
        if is_internal:
            # 内部错误，隔离处理
            bubble.isolate_error(error)
            return ErrorIsolationResult(
                success=True,
                bubble_id=bubble_id,
                error_id=error.get('id', ''),
                isolated=True,
                propagated=False,
                recovery_action="internal_handling",
                message="错误已隔离在气泡内部"
            )
        else:
            # 外部错误，不处理
            return ErrorIsolationResult(
                success=True,
                bubble_id=bubble_id,
                error_id=error.get('id', ''),
                isolated=False,
                propagated=True,
                message="错误在气泡外部，无需隔离"
            )
    
    def send_cross_bubble_message(
        self,
        source_id: str,
        target_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> Optional[CrossBubbleMessage]:
        """
        发送跨气泡消息
        
        Args:
            source_id: 源气泡ID
            target_id: 目标气泡ID
            message_type: 消息类型
            payload: 消息内容
        
        Returns:
            Optional[CrossBubbleMessage]: 发送的消息
        """
        source = self.bubbles.get(source_id)
        target = self.bubbles.get(target_id)
        
        if source is None or target is None:
            return None
        
        # 创建消息
        message = CrossBubbleMessage(
            message_id=str(uuid.uuid4()),
            source_bubble_id=source_id,
            target_bubble_id=target_id,
            message_type=message_type,
            payload=payload,
            timestamp=0  # 将在发送时设置
        )
        
        # 验证消息格式
        if self._validate_message_format(message):
            self.cross_bubble_messages.append(message)
            return message
        
        return None
    
    def receive_cross_bubble_message(self, message_id: str) -> Optional[CrossBubbleMessage]:
        """
        接收跨气泡消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[CrossBubbleMessage]: 接收的消息
        """
        for message in self.cross_bubble_messages:
            if message.message_id == message_id:
                message.validated = True
                return message
        return None
    
    def merge_bubbles(self, bubble_ids: List[str]) -> Optional[Bubble]:
        """
        合并气泡
        
        Args:
            bubble_ids: 要合并的气泡ID列表
        
        Returns:
            Optional[Bubble]: 合并后的气泡
        """
        bubbles = [self.bubbles.get(bid) for bid in bubble_ids if bid in self.bubbles]
        if not bubbles:
            return None
        
        # 创建新气泡
        new_bubble = self.create_bubble(
            checkpoint_id=f"merged_{'_'.join(bubble_ids)}",
            steps=sum([b.contained_steps for b in bubbles], [])
        )
        
        # 关闭原气泡
        for bubble in bubbles:
            bubble.close()
        
        return new_bubble
    
    def split_bubble(self, bubble_id: str, split_point: str) -> Tuple[Optional[Bubble], Optional[Bubble]]:
        """
        分裂气泡
        
        Args:
            bubble_id: 要分裂的气泡ID
            split_point: 分裂点
        
        Returns:
            Tuple[Optional[Bubble], Optional[Bubble]]: 分裂后的两个气泡
        """
        bubble = self.bubbles.get(bubble_id)
        if bubble is None:
            return None, None
        
        # 找到分裂位置
        try:
            split_idx = bubble.contained_steps.index(split_point)
        except ValueError:
            return None, None
        
        # 创建两个新气泡
        bubble_a = self.create_bubble(
            checkpoint_id=f"{bubble_id}_a",
            steps=bubble.contained_steps[:split_idx]
        )
        
        bubble_b = self.create_bubble(
            checkpoint_id=f"{bubble_id}_b",
            steps=bubble.contained_steps[split_idx:]
        )
        
        # 关闭原气泡
        bubble.close()
        
        return bubble_a, bubble_b
    
    def get_bubble_chain(self, bubble_id: str) -> List[Bubble]:
        """
        获取气泡链
        
        Args:
            bubble_id: 起始气泡ID
        
        Returns:
            List[Bubble]: 气泡链
        """
        chain = []
        current_id = bubble_id
        
        while current_id and current_id in self.bubbles:
            bubble = self.bubbles[current_id]
            chain.append(bubble)
            current_id = bubble.parent_bubble_id
        
        return chain
    
    def _init_protocol_rules(self) -> Dict[str, Any]:
        """初始化通信协议规则"""
        return {
            'allow_cross_bubble': True,
            'require_validation': True,
            'message_types': ['data', 'control', 'error', 'sync'],
            'max_message_size': 1024 * 1024,  # 1MB
        }
    
    def _get_active_bubble_id(self) -> Optional[str]:
        """获取当前活动气泡ID"""
        for bid, bubble in self.bubbles.items():
            if bubble.status == BubbleStatus.ACTIVE:
                return bid
        return None
    
    def _validate_message_format(self, message: CrossBubbleMessage) -> bool:
        """验证消息格式"""
        if message.message_type not in self.protocol_rules['message_types']:
            return False
        
        return True
    
    def get_bubble_stats(self) -> Dict[str, Any]:
        """获取气泡统计信息"""
        total = len(self.bubbles)
        by_status = {
            'active': len([b for b in self.bubbles.values() if b.status == BubbleStatus.ACTIVE]),
            'validating': len([b for b in self.bubbles.values() if b.status == BubbleStatus.VALIDATING]),
            'validated': len([b for b in self.bubbles.values() if b.status == BubbleStatus.VALIDATED]),
            'error': len([b for b in self.bubbles.values() if b.status == BubbleStatus.ERROR]),
            'closed': len([b for b in self.bubbles.values() if b.status == BubbleStatus.CLOSED]),
        }
        
        return {
            'total': total,
            'by_status': by_status,
            'cross_bubble_messages': len(self.cross_bubble_messages),
            'protocol_rules': self.protocol_rules
        }
