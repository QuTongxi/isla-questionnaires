# Isla Questionnaires

## 项目是什么

Isla Questionnaires 是一个可在本地离线运行的社会学／心理学问卷库，提供统一的问卷查看、逐题作答、保存恢复、答卷导出和评分接口。可以直接在命令行填写问卷，也可以作为 Python 包接入其他项目。

问卷覆盖人格、职业兴趣、情绪与亲密关系、自我评价、认知与决策、价值观和社会态度等方向。题目、选项、评分规则和来源材料随项目保存，评分过程可逐题追溯。

- **运行环境**：Python 3.11+，运行时仅使用标准库。
- **当前收录**：36 个量表条目，其中 24 个启用本地计分、12 个待核对；另有 1 个人工审核流程示例。
- **题目语言**：已启用的量表目前使用英文；尚未提供核验完成的中文量表。
- **结果形式**：按当前收录版本输出原始总分、维度均分或原题得分；SWLS 另提供作者的满意度解释区间。

“已启用”表示该版本能够执行作答和计分。项目的工程验证范围、来源核对情况与量表的心理测量效度需要分别理解。量表来源和使用条款见 [第三方材料说明](THIRD_PARTY_NOTICES.md)。

## 有哪些问卷

表中的 ID 用于命令行和 Python 接口。题数包含施测时需要回答的不计分题。

### 已启用本地计分（24 个）

| 方向 | 问卷（ID） | 题数 | 主要测量内容与输出 |
| --- | --- | ---: | --- |
| 人格 | 大五人格 BFI（`bfi-44`） | 44 | 外向性、宜人性、尽责性、神经质、开放性；五维均分 |
| 人格 | IPIP 五因素（`ipip-50`） | 50 | 五因素人格特征；五维原始总分 |
| 人格 | IPIP-NEO（`ipip-neo-120`） | 120 | 五大人格领域及 30 个侧面；领域与侧面总分 |
| 人格 | HEXACO（`hexaco-60`） | 60 | 诚实谦逊、情绪性、外向性、宜人性、尽责性、开放性；六因素及 24 个短侧面均分 |
| 人格 | 艾森克人格问卷修订版（`epq-r`） | 100 | 外向性 E、精神质 P、神经质 N、掩饰性 L；原始总分 |
| 职业与活动兴趣 | 基本兴趣综合评估 CABIN（`cabin`） | 164 | 41 个基本兴趣维度，如机械、自然、艺术与社会服务；维度均分 |
| 职业与活动兴趣 | O*NET Mini Interest Profiler（`riasec-mini-ip`） | 30 | 实际型、研究型、艺术型、社会型、企业型、常规型六类兴趣；各维 0–20 分 |
| 情绪与亲密关系 | 情绪智力量表 EIS（`eis`） | 33 | 自评情绪智力；总分 33–165 |
| 情绪与亲密关系 | Wong–Law 情绪智力量表（`wleis`） | 16 | 自我情绪评价、他人情绪评价、情绪运用、情绪调节；四维均分 |
| 情绪与亲密关系 | 情绪调节问卷 ERQ（`erq`） | 10 | 认知重评与表达抑制两种调节策略；两维均分 |
| 情绪与亲密关系 | 亲密关系经历量表修订版（`ecr-r`） | 36 | 依恋焦虑与依恋回避；两维均分 |
| 自我评价与生活态度 | 一般自我效能量表（`gse`） | 10 | 对应对困难、完成任务的信心；总分 10–40 |
| 自我评价与生活态度 | Rosenberg 自尊量表（`rses`） | 10 | 整体自我价值感；总分 0–30 |
| 自我评价与生活态度 | 生活满意度量表（`swls`） | 5 | 对整体生活的主观评价；总分 5–35 及满意度解释区间 |
| 自我评价与生活态度 | 生活定向测验修订版（`lot-r`） | 10 | 乐观倾向；6 个计分题总分 0–24，另含 4 个填充题 |
| 自我评价与生活态度 | 简式坚毅量表（`grit-s`） | 8 | 兴趣一致性与努力坚持性；两维均分及总均分 |
| 自我评价与生活态度 | 内外控制点量表（`ie-4`） | 4 | 对生活结果由自身或外部因素控制的看法；内控／外控均分 |
| 社会行为 | 自我监控量表修订版（`self-monitoring-18`） | 18 | 根据社交情境调整自我呈现与行为的倾向；总分 0–18 |
| 认知与决策 | 认知反思测验（`crt-7`） | 7 | 检查直觉答案并进一步思考的表现；答对题数 0–7 |
| 认知与决策 | 领域风险承担量表（`dospert-rt-30`） | 30 | 伦理、金融、健康安全、娱乐、社交五类风险承担倾向；五维均分 |
| 价值观 | 肖像价值观问卷 ESS 版本（`pvq-21`） | 21 | Schwartz 十种基本价值；均分及中心化值，当前编码下低分表示更强认同 |
| 社会态度 | ESS 社会信任（`ess-social-trust`） | 3 | 对他人可信度、公平性与助人倾向的看法；三题描述性均分 0–10 |
| 社会态度 | ESS 机构信任（`ess-institutional-trust`） | 7 | 对不同公共机构的信任；保留七个原题得分 |
| 社会态度 | ESS 政治效能（`ess-political-efficacy`） | 4 | 对自身政治参与能力及政治体系回应性的看法；保留四个原题得分 |

部分条目具有特定版本边界：`riasec-mini-ip` 使用 2016 年计算机版本，`pvq-21` 使用 ESS 男性肖像措辞，`dospert-rt-30` 仅含风险承担部分。更详细的计分与来源核对范围见 [问卷清单](docs/catalog.md)。

### 已收录、待核对（12 个）

这些条目允许查看题目、测试采集和导出答卷，**自动评分尚未开放**。

| 问卷（ID） | 题数 | 测量方向 | 尚未完成的核对 |
| --- | ---: | --- | --- |
| 原版坚毅量表（`grit-o`） | 12 | 兴趣一致性、努力坚持性 | 恢复原始题目措辞与题序 |
| 人际反应指数量表（`iri-28`） | 28 | 共情，包括观点采择、幻想、共情关怀与个人痛苦 | 核对原题序、选项及 0–4 编码 |
| 不确定性不耐受量表（`ius-12`） | 12 | 对不确定情境的反应 | 恢复被来源改写的原题 |
| Levenson 控制点量表（`levenson-ipc-24`） | 24 | 内控、有势力他人、机遇 | 核对重复／错配题目及响应编码 |
| 道德基础问卷第二版（`mfq-2`） | 36 | 关怀、平等、比例性、忠诚、权威、纯洁 | 核对原题及六点作答格式 |
| 道德基础问卷（`mfq-30`） | 30 | 关怀、公平、忠诚、权威、纯洁 | 补核两道不计分检查题及完整措辞 |
| 认知需求量表（`ncs-18`） | 18 | 对费力思考的偏好 | 核对原版选项含义及编码 |
| 肖像价值观问卷（`pvq-40`） | 40 | Schwartz 十种基本价值 | 核对原题序、代词改编及选项 |
| 修订肖像价值观问卷（`pvq-rr`） | 57 | 更细分的 19 种基本价值 | 核对原文、维度键及编码方向 |
| 自我概念清晰性量表（`scc`） | 12 | 自我认识的清晰、一致与稳定程度 | 修复并核验现有中文译本的语义问题 |
| 社会与经济保守主义量表（`secs`） | 12 | 社会与经济态度 | 核对两个子量表的题目归属及聚合方法 |
| 自陈习惯指数量表（`srhi`） | 12 | 指定行为的习惯强度 | 核对频率措辞和聚合方法 |

### 人工流程示例

`reflection-demo` 包含 3 个本项目编写的开放问题，用于演示作答、导出与人工审核。完成后 `judge()` 返回 `needs_human_review`，分数字段为空。它是接口示例，不属于上述 36 个量表。

## 具体使用方法

### 1. 获取项目

确认已安装 Python 3.11 或以上版本，然后执行：

```bash
git clone https://github.com/QuTongxi/isla-questionnaires.git
cd isla-questionnaires
python3 --version
```

以下命令均在项目根目录运行，无须额外安装运行依赖。若要从其他 Python 项目导入，可在对应的虚拟环境中执行 `python3 -m pip install /path/to/isla-questionnaires`；安装后也可使用 `isla-questionnaires` 命令。

### 2. 选择问卷并查看说明

```bash
# 查看可使用的问卷（含人工流程示例）
python3 -m isla_questionnaires list

# 查看全部条目，包括待核对问卷
python3 -m isla_questionnaires list --all

# 查看一般自我效能量表的介绍与作答说明
python3 -m isla_questionnaires show gse
```

将 `gse` 替换为上表中的 ID 即可选择其他问卷。`show` 展示说明和状态；逐题填写使用下面的 `run` 命令。

### 3. 在命令行作答、保存与恢复

```bash
mkdir -p sessions
python3 -m isla_questionnaires run gse \
  --save sessions/gse.json \
  --sheet sessions/gse.md
```

按屏幕显示的选项值输入答案。每次有效作答后自动保存；输入 `:quit` 或按 Ctrl-C 可退出。完成全部题目后输出评分结果，并将完整答卷写入 `sessions/gse.md`。

继续未完成的作答：

```bash
python3 -m isla_questionnaires run gse \
  --save sessions/gse.json \
  --resume sessions/gse.json \
  --sheet sessions/gse.md
```

每次新作答请使用不同的保存文件名；恢复已有作答时带上 `--resume`。会话和答卷包含个人答案，建议统一放在已被 Git 忽略的 `sessions/` 目录。

### 4. 对已有答案计分

`score` 接收以题目 ID 为键、答案值为值的 JSON 对象。例如，保存以下内容为 `sessions/gse-answers.json`：

```json
{
  "gse1": 4, "gse2": 4, "gse3": 4, "gse4": 4, "gse5": 4,
  "gse6": 4, "gse7": 4, "gse8": 4, "gse9": 4, "gse10": 4
}
```

```bash
python3 -m isla_questionnaires score gse sessions/gse-answers.json

# 查看逐题计分、反向编码及维度计算过程
python3 -m isla_questionnaires score gse sessions/gse-answers.json --trace
```

这个示例的 GSE 总分为 40。它是演示输入，实际使用时应填写真实答案。`score` 所需的答案对象与 `--save` 生成的完整会话文件格式不同；后者用于恢复作答。

### 5. 在 Python 中使用

以下示例使用 GSE 的整数选项，演示逐题提交、保存恢复和答卷导出：

```python
from pathlib import Path
from isla_questionnaires import load_questionnaire, restore_session

Path("sessions").mkdir(exist_ok=True)
q = load_questionnaire("gse")
print(q.describe()["instructions"])

while (question := q.next_question()) is not None:
    print(question.number, question.text)
    for option in question.options:
        print(option["value"], option["label"])
    answer = int(input("选择："))
    q.submit_answer(question.id, answer)
    q.export_session("sessions/gse-python.json")

result = q.judge()
print(result.to_dict())

with open("sessions/gse-python.md", "w", encoding="utf-8") as file:
    q.print(file=file)

resumed = restore_session("sessions/gse-python.json")
assert resumed.judge() == result
```

其他常用接口：

| 接口 | 用途 |
| --- | --- |
| `list_questionnaires(include_review=False)` | 列出问卷；传入 `True` 包含待核对条目 |
| `q.questions()` | 遍历题目、题目 ID 与选项 |
| `q.submit_answers(answers)` | 批量提交答案；整批校验通过后才写入 |
| `q.submit_answer(id, value, replace=True)` | 修改已答题并记录修改历史 |
| `q.audit_definition()` | 查看评分规则、来源、未计分题与核对状态 |
| `q.audit_score()` | 查看当前答卷的逐题计分过程 |
| `q.print(format="json", file=file)` | 导出 JSON 格式的完整答卷 |

已有多组答案时，可使用 `isla_questionnaires.testing` 中的 `score_answers(id, answers)` 或 `batch_score(id, answer_sets)`；批量评分为每组答案创建独立会话。默认需完成全部呈现题目，包括不计分的填充题。

### 6. 查看待核对问卷和人工示例

```bash
python3 -m isla_questionnaires show iri-28 --allow-review

# SRHI 需要明确所评估的行为
python3 -m isla_questionnaires show srhi --allow-review --parameter behavior=Walking

# 开放问题作答与人工审核流程
python3 -m isla_questionnaires run reflection-demo \
  --save sessions/reflection.json \
  --sheet sessions/reflection.md
```

Python 中对应使用 `load_questionnaire("iri-28", allow_review=True)`；SRHI 还需传入 `parameters={"behavior": "Walking"}`。`allow_review=True` 允许检查、采集和导出，但调用待核对量表的 `judge()` 仍会抛出 `ReviewRequired`。

### 7. 验证数据与运行测试

```bash
# 验证问卷结构、评分键和来源文件哈希
python3 -m isla_questionnaires validate

# 查看单个问卷的规则与来源
python3 -m isla_questionnaires audit gse

# 运行单元与集成测试
python3 -m unittest discover -s tests -v
```

需要生成可复现的测试答案时：

```bash
mkdir -p sessions
python3 -m isla_questionnaires generate-answers gse --pattern random --seed 42 \
  > sessions/synthetic-gse.json
python3 -m isla_questionnaires score gse sessions/synthetic-gse.json
```

合成答案仅供工程测试。现有验证记录见 [验证说明](docs/verification.md)。

## 未完成与未来工作

当前核心作答、会话恢复、导出和计分流程已实现。后续工作主要集中在问卷内容核验和使用范围完善，以下均为待办：

- [ ] **完成 12 个待核对条目。** 逐项解决上表中的原文、题序、选项编码和评分键问题，补充参考答案及回归验证后再开放计分。
- [ ] **扩大一手来源核对。** 已对 GSE、SWLS、ECR-R、HEXACO-60、O*NET Mini-IP 核对一手材料；其余已启用条目仍需进一步对照作者或官方施测与评分材料。
- [ ] **补充核验过的中文版本。** 先核实译本来源、授权、措辞和评分一致性，再作为独立语言版本加入；现有 SCC 中文译本需要修复。
- [ ] **完善版本与结果说明。** 为不同措辞、性别版本、编码方向和使用场景补充明确说明；常模与解释阈值需有适用于对应版本和人群的依据。
- [ ] **扩展兼容性验证。** 在更多受支持的 Python 版本和操作系统上验证安装、作答、恢复与计分；当前记录主要来自 macOS / Python 3.13。
- [ ] **完善逐量表的使用与授权说明。** 继续梳理量表本身的使用条件，以及来源代码许可证和量表内容授权的区别。

问卷定义与运行逻辑分开存放：`isla_questionnaires/data/<ID>/` 下的 `questionnaire.json`、`scoring.json`、`provenance.json` 分别保存题目、评分规则和来源记录，原始来源材料位于 `data/sources/`。新增问卷的流程见 [新增问卷指南](docs/adding-questionnaires.md)。
