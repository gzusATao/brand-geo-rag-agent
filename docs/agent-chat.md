# 首页百炼多智能体对话

## 使用与配置

在项目目录运行以下命令，在本地隐藏输入百炼 API Key，不要将密钥贴进聊天、命令行参数或代码：

```powershell
.\.venv\Scripts\python.exe -m scripts.configure_llm
```

默认北京地域兼容接口 `https://dashscope.aliyuncs.com/compatible-mode/v1`，默认模型 `qwen-plus`。请确认密钥地域与接口一致；可使用百炼提供的业务空间专属 HTTPS 域名。配置写入项目已忽略提交的 `.env`，不修改公司项目或公共模块。

配置后重启服务。首页选择品牌项目，在任务类型「启动 AI 自动 GEO · 多 Agent」中发送问题。Ctrl + Enter 也可发送。每次发送会向百炼传输本轮消息、最近四轮成功对话、当前品牌、相关知识片段和被选中的指标汇总。界面展示用户消息、最终回复、知识引用和各角色公开执行摘要，不展示模型内部思维链。

配置状态只表示已填写，不代表连通性已验证。未配置返回明确提示，不生成假回复；密钥无效、配额不足、超时和无效 JSON 均按失败处理。没有配置真实密钥时，接口模拟测试不能作为真实模型联调或毕业论文实验结果。

## 编排方式

参考 `D:\projects\ai-agent-interview-guide` 的多智能体文档、Python 编排器、规划器、工具注册和短期记忆代码，采用受控的 Boss-Worker / Plan-and-Execute 思路。不是复制其整个项目，也没有引入尚未部署的 Redis、Milvus、LangGraph 或任意 SQL 工具。

1. `SupervisorAgent`：模型根据本轮要求和近期对话返回受 Pydantic 校验的 JSON 计划，只能选择 `rag` 和 `tool` 白名单角色。
2. `RagAgent`：读取当前项目最多五个词面检索片段，调用模型整理有来源的答复；不是向量或联网检索。
3. `ToolAgent`：确定性执行只读品牌指标工具，分别统计真实、历史和模拟回答；不接受模型生成的 SQL、项目 ID 或外部 URL。
4. `SummaryAgent`：等待选中的专业任务完成后汇总回复，生成待审核建议或草稿，并校验引用 ID 是否存在于专业结果中。引用 ID 有效不代表所有自然语言事实已经自动核实。

主管与摘要顺序执行，独立的检索和指标任务并行执行。角色实现在 `app/services/agent_roles_service.py`，任务编排与内存会话在 `agent_chat_service.py`，模型适配在 `app/libs/qwen_client.py`。沿用本项目现有 controllers/services/apis 分层，不搬入参考项目的整个目录或额外中间件。

## 限制与安全

- 每轮最多三次模型调用；单次响应最多1800输出 Token，单次45秒，整轮120秒；不自动重试或无限重规划。
- 全局最多两个未完成任务，同一会话不能并发发送；每个会话最多十二轮，仅最近四轮进入模型上下文。
- 内存最多50个会话、约100条任务；空闲一小时过期。页面刷新开启新会话，服务重启全部丢失，不支持断点恢复。
- 不新增数据库表或迁移；聊天结果、轨迹和历史当前都在内存，不改监测回答，不自动保存文章。
- 拒绝跨项目会话与任务读取；所有接口沿用登录、超级管理员及同源校验。
- 模型地址仅允许百炼官方 HTTPS 域名，不跟随重定向；前端、错误和日志不回显密钥或供应商原始报文。
- 角色输出使用 JSON Schema / Pydantic 校验，资料仅作为不可信证据输入；没有开放 shell、任意网络请求、数据库修改或发布工具。

接口：`GET /api/v1/agent-chat/config`、`POST /api/v1/projects/{id}/agent-chat`、`GET /api/v1/projects/{id}/agent-chat/{run_id}`、`GET /api/v1/projects/{id}/agent-sessions/{session_id}`。

百炼官方参考：[兼容接口及模型调用](https://www.alibabacloud.com/help/zh/model-studio/model-calling-in-sub-workspace)、[JSON 结构化输出](https://www.alibabacloud.com/help/zh/model-studio/qwen-structured-output)。
