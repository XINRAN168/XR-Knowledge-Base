# 云澜工具使用经验

> 版本：v7.5 | 更新：2026-04-19
> 本文档是云澜思维V9.0的支撑文档

---

## ⛔ 关键原则：子任务结果必须验证

**教训来源**：2026-04-19 V9.0同步任务

**问题**：子任务返回"MEMORY.md已更新完成"，但实际文件根本没有更新。我没有验证就告诉用户"完成了"。

**原则**：
1. ❌ 不能直接相信子任务的返回报告
2. ✅ 关键文件更新后必须亲自read_file验证
3. ✅ 验证内容是否正确，不是只看"成功"状态
4. ✅ 发现问题时立即手动修复，不能隐瞒

**验证清单**：
- 子任务说文件已更新 → 亲自read_file确认内容
- 子任务说任务完成 → 检查产出是否真实存在
- 子任务说数据已写入 → 验证数据是否正确

---

## 一、核心工具矩阵

### 1.1 信息获取工具

| 工具 | 适用场景 | 使用要点 |
|:---:|:---|:---|
| **search_web** | 联网搜索 | 关键词精简1-6个词，去口语化；搜索历史人物时，采用"人物名 核心标签 领域智慧"格式，如"李世民 帝王格局 领导智慧"；搜索现代独立创业者时，采用"人物名 核心关键词 年份"格式，如"Dan Koe success philosophy mindset 2024"，可提高结果相关性 |
| **fetch_web** | 网页内容获取 | 动态内容需配合agent-browser |
| **read_file** | 本地文件读取 | 大文件分批读取，通过offset和limit参数分段获取内容，避免上下文溢出或处理缓慢 |

### 1.2 内容创作工具

| 工具 | 适用场景 | 使用要点 |
|:---:|:---|:---|
| **create_podcast** | 播客生成 | 支持单人/双人播客 |
| **image_generate** | 图片生成 | 批量需求合并调用 |
| **run_video_task** | 视频生成 | 支持seedance2.0_pro/1.5_pro |

### 1.3 文档处理工具

| 工具 | 适用场景 | 使用要点 |
|:---:|:---|:---|
| **docx** | Word文档处理 | 支持创建、编辑、修订追踪 |
| **pdf** | PDF处理 | 提取、创建、合并、表单 |
| **excel_master** | Excel处理 | 数据分析、报表生成 |

### 1.4 浏览器自动化

| 工具 | 适用场景 | 使用要点 |
|:---:|:---|:---|
| **agent-browser** | 网页操作 | 需先启动虚拟显示(Xvfb) |
| **mobile_use** | 手机App操作 | 异步执行，异步返回 |

---

## 二、云澜技能库

### 2.1 核心能力技能

| 技能 | 用途 | 场景 |
|:---:|:---|:---|
| **excel_master** | 数据处理、表格分析 | 数据分析、报表生成 |
| **echart** | 数据可视化 | 图表生成、可视化报告 |
| **drawio-generator** | 流程图、架构图 | 系统设计、流程梳理 |
| **使用要点** | 1. 加载技能：`skill_load --skill drawio-generator`
2. 读取对应图表类型的规则文件（如`references/flowchart/flowchart_rule.md`）
3. 生成Draw.io XML格式内容
4. 保存为`.drawio`文件
5. 运行修正脚本：`python .skills/skill_drawio-generator/script/fix_drawio_xml.py 文件路径`
6. 运行对齐脚本：`python .skills/skill_drawio-generator/script/align_drawio_nodes.py 文件路径`
7. 确保最终文件可在diagrams.net中正确打开和编辑 |
| **create-ppt** | PPT自动生成 | 演示文稿、汇报材料 |
| **pdf/docx** | 文档处理 | 读取、生成、转换 |
| **agent-browser** | 浏览器自动化 | 网页抓取、自动化操作 |

### 2.2 技能选型策略

- **需求匹配优先**：根据description判断是否匹配用户需求
- **允许组合**：复杂任务可同时加载多个技能
- **渐进式加载**：调用skill_load工具加载技能

---

## 三、浏览器操作规范

### 3.1 云电脑环境配置

```bash
# 启动虚拟显示
export DISPLAY=:99 && Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Chrome进程故障处理
pkill -9 -f chrome 2>/dev/null
rm -f ~/.agent-browser/*.lock /app/browser/profile/*.lock 2>/dev/null
```

### 3.2 常用命令

| 命令 | 功能 |
|:---:|:---|
| `agent-browser open URL` | 访问页面 |
| `agent-browser snapshot -i` | 获取元素快照 |
| `agent-browser click @eX` | 点击元素 |
| `agent-browser wait --load networkidle` | 等待页面加载 |
| `agent-browser screenshot path` | 截图保存 |

---

## 四、扣子平台操作指南

### Bot状态检查与修复流程

#### 核心任务
检查云澜AI团队Bot的发布状态，确保飞书渠道正常运行，解决消息无回复问题。

#### 操作步骤
1. **加载浏览器工具**：
   ```bash
   skill_load --skill agent-browser
   ```
2. **访问扣子平台**：
   ```bash
   agent-browser open https://code.coze.cn/w/7389295509150285887/projects
   ```
3. **进入云澜AI团队项目**：
   - 等待页面加载完成
   - 点击目标智能体项目
4. **检查Bot状态**：
   - 查看是否显示"草稿"标签
   - 点击"发布"按钮检查渠道配置
5. **修复问题**：
   - 确保飞书渠道已勾选且已授权
   - 执行发布操作
6. **验证结果**：
   - 确认发布成功提示
   - 截图保存证据
   - 报告修复结果

#### 关键命令
| 命令 | 用途 |
|------|------|
| `agent-browser wait --load networkidle` | 等待页面完全加载 |
| `agent-browser snapshot -i` | 获取页面元素快照 |
| `agent-browser click @eX` | 点击指定元素 |
| `agent-browser screenshot path` | 截图保存结果 |

#### 注意事项
- 飞书渠道必须已授权且勾选才能正常接收消息
- 发布完成后可能需要等待1-2分钟生效
- 故障排查时需检查发布记录中的版本状态

### 插件配置注意事项
#### 添加插件问题
扣子平台页面结构复杂，添加插件的UI入口不够明显，当前插件区域仅显示已配置的插件列表，没有明确的"添加插件"按钮。可能需要：
- 手动滚动到特定位置
- 点击特定的UI元素来展开添加界面
- 或者该功能需要特定的权限才能访问

#### 常用插件推荐
1. **查壹得·企业经营/park** - 查询企业所属园区信息
2. **政策工具箱/company_policy_match** - 政策匹配功能
3. **幸福里系列插件** - 租房/二手房/新房信息（含图片）
4. **立业云/searchDevelopmentOrPark** - 信息提取助手

#### 图片能力实现
- 幸福里系列插件已支持返回图片，适合房产类场景
- 如需专门的图片生成或搜图插件，需手动在扣子平台添加

---

## 五、文件处理规范

### 4.1 文件命名原则

- 文件名简短且体现内容意义
- 仅限中英文、数字、下划线、短横线
- **禁止**：空格及特殊字符

### 4.2 路径规范

- 使用相对路径，**禁止**绝对路径
- **禁止**保存到`/tmp/`等系统临时目录
- 必须使用`open`或`create_file`工具写入

### 4.3 JSON文件注意事项
- 字符串内部使用双引号时需要转义（`\"`），或者使用单引号代替双引号
- 避免在字符串中使用未转义的双引号，会导致JSON解析错误
- 创建JSON文件后建议使用`python3 -c \"import json; json.load(open('文件路径'))\"`验证格式正确性

---

## 五、AI开发工具（云澜技能库）

| 工具 | 定位 | 核心能力 |
|:---:|:---|:---|
| **Gstack** | AI软件工厂 | 1人顶20人团队的软件交付 |
| **MetaGPT** | 多Agent协作 | 角色专业化实现复杂任务分工 |
| **Composio** | AI技能平台 | 1000+应用集成，自动OAuth |
| **Claude Code** | AI编程工具 | 自主执行复杂编程任务 |
| **Coze CLI** | Coze平台工具 | 项目开发部署、媒体生成、文件上传 |
| **MatchCalculator** | YL思维V7.0核心模块 | 计算问题与神经元的匹配度，作为脉冲强度计算的基础 |
| **DataRecorder** | YL思维V7.0核心模块 | 实现"数据积累→分析→固化预设"的演进机制，记录神经元激活数据、分析模式、生成固化预设 |
| **PerformanceOptimizer** | YL思维V7.0性能优化核心模块 | 10,000次人生模拟性能优化，支持并行执行、早期收敛检测、批量结果处理、场景缓存 |
| **XumiSimulator** | YL思维V7.0须弥推演境核心模块 | 真实环境模拟器，支持蒙特卡洛模拟、多场景推演、风险量化分析、可执行方案生成 |

---

## 六、MatchCalculator 使用指南

### 6.1 核心定位
YL思维V7.0核心模块，用于计算问题与神经元的匹配度，作为脉冲强度计算的基础。

### 6.2 计算逻辑
匹配度 = 关键词匹配(40%) + 问题类型匹配(30%) + 语义相似度(30%)

### 6.3 核心类与方法

#### MatchCalculator 类
```python
class MatchCalculator:
    def __init__(self):
        # 初始化匹配度计算器
        
    def extract_keywords(self, text: str) -> List[str]:
        # 从文本中提取关键词，支持中文2-4字词组、常见词组匹配
        
    def classify_question(self, question: str) -> Tuple[str, float]:
        # 识别问题类型，返回(问题类型, 置信度)
        
    def calculate_match_score(self, question: str, neuron: Dict[str, Any]) -> Dict[str, Any]:
        # 计算问题与神经元的综合匹配度
        
    def rank_neurons(self, question: str, neurons: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        # 对神经元进行匹配度排序，返回前top_k个结果
```

### 6.4 问题类型定义
支持10种问题类型：
- 战略决策
- 竞争分析
- 执行落地
- 个人发展
- 创业投资
- 人际关系
- 团队领导
- 产品市场
- 危机处理
- 日常咨询

每种类型包含关键词列表和匹配权重，可通过QUESTION_TYPES属性查看和修改。

### 6.5 使用示例
```python
from match_calculator import MatchCalculator, EXAMPLE_NEURONS

# 初始化计算器
calculator = MatchCalculator()

# 计算单个问题与神经元的匹配度
question = "公司明年应该往什么方向发展？"
result = calculator.calculate_match_score(question, EXAMPLE_NEURONS[0])
print(result)

# 对多个神经元进行排序
ranked_neurons = calculator.rank_neurons(question, EXAMPLE_NEURONS)
for neuron in ranked_neurons:
    print(f"排名 #{neuron['rank']}: {neuron['neuron_name']} - 综合得分: {neuron['total_match']:.2%}")
```

### 6.6 输出格式
```python
{
    "neuron_id": 1,
    "neuron_name": "谋士层",
    "keyword_match": 0.8,
    "type_match": 0.9,
    "semantic_match": 0.75,
    "total_match": 0.82,
    "question_type": "战略决策",
    "question_keywords": ["公司", "发展", "方向"],
    "type_confidence": 0.95
}
```

### 6.7 技术细节
- **关键词匹配**：使用Jaccard相似度和覆盖率综合计算
- **问题类型匹配**：基于关键词规则和类型关联矩阵
- **语义相似度**：基于TF-IDF的余弦相似度，结合关键词直接匹配
- **中文分词**：支持2-4字词组提取、常见词组匹配，优化中文关键词识别

## 七、Coze CLI 使用指南

### 6.1 核心功能
- 项目开发部署
- 媒体生成（音频、图片、视频）
- 文件上传生成在线可访问链接

### 6.2 文件上传步骤
1. **检查授权状态**：
   ```bash
   coze auth status
   ```
   确保已登录（显示`logged_in: true`）

2. **上传文件**：
   ```bash
   coze file upload ./path/to/your/file --format json
   ```
   支持多种文件类型：HTML、CSS、JavaScript、图片、音频等

3. **获取在线链接**：
   上传成功后，会返回`file_url`字段，这是用户可以直接访问的在线链接

### 6.3 注意事项
- 必须使用`--format json`参数以获取结构化输出
- 上传的文件大小限制：单个文件不超过100MB
- 在线链接有效期：默认30天，可通过Coze平台设置延长
- 禁止将本地路径直接发给用户，必须上传后返回在线链接

---

## 六、Signal Arena API调用指南

### 6.1 基础配置
- **API Base URL**: `https://signal.coze.site`
- **Authorization Header**: `Bearer <API Key>`
- **Content-Type**: `application/json`

### 6.2 常用接口

#### 获取全局状态
```bash
curl -s -X GET "https://signal.coze.site/api/v1/arena/home" \
  -H "Authorization: Bearer <API Key>" \
  -H "Content-Type: application/json"
```

#### 获取涨幅榜
```bash
curl -s -X GET "https://signal.coze.site/api/v1/arena/top-movers" \
  -H "Authorization: Bearer <API Key>" \
  -H "Content-Type: application/json"
```

#### 获取持仓信息
```bash
curl -s -X GET "https://signal.coze.site/api/v1/arena/portfolio" \
  -H "Authorization: Bearer <API Key>"
```

#### 执行交易
```bash
curl -s -X POST "https://signal.coze.site/api/v1/arena/trade" \
  -H "Authorization: Bearer <API Key>" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "<股票代码>", "action": "buy/sell", "shares": <数量>, "reason": "<交易理由>"}'
```
> 说明：`reason`参数用于记录交易逻辑和决策依据，方便后续复盘和策略优化，建议每次交易都添加明确的理由

### 6.3 注意事项
- 交易订单提交后处于pending状态，需等待结算时按最新价格成交
- 美股交易最小单位为1股，港股为1000股，A股为100股
- 注意不同市场的交易规则（如T+0/T+1）
- API请求必须使用正确的域名https://signal.coze.site，避免使用错误的api.coze.site域名导致请求失败

---

## 七、InkWell API调用指南

### 7.1 基础配置
- **API Base URL**: `https://inkwell.coze.site`
- **Authorization Header**: `agent-auth-api-key: <API Key>` 或 `Authorization: Bearer <API Key>`
- **Content-Type**: `application/json`

### 7.2 常用接口

#### 获取首页仪表盘
```bash
curl -s -X GET "https://inkwell.coze.site/api/v1/home" \
  -H "agent-auth-api-key: <API Key>"
```
返回：最新文章、热门文章、分类统计、个人数据

#### 获取分类列表
```bash
curl -s -X GET "https://inkwell.coze.site/api/v1/categories" \
  -H "agent-auth-api-key: <API Key>"
```
返回：所有分类名称及文章数量

#### 获取文章列表
```bash
curl -s -X GET "https://inkwell.coze.site/api/v1/articles?limit=10&sort=date" \
  -H "agent-auth-api-key: <API Key>"
```
参数：
- limit: 返回数量（默认20）
- sort: 排序方式（date/likes）
- category: 分类筛选（如AI+%26+ML）

#### 获取文章详情
```bash
curl -s -X GET "https://inkwell.coze.site/api/v1/articles/{article_id}" \
  -H "agent-auth-api-key: <API Key>"
```
返回：文章完整内容、来源、分类、互动数据

#### 收藏文章
```bash
curl -s -X POST "https://inkwell.coze.site/api/v1/bookmarks" \
  -H "agent-auth-api-key: <API Key>" \
  -H "Content-Type: application/json" \
  -d '{"article_id": "<article_id>", "note": "<阅读笔记>"}'
```

#### 点赞文章
```bash
curl -s -X POST "https://inkwell.coze.site/api/v1/articles/{article_id}/like" \
  -H "agent-auth-api-key: <API Key>"
```

#### 获取个人信息
```bash
curl -s -X GET "https://inkwell.coze.site/api/v1/agents/me" \
  -H "agent-auth-api-key: <API Key>"
```
返回：用户名、昵称、头像、个人简介、统计数据

### 7.3 注意事项
- API Key与Agent World主账号通用
- 部分接口（如分类列表）无需认证即可访问，但认证后返回更丰富数据
- 请求频率限制：60 GET/分钟 + 30 POST/分钟
- 建议使用curl或HTTP库调用，避免直接用fetch_web处理API请求（可能有格式问题）

---

## 八、V7.4 核心模块（历史版本）

**说明**：V7.4核心模块已整合到V9.0架构中，以下为简要说明。

### 8.1 记忆索引系统（memory_indexer.py）
**功能**：快速定位历史对话，支持关键词/语义/时间范围搜索
**性能**：关键词<50ms、语义<100ms、时间范围<30ms、综合<150ms

### 8.2 情感感知系统（emotion_sensor.py）
**功能**：10+种情绪类型识别，自然回应，陪伴感，情绪记忆趋势分析

### 8.3 数据真实性约束系统（data_constraint.py）
**定位**：须弥推演境核心约束，确保模拟数据贴近现实
**组件**：数据边界、历史数据注入、现实性检查、行业基准、合理性检查

---

## 九、DataRecorder（历史版本）

**定位**：YL思维V7.0核心模块，数据积累→分析→固化预设的演进机制

**核心组件**：
- **ActivationRecorder**：记录神经元激活数据
- **PatternAnalyzer**：分析数据模式规律
- **PresetGenerator**：生成固化预设
- **SolidificationChecker**：固化条件检查

**固化条件**：总记录≥100、同类型问题≥10、置信度≥0.8

**状态**：已整合到V9.0记忆系统M2层

---

## 十、PerformanceOptimizer（历史版本）

**定位**：YL思维V7.0性能优化核心模块，解决10,000次人生模拟速度问题

**核心组件**：
- **ParallelSimulationEngine**：多进程并行模拟引擎
- **EarlyConvergenceDetector**：早期收敛检测器
- **BatchResultProcessor**：批量结果处理器
- **CacheManager**：场景缓存管理器
- **OptimizedSimulator**：整合优化器

**性能目标达成**：
- 100次：5秒 → 0.004秒
- 1,000次：50秒 → 0.02秒
- 10,000次：8分钟 → 0.36秒

**状态**：已整合到V9.0 M3推演系统层

---

## 十一、XumiSimulator（历史版本）

**定位**：YL思维V7.0须弥推演境核心模块，真实环境模拟器

**核心组件**：
- **EnvironmentModeler**：环境建模器
- **MonteCarloEngine**：蒙特卡洛引擎
- **RiskAnalyzer**：风险分析器
- **ExecutablePlanGenerator**：可执行方案生成器
- **XumiSimulator**：核心整合类

**技术特性**：多领域覆盖、场景化模拟、风险量化、可执行方案

**状态**：已整合到V9.0 M3推演系统层

---

## 十二、Git操作指南

### 11.1 常见问题处理
#### Git index.lock文件存在问题
当出现"fatal: Unable to create '/path/.git/index.lock': File exists"错误时，执行以下命令删除锁文件：
```bash
rm -f ./github/.git/index.lock
```

#### Git add超时问题
当文件数量过多导致Git add命令超时或失败时，采用分批提交策略：
```bash
# 方法1：按目录分批提交
cd ./github/XR-Knowledge-Base
for dir in */; do
    git add "$dir"
    git commit -m "feat: 提交${dir%/}目录档案"
done

# 方法2：按文件类型分批提交
git add *.md --dry-run  # 预览要提交的文件
find . -name "*.md" | head -50 | xargs git add  # 提交前50个md文件
git commit -m "feat: 提交第一批档案文件"
```

#### 批量提交脚本
创建批量提交脚本`batch_commit.sh`：
```bash
#!/bin/bash
cd ./github/XR-Knowledge-Base

# 提交根目录文件
git add *.md 2>/dev/null
if git diff --cached --quiet; then
    echo "根目录无新文件需要提交"
else
    git commit -m "feat: 提交根目录文件"
fi

# 按子目录分批提交
for dir in */; do
    if [ -d "$dir" ]; then
        cd "$dir"
        git add .
        if git diff --cached --quiet; then
            echo "目录 ${dir%/} 无新文件需要提交"
        else
            git commit -m "feat: 提交${dir%/}目录档案"
        fi
        cd ..
    fi
done

echo "所有档案提交完成"
```

使用方法：
```bash
chmod +x batch_commit.sh
./batch_commit.sh
```

### 11.2 目录结构创建
创建多层级目录使用`mkdir -p`命令，确保父目录不存在时自动创建：
```bash
mkdir -p ./github/XR-Knowledge-Base/N01_战略层/战略家_古 ./github/XR-Knowledge-Base/N01_战略层/战略家_今
```

### 11.3 代码提交步骤
1. **添加文件到暂存区**：
   ```bash
   git add N01_战略层
   ```
2. **提交变更**：
   ```bash
   git commit -m "feat: 谋士层人物档案（19位战略家）
   
   古代中国谋士13人：诸葛亮、张良、范蠡、刘伯温、姜子牙、司马懿、郭嘉、荀彧、孙膑、鬼谷子、庞统、苏秦、张仪
   
   古代世界谋士3人：俾斯麦、马基雅维利、塔列朗
   
   现代战略家3人：基辛格、布热津斯基、亨廷顿
   
   五维度分析：核心思维、底层逻辑、行为准则、价值观、心力韧性"
   ```

### 11.4 知识库目录规范
YL思维V8.0神经元体系的档案文件应存储在以下路径：
```
./github/XR-Knowledge-Base/N01_战略层/战略家_古/  # 古代战略家档案
./github/XR-Knowledge-Base/N01_战略层/战略家_今/  # 现代战略家档案
```

---

**v7.4 | 云澜工具使用经验**

---

## 十二、大型文件验证指南

### JSON大型数据文件验证
```bash
# 统计JSON中的人物数量（以五维灵魂档案为例）
python3 -c "import json; d=json.load(open('文件路径')); print(f'人物数量: {sum(len(v) for v in d[\"neurons\"].values())}')"
```

### 通用文件验证
- 使用`md5sum`/`sha256sum`生成文件哈希校验完整性
- 使用`head`/`tail`查看文件开头结尾确认结构正确性

---

## 版本升级教训（2026-04-19）
**核心原则：**
1. 全面升级必须检查所有相关文件
2. 用版本同步检查清单逐项核对
3. 更新后必须read_file验证
4. 不完成不说完成，不确定不说确定