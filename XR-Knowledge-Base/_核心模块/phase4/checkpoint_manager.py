# -*- coding: utf-8 -*-
"""
检查点管理器 - 云澜记忆系统 V3.0 Phase 4

实现四种检查点类型：
- 类型A：数据入口检查点（存在性、完整性、时效性、合理性）
- 类型B：逻辑一致性检查点（前置结论兼容性、假设条件满足度）
- 类型C：置信度评估检查点（累积置信度、结论独立置信度）
- 类型D：回滚恢复检查点（状态快照、错误回退）

作者：云澜AI Agent
版本：V3.0 Phase 4
"""

from .checkpoint_type_a import DataEntryCheckpoint
from .checkpoint_type_b import LogicConsistencyCheckpoint
from .checkpoint_type_c import ConfidenceCheckpoint
from .checkpoint_type_d import RollbackCheckpoint

__all__ = [
    'DataEntryCheckpoint',
    'LogicConsistencyCheckpoint', 
    'ConfidenceCheckpoint',
    'RollbackCheckpoint',
    'CheckpointManager'
]


class CheckpointManager:
    """
    检查点管理器
    
    统一管理四种检查点类型的创建、触发和验证。
    """
    
    def __init__(self):
        self.checkpoints = {
            'data_entry': DataEntryCheckpoint(),
            'logic_consistency': LogicConsistencyCheckpoint(),
            'confidence': ConfidenceCheckpoint(),
            'rollback': RollbackCheckpoint()
        }
        self.checkpoint_history = []
        self.checkpoint_counter = 0
    
    def create_checkpoint(self, checkpoint_type: str, context: dict) -> 'Checkpoint':
        """创建检查点"""
        self.checkpoint_counter += 1
        checkpoint_id = f"cp_{self.checkpoint_counter}"
        
        checkpoint = self.checkpoints.get(checkpoint_type)
        if checkpoint:
            checkpoint.create(checkpoint_id, context)
            self.checkpoint_history.append({
                'id': checkpoint_id,
                'type': checkpoint_type,
                'context': context
            })
            return checkpoint
        raise ValueError(f"Unknown checkpoint type: {checkpoint_type}")
    
    def validate(self, checkpoint_type: str, data: dict) -> 'ValidationResult':
        """执行检查点验证"""
        checkpoint = self.checkpoints.get(checkpoint_type)
        if checkpoint:
            return checkpoint.validate(data)
        raise ValueError(f"Unknown checkpoint type: {checkpoint_type}")
    
    def get_checkpoint(self, checkpoint_id: str) -> dict:
        """获取检查点详情"""
        for cp in self.checkpoint_history:
            if cp['id'] == checkpoint_id:
                return cp
        return None
