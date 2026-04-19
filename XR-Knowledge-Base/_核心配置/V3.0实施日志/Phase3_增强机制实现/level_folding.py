# 云澜记忆系统 V3.0 Phase 3 - 层级折叠机制

"""
层级折叠机制模块
- 四级折叠规则（7天→摘要、30天→索引、180天→元数据、360天→归档）
- 不可折叠标记机制
- SHA256完整性校验
- 按需解压机制
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json


class FoldingLevel(Enum):
    """折叠层级"""
    L0_NORMAL = "L0"      # 未折叠
    L1_SUMMARY = "L1"     # 摘要层
    L2_INDEX = "L2"       # 索引层
    L3_METADATA = "L3"    # 元数据层
    L4_ARCHIVE = "L4"     # 归档层


from enum import Enum


# 四级折叠配置
FOLDING_LEVELS = {
    FoldingLevel.L0_NORMAL: {
        "trigger_days": 0,
        "compression_ratio": 1.0,
        "keep_content": ["全部内容"],
        "remove_content": []
    },
    FoldingLevel.L1_SUMMARY: {
        "trigger_days": 7,
        "compression_ratio": 0.80,
        "keep_content": ["核心结论", "索引指针", "元数据"],
        "remove_content": ["细节描述", "中间过程"]
    },
    FoldingLevel.L2_INDEX: {
        "trigger_days": 30,
        "compression_ratio": 0.95,
        "keep_content": ["主题标签", "检索关键词", "存储位置"],
        "remove_content": ["正文内容", "摘要"]
    },
    FoldingLevel.L3_METADATA: {
        "trigger_days": 180,
        "compression_ratio": 0.99,
        "keep_content": ["基本标识", "创建时间", "关联关系"],
        "remove_content": ["全部内容"]
    },
    FoldingLevel.L4_ARCHIVE: {
        "trigger_days": 360,
        "compression_ratio": 0.999,
        "keep_content": ["唯一ID", "外部引用计数"],
        "remove_content": ["所有内容"]
    }
}


@dataclass
class FoldingProtection:
    """折叠保护标记"""
    protected: bool = False
    reason: str = ""
    protected_at: str = ""
    protected_by: str = "system"


@dataclass
class FoldedMemory:
    """折叠记忆"""
    id: str
    original_id: str
    folding_level: FoldingLevel
    original_content: str
    content_hash: str
    summary: str
    metadata: Dict = field(default_factory=dict)
    created_at: str = ""
    folded_at: str = ""
    last_accessed: str = ""
    status: str = "folded"  # folded/decompressed


class MemoryFoldingEngine:
    """记忆折叠引擎"""
    
    def __init__(self):
        self.folding_levels = FOLDING_LEVELS
    
    def evaluate_folding_candidate(
        self, 
        memory: Dict,
        current_time: datetime = None
    ) -> Optional[Dict]:
        """
        评估记忆是否应该折叠
        
        返回折叠建议或None（如果被保护）
        """
        # 检查保护标记
        if memory.get("folding_protection", {}).get("protected", False):
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        # 计算未激活天数
        last_accessed = self._parse_time(memory.get("last_accessed"))
        if not last_accessed:
            return None
        
        inactive_days = (current_time - last_accessed).days
        
        # 确定折叠层级
        for level, config in sorted(self.folding_levels.items(), key=lambda x: x[1]["trigger_days"]):
            if inactive_days >= config["trigger_days"] and level != FoldingLevel.L0_NORMAL:
                return {
                    "memory_id": memory["id"],
                    "folding_level": level,
                    "inactive_days": inactive_days,
                    "compression_ratio": config["compression_ratio"]
                }
        
        return None
    
    def generate_summary(self, memory: Dict, level: FoldingLevel) -> str:
        """
        生成折叠摘要
        
        简化实现：实际需要LLM参与
        """
        content = memory.get("content", "")
        
        if level == FoldingLevel.L1_SUMMARY:
            # 提取核心结论（前50字）
            return content[:50] + "..." if len(content) > 50 else content
        
        elif level == FoldingLevel.L2_INDEX:
            # 主题标签
            tags = memory.get("tags", [])
            return f"[{'|'.join(tags)}] {content[:30]}..."
        
        elif level == FoldingLevel.L3_METADATA:
            # 基本信息
            return f"ID:{memory.get('id')} | 创建:{memory.get('created_at', '')[:10]}"
        
        elif level == FoldingLevel.L4_ARCHIVE:
            # 唯一标识
            return f"ID:{memory.get('id')}"
        
        return content
    
    def calculate_content_hash(self, content: str) -> str:
        """计算内容SHA256哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def execute_folding(
        self, 
        memory: Dict, 
        level: FoldingLevel,
        current_time: datetime = None
    ) -> FoldedMemory:
        """
        执行折叠操作
        
        流程：
        1. 生成摘要
        2. 计算哈希
        3. 创建折叠对象
        4. 保留原始内容用于解压
        """
        if current_time is None:
            current_time = datetime.now()
        
        original_content = memory.get("content", "")
        content_hash = self.calculate_content_hash(original_content)
        summary = self.generate_summary(memory, level)
        
        return FoldedMemory(
            id=f"folded_{memory.get('id', 'unknown')}_{level.value}",
            original_id=memory.get("id", ""),
            folding_level=level,
            original_content=original_content,
            content_hash=content_hash,
            summary=summary,
            metadata={
                "core_entities": memory.get("core_entities", []),
                "tags": memory.get("tags", []),
                "created_at": memory.get("created_at", ""),
                "source": memory.get("source", "")
            },
            created_at=memory.get("created_at", current_time.isoformat()),
            folded_at=current_time.isoformat(),
            last_accessed=current_time.isoformat(),
            status="folded"
        )
    
    def preview_before_folding(self, memory: Dict, level: FoldingLevel) -> Dict:
        """
        折叠前生成摘要预览供确认
        """
        config = self.folding_levels[level]
        summary = self.generate_summary(memory, level)
        
        return {
            "original_id": memory.get("id"),
            "folding_level": level.value,
            "summary_preview": summary,
            "compression_ratio": config["compression_ratio"],
            "items_to_keep": config["keep_content"],
            "items_to_remove": config["remove_content"],
            "confirm_required": True
        }
    
    def _parse_time(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None


class MemoryDecompressor:
    """记忆解压器"""
    
    DECOMPRESSION_DELAYS = {
        FoldingLevel.L0_NORMAL: "<10ms",
        FoldingLevel.L1_SUMMARY: "<100ms",
        FoldingLevel.L2_INDEX: "<1s",
        FoldingLevel.L3_METADATA: "<10s",
        FoldingLevel.L4_ARCHIVE: "<60s"
    }
    
    def __init__(self):
        self.folding_engine = MemoryFoldingEngine()
    
    def decompress(
        self, 
        folded_memory: FoldedMemory,
        current_time: datetime = None
    ) -> Dict:
        """
        按需解压记忆
        
        返回解压后的完整记忆
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 如果未折叠，直接返回
        if folded_memory.folding_level == FoldingLevel.L0_NORMAL:
            return {
                "id": folded_memory.original_id,
                "content": folded_memory.original_content,
                "folding_level": FoldingLevel.L0_NORMAL.value,
                "status": "normal"
            }
        
        # 验证完整性
        original_hash = self.folding_engine.calculate_content_hash(folded_memory.original_content)
        if original_hash != folded_memory.content_hash:
            raise IntegrityError(
                f"记忆完整性校验失败: {folded_memory.original_id}"
            )
        
        # 恢复完整内容
        decompressed = {
            "id": folded_memory.original_id,
            "content": folded_memory.original_content,
            "folding_level": FoldingLevel.L0_NORMAL.value,
            "metadata": folded_memory.metadata,
            "decompressed_at": current_time.isoformat(),
            "status": "decompressed",
            "last_accessed": current_time.isoformat()
        }
        
        return decompressed
    
    def batch_decompress(
        self, 
        folded_memories: List[FoldedMemory]
    ) -> List[Dict]:
        """批量解压"""
        results = []
        for fm in folded_memories:
            try:
                results.append(self.decompress(fm))
            except IntegrityError as e:
                results.append({
                    "id": fm.original_id,
                    "status": "error",
                    "error": str(e)
                })
        return results


class IntegrityError(Exception):
    """完整性错误"""
    pass


# ==================== 单元测试 ====================

def test_level_folding():
    """测试层级折叠机制"""
    from datetime import datetime, timedelta
    
    engine = MemoryFoldingEngine()
    decompressor = MemoryDecompressor()
    
    # 模拟记忆数据
    memory = {
        "id": "mem_001",
        "content": "这是一个关于战略规划的重要记忆。我们讨论了如何制定长期目标，分析了市场竞争格局，确定了资源配置优先级，并制定了详细的执行计划。",
        "core_entities": ["战略", "规划", "资源"],
        "tags": ["战略规划", "重要决策"],
        "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
        "last_accessed": (datetime.now() - timedelta(days=8)).isoformat(),
        "source": "对话记录"
    }
    
    print("=" * 50)
    print("测试1: 评估折叠候选")
    candidate = engine.evaluate_folding_candidate(memory)
    print(f"折叠候选: {candidate}")
    
    print("=" * 50)
    print("测试2: 执行L1折叠")
    if candidate and candidate["folding_level"] == FoldingLevel.L1_SUMMARY:
        folded = engine.execute_folding(memory, FoldingLevel.L1_SUMMARY)
        print(f"折叠ID: {folded.id}")
        print(f"摘要: {folded.summary}")
        print(f"哈希: {folded.content_hash[:16]}...")
        
        print("=" * 50)
        print("测试3: 解压验证")
        try:
            decompressed = decompressor.decompress(folded)
            print(f"解压后ID: {decompressed['id']}")
            print(f"解压后状态: {decompressed['status']}")
            print(f"内容匹配: {decompressed['content'] == memory['content']}")
        except IntegrityError as e:
            print(f"错误: {e}")
    
    print("=" * 50)
    print("测试4: 保护标记检查")
    protected_memory = {
        **memory,
        "folding_protection": {"protected": True, "reason": "主人要求记住"}
    }
    candidate = engine.evaluate_folding_candidate(protected_memory)
    print(f"受保护记忆折叠候选: {candidate}")  # 应为None
    
    print("=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    test_level_folding()
