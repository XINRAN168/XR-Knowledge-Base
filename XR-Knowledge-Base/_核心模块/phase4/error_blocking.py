# -*- coding: utf-8 -*-
"""
错误传导阻断机制

四种阻断机制：
- 硬阻断 (Hard Block): C < 0.80
- 软阻断 (Soft Block): 0.80 ≤ C < 0.95
- 降级阻断 (Degraded Block): 0.95 ≤ C < 0.99
- 人工阻断 (Manual Block): 主人干预

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid


class BlockType(Enum):
    """阻断类型"""
    HARD = "hard"           # 硬阻断
    SOFT = "soft"           # 软阻断
    DEGRADED = "degraded"   # 降级阻断
    MANUAL = "manual"       # 人工阻断


class BlockStatus(Enum):
    """阻断状态"""
    PENDING = "pending"     # 待处理
    ACTIVE = "active"       # 阻断中
    RECOVERING = "recovering"  # 恢复中
    RECOVERED = "recovered"    # 已恢复
    EXPIRED = "expired"        # 已过期


@dataclass
class Block:
    """阻断"""
    block_id: str
    block_type: BlockType
    status: BlockStatus
    confidence: float
    trigger_condition: str
    created_at: float
    triggered_at: Optional[float] = None
    recovered_at: Optional[float] = None
    recovery_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockResult:
    """阻断结果"""
    blocked: bool
    block_id: Optional[str]
    block_type: Optional[BlockType]
    immediate_action: str
    requires_manual_intervention: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """恢复操作"""
    action_id: str
    action_type: str
    target_block_id: str
    executed: bool = False
    result: Optional[Dict[str, Any]] = None


class BlockingStrategy:
    """阻断策略基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def should_block(self, confidence: float, context: Dict[str, Any]) -> bool:
        """判断是否应该阻断"""
        raise NotImplementedError
    
    def get_immediate_action(self) -> str:
        """获取立即执行的动作"""
        raise NotImplementedError


class HardBlockStrategy(BlockingStrategy):
    """硬阻断策略"""
    
    def should_block(self, confidence: float, context: Dict[str, Any]) -> bool:
        """硬阻断条件：C < 0.80"""
        return confidence < 0.80
    
    def get_immediate_action(self) -> str:
        return "STOP_AND_WAIT_MANUAL"


class SoftBlockStrategy(BlockingStrategy):
    """软阻断策略"""
    
    def should_block(self, confidence: float, context: Dict[str, Any]) -> bool:
        """软阻断条件：0.80 ≤ C < 0.95"""
        return 0.80 <= confidence < 0.95
    
    def get_immediate_action(self) -> str:
        return "PAUSE_AND_AWAIT_REVIEW"


class DegradedBlockStrategy(BlockingStrategy):
    """降级阻断策略"""
    
    def should_block(self, confidence: float, context: Dict[str, Any]) -> bool:
        """降级阻断条件：0.95 ≤ C < 0.99"""
        return 0.95 <= confidence < 0.99
    
    def get_immediate_action(self) -> str:
        return "ADD_VERIFICATION_STEP"


class ManualBlockStrategy(BlockingStrategy):
    """人工阻断策略"""
    
    def should_block(self, confidence: float, context: Dict[str, Any]) -> bool:
        """人工阻断条件：主人主动干预"""
        return context.get('manual_intervention', False)
    
    def get_immediate_action(self) -> str:
        return "AWAIT_OWNER_COMMAND"


class ErrorBlocking:
    """
    错误传导阻断机制
    
    通过四种独立的阻断机制，防止推演过程中的错误
    从一个步骤传导到后续步骤。
    """
    
    def __init__(self):
        self.blocking_strategies = {
            BlockType.HARD: HardBlockStrategy(),
            BlockType.SOFT: SoftBlockStrategy(),
            BlockType.DEGRADED: DegradedBlockStrategy(),
            BlockType.MANUAL: ManualBlockStrategy(),
        }
        
        self.active_blocks: Dict[str, Block] = {}
        self.block_history: List[Block] = []
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # 配置
        self.config = {
            'auto_expire_seconds': 3600,  # 自动过期时间
            'soft_block_timeout_seconds': 300,  # 软阻断超时
            'max_concurrent_blocks': 10,  # 最大并发阻断数
        }
    
    def block_error(self, error: Dict[str, Any], confidence: float, context: Dict[str, Any] = None) -> BlockResult:
        """
        阻断错误传播
        
        Args:
            error: 错误信息
            confidence: 当前置信度
            context: 上下文信息
        
        Returns:
            BlockResult: 阻断结果
        """
        context = context or {}
        
        # 确定阻断类型
        block_type = self._determine_block_type(confidence, context)
        
        # 创建阻断
        block = self._create_block(block_type, confidence, error, context)
        
        # 执行阻断
        strategy = self.blocking_strategies.get(block_type)
        immediate_action = strategy.get_immediate_action() if strategy else "UNKNOWN"
        
        requires_manual = block_type in (BlockType.HARD, BlockType.MANUAL)
        
        return BlockResult(
            blocked=True,
            block_id=block.block_id,
            block_type=block_type,
            immediate_action=immediate_action,
            requires_manual_intervention=requires_manual,
            message=self._generate_block_message(block_type, confidence),
            metadata={
                'error_id': error.get('id', ''),
                'confidence': confidence,
                'block_created_at': block.created_at
            }
        )
    
    def recover_from_block(self, block_id: str, action: RecoveryAction) -> bool:
        """
        从阻断中恢复
        
        Args:
            block_id: 阻断ID
            action: 恢复操作
        
        Returns:
            bool: 是否成功恢复
        """
        block = self.active_blocks.get(block_id)
        if block is None:
            return False
        
        # 执行恢复操作
        handler = self.recovery_handlers.get(action.action_type)
        if handler:
            result = handler(block, action)
            action.executed = True
            action.result = result if isinstance(result, dict) else {'success': result}
        
        # 更新阻断状态
        block.status = BlockStatus.RECOVERED
        block.recovered_at = action.result.get('timestamp') if isinstance(action.result, dict) else None
        block.recovery_action = action.action_type
        
        # 从活动阻断中移除
        self.active_blocks.pop(block_id)
        self.block_history.append(block)
        
        return True
    
    def check_and_upgrade_block(self, block_id: str, new_confidence: float) -> Optional[BlockType]:
        """
        检查并升级阻断
        
        Args:
            block_id: 阻断ID
            new_confidence: 新的置信度
        
        Returns:
            Optional[BlockType]: 是否需要升级，以及升级后的类型
        """
        block = self.active_blocks.get(block_id)
        if block is None:
            return None
        
        # 确定新的阻断类型
        new_type = self._determine_block_type(new_confidence, {})
        
        # 检查是否需要升级
        if self._is_upgrade(block.block_type, new_type):
            # 执行升级
            block.block_type = new_type
            block.confidence = new_confidence
            return new_type
        
        return None
    
    def get_active_blocks(self) -> List[Block]:
        """获取当前活动阻断列表"""
        return list(self.active_blocks.values())
    
    def register_recovery_handler(self, action_type: str, handler: Callable) -> None:
        """注册恢复处理器"""
        self.recovery_handlers[action_type] = handler
    
    def _determine_block_type(self, confidence: float, context: Dict[str, Any]) -> BlockType:
        """确定阻断类型"""
        # 按优先级检查
        if context.get('manual_intervention', False):
            return BlockType.MANUAL
        if confidence < 0.80:
            return BlockType.HARD
        if confidence < 0.95:
            return BlockType.SOFT
        if confidence < 0.99:
            return BlockType.DEGRADED
        return BlockType.MANUAL  # 兜底
    
    def _create_block(
        self,
        block_type: BlockType,
        confidence: float,
        error: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Block:
        """创建阻断"""
        block_id = f"block_{uuid.uuid4()}"
        
        block = Block(
            block_id=block_id,
            block_type=block_type,
            status=BlockStatus.ACTIVE,
            confidence=confidence,
            trigger_condition=f"confidence={confidence}",
            created_at=0,  # 将在初始化时设置
            metadata={
                'error': error,
                'context': context
            }
        )
        
        self.active_blocks[block_id] = block
        return block
    
    def _is_upgrade(self, current: BlockType, new: BlockType) -> bool:
        """检查是否为升级"""
        # 优先级：HARD > SOFT > DEGRADED > MANUAL
        priority = {
            BlockType.MANUAL: 0,
            BlockType.DEGRADED: 1,
            BlockType.SOFT: 2,
            BlockType.HARD: 3,
        }
        return priority.get(new, 0) > priority.get(current, 0)
    
    def _generate_block_message(self, block_type: BlockType, confidence: float) -> str:
        """生成阻断消息"""
        messages = {
            BlockType.HARD: f"硬阻断触发：置信度过低 ({confidence:.4f} < 0.80)，需要人工确认",
            BlockType.SOFT: f"软阻断触发：置信度偏低 ({confidence:.4f})，等待人工复核",
            BlockType.DEGRADED: f"降级阻断触发：置信度不足 ({confidence:.4f})，增加验证步骤",
            BlockType.MANUAL: "人工阻断触发：等待主人指令",
        }
        return messages.get(block_type, "未知阻断类型")
    
    def get_block_stats(self) -> Dict[str, Any]:
        """获取阻断统计"""
        return {
            'active_blocks': len(self.active_blocks),
            'total_blocks': len(self.block_history),
            'by_type': {
                'hard': len([b for b in self.active_blocks.values() if b.block_type == BlockType.HARD]),
                'soft': len([b for b in self.active_blocks.values() if b.block_type == BlockType.SOFT]),
                'degraded': len([b for b in self.active_blocks.values() if b.block_type == BlockType.DEGRADED]),
                'manual': len([b for b in self.active_blocks.values() if b.block_type == BlockType.MANUAL]),
            },
            'config': self.config
        }
