# 本地 TeX 环境

2026 年 9 月 24 日在本机安装官方 TeX Live 2026，路径为 `/Users/bytedance/Library/TeXLive/2026`，占用约 634 MiB。按需安装，不包含完整发行版的所有宏包、文档和源码；未写入系统 TeX 目录，不需要管理员权限。

## 使用

新开的 Bash 和 Zsh 登录终端已加入命令路径。已有终端执行：

```bash
export PATH="/Users/bytedance/Library/TeXLive/2026/bin/universal-darwin:$PATH"
source .venv/bin/activate
thesis doctor
thesis build /path/to/main.tex /path/to/new-output
```

PATH 配置位于本机 `.bash_profile` 和 `.zprofile`，工具代码不包含本机安装路径。`build` 输出目录须不存在或为空。其他项目仍可直接使用 `latexmk`、`xelatex` 和 `biber`。

## 中文

已安装 ctex、xeCJK、Fandol、中文参考文献样式，以及表格、代码、数学和 PGF 绘图宏包。通用中文工程可使用：

```tex
\documentclass[UTF8,fontset=fandol]{ctexart}
```

Fandol 随 TeX Live 安装，不依赖 Word 或学校平台。当前南大模板副本使用 `fontset=macoffice`，由模板读取本机 Microsoft Word 已有的宋体、黑体、仿宋、楷体和华文中宋。原模板的 `fontset=win` 保持不变。Word 字体未复制、未打包分发，其他机器须自行具备对应字体或明确选择另一套字体。

## 版本对照

线上列取自 [2026 年 9 月 5 日保存的完整编译日志](../output/native-template-baseline/compile.log)，不是今天重新编译的结果。

| 组件 | 本机 | 线上历史对照工程 |
|---|---|---|
| TeX Live | 2026 | 2026 |
| XeTeX | 3.141592653-2.6-0.999998 | 3.141592653-2.6-0.999998 |
| LaTeX2e | 2026-06-01 | 2026-06-01 |
| L3 | 2026-09-09 | 2026-08-10 |
| ctex | 2.6.5 | 2.6.5 |
| xeCJK | 3.10.6 | 3.10.5 |
| fontspec | 2.9h | 2.9h |
| biblatex | 3.22 | 3.22 |
| NJUThesis 工程文件 | 1.5.1 | 1.5.1 |

本机 latexmk 为 4.88，Biber 为 2.22。安装清单与修订号保存在 TeX Live 自身的 `tlpkg/texlive.tlpdb`，安装命令记录在 `texmf-var/web2c/tlmgr-commands.log`。

NJU TeX 不存在可直接假定的统一版本。历史记录中，用户原项目使用 TeX Live 2022 并出现模板错误，独立对照项目使用 2026 编译通过。本机按这个可用基线配置 2026，未将工具绑定到特定学校服务器。

2026 年 9 月 24 日完成 SSO 后，已在原项目设置页核对当前配置为 XeLaTeX、TeX Live 2022，主文件为 `njuthesis-sample.tex`。本机使用 2026，与原项目尚未对齐；需要改变线上编译版本或另备 2022 环境时，应先确认目标工程。未修改线上设置或上传文件。原项目启用了打开时自动编译，因此打开编辑器可能由平台自动触发编译，不能把页面检查描述为保证未编译。

独立对照项目的 2026 年 9 月 5 日完整日志仍只作为历史基线。当前日志接口未取得可读结果，线上宏包精确版本未重新验证。本机与历史基线同年份、同引擎，但 L3、xeCJK 和字体配置有差异，不能声称逐页一致。

## 验证

| 工程 | 结果 |
|---|---|
| [通用中文样例](../output/local-tex-20260924/chinese-project/main.tex) | 1 页 PDF，中文、公式、表格、代码、矢量插图、Biber 文献及交叉引用通过，已查看完整页面 |
| [南大模板副本](../output/local-tex-20260924/nju-project/njuthesis-sample.tex) | 30 页 PDF，编译、最终日志和结构检查通过，已查看页面缩略图；保留原文，仅改副本字体选项 |

PDF、源副本和完整日志保存在 `output/local-tex-20260924/`。通用样例使用合成数据和明确标注的合成文献；南大工程为历史演示稿，不代表当前 toolkit 设计或可提交的学位论文。南大日志还有两处轻微超宽和若干欠满提示，版式及内容需另行审阅。

实际编译修复了两处日志误判：长输出路径换行不再被视为没有产物，`LaTeX Font Info` 的正常字形替换不再被视为缺失字体。缺字、字体错误、未解析引用和编译错误仍参与检查。未新增测试套件。
