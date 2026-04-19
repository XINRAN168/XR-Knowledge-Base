# -*- coding: utf-8 -*-
"""
类型A：数据入口检查点

触发时机：推演步骤需要读取外部数据时

校验内容：
- 数据存在性：所需数据是否存在
- 数据完整性：关键字段是否缺失
- 数据时效性：数据是否在有效期内
- 数据合理性：数值是否在合理范围内

作者：云澜AI Agent
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ValidationType(Enum):
    """验证类型"""
    PASS = "pass"
    FAIL_EXISTENCE = "fail_existence"
    FAIL_COMPLETENESS = "fail_completeness"
    FAIL_TIMELINESS = "fail_timeliness"
    FAIL_REASONABLENESS = "fail_reasonableness"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    validation_type: ValidationType
    confidence: float
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        status = "✅ PASS" if self.is_valid else "❌ FAIL"
        return f"{status} [{self.validation_type.value}] 置信度: {self.confidence:.4f}"


@dataclass
class DataRequirements:
    """数据需求定义"""
    required_fields: List[str]  # 必填字段
    optional_fields: List[str] = field(default_factory=list)  # 可选字段
    validity_period: Optional[timedelta] = None  # 有效期
    value_ranges: Dict[str, tuple] = field(default_factory=dict)  # 数值范围
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DataRequirements':
        """从字典创建数据需求"""
        return cls(
            required_fields=data.get('required_fields', []),
            optional_fields=data.get('optional_fields', []),
            validity_period=data.get('validity_period'),
            value_ranges=data.get('value_ranges', {})
        )


class DataEntryCheckpoint:
    """
    类型A：数据入口检查点
    
    在推演步骤需要读取外部数据时触发，验证数据的存在性、
    完整性、时效性和合理性。
    """
    
    def __init__(self):
        self.check_types = ['existence', 'completeness', 'timeliness', 'reasonableness']
        self.default_validity_days = 30  # 默认有效期30天
    
    def validate(self, data: Any, requirements: DataRequirements) -> ValidationResult:
        """
        执行数据入口验证
        
        Args:
            data: 待验证的数据
            requirements: 数据需求定义
        
        Returns:
            ValidationResult: 验证结果
        """
        issues = []
        confidence_scores = []
        
        # 1. 检查存在性
        existence_result = self._check_existence(data)
        if not existence_result['valid']:
            issues.append(f"数据不存在: {existence_result.get('reason', '未知原因')}")
            confidence_scores.append(0.0)
        else:
            confidence_scores.append(1.0)
        
        # 如果数据不存在，直接返回失败
        if not existence_result['valid']:
            return ValidationResult(
                is_valid=False,
                validation_type=ValidationType.FAIL_EXISTENCE,
                confidence=0.0,
                issues=issues,
                metadata=existence_result
            )
        
        # 2. 检查完整性
        completeness_result = self._check_completeness(data, requirements)
        if not completeness_result['valid']:
            issues.append(f"数据不完整: {', '.join(completeness_result.get('missing_fields', []))}")
            confidence_scores.append(0.5)
        else:
            confidence_scores.append(1.0)
        
        # 3. 检查时效性
        timeliness_result = self._check_timeliness(data, requirements)
        if not timeliness_result['valid']:
            issues.append(f"数据过期: {timeliness_result.get('reason', '超过有效期')}")
            confidence_scores.append(0.7)  # 时效性问题降级处理
        else:
            confidence_scores.append(1.0)
        
        # 4. 检查合理性
        reasonableness_result = self._check_reasonableness(data, requirements)
        if not reasonableness_result['valid']:
            issues.append(f"数据不合理: {', '.join(reasonableness_result.get('invalid_fields', []))}")
            confidence_scores.append(0.6)  # 合理性问题降级处理
        else:
            confidence_scores.append(1.0)
        
        # 计算综合置信度
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type=ValidationType.PASS if is_valid else self._determine_failure_type(issues),
            confidence=overall_confidence,
            issues=issues,
            metadata={
                'existence': existence_result,
                'completeness': completeness_result,
                'timeliness': timeliness_result,
                'reasonableness': reasonableness_result
            }
        )
    
    def _check_existence(self, data: Any) -> Dict[str, Any]:
        """检查数据存在性"""
        if data is None:
            return {'valid': False, 'reason': '数据为None'}
        
        if isinstance(data, dict) and len(data) == 0:
            return {'valid': False, 'reason': '数据为空字典'}
        
        if isinstance(data, (list, str)) and len(data) == 0:
            return {'valid': False, 'reason': '数据为空集合'}
        
        return {'valid': True}
    
    def _check_completeness(self, data: Any, requirements: DataRequirements) -> Dict[str, Any]:
        """检查数据完整性"""
        if not isinstance(data, dict):
            return {'valid': True, 'missing_fields': []}
        
        missing_fields = []
        for field in requirements.required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields
        }
    
    def _check_timeliness(self, data: Any, requirements: DataRequirements) -> Dict[str, Any]:
        """检查数据时效性"""
        # 如果没有指定有效期，直接通过
        if requirements.validity_period is None:
            return {'valid': True}
        
        if not isinstance(data, dict):
            return {'valid': True}
        
        # 检查数据中的时间戳
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'data_time']
        
        for field in timestamp_fields:
            if field in data:
                try:
                    if isinstance(data[field], str):
                        data_time = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    elif isinstance(data[field], datetime):
                        data_time = data[field]
                    else:
                        continue
                    
                    # 检查是否在有效期内
                    age = datetime.now() - data_time.replace(tzinfo=None)
                    if age > requirements.validity_period:
                        return {
                            'valid': False,
                            'reason': f'数据已过期 {age.days} 天，超过有效期 {requirements.validity_period.days} 天',
                            'age_days': age.days
                        }
                    return {'valid': True}
                except (ValueError, TypeError):
                    continue
        
        # 没有找到时间戳，检查是否有默认有效期
        return {'valid': True}
    
    def _check_reasonableness(self, data: Any, requirements: DataRequirements) -> Dict[str, Any]:
        """检查数据合理性"""
        if not isinstance(data, dict):
            return {'valid': True, 'invalid_fields': []}
        
        invalid_fields = []
        
        for field, (min_val, max_val) in requirements.value_ranges.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, (int, float)):
                    invalid_fields.append(f"{field}(类型错误:{type(value).__name__})")
                elif value < min_val or value > max_val:
                    invalid_fields.append(f"{field}(值{value}超出范围[{min_val},{max_val}])")
        
        return {
            'valid': len(invalid_fields) == 0,
            'invalid_fields': invalid_fields
        }
    
    def _determine_failure_type(self, issues: List[str]) -> ValidationType:
        """确定失败类型"""
        for issue in issues:
            if '不存在' in issue:
                return ValidationType.FAIL_EXISTENCE
            if '不完整' in issue:
                return ValidationType.FAIL_COMPLETENESS
            if '过期' in issue:
                return ValidationType.FAIL_TIMELINESS
            if '不合理' in issue:
                return ValidationType.FAIL_REASONABLENESS
        return ValidationType.FAIL_COMPLETENESS
    
    def validate_multiple(self, data_list: List[Any], requirements: DataRequirements) -> List[ValidationResult]:
        """批量验证数据"""
        return [self.validate(data, requirements) for data in data_list]
