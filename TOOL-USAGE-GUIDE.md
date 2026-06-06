# 工具使用避坑指南

> 记录于 2026-06-06，避免重复犯错。子 Agent 启动前注入。

## 工具与运行环境

| 工具 | 实际环境 | 语法 |
|------|----------|------|
| **Bash** | Unix-like shell (Git Bash) | Bash 语法，正斜杠路径 |
| **PowerShell** | Windows PowerShell 5.1 | PowerShell 语法，反斜杠路径 |

## 核心原则：优先用专用工具

| 场景 | ✅ 正确做法 | ❌ 错误做法 |
|------|------------|------------|
| 搜索文件名 | **Glob** | `ls`、`find`、`Get-ChildItem` |
| 搜索文件内容 | **Grep** | `grep`、`Select-String` |
| 读取文件 | **Read** | `cat`、`Get-Content` |
| 编辑文件 | **Edit** | `sed`、`Set-Content` |
| 写文件 | **Write** | `Out-File`、`Set-Content` |
| PowerShell 命令 | **PowerShell 工具** | Bash 工具 |
| Bash 命令 | **Bash 工具** | PowerShell 工具 |

## 常见错误

### 1. Bash 中用了 PowerShell 语法
```bash
# ❌ 错误
command 2>$null          # $null 是 PS 变量
# ✅ 正确
command 2>/dev/null      # Bash 的 stderr 重定向
```

### 2. Bash 中用了 Windows 反斜杠路径
```bash
# ❌ 错误 — \ 被当成转义字符
ls D:\code\demo
# ✅ 正确 — 用正斜杠
ls D:/code/demo
```

### 3. PowerShell 中 Expand-Archive 不支持 .docx
```powershell
# ❌ 错误 — Expand-Archive 只认 .zip
Expand-Archive "file.docx"
# ✅ 正确 — 先改扩展名
Copy-Item "file.docx" "temp.zip"
Expand-Archive "temp.zip"
```

### 4. PowerShell 5.1 限制
- 没有 `&&` / `||` 管道链运算符
- 没有三元运算符 `?:`
- 没有 null-coalescing `??`
- 用 `if/else` 代替
