# 写作指令来源

这五份任务指令由本项目编写，参考了下列开源方法，并非直接复用一套经过验证的论文写作方案。链接固定到本次读取的提交版本。

## 方法对应

| 本地位置 | 保留的方法 | 原文位置 |
|---|---|---|
| Skill 共用规则 | 按已有材料写作，事实与待查事项分开 | [Scientific Writing：No fabrication、Scientific fidelity](https://github.com/K-Dense-AI/scientific-agent-skills/blob/49c6e97775eaa18ba791bebe23162a70ae601c18/skills/scientific-writing/SKILL.md#L32-L61) |
| 材料与提纲 | 章节对应问题与依据，材料不足时收缩目录 | [中文论文写作：提纲构造](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/blob/480ed5788d0ffc6635ea785bc9a06e7a000090d8/chinese-academic-writing-assistant/references/academic-writing.md#L17-L21) |
| 章节写作 | 按论证关系分段，范文用于校准表达而非移植事实 | [中文论文写作：规划、成段与文体](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/blob/480ed5788d0ffc6635ea785bc9a06e7a000090d8/chinese-academic-writing-assistant/references/academic-writing.md#L3-L14) |
| 文献与相关工作 | 分别核对来源、书目、论断支持和著录格式 | [中文论文写作：内部证据账本](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/blob/480ed5788d0ffc6635ea785bc9a06e7a000090d8/chinese-academic-writing-assistant/SKILL.md#L38-L47) |
| 全文修订 | 核对跨处数字、单位和方法结果对应关系 | [Scientific Writing：Numbers and units、Methods and results](https://github.com/K-Dense-AI/scientific-agent-skills/blob/49c6e97775eaa18ba791bebe23162a70ae601c18/skills/scientific-writing/references/writing_principles.md#L39-L65) |

上述方法作了简化转述，未引入上游的证据编号、清单脚本或审批流程。来源说明的是方法出处，不是本地 Prompt 的效果证明。

## 本项目约定

1. 工程论文章节分工是内容组织建议，依据作者模板调整，不是南京大学发布的统一目录。
2. 仓库分析与摘录操作见 [代码材料](code-evidence.md)；图型、源文件、SVG 与矢量 PDF 交付见 [论文图表](diagrams.md)。这些是工具约定，不归为上游学术方法。
3. 各份 Example 是合成案例。写法尚未用用户提供的完整论文范文校准，也未进行跨模型效果评测。

## 其他查阅项目

1. [Thesis Skill Hub 章节写作](https://github.com/DQXCJ-a11y/thesis-skill-hub/blob/0947beb624fa3aa70b4524343e660e5d8abbdd03/skills/04-%E7%AB%A0%E8%8A%82%E5%86%99%E4%BD%9C.md)：作为候选查阅，未采用其逐节确认与句式模板。
2. [南大论文自检](https://github.com/dongshao/nju-se-thesis-self-check/tree/1be6f76f9c2bc3364aa8e68082aecf0cc18c8ba4)：可选外部审阅参考，未复制规则或脚本。

## 许可证

- [K-Dense MIT](https://github.com/K-Dense-AI/scientific-agent-skills/blob/49c6e97775eaa18ba791bebe23162a70ae601c18/LICENSE.md)
- [中文论文写作 MIT](https://github.com/gongyu0918-debug/chinese-academic-writing-skill/blob/480ed5788d0ffc6635ea785bc9a06e7a000090d8/LICENSE)
- [Thesis Skill Hub MIT](https://github.com/DQXCJ-a11y/thesis-skill-hub/blob/0947beb624fa3aa70b4524343e660e5d8abbdd03/LICENSE)

查阅时未在南大论文自检仓库找到许可证，仅保留链接。直接分发上游文本或代码前，须核对许可并保留相应声明。
