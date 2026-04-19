# -*- coding: utf-8 -*-
"""
不确定性追踪机制

假设分类：
- 事实性假设 (Factual): 基于可验证事实
- 推断性假设 (Inferential): 基于现有信息推断
- 情景性假设 (Scenario): 假设性情景构建

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AssumptionType(Enum):
    """假设类型"""
    FACTUAL = "factual"           # 事实性假设
    INFERENTIAL = "inferential"   # 推断性假设
    SCENARIO = "scenario"         # 情景性假设


class UncertaintyTag(Enum):
    """不确定性标签"""
    CERTAIN = "U_certain"         # 确定性
    ASSUMPTION = "U_assumption"   # 假设性
    BRANCH = "U_branch"           # 分支性
    CONFLICT = "U_conflict"       # 矛盾性


@dataclass
class Assumption:
    """推演假设"""
    id: str
    type: AssumptionType
    content: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = ""
    is_active: bool = True
    
    @property
    def base_confidence_range(self) -> Tuple[float, float]:
        """获取基础置信度范围"""
        ranges = {
            AssumptionType.FACTUAL: (0.95, 0.9999),
            AssumptionType.INFERENTIAL: (0.30, 0.90),
            AssumptionType.SCENARIO: (0.0, 0.1),
        }
        return ranges.get(self.type, (0.0, 1.0))


@dataclass
class UncertaintyLabel:
    """不确定性标签"""
    tag: UncertaintyTag
    source: str
    reason: str
    related_assumptions: List[str] = field(default_factory=list)
    propagated_from: List[str] = field(default_factory=list)


@dataclass
class ConfidenceCalculation:
    """置信度计算结果"""
    assumption_confidence: float
    evidence_confidence: float
    logic_confidence: float
    source_confidence: float
    final_confidence: float
    weights: Dict[str, float]


@dataclass
class CumulativeConfidenceResult:
    """累积置信度结果"""
    assumptions: List[Assumption]
    cumulative_confidence: float
    below_threshold: bool
    threshold: float
    warnings: List[str]


@dataclass
class PropagationResult:
    """标签传播结果"""
    original_tag: UncertaintyTag
    propagated_tags: List[UncertaintyTag]
    final_tag: UncertaintyTag
    propagation_chain: List[str]


class UncertaintyTracker:
    """
    不确定性追踪机制
    
    追踪推演过程中的假设分类、置信度计算和不确定性标签传播。
    """
    
    def __init__(self):
        self.assumptions: Dict[str, Assumption] = {}
        self.assumption_counter = 0
        
        # 置信度权重配置
        self.weights = {
            AssumptionType.FACTUAL: {'evidence': 0.50, 'logic': 0.30, 'source': 0.20},
            AssumptionType.INFERENTIAL: {'evidence': 0.30, 'logic': 0.40, 'source': 0.30},
            AssumptionType.SCENARIO: {'evidence': 0.20, 'logic': 0.50, 'source': 0.30},
        }
        
        # 标签优先级
        self.tag_priority = {
            UncertaintyTag.CONFLICT: 4,
            UncertaintyTag.ASSUMPTION: 3,
            UncertaintyTag.BRANCH: 2,
            UncertaintyTag.CERTAIN: 1,
        }
        
        # 置信度警告阈值
        self.confidence_threshold = 0.95
    
    def create_assumption(
        self,
        content: str,
        assumption_type: AssumptionType,
        evidence: List[str] = None,
        source: str = ""
    ) -> Assumption:
        """
        创建假设
        
        Args:
            content: 假设内容
            assumption_type: 假设类型
            evidence: 证据列表
            source: 来源
        
        Returns:
            Assumption: 创建的假设
        """
        self.assumption_counter += 1
        assumption_id = f"assumption_{self.assumption_counter}"
        
        # 计算基础置信度
        base_range = self._get_base_confidence_range(assumption_type)
        base_confidence = sum(base_range) / 2
        
        assumption = Assumption(
            id=assumption_id,
            type=assumption_type,
            content=content,
            evidence=evidence or [],
            confidence=base_confidence,
            source=source
        )
        
        self.assumptions[assumption_id] = assumption
        return assumption
    
    def calculate_assumption_confidence(
        self,
        assumption: Assumption,
        evidence_strength: float = 0.5,
        logic_consistency: float = 0.5,
        source_reliability: float = 0.5
    ) -> ConfidenceCalculation:
        """
        计算假设置信度
        
        Args:
            assumption: 假设
            evidence_strength: 证据强度
            logic_consistency: 逻辑一致性
            source_reliability: 来源可靠性
        
        Returns:
            ConfidenceCalculation: 置信度计算结果
        """
        # 获取权重
        weights = self.weights.get(assumption.type, self.weights[AssumptionType.INFERENTIAL])
        
        # 计算各维度置信度
        evidence_conf = evidence_strength
        logic_conf = logic_consistency
        source_conf = source_reliability
        
        # 综合计算
        final_conf = (
            weights['evidence'] * evidence_conf +
            weights['logic'] * logic_conf +
            weights['source'] * source_conf
        )
        
        # 应用基础置信度范围
        base_range = assumption.base_confidence_range
        adjusted_conf = base_range[0] + (base_range[1] - base_range[0]) * final_conf
        
        return ConfidenceCalculation(
            assumption_confidence=adjusted_conf,
            evidence_confidence=evidence_conf,
            logic_confidence=logic_conf,
            source_confidence=source_conf,
            final_confidence=adjusted_conf,
            weights=weights
        )
    
    def calculate_cumulative_confidence(
        self,
        assumption_ids: List[str],
        threshold: float = 0.95
    ) -> CumulativeConfidenceResult:
        """
        计算累积置信度
        
        乘法原则：C_total = C_a1 × C_a2 × ... × C_an
        
        Args:
            assumption_ids: 假设ID列表
            threshold: 警告阈值
        
        Returns:
            CumulativeConfidenceResult: 累积置信度结果
        """
        assumptions = [self.assumptions.get(aid) for aid in assumption_ids if aid in self.assumptions]
        warnings = []
        
        if not assumptions:
            return CumulativeConfidenceResult(
                assumptions=[],
                cumulative_confidence=1.0,
                below_threshold=False,
                threshold=threshold,
                warnings=["无有效假设"]
            )
        
        # 乘法累积
        cumulative = 1.0
        for assumption in assumptions:
            cumulative *= assumption.confidence
        
        below_threshold = cumulative < threshold
        
        if below_threshold:
            warnings.append(
                f"累积置信度 {cumulative:.4f} 低于阈值 {threshold}，结论不确定性高"
            )
            
            # 添加具体警告
            low_confidence_assumptions = [
                f"{a.id}({a.confidence:.2f})" 
                for a in assumptions if a.confidence < 0.5
            ]
            if low_confidence_assumptions:
                warnings.append(f"低置信度假设: {', '.join(low_confidence_assumptions)}")
        
        return CumulativeConfidenceResult(
            assumptions=assumptions,
            cumulative_confidence=cumulative,
            below_threshold=below_threshold,
            threshold=threshold,
            warnings=warnings
        )
    
    def tag_conclusion(self, conclusion: Dict[str, Any], context: Dict[str, Any]) -> UncertaintyLabel:
        """
        为结论添加不确定性标签
        
        Args:
            conclusion: 结论
            context: 上下文
        
        Returns:
            UncertaintyLabel: 不确定性标签
        """
        # 确定基础标签
        has_assumptions = len(context.get('assumption_ids', [])) > 0
        is_branch = context.get('is_branch', False)
        has_conflict = context.get('has_conflict', False)
        
        if has_conflict:
            tag = UncertaintyTag.CONFLICT
            reason = "存在逻辑矛盾"
        elif has_assumptions:
            tag = UncertaintyTag.ASSUMPTION
            reason = "基于假设的结论"
        elif is_branch:
            tag = UncertaintyTag.BRANCH
            reason = "分支选择结论"
        else:
            tag = UncertaintyTag.CERTAIN
            reason = "确定性结论"
        
        return UncertaintyLabel(
            tag=tag,
            source=conclusion.get('id', ''),
            reason=reason,
            related_assumptions=context.get('assumption_ids', []),
            propagated_from=[]
        )
    
    def propagate_tag(self, current_tag: UncertaintyLabel, history_tags: List[UncertaintyLabel]) -> PropagationResult:
        """
        传播不确定性标签
        
        规则：最终不确定性 = max(所有前置不确定性)
        
        Args:
            current_tag: 当前标签
            history_tags: 历史标签列表
        
        Returns:
            PropagationResult: 传播结果
        """
        all_tags = [current_tag] + history_tags
        propagated_tags = [t.tag for t in all_tags]
        
        # 计算最终标签（取最高优先级）
        final_tag = max(
            propagated_tags,
            key=lambda t: self.tag_priority.get(t, 0)
        )
        
        # 构建传播链
        propagation_chain = [t.source for t in all_tags if t.source]
        
        return PropagationResult(
            original_tag=current_tag.tag,
            propagated_tags=propagated_tags,
            final_tag=final_tag,
            propagation_chain=propagation_chain
        )
    
    def classify_assumption(self, content: str) -> Tuple[AssumptionType, float]:
        """
        分类假设
        
        Args:
            content: 假设内容
        
        Returns:
            Tuple[AssumptionType, float]: 假设类型和置信度
        """
        content_lower = content.lower()
        
        # 事实性关键词
        factual_keywords = ['出生', '死亡', '发生在', '是', '存在', '位于']
        # 推断性关键词
        inferential_keywords = ['可能', '也许', '推测', '认为', '估计', '似乎']
        # 情景性关键词
        scenario_keywords = ['假设', '假如', '假设如果', '设想', '虚构', '想象']
        
        # 评分
        scores = {
            AssumptionType.FACTUAL: sum(1 for k in factual_keywords if k in content_lower),
            AssumptionType.INFERENTIAL: sum(1 for k in inferential_keywords if k in content_lower),
            AssumptionType.SCENARIO: sum(1 for k in scenario_keywords if k in content_lower),
        }
        
        # 确定类型
        max_score = max(scores.values())
        if max_score == 0:
            return AssumptionType.INFERENTIAL, 0.5
        
        for atype, score in scores.items():
            if score == max_score:
                # 计算置信度
                confidence = min(0.5 + score * 0.15, 0.95)
                return atype, confidence
        
        return AssumptionType.INFERENTIAL, 0.5
    
    def get_assumption_stats(self) -> Dict[str, Any]:
        """获取假设统计"""
        total = len(self.assumptions)
        by_type = {
            'factual': len([a for a in self.assumptions.values() if a.type == AssumptionType.FACTUAL]),
            'inferential': len([a for a in self.assumptions.values() if a.type == AssumptionType.INFERENTIAL]),
            'scenario': len([a for a in self.assumptions.values() if a.type == AssumptionType.SCENARIO]),
        }
        
        avg_confidence = (
            sum(a.confidence for a in self.assumptions.values()) / total 
            if total > 0 else 0
        )
        
        return {
            'total': total,
            'by_type': by_type,
            'average_confidence': avg_confidence,
            'threshold': self.confidence_threshold
        }
    
    def _get_base_confidence_range(self, assumption_type: AssumptionType) -> Tuple[float, float]:
        """获取基础置信度范围"""
        ranges = {
            AssumptionType.FACTUAL: (0.95, 0.9999),
            AssumptionType.INFERENTIAL: (0.30, 0.90),
            AssumptionType.SCENARIO: (0.0, 0.1),
        }
        return ranges.get(assumption_type, (0.0, 1.0))
