# 云澜记忆系统 V3.0 Phase 3 - 稀疏激活机制

"""
稀疏激活机制模块
- 四级阈值配置（strict/normal/loose/explore）
- Top-K激活实现
- 三级降级策略
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ActivationMode(Enum):
    """激活模式枚举"""
    STRICT = "strict"      # 核心决策、高精度要求
    NORMAL = "normal"      # 标准对话（默认）
    LOOSE = "loose"        # 探索性对话、宽泛场景
    EXPLORE = "explore"    # 主人说"随便聊聊"


# 四级阈值配置
THRESHOLD_CONFIG = {
    ActivationMode.STRICT: {
        "threshold": 0.7,
        "k_max": 3,
        "description": "核心决策、高精度要求"
    },
    ActivationMode.NORMAL: {
        "threshold": 0.6,
        "k_max": 5,
        "description": "标准对话（默认）"
    },
    ActivationMode.LOOSE: {
        "threshold": 0.5,
        "k_max": 8,
        "description": "探索性对话、宽泛场景"
    },
    ActivationMode.EXPLORE: {
        "threshold": 0.4,
        "k_max": 10,
        "description": "主人说'随便聊聊'"
    }
}

# 默认激活神经元（降级策略第二级）
DEFAULT_NEURONS = ["谋士层", "主人层", "商战层"]


@dataclass
class ActivationResult:
    """激活结果"""
    status: str                    # success/explore_mode/default_activated
    activated_neurons: List[Dict]
    mode: str
    threshold_used: float
    k_max: int
    fallback_level: Optional[int] = None  # 降级层级


class SparseActivator:
    """稀疏激活器 - 精准激活相关神经元"""
    
    def __init__(self):
        self.current_mode = ActivationMode.NORMAL
    
    def set_mode(self, mode: ActivationMode):
        """设置激活模式"""
        self.current_mode = mode
    
    def activate(
        self, 
        question: str, 
        neurons: List[Dict],
        mode: ActivationMode = None
    ) -> ActivationResult:
        """
        稀疏激活主函数
        
        参数：
        - question: 用户问题
        - neurons: 可用神经元列表
        - mode: 激活模式（可选，默认使用当前模式）
        
        返回：ActivationResult
        """
        if mode is None:
            mode = self.current_mode
        
        config = THRESHOLD_CONFIG[mode]
        threshold = config["threshold"]
        k_max = config["k_max"]
        
        # Step 1: 计算相关性分数
        scored_neurons = []
        for neuron in neurons:
            relevance = self.calculate_relevance(question, neuron)
            scored_neurons.append({
                "neuron": neuron,
                "relevance": relevance
            })
        
        # Step 2: 过滤达标神经元
        qualified = [n for n in scored_neurons if n["relevance"] >= threshold]
        
        # Step 3: 按分数降序排列
        qualified.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Step 4: 取前K个
        activated = qualified[:k_max]
        
        if activated:
            return ActivationResult(
                status="success",
                activated_neurons=[a["neuron"] for a in activated],
                mode=mode.value,
                threshold_used=threshold,
                k_max=k_max
            )
        
        # Step 5: 第一降级 - 降低阈值
        result = self._degrade_threshold(question, neurons, threshold, k_max, mode)
        if result:
            return result
        
        # Step 6: 第二降级 - 激活默认神经元
        result = self._degrade_default(k_max)
        if result:
            return result
        
        # Step 7: 第三降级 - 进入探索模式
        return ActivationResult(
            status="explore_mode",
            activated_neurons=[],
            mode=mode.value,
            threshold_used=threshold,
            k_max=k_max,
            fallback_level=3
        )
    
    def _degrade_threshold(
        self,
        question: str,
        neurons: List[Dict],
        original_threshold: float,
        k_max: int,
        original_mode: ActivationMode
    ) -> Optional[ActivationResult]:
        """
        第一降级：降低阈值重试
        
        阈值最低降至0.3
        """
        current_threshold = original_threshold - 0.1
        min_threshold = 0.3
        
        while current_threshold >= min_threshold:
            scored_neurons = []
            for neuron in neurons:
                relevance = self.calculate_relevance(question, neuron)
                scored_neurons.append({
                    "neuron": neuron,
                    "relevance": relevance
                })
            
            qualified = [n for n in scored_neurons if n["relevance"] >= current_threshold]
            qualified.sort(key=lambda x: x["relevance"], reverse=True)
            activated = qualified[:k_max]
            
            if activated:
                return ActivationResult(
                    status="success",
                    activated_neurons=[a["neuron"] for a in activated],
                    mode=original_mode.value,
                    threshold_used=current_threshold,
                    k_max=k_max,
                    fallback_level=1
                )
            
            current_threshold -= 0.1
        
        return None
    
    def _degrade_default(self, k_max: int) -> Optional[ActivationResult]:
        """
        第二降级：激活默认神经元
        
        返回最多K_max个默认神经元
        """
        default_neurons = [
            {"id": "neuron_001", "name": "谋士层"},
            {"id": "neuron_002", "name": "主人层"},
            {"id": "neuron_003", "name": "商战层"}
        ]
        
        if default_neurons:
            return ActivationResult(
                status="default_activated",
                activated_neurons=default_neurons[:k_max],
                mode="default",
                threshold_used=0.0,
                k_max=k_max,
                fallback_level=2
            )
        
        return None
    
    def calculate_relevance(self, question: str, neuron: Dict) -> float:
        """
        计算问题与神经元的相关性分数
        
        参数：
        - question: 用户问题
        - neuron: 神经元数据
        
        返回：0-1的相关性分数
        """
        # 关键词匹配
        question_keywords = self._extract_keywords(question)
        neuron_keywords = neuron.get("keywords", [])
        
        if not question_keywords or not neuron_keywords:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(set(question_keywords) & set(neuron_keywords))
        union = len(set(question_keywords) | set(neuron_keywords))
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # 考虑神经元类型匹配
        type_bonus = 0.0
        for keyword in question_keywords:
            if keyword in neuron.get("type_tags", []):
                type_bonus += 0.1
        
        return min(1.0, jaccard + type_bonus)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词（简化版）"""
        # 去除标点符号
        import re
        text = re.sub(r'[^\w\s]', '', text)
        
        # 简单分词
        words = text.split()
        
        # 过滤停用词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        return [w for w in words if len(w) >= 2 and w not in stopwords]


# ==================== 单元测试 ====================

def test_sparse_activation():
    """测试稀疏激活机制"""
    activator = SparseActivator()
    
    # 模拟神经元数据
    neurons = [
        {"id": "n1", "name": "谋士层", "keywords": ["战略", "谋略", "决策"], "type_tags": ["战略"]},
        {"id": "n2", "name": "毒士层", "keywords": ["阴谋", "诡计", "权谋"], "type_tags": ["策略"]},
        {"id": "n3", "name": "商战层", "keywords": ["商业", "投资", "市场"], "type_tags": ["商业"]},
        {"id": "n4", "name": "外交层", "keywords": ["谈判", "外交", "联盟"], "type_tags": ["外交"]},
        {"id": "n5", "name": "将军层", "keywords": ["战争", "军事", "战术"], "type_tags": ["军事"]},
        {"id": "n6", "name": "谋士层-v2", "keywords": ["战略", "规划", "布局"], "type_tags": ["战略"]},
    ]
    
    # 测试1: Normal模式，5个高相关
    print("=" * 50)
    print("测试1: Normal模式")
    result = activator.activate("如何制定战略决策？", neurons, ActivationMode.NORMAL)
    print(f"状态: {result.status}")
    print(f"激活数量: {len(result.activated_neurons)}")
    print(f"使用阈值: {result.threshold_used}")
    print(f"降级层级: {result.fallback_level}")
    
    # 测试2: Strict模式，最多3个
    print("=" * 50)
    print("测试2: Strict模式")
    result = activator.activate("如何制定战略决策？", neurons, ActivationMode.STRICT)
    print(f"状态: {result.status}")
    print(f"激活数量: {len(result.activated_neurons)}")
    
    # 测试3: 低相关问题，触发降级
    print("=" * 50)
    print("测试3: 低相关问题")
    result = activator.activate("今天天气怎么样？", neurons, ActivationMode.STRICT)
    print(f"状态: {result.status}")
    print(f"降级层级: {result.fallback_level}")
    
    # 测试4: 无相关问题，触发默认激活
    print("=" * 50)
    print("测试4: 无相关问题")
    result = activator.activate("...", neurons, ActivationMode.NORMAL)
    print(f"状态: {result.status}")
    
    print("=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    test_sparse_activation()
