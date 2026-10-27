# 新增问卷

运行时只读取 JSON。本工程不需要安装 LangChain、DeepAgent、InCharacter，也不需要网络或模型 API。

## 数据契约

在 `isla_questionnaires/data/<id>/` 新建三个文件。ID 使用小写字母、数字、连字符。

1. `questionnaire.json`：`schema_version: 1`、`id`、`version`、`name`、`languages`、`default_language`、`status`、`instructions`、`expected_items`、`items`。
2. `scoring.json`：`schema_version: 1`、`questionnaire_id`、`mode`、`missing_policy: "require_complete"`、`dimensions`。
3. `provenance.json`：来源版本与 URL、证据文件列表 `files: [{path, sha256}]`、`verification`、`transformations`、授权信息。

可以从最接近的已收录量表复制结构。不要复制原量表的题目或规则后只改名称。版本改变必须修改 `version`；已保存的会话不会自动迁移到新版本。

题目类型示例：

```json
{
  "id": "q1",
  "text": "Exact source item text",
  "type": "choice",
  "options": [
    {"value": 0, "label": "No"},
    {"value": 1, "label": "Yes"}
  ],
  "help": "Exact source instruction"
}
```

`choice` 使用明确的数值选项；不接受字符串数字、布尔值或范围内但未列出的中间值。`number` 可带 `min`、`max`、`integer`，支持有范围的连续评分和无范围的数学题。`text` 收取非空字符串。文本字段可用字符串，或使用语言到文本的字典；列出的语言必须完整提供，不能静默回退。

评分示例：

```json
{
  "schema_version": 1,
  "questionnaire_id": "example",
  "mode": "automatic",
  "missing_policy": "require_complete",
  "dimensions": [{
    "id": "total",
    "name": "Total",
    "description": "Exact meaning and score direction supported by the scale.",
    "operation": "sum",
    "terms": [{"item": "q1", "reverse": false}]
  }]
}
```

支持的运算：

| operation | 定义 |
| --- | --- |
| `sum` | 各题编码后加权求和 |
| `mean` | 各题编码后加权平均 |
| `centered_mean` | 该维度均分减去 `reference_items` 指定的全部原始作答均分 |
| `correct_count` | 按每项 `accepted` 答案键计分；字符串只做去首尾空白和大小写归一 |

`reverse: true` 使用该题显式选项范围的 `min + max - answer`；默认权重 1，支持正数 `weight` 和维度 `offset`。不要用不连续数值选项模拟需要额外映射的复杂标准；需要新运算时扩展核心并提供独立参考样例，不能悄悄套用已有公式。

`manual` 和 `export_only` 不生成分数。题目需要行为背景时，在 `parameters` 声明必填文本参数，使用 `{{behavior}}` 形式占位；见 SRHI。这只用于源量表本来就要求的上下文，不用于自由改写标准题目。

## 接入与核对

- 复制原始材料到 `data/sources/`；记录作者、版本、语言、原文、选项、题序、反向题、维度键、缺失值要求与使用条款。
- 原始文件可以作为审计证据保留，但不能在运行时导入原仓库的类、评分函数或模型提示词。
- 如果有未解决的标准差异，设 `status: "review_required"`，在 `review_notes` 和来源记录中写出具体差异。工程测试通过不能替代这些核对。
- 将手工计算或作者公布的样例加入测试；至少有能区分反向题、总分／均分和特殊编码的输入。
- 执行 `python3 tools/reindex.py`，再运行 `python3 -m isla_questionnaires validate` 和单元测试。`reindex` 不会重写来源证据哈希，也不会解除待核对状态。
- 原首批目录数量测试固定了 36 个量表和一个演示；正式新增量表时更新相应数量断言与清单。

`tools/build_catalog.py` 专门重现首批数据转换，会重新生成首批量表；日常新增或审核后的 JSON 修改使用 `reindex.py`。转换 TypeScript 快照时才需要 Node 24+ 与 `node tools/extract_sources.mjs`。快照内容应在执行前审查；最终用户运行只需 Python。

维度可选 `interpretation: {source, bands}`，其中 `bands` 为按分数递增排列、不重叠的 `{min, max, label}` 区间，边界包含在内。仅允许写入有明确来源、适用当前版本的解释区间；结果与审计轨迹同时返回命中的区间和出处。SWLS 已按作者原表接入。依赖年龄、语言、群体等条件的常模，仍需扩展显式的适用条件及独立测试；不能直接套用单套区间。未配置解释规则时只交付原生分数与维度说明。
