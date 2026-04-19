# -*- coding: utf-8 -*-
"""
类型D：回滚恢复检查点

触发时机：每完成一个完整推演阶段后

保存内容：
- 当前推演状态快照
- 已验证的中间结论
- 使用的假设条件
- 检查点置信度历史

恢复流程：
发现错误 → 定位最近有效检查点 → 恢复状态 → 修正后继续

作者：云澜AI Agent
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy


class SnapshotStatus(Enum):
    """快照状态"""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    INVALID = "invalid"


@dataclass
class Snapshot:
    """推演状态快照"""
    snapshot_id: str
    checkpoint_id: str
    created_at: float
    state: Dict[str, Any]
    conclusions: List[Dict[str, Any]]
    assumptions: List[Dict[str, Any]]
    confidence_history: List[Dict[str, float]]
    checksum: str
    status: SnapshotStatus = SnapshotStatus.ACTIVE
    version: int = 1
    parent_snapshot_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'snapshot_id': self.snapshot_id,
            'checkpoint_id': self.checkpoint_id,
            'created_at': self.created_at,
            'state': self.state,
            'conclusions': self.conclusions,
            'assumptions': self.assumptions,
            'confidence_history': self.confidence_history,
            'checksum': self.checksum,
            'status': self.status.value,
            'version': self.version,
            'parent_snapshot_id': self.parent_snapshot_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """从字典创建"""
        return cls(
            snapshot_id=data['snapshot_id'],
            checkpoint_id=data['checkpoint_id'],
            created_at=data['created_at'],
            state=data['state'],
            conclusions=data['conclusions'],
            assumptions=data['assumptions'],
            confidence_history=data['confidence_history'],
            checksum=data['checksum'],
            status=SnapshotStatus(data['status']),
            version=data.get('version', 1),
            parent_snapshot_id=data.get('parent_snapshot_id'),
            metadata=data.get('metadata', {})
        )


@dataclass
class RollbackResult:
    """回滚结果"""
    success: bool
    target_snapshot_id: Optional[str]
    restored_state: Optional[Dict[str, Any]]
    recovered_conclusions: List[Dict[str, Any]]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RollbackCheckpoint:
    """
    类型D：回滚恢复检查点
    
    在每完成一个完整推演阶段后触发，保存推演状态快照，
    支持错误发现后的状态恢复。
    """
    
    def __init__(self):
        self.checkpoint_id: Optional[str] = None
        self.snapshots: Dict[str, Snapshot] = {}
        self.snapshot_counter = 0
        
        # 快照管理器配置
        self.config = {
            'max_snapshots': 100,          # 最大保存快照数
            'auto_commit_interval': 5,      # 自动提交间隔（步数）
            'enable_incremental': True,     # 启用增量快照
            'enable_compression': True,    # 启用快照压缩
        }
    
    def create(self, checkpoint_id: str, context: Dict[str, Any]) -> None:
        """创建检查点"""
        self.checkpoint_id = checkpoint_id
        if 'config' in context:
            self.config.update(context['config'])
    
    def create_snapshot(self, state: Dict[str, Any]) -> Snapshot:
        """
        创建状态快照
        
        Args:
            state: 当前推演状态
        
        Returns:
            Snapshot: 创建的快照
        """
        self.snapshot_counter += 1
        snapshot_id = f"snap_{self.snapshot_counter}"
        
        # 提取快照内容
        conclusions = state.get('conclusions', [])
        assumptions = state.get('assumptions', [])
        confidence_history = state.get('confidence_history', [])
        
        # 计算校验和
        content_for_checksum = {
            'state': state,
            'conclusions': conclusions,
            'assumptions': assumptions
        }
        checksum = self._calculate_checksum(content_for_checksum)
        
        # 确定父快照
        parent_id = self._get_latest_snapshot_id()
        
        # 创建快照
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            checkpoint_id=self.checkpoint_id,
            created_at=time.time(),
            state=deepcopy(state),
            conclusions=deepcopy(conclusions),
            assumptions=deepcopy(assumptions),
            confidence_history=deepcopy(confidence_history),
            checksum=checksum,
            status=SnapshotStatus.ACTIVE,
            version=1,
            parent_snapshot_id=parent_id
        )
        
        # 保存快照
        self.snapshots[snapshot_id] = snapshot
        
        # 清理旧快照
        self._cleanup_old_snapshots()
        
        return snapshot
    
    def restore_snapshot(self, snapshot_id: str) -> RollbackResult:
        """
        恢复状态快照
        
        Args:
            snapshot_id: 快照ID
        
        Returns:
            RollbackResult: 回滚结果
        """
        # 获取快照
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot is None:
            return RollbackResult(
                success=False,
                target_snapshot_id=snapshot_id,
                restored_state=None,
                recovered_conclusions=[],
                error_message=f"快照不存在: {snapshot_id}"
            )
        
        # 验证快照完整性
        if not self.validate_snapshot(snapshot):
            # 标记为无效
            snapshot.status = SnapshotStatus.INVALID
            return RollbackResult(
                success=False,
                target_snapshot_id=snapshot_id,
                restored_state=None,
                recovered_conclusions=[],
                error_message="快照完整性校验失败"
            )
        
        # 执行恢复
        snapshot.status = SnapshotStatus.ROLLED_BACK
        
        return RollbackResult(
            success=True,
            target_snapshot_id=snapshot_id,
            restored_state=deepcopy(snapshot.state),
            recovered_conclusions=deepcopy(snapshot.conclusions),
            metadata={
                'checkpoint_id': snapshot.checkpoint_id,
                'created_at': snapshot.created_at,
                'version': snapshot.version
            }
        )
    
    def validate_snapshot(self, snapshot: Snapshot) -> bool:
        """
        验证快照完整性
        
        Args:
            snapshot: 待验证的快照
        
        Returns:
            bool: 验证是否通过
        """
        # 重新计算校验和
        content = {
            'state': snapshot.state,
            'conclusions': snapshot.conclusions,
            'assumptions': snapshot.assumptions
        }
        expected_checksum = self._calculate_checksum(content)
        
        # 比对校验和
        return snapshot.checksum == expected_checksum
    
    def commit_snapshot(self, snapshot_id: str) -> bool:
        """
        提交快照（标记为已确认）
        
        Args:
            snapshot_id: 快照ID
        
        Returns:
            bool: 是否成功
        """
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot is None:
            return False
        
        snapshot.status = SnapshotStatus.COMMITTED
        return True
    
    def get_latest_snapshot(self) -> Optional[Snapshot]:
        """获取最新的有效快照"""
        active_snapshots = [
            s for s in self.snapshots.values()
            if s.status == SnapshotStatus.ACTIVE
        ]
        
        if not active_snapshots:
            return None
        
        return max(active_snapshots, key=lambda s: s.created_at)
    
    def get_snapshot_chain(self, snapshot_id: str) -> List[Snapshot]:
        """
        获取快照链（用于追溯）
        
        Args:
            snapshot_id: 起始快照ID
        
        Returns:
            List[Snapshot]: 快照链
        """
        chain = []
        current = self.snapshots.get(snapshot_id)
        
        while current:
            chain.append(current)
            current = self.snapshots.get(current.parent_snapshot_id) if current.parent_snapshot_id else None
        
        return chain
    
    def find_valid_checkpoint(self, error_step: int) -> Optional[str]:
        """
        查找最近的有效检查点
        
        Args:
            error_step: 出错的步骤号
        
        Returns:
            Optional[str]: 检查点ID
        """
        valid_snapshots = [
            s for s in self.snapshots.values()
            if s.status == SnapshotStatus.ACTIVE and s.created_at <= time.time()
        ]
        
        if not valid_snapshots:
            return None
        
        # 返回最新的有效快照
        latest = max(valid_snapshots, key=lambda s: s.created_at)
        return latest.checkpoint_id
    
    def _calculate_checksum(self, content: Dict[str, Any]) -> str:
        """计算内容校验和"""
        # 序列化内容（排除时间戳等不确定因素）
        serializable = self._make_serializable(content)
        json_str = json.dumps(serializable, sort_keys=True, ensure_ascii=False)
        
        # 计算SHA256
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def _make_serializable(self, obj: Any) -> Any:
        """转换为可序列化格式"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def _get_latest_snapshot_id(self) -> Optional[str]:
        """获取最新快照ID"""
        latest = self.get_latest_snapshot()
        return latest.snapshot_id if latest else None
    
    def _cleanup_old_snapshots(self) -> None:
        """清理旧快照"""
        if len(self.snapshots) <= self.config['max_snapshots']:
            return
        
        # 获取已提交和已回滚的快照
        old_snapshots = [
            s for s in self.snapshots.values()
            if s.status in (SnapshotStatus.COMMITTED, SnapshotStatus.ROLLED_BACK)
        ]
        
        # 按创建时间排序，保留最新的
        old_snapshots.sort(key=lambda s: s.created_at, reverse=True)
        
        # 删除超出限制的旧快照
        snapshots_to_delete = old_snapshots[self.config['max_snapshots']:]
        for snapshot in snapshots_to_delete:
            del self.snapshots[snapshot.snapshot_id]
    
    def get_snapshot_stats(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        total = len(self.snapshots)
        by_status = {
            'active': len([s for s in self.snapshots.values() if s.status == SnapshotStatus.ACTIVE]),
            'committed': len([s for s in self.snapshots.values() if s.status == SnapshotStatus.COMMITTED]),
            'rolled_back': len([s for s in self.snapshots.values() if s.status == SnapshotStatus.ROLLED_BACK]),
            'invalid': len([s for s in self.snapshots.values() if s.status == SnapshotStatus.INVALID]),
        }
        
        return {
            'total': total,
            'by_status': by_status,
            'latest_snapshot_id': self._get_latest_snapshot_id(),
            'config': self.config
        }
