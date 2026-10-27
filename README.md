# Isla Questionnaires

独立、离线运行的社会学／心理学问卷工程。Python 3.11+，运行时仅使用标准库。

题目、作答选项、评分规则和来源证据都是本项目内的文件；不导入、不调用、不通过软链接引用原项目或 InCharacter。保留原量表维度，排除角色扮演评分、角色相似度、LLM 判断和未经证实的常模。

## 当前交付范围

收录 **36 个量表条目**：**24 个已启用本地计分，12 个待核对、自动评分被禁用**。另有 `reflection-demo`，仅演示人工审核流程，不计入量表数量。

“已启用”表示该固定来源版本能够运行，不等于完成新的心理测量效度验证。GSE、SWLS、ECR-R、HEXACO-60、O*NET Mini-IP 核对了一手材料；其余已启用条目保留来源题库的题目和维度键，验证范围写在 `provenance.json` 中。详细清单和疑点见 [量表清单](docs/catalog.md)。

当前正式启用的题目为英文。SCC 的中文译本存在语义问题，保留在待核对区；不会自动翻译题目或将未验证的译本冒充标准中文版。

## 立即运行

在本项目目录执行，无须安装任何包：

```bash
python3 -m isla_questionnaires list
python3 -m isla_questionnaires show gse
mkdir -p sessions
python3 -m isla_questionnaires run gse --save sessions/gse.json --sheet sessions/gse.md
```

输入选项对应的数字。输入 `:quit` 或 Ctrl-C 保存退出。恢复：

```bash
python3 -m isla_questionnaires run gse --save sessions/gse.json --resume sessions/gse.json
```

需要从别的工程导入时，在使用方的虚拟环境安装本项目即可：

```bash
python3 -m pip install /path/to/isla-questionnaires
```

安装后也可使用 `isla-questionnaires` 命令。构建需要 setuptools；安装后的运行不访问网络。

## Python 接口

```python
from isla_questionnaires import load_questionnaire, restore_session

q = load_questionnaire("gse")
print(q.describe()["instructions"])

while (question := q.next_question()) is not None:
    print(question.number, question.text)
    print(question.options)
    answer = int(input("选择："))
    q.submit_answer(question.id, answer)

result = q.judge()
print(result.to_dict())
q.export_session("gse-session.json")
with open("gse-answer-sheet.md", "w", encoding="utf-8") as file:
    q.print(file=file)

resumed = restore_session("gse-session.json")
assert resumed.judge() == result
```

同时支持最初约定的拼写 `load_questionaire()` 和 `Questionaire`。推荐新代码使用 `load_questionnaire` / `Questionnaire`。

| 接口 | 行为 |
| --- | --- |
| `list_questionnaires(include_review=False)` | 默认只列出可使用的条目；可包含待核对条目 |
| `load_questionnaire(id, language=..., version=...)` | 精确选择已安装版本；不静默翻译或降级 |
| `q.next_question()` | 查看第一道未答题；反复调用不会跳题；全部完成返回 `None` |
| `q.questions()` | 按问卷固定顺序遍历题目 |
| `q.submit_answer(id, value)` | 校验并记录答案；修改已答题须明确 `replace=True` |
| `q.submit_answers({id: value})` | 整批预检，任一答案非法则整批不写入 |
| `q.judge()` | 返回版本、分数、维度说明、来源核对级别和内容哈希 |
| `q.print(format="markdown", file=...)` | 打印并返回完整答卷，支持 JSON；不会推断人工结论 |
| `q.export_session(path)` / `restore_session(path)` | 保存、恢复答案及修改历史 |
| `q.audit_definition()` | 审计规则、来源、未计分题、核对状态；未作答也能使用 |
| `q.audit_score()` | 逐题查看原始答案、反向编码、贡献、除数、中心化和最终结果 |

自动量表 `judge().status == "scored"`。例如 GSE 每题选 4，原生总分是 40/40，含义为更强的一般自我效能；不会凭空添加一个“正常”阈值。SWLS 额外返回作者原表明确列出的满意度区间标签，例如 31–35 为 `Extremely satisfied`；这是量表分数解释，不是临床诊断。ESS 机构信任／政治效能返回原题得分；本工程没有把第三方自定聚合分数称为 ESS 的官方分类。

人工问卷返回 `needs_human_review`，分数字段为空。可用 `reflection-demo` 检查完整作答、打印、交给人工的流程。

待核对量表默认加载时抛出 `ReviewRequired`。`allow_review=True` 仅允许查看、测试采集和导出，**不会绕过 `judge()` 的禁用状态**。SRHI 还需传 `parameters={"behavior": "Walking"}`，以明确所评估的行为。

## 逻辑与数据分开

```text
isla_questionnaires/
  session.py           # 作答、导出、恢复
  scoring.py           # 确定性的通用评分运算
  validation.py        # 问卷与答案校验
  catalog.py           # 目录及内容完整性检查
  cli.py               # 命令行
  testing.py           # 可复现的合成答案和批量测试
  data/
    catalog.json
    <量表 ID>/
      questionnaire.json   # 题目、选项、指导语、版本
      scoring.json         # 维度、题号、反向题、计算方法
      provenance.json      # 来源、哈希、变更与待核对事项
    sources/               # 复制进来的证据快照及原许可证
tools/                 # 开发期数据转换和目录重建；运行时不调用
tests/                 # 原生分数、会话、完整性及 CLI 回归测试
```

新增常规量表只需增加数据文件及参考答案，不必修改运行核心。详见 [新增问卷](docs/adding-questionnaires.md)。

## 测试与审计

```bash
python3 -m unittest discover -s tests -v
python3 -m isla_questionnaires validate
python3 -m isla_questionnaires audit gse
python3 -m isla_questionnaires list --all

# 合成数据，仅供工程测试；不是有效被试数据
python3 -m isla_questionnaires generate-answers gse --pattern max > sessions/synthetic-gse.json
python3 -m isla_questionnaires score gse sessions/synthetic-gse.json --trace
```

Python 测试辅助接口：`synthetic_answers(q, pattern="random", seed=42)`、`score_answers(id, answers)`、`batch_score(id, answer_sets)`，位于 `isla_questionnaires.testing`。所有批量评分使用独立会话。

默认要求完成全部呈现题目，包括不计分的填充题；不自动补缺失值。哈希和事件链用于发现内容漂移或文件损坏，不是签名，也不能证明被试身份或防止攻击者重算全部哈希。会话包含答案，建议保存在已忽略的 `sessions/` 下。

来源代码许可证不自动覆盖量表版权。复制文件、作者条款与使用范围见 [第三方材料说明](THIRD_PARTY_NOTICES.md)。
