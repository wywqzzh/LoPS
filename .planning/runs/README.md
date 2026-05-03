# 重构轮次目录

`.planning/runs/` 用于保存多轮科研脚本重构实例，不用于保存 GSD phase 计划。GSD 阶段计划保存在 `.planning/phases/`；具体某一轮外部科研脚本重构的信息保存在 `.planning/runs/`。

## 目录命名

每轮目录命名格式必须是：

```text
YYYY-MM-DD-short-name
```

`short-name` 只能使用小写 ASCII 字母、数字和连字符，并应从目标脚本或科研功能派生。示例：

```text
.planning/runs/2026-05-03-kalman-filter/
```

每轮目录中的入口文件建议命名为 `intake.md`。

## 最低必填信息

进入后续分析前，`intake.md` 至少需要填写：

- 目标脚本路径
- 运行环境
- 数据来源

运行命令、必要权限、预期输出可以先写“待补充”。这些占位内容表示信息尚未确认，下游阶段不能把它们当作已验证事实。

## 模板

从 `.planning/runs/INTAKE-TEMPLATE.md` 复制内容，创建新一轮的 `intake.md`。

## 安全提醒

不要在 intake 中记录 API keys、密码、token 或私有凭据。需要权限或凭据时，只记录“需要用户授权”或“待补充”，不要写入实际秘密值。

## 当前边界

Phase 1 只提供最小入口骨架，不提供完整任务管理系统。具体脚本分析、重构方案、执行结果和一致性验证会在后续阶段逐步补充。
