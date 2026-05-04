# generateGrammar 完整重构计划

**制定日期**: 2026-05-04  
**目标**: 重构 generateGrammar.py 及其所有依赖模块，确保在 LoPS 中可独立运行

---

## 依赖链分析

```
generateGrammar.py (664行)
├── src.bayesianScore (372行) ✓ 必须重构
│   ├── learnBayesNetBlock() - 被调用
│   ├── BDscore() - 被调用
│   ├── src.Utils (104行) ✓ 必须重构
│   │   └── count() - 被 BDscore 调用
│   └── src.condindepEmp (78行) ✗ 不在调用链中
│       └── 导入但未使用
```

**关键发现**：
- `condindepEmp.py` 被 `bayesianScore.py` 导入（`from src.condindepEmp import *`）但在当前执行路径中**未被调用**
- 只需重构 3 个模块：`generateGrammar.py`、`bayesianScore.py`、`Utils.py`

---

## 重构模块清单

### 1. Utils.py (104行)
**位置**: `/home/zzh/project/Pacman/2.Pac-man/structre-learning/src/Utils.py`

**被调用函数**：
- `count(data, nstates)` - 被 `BDscore` 调用

**未被调用函数**（可忽略）：
- `neighboursize()`, `neighbor()`, `mynchoosek()`, `graph_dline()`, `subv2ind()`, `Sort()`

**重构策略**：
- 只迁移 `count()` 函数到 `src/LoPS/grammar_chunking/utils.py`
- 保留原始实现，不做优化

**验证**：
- 单元测试：使用已知输入输出验证 `count()` 函数
- 集成测试：在 `BDscore` 中验证

---

### 2. bayesianScore.py (372行)
**位置**: `/home/zzh/project/Pacman/2.Pac-man/structre-learning/src/bayesianScore.py`

**被调用函数**：
- `BDscore(dataV, dataParents, nstatesV, nstatesPa, u)` - 核心评分函数
- `learnBayesNetBlock(data, nstates, blockMessage, casualNum, blockNum, effectNum, alpha, conditions)` - 贝叶斯网络学习

**未被调用函数**（可忽略）：
- `data_balance()` - 已被注释掉
- `learnBayesNet_Option()`, `learnBayesNet()`, `learnBayesNet_noparallelize()`, `learnBayesNet_f()`
- 全局变量和辅助函数（`deep_rule` 等）

**重构策略**：
- 迁移 `BDscore()` 和 `learnBayesNetBlock()` 到 `src/LoPS/grammar_chunking/bayesian_score.py`
- 移除 `from src.condindepEmp import *`（未使用）
- 保留 `from src.Utils import count` 改为导入本地 utils

**验证**：
- 单元测试：使用已知输入输出验证 `BDscore()`
- 集成测试：在 `learnBayesNetBlock()` 中验证
- 完整测试：在 generateGrammar 流程中验证

---

### 3. generateGrammar.py (664行)
**位置**: `/home/zzh/project/Pacman/2.Pac-man/structre-learning/scripts/fmriDataProcess/generateGrammar.py`

**核心类和函数**：
- `Tools` 类：`static_pro()`, `choice_max_n()`, `KL()`
- `Chunk` 类：`parse()`, `parse_pro()`, `deep()`, `get_cover_set()`, `organize_data()`, `skip_gram()`, `Chunking()`
- `getConditionGraph()` 函数
- `main()` 函数

**重构策略**：
- 迁移所有类和函数到 `src/LoPS/grammar_chunking/chunking.py`
- 修改导入：`from src.bayesianScore import ...` → `from .bayesian_score import ...`
- 保留原始算法逻辑，不做优化

**验证**：
- 端到端测试：使用 1 个输入文件验证完整流程
- 批量测试：验证全部 34 个文件

---

## 新模块结构

```
src/LoPS/grammar_chunking/
├── __init__.py                 # 导出主要接口
├── utils.py                    # count() 函数
├── bayesian_score.py           # BDscore, learnBayesNetBlock
├── chunking.py                 # Tools, Chunk 类和 main 逻辑
└── data_loader.py              # pickle 加载/保存（可选，简化 main）

script/
└── run_generateGrammar.py      # 运行脚本，调用 chunking_pipeline()
```

---

## 接口设计

### 主函数签名
```python
def chunking_pipeline(
    input_dir: str,              # 序列数据目录（绝对路径）
    state_dir: str,              # 状态图目录（绝对路径）
    output_dir: str,             # 输出目录（绝对路径）
    state_names: list[str],      # 状态变量名
    alpha: float = 0.5,          # BDscore 超参数
    file_filter: list[str] = None  # 可选：只处理指定文件
) -> dict:
    """
    执行语法分块算法
    
    Returns:
        {
            "processed_files": int,
            "results": {filename: result_path, ...}
        }
    """
```

### 运行脚本示例
```python
# script/run_generateGrammar.py
from src.LoPS.grammar_chunking import chunking_pipeline

result = chunking_pipeline(
    input_dir="/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StrategySequence/",
    state_dir="/home/zzh/project/Pacman/2.Pac-man/Monkey_Analysis/fmri_data_process/StateGraph/",
    output_dir="./output/grammar2/",
    state_names=["IS1", "IS2", "PG1", "PG2", "PE", "BN5"],
    alpha=0.5
)
```

---

## 验证策略

### 阶段 1：单元测试（模块级）
1. **utils.count()** - 使用构造的测试数据验证
2. **bayesian_score.BDscore()** - 使用已知输入输出验证
3. **bayesian_score.learnBayesNetBlock()** - 使用小规模数据验证

### 阶段 2：集成测试（单文件）
1. 选择 1 个输入文件（如 `031222-401.pkl`）
2. 运行原始脚本，保存输出到 `original_output/`
3. 运行新实现，保存输出到 `new_output/`
4. 逐字段比较两个输出 pickle 文件

**比较策略**：
- 字符串字段：完全一致
- 列表字段：长度和元素完全一致
- 浮点数组：`np.allclose(rtol=1e-9, atol=1e-12)`
- DataFrame：`pd.testing.assert_frame_equal()`

### 阶段 3：批量测试（全部文件）
1. 运行新实现处理全部 34 个文件
2. 逐个比较与原始输出
3. 记录每个文件的验证结果

### 阶段 4：清理
- 删除 `src/LoPS/temp/`（如果创建了临时代码）
- 记录验证结论到 `.planning/runs/2026-05-04-generateGrammar/verification.md`

---

## 实施步骤

### Step 1: 创建模块骨架
- [ ] 创建 `src/LoPS/grammar_chunking/` 目录
- [ ] 创建 `__init__.py`, `utils.py`, `bayesian_score.py`, `chunking.py`

### Step 2: 迁移 Utils.py
- [ ] 复制 `count()` 函数到 `utils.py`
- [ ] 添加类型注解和文档字符串
- [ ] 编写单元测试

### Step 3: 迁移 bayesianScore.py
- [ ] 复制 `BDscore()` 和 `learnBayesNetBlock()` 到 `bayesian_score.py`
- [ ] 修改导入：`from src.Utils import count` → `from .utils import count`
- [ ] 移除未使用的导入（`condindepEmp`）
- [ ] 编写单元测试

### Step 4: 迁移 generateGrammar.py
- [ ] 复制 `Tools`, `Chunk`, `getConditionGraph`, `main` 到 `chunking.py`
- [ ] 修改导入：`from src.bayesianScore import ...` → `from .bayesian_score import ...`
- [ ] 重构 `main()` 为 `chunking_pipeline()`，接收绝对路径参数
- [ ] 创建 `script/run_generateGrammar.py`

### Step 5: 单文件验证
- [ ] 运行原始脚本，保存 1 个文件的输出
- [ ] 运行新实现，保存输出
- [ ] 逐字段比较，记录差异

### Step 6: 修复差异（如果有）
- [ ] 分析差异原因
- [ ] 修复新实现
- [ ] 重新验证

### Step 7: 批量验证
- [ ] 运行新实现处理全部 34 个文件
- [ ] 逐个比较输出
- [ ] 记录验证结果

### Step 8: 清理和文档
- [ ] 删除临时代码
- [ ] 编写 `verification.md`
- [ ] 更新 `README.md`

---

## 风险和注意事项

### 高风险项
1. **浮点数精度**：BDscore 涉及 `gammaln` 和大量浮点运算，可能有微小差异
   - **缓解**：使用 `np.allclose` 而非完全一致
   
2. **文件遍历顺序**：`os.listdir()` 顺序不保证
   - **缓解**：在新实现中排序文件名列表

3. **多进程行为**：`multiprocessing.dummy.Pool` 可能有非确定性
   - **缓解**：确认当前执行路径不使用多进程

### 中风险项
1. **Pickle 版本兼容性**：Python 版本差异可能影响 pickle 格式
   - **缓解**：使用相同 Python 版本（3.10.16）

2. **NumPy/Pandas 版本差异**：不同版本可能有行为差异
   - **缓解**：记录版本，验证时使用相同版本

### 低风险项
1. **导入路径变化**：从 `src.bayesianScore` 改为相对导入
   - **缓解**：仔细测试导入

---

## 成功标准

1. ✅ 所有 3 个模块成功迁移到 `src/LoPS/grammar_chunking/`
2. ✅ 单元测试通过（utils, bayesian_score）
3. ✅ 单文件验证：新旧输出完全一致（或在容差范围内）
4. ✅ 批量验证：全部 34 个文件输出一致
5. ✅ 运行脚本可独立执行，不依赖外部项目路径
6. ✅ 验证文档完整记录结果和任何容差

---

**下一步**: 开始执行 Step 1 - 创建模块骨架
