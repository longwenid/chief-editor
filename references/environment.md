# L3 环境适配：引擎、解释器、编码与路径

何时读：会话开始（唤醒之前）、引擎路径或解释器报错时、第一次写记忆前。

本文件是**唯一**允许出现具体绝对路径、Windows 专有写法和平台差异的地方。其他任何文件只写 `<novel-ledger>`、`$NOVEL_LEDGER`、`$PROJECT`、`$CHIEF_EDITOR_MEMORY` 这些占位符，由本文件的解析结果代入。`scripts/check_layers.py` 会拦截违规的绝对路径，所以不要图省事把路径抄进流程文件。

## 1 引擎目录（$NOVEL_LEDGER）解析顺序

按序试，命中即用；四种都不命中就停下来问用户，不要自造第四种解法：

1. 环境变量 `NOVEL_LEDGER`（用户显式指定，最高优先）；
2. 本技能目录的同级兄弟目录 `../novel-ledger`（开发态布局，改引擎时常见）；
3. 安装态默认 `~/.zcode/skills/novel-ledger`（macOS/Linux）；
4. Windows 安装态 `%USERPROFILE%\.zcode\skills\novel-ledger`。
全都找不到时：向用户要一个路径后写进 `NOVEL_LEDGER`，**不要自造或临时修补引擎**（`references/red-lines.md#12`）。判失效前先做文件系统核实——路径字面看着不对不等于真失效；已有待办先核实固定构建与原执行者，再按唤醒流程刷新。

### 固定运行入口

上述解析只定位可信入口；写作运行与引擎开发目录分离。开始连续写作前，按 `$NOVEL_LEDGER/references/runtime.md#固定运行版本与受控切换` 使用 `pin-engine --output "$RUNTIME"` 创建或复用清单有效的固定副本。`$RUNTIME` 是开发树以外的独立路径；保留源入口位置，将后续 `$NOVEL_LEDGER` 设为实际返回的 `runtime_root`，所有主控与 Worker 命令沿同一固定入口。不得把副本链接回开发树或手工改副本文件。

已有项目须核对其冻结构建：用准确源入口带 `--project "$PROJECT"` 执行 `pin-engine`；必要时 `--ref` 使用发布记录核实的引用，不按版本号猜指纹。该入口只读项目冻结指纹，不取消待办、不改开发检出。若需要切换构建，先保留现场并取本次升级授权，再从新固定入口对准确 task/input_hash 执行 `recover-engine`；原执行者停止由宿主核实。恢复同一构建与升级是两条不同路径，不能用技术重试消除 `engine_changed`。

## 2 解释器

| 平台 | 解释器 | 备注 |
|---|---|---|
| Windows | `python` | Git Bash；`python3` 常缺，不要用 |
| macOS / Linux | `python3` | 没有 `python3` 再退 `python` |

派工前核实命令里的解释器与脚本真实存在一次；别凭上次会话的印象。

## 3 编码

每个新 shell 第一件事：`export PYTHONUTF8=1`。

引擎输出是 UTF-8，Windows GBK 控制台会把中文长文本变成乱码。所以：

- 人读的长内容一律走引擎物化到磁盘的文件（`board.md`、`question.json`、`dispatch.md`、`brief.md`、`task.json`、`proposal.plan_path`）；
- 控制台只看机器可读的短 JSON；
- 长中文绝不在命令行内联，用 `--file` 提交。

## 4 命令形状

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" <子命令> ...
```

- 路径一律加引号——项目目录常含中文与空格；
- `commands` 是 argv 数组，按数组逐个执行，不拼 shell 字符串（red-lines #9）；
- 项目命令必须带 `--project`，多项目并行时绝不省略；仅新建固定副本的 `pin-engine` 不带项目，已有待办的构建恢复必须带项目。

## 5 记忆根（$CHIEF_EDITOR_MEMORY）

技能目录只放模板：`memory/templates.md` 与空目录的 `.gitkeep`。实例数据（台账、快照、拆解、决策、复盘）全部写在记忆根：

1. 环境变量 `CHIEF_EDITOR_MEMORY`；
2. 默认 `~/.chief-editor`（macOS/Linux）或 `%USERPROFILE%\.chief-editor`（Windows）。

首次运行时记忆根不存在：按 `memory/templates.md` 建档。如果技能目录里已经躺着历史实例（旧版本遗留），整体迁到记忆根再继续，迁移前留一份快照即可，**不要边迁边改内容**。多项目并行时记忆根是共用的，项目目录各自独立——这是两套路径，别混。

## 6 项目目录（$PROJECT）

每本书一个独立的绝对路径，由作者决定或在立项时确认。不覆盖已有目录，不把项目建在技能目录或记忆根里。项目目录里的正文、卷纲章纲、world_model、任务文件只在该项目自己的流程上下文中读取（red-lines #12）。

## 7 平台差异速查

| 项 | Windows | macOS / Linux |
|---|---|---|
| shell | Git Bash | bash / zsh |
| 路径写法 | Git Bash 内用 `/` 亦可 | `/` |
| 编码 | `PYTHONUTF8=1` 必须 | 建议同样设置 |
| 解释器 | `python` | `python3` |
| 记忆根默认 | `%USERPROFILE%\.chief-editor` | `~/.chief-editor` |
