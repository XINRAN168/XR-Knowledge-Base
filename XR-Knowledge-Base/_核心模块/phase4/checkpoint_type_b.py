# -*- coding: utf-8 -*-
"""
类型B：逻辑一致性检查点

触发时机：推演进行到关键逻辑节点时

校验内容：
- 前置结论兼容性：当前结论是否与之前结论矛盾
- 假设条件满足度：依赖的假设是否仍然成立
- 中间结果自洽：推演链条内部是否一致
- 边界条件检查：是否触及推演边界

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class ConsistencyType(Enum):
    """一致性检查类型"""
    PASS = "pass"
    FAIL_COMPATIBILITY = "fail_compatibility"
    FAIL_ASSUMPTION = "fail_assumption"
    FAIL_SELF_CONSISTENCY = "fail_self_consistency"
    FAIL_BOUNDARY = "fail_boundary"


@dataclass
class Conclusion:
    """推演结论"""
    id: str
    content: Any
    timestamp: float
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他结论ID
    assumptions: List[str] = field(default_factory=list)  # 依赖的假设ID
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Assumption:
    """推演假设"""
    id: str
    type: str  # 'factual', 'inferential', 'scenario'
    content: str
    confidence: float
    is_active: bool = True


@dataclass
class ConsistencyResult:
    """一致性检查结果"""
    is_consistent: bool
    consistency_type: ConsistencyType
    confidence: float
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogicConsistencyCheckpoint:
    """
    类型B：逻辑一致性检查点
    
    在推演进行到关键逻辑节点时触发，验证：
    - 前置结论兼容性
    - 假设条件满足度
    - 中间结果自洽性
    - 边界条件
    """
    
    def __init__(self):
        self.checkpoint_id: Optional[str] = None
        self.conclusions: Dict[str, Conclusion] = {}
        self.assumptions: Dict[str, Assumption] = {}
        self.boundary_limits: Dict[str, Any] = {}
        
        # 默认边界限制
        self.default_boundary_limits = {
            'max_steps': 1000,
            'max_depth': 50,
            'max_conclusions': 500,
            'max_assumptions': 100,
            'time_range': (-300, 300),  # 公元前年份范围
        }
    
    def create(self, checkpoint_id: str, context: Dict[str, Any]) -> None:
        """创建检查点"""
        self.checkpoint_id = checkpoint_id
        self.conclusions = context.get('conclusions', {})
        self.assumptions = context.get('assumptions', {})
        self.boundary_limits = context.get('boundary_limits', self.default_boundary_limits)
    
    def validate(self, state: Dict[str, Any]) -> ConsistencyResult:
        """
        执行逻辑一致性验证
        
        Args:
            state: 推演状态，包含当前结论、假设等
        
        Returns:
            ConsistencyResult: 一致性检查结果
        """
        current_conclusion = state.get('current_conclusion')
        all_conclusions = state.get('all_conclusions', [])
        all_assumptions = state.get('all_assumptions', [])
        
        conflicts = []
        warnings = []
        confidence_scores = []
        
        # 1. 检查前置结论兼容性
        compatibility_result = self._check_compatibility(current_conclusion, all_conclusions)
        if not compatibility_result['valid']:
            conflicts.extend(compatibility_result.get('conflicts', []))
            confidence_scores.append(0.3)
        else:
            confidence_scores.append(1.0)
        
        # 2. 检查假设条件满足度
        assumption_result = self._check_assumptions(current_conclusion, all_assumptions)
        if not assumption_result['valid']:
            conflicts.extend(assumption_result.get('violations', []))
            confidence_scores.append(0.4)
        else:
            confidence_scores.append(1.0)
        
        # 3. 检查中间结果自洽性
        self_consistency_result = self._check_self_consistency(all_conclusions)
        if not self_consistency_result['valid']:
            conflicts.extend(self_consistency_result.get('inconsistencies', []))
            warnings.append("推演链内部存在不一致")
            confidence_scores.append(0.5)
        else:
            confidence_scores.append(1.0)
        
        # 4. 检查边界条件
        boundary_result = self._check_boundaries(state)
        if not boundary_result['valid']:
            conflicts.extend(boundary_result.get('violations', []))
            confidence_scores.append(0.6)
        else:
            confidence_scores.append(1.0)
        
        # 计算综合置信度
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 1.0
        is_consistent = len(conflicts) == 0
        
        return ConsistencyResult(
            is_consistent=is_consistent,
            consistency_type=ConsistencyType.PASS if is_consistent else self._determine_failure_type(conflicts),
            confidence=overall_confidence,
            conflicts=conflicts,
            warnings=warnings,
            metadata={
                'compatibility': compatibility_result,
                'assumption': assumption_result,
                'self_consistency': self_consistency_result,
                'boundary': boundary_result
            }
        )
    
    def _check_compatibility(self, current: Conclusion, history: List[Conclusion]) -> Dict[str, Any]:
        """检查前置结论兼容性"""
        conflicts = []
        
        if current is None:
            return {'valid': True, 'conflicts': []}
        
        # 检查与历史结论的兼容性
        for hist in history:
            if hist.id == current.id:
                continue
            
            # 检查依赖关系
            if current.id in hist.dependencies:
                # 当前结论被历史结论依赖，需要检查是否矛盾
                if self._are_conflicting(hist, current):
                    conflicts.append({
                        'type': 'dependency_conflict',
                        'conclusion_a': hist.id,
                        'conclusion_b': current.id,
                        'reason': '历史结论依赖的结论与当前结论矛盾'
                    })
        
        # 检查逆向兼容性
        for hist in history:
            if hist.id in current.dependencies:
                if self._are_conflicting(current, hist):
                    conflicts.append({
                        'type': 'dependency_conflict',
                        'conclusion_a': current.id,
                        'conclusion_b': hist.id,
                        'reason': '当前结论依赖的结论与历史结论矛盾'
                    })
        
        return {
            'valid': len(conflicts) == 0,
            'conflicts': conflicts
        }
    
    def _are_conflicting(self, a: Conclusion, b: Conclusion) -> bool:
        """检查两个结论是否矛盾"""
        # 简单实现：检查内容是否直接矛盾
        if not isinstance(a.content, str) or not isinstance(b.content, str):
            return False
        
        # 矛盾词检测
        contradiction_pairs = [
            ('是', '不是'),
            ('有', '没有'),
            ('成功', '失败'),
            ('正确', '错误'),
            ('支持', '反对'),
            ('进攻', '防守'),
        ]
        
        content_a = a.content
        content_b = b.content
        
        for word_a, word_b in contradiction_pairs:
            if word_a in content_a and word_b in content_b:
                return True
            if word_b in content_a and word_a in content_b:
                return True
        
        return False
    
    def _check_assumptions(self, current: Conclusion, assumptions: List[Assumption]) -> Dict[str, Any]:
        """检查假设条件满足度"""
        violations = []
        
        if current is None or not current.assumptions:
            return {'valid': True, 'violations': []}
        
        active_assumptions = {a.id: a for a in assumptions if a.is_active}
        
        for assumption_id in current.assumptions:
            if assumption_id not in active_assumptions:
                violations.append({
                    'type': 'missing_assumption',
                    'assumption_id': assumption_id,
                    'conclusion_id': current.id,
                    'reason': '依赖的假设不存在'
                })
            elif active_assumptions[assumption_id].confidence < 0.5:
                violations.append({
                    'type': 'low_confidence_assumption',
                    'assumption_id': assumption_id,
                    'conclusion_id': current.id,
                    'confidence': active_assumptions[assumption_id].confidence,
                    'reason': f'假设置信度较低: {active_assumptions[assumption_id].confidence}'
                })
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    def _check_self_consistency(self, conclusions: List[Conclusion]) -> Dict[str, Any]:
        """检查中间结果自洽性"""
        inconsistencies = []
        
        # 构建依赖图
        dependency_graph: Dict[str, Set[str]] = {}
        for c in conclusions:
            dependency_graph[c.id] = set(c.dependencies)
        
        # 检测循环依赖
        cycles = self._detect_cycles(dependency_graph)
        if cycles:
            inconsistencies.extend([
                {'type': 'circular_dependency', 'cycle': cycle}
                for cycle in cycles
            ])
        
        # 检测矛盾结论
        for i, c1 in enumerate(conclusions):
            for c2 in conclusions[i+1:]:
                if c1.id in c2.dependencies and c2.id in c1.dependencies:
                    if self._are_conflicting(c1, c2):
                        inconsistencies.append({
                            'type': 'mutual_conflict',
                            'conclusion_a': c1.id,
                            'conclusion_b': c2.id
                        })
        
        return {
            'valid': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies
        }
    
    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """检测有向图中的环"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # 发现环
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _check_boundaries(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """检查边界条件"""
        violations = []
        
        step_count = state.get('step_count', 0)
        depth = state.get('depth', 0)
        conclusion_count = state.get('conclusion_count', 0)
        
        # 检查步骤数
        max_steps = self.boundary_limits.get('max_steps', 1000)
        if step_count >= max_steps:
            violations.append({
                'type': 'max_steps_exceeded',
                'current': step_count,
                'limit': max_steps,
                'reason': '推演步骤数达到上限'
            })
        
        # 检查深度
        max_depth = self.boundary_limits.get('max_depth', 50)
        if depth >= max_depth:
            violations.append({
                'type': 'max_depth_exceeded',
                'current': depth,
                'limit': max_depth,
                'reason': '推演深度达到上限'
            })
        
        # 检查结论数
        max_conclusions = self.boundary_limits.get('max_conclusions', 500)
        if conclusion_count >= max_conclusions:
            violations.append({
                'type': 'max_conclusions_exceeded',
                'current': conclusion_count,
                'limit': max_conclusions,
                'reason': '结论数量达到上限'
            })
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    def _determine_failure_type(self, conflicts: List[Dict[str, Any]]) -> ConsistencyType:
        """确定失败类型"""
        if not conflicts:
            return ConsistencyType.PASS
        
        # 按优先级确定失败类型
        for conflict in conflicts:
            conflict_type = conflict.get('type', '')
            if 'dependency' in conflict_type or 'mutual' in conflict_type:
                return ConsistencyType.FAIL_COMPATIBILITY
            if 'assumption' in conflict_type:
                return ConsistencyType.FAIL_ASSUMPTION
            if 'circular' in conflict_type:
                return ConsistencyType.FAIL_SELF_CONSISTENCY
            if 'max_' in conflict_type:
                return ConsistencyType.FAIL_BOUNDARY
        
        return ConsistencyType.FAIL_SELF_CONSISTENCY
