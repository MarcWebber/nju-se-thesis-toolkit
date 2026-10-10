# 南大平台

平台操作直接使用用户已有的 NjuCLI，不另建登录器、上传器或编译客户端。先读取安装中的 `njucli-tex` Skill，运行 `njucli tex --help` 核对接口。CLI 未在 PATH 时，可使用用户提供的 Node 入口；不要自动下载同名包。

本机已核对的入口为 `node /Users/bytedance/project/njucli/dist/cli.js`。这是当前机器的路径，不是安装包默认配置。

从 `projects` 和 `files` 读取真实项目、版本和路径。写操作前确认目标工程和文件范围；用户模板保留不动。认证按错误中的 `auth_command` 处理，SSO 由用户在 CLI 专用浏览器完成。

```bash
njucli tex projects --format json
njucli tex files PROJECT --version VERSION --format json
njucli tex download PROJECT --version VERSION --output ./backup.zip --format json
njucli tex read PROJECT FILE_KEY --version VERSION --format json
njucli tex write PROJECT main.tex --version VERSION --input ./main.tex --yes --format json
njucli tex upload PROJECT ./figure.pdf --version VERSION --yes --format json
njucli tex compile PROJECT main.tex --version VERSION --output ./paper.pdf --yes --format json
njucli tex log PROJECT --version VERSION --format json
```

`write` 替换已有文本文件，包含已有子目录文件。`upload` 仅上传根目录单文件，同名会替换，不支持递归目录或 ZIP 工程导入。不能把本地源包直接传给 `upload` 就声称完成部署。目标缺少目录时，需要平台原生导入或明确调整工程路径。

同一账号串行操作，不自动重放失败写入。检查退出码和 JSON `ok`。`compile` 已下载本次 PDF，随后保存 `log` 返回的原始正文，不把 JSON 信封当编译日志。检查引用、字体和版面后再交付。

下载结果后用 `thesis check-log` 检查完整编译日志，用 `thesis inspect-pdf` 检查 PDF 结构，再逐页查看排版。记录实际项目、版本和文件范围，归档时将源工程、PDF、日志与图源一并传给 `thesis pack`。
