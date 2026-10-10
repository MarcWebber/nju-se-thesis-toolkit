# macOS TeX 环境

MacTeX 和 BasicTeX 二选一，两个 Homebrew 安装包互斥。安装前确认所选版本的下载量、磁盘占用和系统目录变更，经用户同意后执行。

## MacTeX

推荐 MacTeX 无 GUI 版，包含完整 TeX Live，宏包较齐全。

```bash
brew install --cask mactex-no-gui
eval "$(/usr/libexec/path_helper)"
```

## BasicTeX

BasicTeX 体积较小，需要按论文依赖补装工具和宏包。选择该方案时运行 `brew install --cask basictex`，安装后重新打开终端。

## 验证

先确认命令可用，再检查论文使用的宏包和字体。NJUThesis 示例与字体配置见 [模板说明](nju-se-engineering.md)。编译命令直接接收主 TeX 文件。

```bash
latexmk --version
xelatex --version
biber --version
thesis doctor
thesis build /path/to/main.tex /path/to/compiled
```

环境诊断不代表编译成功，最终以编译退出码、日志和本次生成的 PDF 为准。

## 来源

- [MacTeX](https://tug.org/mactex/)
- [Homebrew MacTeX](https://formulae.brew.sh/cask/mactex-no-gui)
- [Homebrew BasicTeX](https://formulae.brew.sh/cask/basictex)
- [NJUThesis 安装说明](https://github.com/nju-lug/NJUThesis/wiki/%E5%AE%89%E8%A3%85)
