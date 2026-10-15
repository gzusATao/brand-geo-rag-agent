# 基于RAG与智能体的品牌GEO优化系统

仓库仅包含源码、测试、结构 SQL、文档和运行所需的静态素材。真实 `.env`、密钥、数据库文件、上传资料、IDE 配置及本地过程截图不提交；首次克隆后按下方步骤配置自己的数据库、管理员和百炼密钥，不能直接使用开发机配置。

当前为单机单用户毕业设计原型，不是全部毕业设计成果。已支持项目、问句、CSV回答导入、模拟监测、规则指标与原始证据、文本资料词面检索、固定工具辅助优化、草稿编辑审核和Markdown导出。新增首页百炼多智能体对话：配置密钥后，用户发送消息才会调用收费模型；模拟监测和原固定工作流不调用模型，不会自动发布。

首页大输入框已连接主管、RAG检索、数据工具、摘要四个角色，支持多轮追问和执行状态。模型配置与参考项目的架构映射见[多智能体对话说明](docs/agent-chat.md)。未配置密钥时明确报错，不返回伪造模型回复。

## 启动

使用Python 3.10或以上，在本目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.configure_mysql
.\.venv\Scripts\python.exe -m scripts.init_db
.\.venv\Scripts\python.exe -m scripts.create_admin
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000/login，使用自己配置的账号密码登录。接口文档 http://127.0.0.1:8000/docs。先创建项目和问句，再模拟监测或导入CSV。录入品牌资料后检索、辅助优化、人工审核及导出。

默认连接MySQL。`scripts.configure_mysql`交互读取数据库账号密码，连接成功后保存到本项目忽略提交的`.env`，不修改原GEO配置。建表账号需具有创建独立库和表的权限；应用运行仅需要该库的读写权限。请使用专用数据库账号，不要把公司的连接配置复制进本项目。

`sql/schema.mysql.sql`执行范围仅为独立毕设库`brand_geo_rag_agent`，不是公司主库或国家库。包含9张表：users、projects、questions、batches、answers、documents、chunks、optimizations、reviews。可手动执行SQL，或显式执行`scripts.init_db`；只初始化结构，没有迁移文件、不写业务数据、不覆盖已有表或旧样本。所有表最后两个字段依次为created_at、updated_at，服务启动不会自动建表。SQLite旧数据不会自动迁入MySQL。

管理员创建是独立的业务数据程序`scripts.create_admin`，会创建`admin`账号、`superadmin`角色并以带随机盐的scrypt哈希保存密码。按当前本机演示要求可输入指定的简单密码；此类密码不得用于公网部署。没有在代码中写死默认密码，已有admin时脚本拒绝覆盖。登录会逐次核验数据库中的账号启用状态和角色，超级管理员可操作全部现有工作台功能；不提供账号管理页面或多用户权限隔离。

`.env`自动读取，但已有环境变量优先；切换数据库时需清除终端里旧的`GEO_DB_ENGINE`等设置。`.env.example`只是示例。设置`GEO_DB_ENGINE=sqlite`并显式执行初始化可使用离线后端，管理员创建方式不变。API时间在MySQL驱动边界转换，统一到`YYYY-MM-DD HH:mm:ss`，业务日期为`YYYY-MM-DD`，空日期保留null。

登录使用 HttpOnly、SameSite=Strict Cookie，8小时后失效；退出及服务重启后旧会话失效。写操作校验同源及自定义请求头，同一来源连续5次登录失败会锁定5分钟。单管理员、单服务进程的研究原型，不是生产级多用户权限系统；默认只绑定回环地址，不要暴露到公网。不提供短信、注册或找回密码。HTTPS部署应设置`GEO_SESSION_SECURE=1`；本地HTTP保持0。仅使用一个服务进程，不使用多Worker。

可选`GEO_API_TOKEN`仅供程序化客户端通过`X-API-Key`访问业务API，不在网页输入，也不用于网页登录。API文档不存储该令牌；Cookie登录后可在同源文档中查询，但写操作需提供`X-GEO-Request: 1`，建议使用工作台完成操作。

## 与原GEO项目的目录对齐

- 根目录`main.py`：FastAPI入口和生命周期。
- `app/apis/base.py、project.py、task.py、knowledge_base.py、article_task.py`：按业务拆分中文请求响应模型。
- `app/controllers/*_controller.py`：路由与参数传递。
- `app/services/*_service.py`：业务流程与查询；与原项目相同，不额外引入仓储层。
- `app/auth/auth.py`：密码哈希、登录会话与API令牌校验；`auth_controller.py`提供登录、会话查询、退出接口。
- `app/libs/database.py`：本项目独立连接，不依赖公司hlg_common_import。
- `app/utils/date_utils.py`：统一日期时间。
- `app/templates`：参考原GEO黑白蓝风格的工作台和左右分栏登录页，无外部图片或付费服务依赖；不是公司正式前端。
- `sql、scripts、tests、docs、examples`：独立结构SQL、初始化、测试、实施说明与模拟CSV。

后续真正接入后台任务、定时任务和中间件时分别使用原项目的app/background_tasks、app/jobs、app/middlewares，不复制空框架或公司配置。

## 数据与结论边界

CSV表头：`question,answer,model,source,collected_date`。前四列必填，日期可空且为YYYY-MM-DD；UTF-8，单次最多500条，回答最长20000字符。source只能是mock、historical、real，必须如实填写；系统无法自动认证数据真实性。examples/answers.csv全部是模拟数据。

指标分母为当前筛选下全部回答数，来源和批次可筛选。规则提取采用品牌词典和保守推荐/否定词识别，只有正向推荐的明确编号才有排名，无编号返回null。跨句否定、比较、引述、中文短别名等仍可能误判，正式实验需人工核验。辅助诊断排除模拟回答，不证明公共模型收录或优化效果。

知识检索为中文字符二元组与英文词余弦基线，不是向量语义检索。文章管理中的原固定工作流草稿仍是原文摘录；首页新增的百炼多智能体对话则使用模型路由、知识证据和受控工具生成回复或待审核草稿。聊天回复暂不自动写入文章管理，也不直接导出或发布。审核历史独立保存，未通过不能导出；人工编辑后仍需核查引用一致性。

CSV重导入产生新批次，项目汇总会累计。实验比较用batch_id筛选，避免重复样本混入。后台任务为进程内执行，服务重启会标记未完成批次中断并保留回答，尚不支持自动恢复和重试。

## 测试与后续工作

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

常规测试使用隔离SQLite库，真实MySQL联调默认跳过。需要联调时在本地交互输入admin密码（不写入命令参数或文件）：

```powershell
.\.venv\Scripts\python.exe -c "from getpass import getpass; import os,pytest; os.environ['GEO_TEST_MYSQL']='1'; os.environ['GEO_TEST_ADMIN_PASSWORD']=getpass('请输入管理员密码：'); raise SystemExit(pytest.main(['-q','tests/test_mysql_integration.py']))"
```

联调使用事务回滚全部测试业务样本，不清空表、不覆盖管理员密码。服务启动检查会按现有规则中断未完成批次，请在没有运行中监测任务时执行。当前9张表及MySQL完整业务链路已核验通过。

后续重点：持久任务、真实模型适配器、Dify/等效RAG生成、自主智能体工具调用、人工标注与对照评测。详见docs/implementation.md。尚未产生正式RAG或Agent实验结果，首版规则流程仅作为基线。
