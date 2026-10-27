# 第三方材料说明

本工程的评分核心为独立编写；题目和部分规则从以下固定来源复制，另依据作者材料纠正了若干转录／版本问题。代码库许可证与量表本身的授权是两件事，本项目没有将这些材料统一重新许可为 MIT 或公有领域。

每个条目的具体出处、转换记录和源文件 SHA-256 均在 `data/<id>/provenance.json` 中。原许可证原样保存在来源目录。

| 来源 | 固定 commit | 许可证文件 |
| --- | --- | --- |
| [Neph0s/InCharacter](https://github.com/Neph0s/InCharacter) | `f554202a94d4a83dc5407245bb18981899e872e6` | [LICENSE](isla_questionnaires/data/sources/incharacter/LICENSE) |
| [stmueller/OpenScales](https://github.com/stmueller/OpenScales) | `d555b04a1961181a63f91b534bc1096bcbd1dcdc` | [LICENSE](isla_questionnaires/data/sources/openscales/LICENSE) |
| [AnthonyDavidAdams/personality-bench](https://github.com/AnthonyDavidAdams/personality-bench) | `fe3b6ddf2eda9d2cee39c7db55f14f8d7f73db1d` | [LICENSE](isla_questionnaires/data/sources/personality-bench/LICENSE) |
| [rubynor/bigfive-web](https://github.com/rubynor/bigfive-web) | `e8f3caca49edafb9bc6b927eff7fbc1264312c24` | [LICENSE](isla_questionnaires/data/sources/bigfive-web/LICENSE) |
| [AshitaOrbis/psyche-public](https://github.com/AshitaOrbis/psyche-public) | `28480802ce025a986a6574c013d2c7d07084c8ec` | [LICENSE](isla_questionnaires/data/sources/psyche/LICENSE) |
| [Chuan-Peng-Lab/PSV_Dataset](https://github.com/Chuan-Peng-Lab/PSV_Dataset) | `c72034ffc8303fa230a6b0334872245380e42558` | 快照中未收录许可证；未推定为开放授权 |
| [holi-lab/Psychometric-Item-Validation](https://github.com/holi-lab/Psychometric-Item-Validation) | `798253a4b123865e5a5add337c8fbcf55d29ff03` | [LICENSE](isla_questionnaires/data/sources/holi/LICENSE) |
| [Aurareus/PVQ-RR-Assessment](https://github.com/Aurareus/PVQ-RR-Assessment) | `09b251f334609dd028f997ea1fa9666c3932a3fb` | [LICENSE](isla_questionnaires/data/sources/pvq-rr/LICENSE) |
| [KaluJo/chatbot-study](https://github.com/KaluJo/chatbot-study) | `c1585408c63be7e4a6b7c3595f688026c18c03e9` | [LICENSE](isla_questionnaires/data/sources/chatbot-study/LICENSE) |
| [Bulgy404/health-habit-hub](https://github.com/Bulgy404/health-habit-hub) | `758aaafb6f747d160cfd3dd120e2015eeea33a01` | 快照中未收录许可证；未推定为开放授权 |
| [thphuc06/agentic-career-recommendation-system](https://github.com/thphuc06/agentic-career-recommendation-system) | `87844ee3e19717875f59f727b5a313b231f5a81e` | 快照中未收录许可证；未推定为开放授权 |

## 作者材料

- HEXACO：© Kibeom Lee 与 Michael C. Ashton。作者材料限定非营利学术研究；面向公众的在线问卷／App 有访问限制要求，其他用途需联系作者。保留的原条款位于 `sources/primary/hexaco-terms.html`；详见 [作者页面](https://hexaco.org/hexaco-inventory)。
- O*NET Mini Interest Profiler：National Center for O*NET Development，2016。保留报告原文及名称归属。使用与再分发须遵循 [O*NET 许可页面](https://www.onetcenter.org/license.html) 的相应材料许可；本实现没有职业匹配数据库。
- GSE、SWLS、ECR-R：保留作者页面快照和来源链接；其题目版权／使用条款以作者材料为准。
- OpenScales 整库使用 CC BY-NC-SA 4.0；个别量表文件还声明了作者授权或其他许可，声明保留在 `.osd` 中。未将这些声明扩展为本项目对所有量表的统一保证。

## 本次材料修改

题目／选项／维度键转换为 JSON；移除角色扮演改写与 LLM 评价；修正 GSE 原文、SWLS 选项方向、ECR-R 转录错误；以作者资料替换误标的 HEXACO 与 O*NET 题库。待核对版本仍保留来源差异，不解除自动计分限制。详细修改见每个量表的 `transformations`。

仅把本目录建立为本地独立项目；尚未设置远程仓库或发布软件包。复制和审计证据的保留不表示已取得额外商业使用／公开再分发许可。
