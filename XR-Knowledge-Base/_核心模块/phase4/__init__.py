# -*- coding: utf-8 -*-
"""
Phase 4 模块初始化
"""

from .checkpoint_manager import CheckpointManager
from .checkpoint_type_a import DataEntryCheckpoint
from .checkpoint_type_b import LogicConsistencyCheckpoint
from .checkpoint_type_c import ConfidenceCheckpoint
from .checkpoint_type_d import RollbackCheckpoint
from .bubble_isolation import BubbleIsolation, Bubble, BubbleStatus
from .error_blocking import ErrorBlocking, BlockType, BlockStatus
from .uncertainty_tracker import UncertaintyTracker, AssumptionType, UncertaintyTag

__version__ = "3.0.4"
__all__ = [
    # 检查点管理器
    'CheckpointManager',
    'DataEntryCheckpoint',
    'LogicConsistencyCheckpoint',
    'ConfidenceCheckpoint',
    'RollbackCheckpoint',
    
    # 气泡隔离
    'BubbleIsolation',
    'Bubble',
    'BubbleStatus',
    
    # 错误阻断
    'ErrorBlocking',
    'BlockType',
    'BlockStatus',
    
    # 不确定性追踪
    'UncertaintyTracker',
    'AssumptionType',
    'UncertaintyTag',
]
