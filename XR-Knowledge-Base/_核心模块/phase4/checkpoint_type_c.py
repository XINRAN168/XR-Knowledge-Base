# -*- coding: utf-8 -*-
"""
类型C：置信度评估检查点

触发时机：每个分支选择或结论输出前

校验内容：
- 路径置信度：从起点到当前点的累积置信度
- 结论置信度：当前结论的独立置信度
- 替代路径存在性：是否存在其他高置信度路径

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConfidenceLevel(Enum):
    """置信度等级"""
    EXECUTE_AUTO = "execute_auto"      # C >= 0.9999，直接执行
    EXECUTE_FAST = "execute_fast"       # 0.9990 <= C < 0.9999，快速执行
    EXECUTE_WARN = "execute_warn"       # 0.9500 <= C < 0.9990，带警告执行
    PAUSE_REVIEW = "pause_review"       # 0.8000 <= C < 0.9500，暂缓执行
    REJECT = "reject"                   # C < 0.8000，拒绝执行


@dataclass
class PathConfidence:
    """路径置信度"""
    path_id: str
    steps: List[str]  # 路径上的步骤ID列表
    cumulative_confidence: float
    step_confidences: List[float]  # 每步的置信度
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """获取置信度等级"""
        if self.cumulative_confidence >= 0.9999:
            return ConfidenceLevel.EXECUTE_AUTO
        elif self.cumulative_confidence >= 0.9990:
            return ConfidenceLevel.EXECUTE_FAST
        elif self.cumulative_confidence >= 0.9500:
            return ConfidenceLevel.EXECUTE_WARN
        elif self.cumulative_confidence >= 0.8000:
            return ConfidenceLevel.PAUSE_REVIEW
        else:
            return ConfidenceLevel.REJECT


@dataclass
class ConclusionConfidence:
    """结论置信度"""
    conclusion_id: str
    independent_confidence: float  # 结论独立置信度
    base_confidence: float         # 基础置信度
    adjustment_factors: List[Dict[str, float]] = field(default_factory=list)  # 调整因子
    
    @property
    def final_confidence(self) -> float:
        """计算最终置信度"""
        confidence = self.base_confidence
        for factor in self.adjustment_factors:
            confidence *= factor.get('multiplier', 1.0)
            confidence += factor.get('offset', 0.0)
        return max(0.0, min(1.0, confidence))  # 限制在[0, 1]范围内


@dataclass
class AlternativePath:
    """替代路径"""
    path_id: str
    confidence: float
    divergence_point: str  # 分叉点
    main_differences: List[str] = field(default_factory=list)


@dataclass
class ConfidenceEvaluationResult:
    """置信度评估结果"""
    path_confidence: PathConfidence
    conclusion_confidence: ConclusionConfidence
    alternative_paths: List[AlternativePath] = field(default_factory=list)
    decision: ConfidenceLevel
    should_block: bool
    block_type: Optional[str] = None  # 'hard', 'soft', 'degraded', None
    warnings: List[str] = field(default_factory=list)


class ConfidenceCheckpoint:
    """
    类型C：置信度评估检查点
    
    在每个分支选择或结论输出前触发，评估：
    - 路径置信度：从起点到当前点的累积置信度
    - 结论置信度：当前结论的独立置信度
    - 替代路径存在性：是否存在其他高置信度路径
    """
    
    def __init__(self):
        self.checkpoint_id: Optional[str] = None
        
        # 置信度阈值配置
        self.thresholds = {
            'auto_execute': 0.9999,
            'fast_execute': 0.9990,
            'warn_execute': 0.9500,
            'pause_review': 0.8000,
        }
    
    def create(self, checkpoint_id: str, context: Dict[str, Any]) -> None:
        """创建检查点"""
        self.checkpoint_id = checkpoint_id
        if 'thresholds' in context:
            self.thresholds.update(context['thresholds'])
    
    def evaluate(self, state: Dict[str, Any]) -> ConfidenceEvaluationResult:
        """
        执行置信度评估
        
        Args:
            state: 推演状态
        
        Returns:
            ConfidenceEvaluationResult: 置信度评估结果
        """
        # 1. 计算路径置信度
        path_confidence = self._calculate_path_confidence(
            state.get('path_steps', []),
            state.get('step_confidences', [])
        )
        
        # 2. 计算结论置信度
        conclusion_confidence = self._calculate_conclusion_confidence(
            state.get('conclusion', {}),
            state.get('base_confidence', 1.0),
            state.get('adjustments', [])
        )
        
        # 3. 检查替代路径
        alternative_paths = self._check_alternative_paths(
            state.get('current_path_id'),
            state.get('all_paths', [])
        )
        
        # 4. 综合决策
        decision, should_block, block_type = self._make_decision(
            path_confidence.cumulative_confidence,
            conclusion_confidence.final_confidence
        )
        
        # 5. 生成警告
        warnings = self._generate_warnings(
            path_confidence,
            conclusion_confidence,
            alternative_paths
        )
        
        return ConfidenceEvaluationResult(
            path_confidence=path_confidence,
            conclusion_confidence=conclusion_confidence,
            alternative_paths=alternative_paths,
            decision=decision,
            should_block=should_block,
            block_type=block_type,
            warnings=warnings
        )
    
    def _calculate_path_confidence(self, steps: List[str], step_confidences: List[float]) -> PathConfidence:
        """
        计算累积路径置信度
        
        使用乘法原则：累积置信度 = Π(每步置信度)
        """
        path_id = "_".join(steps) if steps else "root"
        
        if not step_confidences:
            # 没有步骤置信度，返回默认高置信度
            return PathConfidence(
                path_id=path_id,
                steps=steps,
                cumulative_confidence=1.0,
                step_confidences=[]
            )
        
        # 乘法累积
        cumulative = 1.0
        for conf in step_confidences:
            cumulative *= conf
        
        return PathConfidence(
            path_id=path_id,
            steps=steps,
            cumulative_confidence=cumulative,
            step_confidences=step_confidences
        )
    
    def _calculate_conclusion_confidence(
        self, 
        conclusion: Dict[str, Any],
        base_confidence: float,
        adjustments: List[Dict[str, float]]
    ) -> ConclusionConfidence:
        """计算结论置信度"""
        conclusion_id = conclusion.get('id', 'unknown')
        
        return ConclusionConfidence(
            conclusion_id=conclusion_id,
            independent_confidence=conclusion.get('confidence', base_confidence),
            base_confidence=base_confidence,
            adjustment_factors=adjustments
        )
    
    def _check_alternative_paths(self, current_path_id: str, all_paths: List[Dict[str, Any]]) -> List[AlternativePath]:
        """检查替代路径"""
        alternatives = []
        
        for path in all_paths:
            if path.get('id') != current_path_id:
                alternatives.append(AlternativePath(
                    path_id=path.get('id'),
                    confidence=path.get('confidence', 0.0),
                    divergence_point=path.get('divergence_point', ''),
                    main_differences=path.get('differences', [])
                ))
        
        # 按置信度排序
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        
        return alternatives
    
    def _make_decision(self, path_conf: float, conclusion_conf: float) -> Tuple[ConfidenceLevel, bool, Optional[str]]:
        """
        做出置信度决策
        
        Returns:
            (decision, should_block, block_type)
        """
        # 取路径置信度和结论置信度的最小值
        min_confidence = min(path_conf, conclusion_conf)
        
        # 根据阈值确定决策
        if min_confidence >= self.thresholds['auto_execute']:
            return (ConfidenceLevel.EXECUTE_AUTO, False, None)
        elif min_confidence >= self.thresholds['fast_execute']:
            return (ConfidenceLevel.EXECUTE_FAST, False, None)
        elif min_confidence >= self.thresholds['warn_execute']:
            return (ConfidenceLevel.EXECUTE_WARN, False, 'degraded')
        elif min_confidence >= self.thresholds['pause_review']:
            return (ConfidenceLevel.PAUSE_REVIEW, True, 'soft')
        else:
            return (ConfidenceLevel.REJECT, True, 'hard')
    
    def _generate_warnings(
        self,
        path_confidence: PathConfidence,
        conclusion_confidence: ConclusionConfidence,
        alternative_paths: List[AlternativePath]
    ) -> List[str]:
        """生成警告信息"""
        warnings = []
        
        # 检查路径置信度
        if path_confidence.cumulative_confidence < 0.95:
            warnings.append(f"路径置信度较低: {path_confidence.cumulative_confidence:.4f}")
        
        # 检查结论置信度
        if conclusion_confidence.final_confidence < 0.95:
            warnings.append(f"结论置信度较低: {conclusion_confidence.final_confidence:.4f}")
        
        # 检查替代路径
        if alternative_paths:
            best_alt = alternative_paths[0]
            if best_alt.confidence > path_confidence.cumulative_confidence * 0.9:
                warnings.append(
                    f"存在更高置信度替代路径: {best_alt.path_id} "
                    f"(置信度: {best_alt.confidence:.4f})"
                )
        
        return warnings
    
    def validate_confidence(self, confidence: float, required_level: ConfidenceLevel) -> bool:
        """验证置信度是否满足要求"""
        level = self._get_level(confidence)
        return self._level_sufficient(level, required_level)
    
    def _get_level(self, confidence: float) -> ConfidenceLevel:
        """获取置信度等级"""
        if confidence >= 0.9999:
            return ConfidenceLevel.EXECUTE_AUTO
        elif confidence >= 0.9990:
            return ConfidenceLevel.EXECUTE_FAST
        elif confidence >= 0.9500:
            return ConfidenceLevel.EXECUTE_WARN
        elif confidence >= 0.8000:
            return ConfidenceLevel.PAUSE_REVIEW
        else:
            return ConfidenceLevel.REJECT
    
    def _level_sufficient(self, actual: ConfidenceLevel, required: ConfidenceLevel) -> bool:
        """检查等级是否满足要求"""
        level_order = [
            ConfidenceLevel.REJECT,
            ConfidenceLevel.PAUSE_REVIEW,
            ConfidenceLevel.EXECUTE_WARN,
            ConfidenceLevel.EXECUTE_FAST,
            ConfidenceLevel.EXECUTE_AUTO
        ]
        return level_order.index(actual) >= level_order.index(required)
