# 双模块交付包说明

本交付包包含两个并行功能模块，均为纯前端单页工具，不依赖后端，不保存用户数据，可独立嵌入 Coze 页面。

## 模块一：单店模型诊断器

路径：`/store-diagnostic/index.html`

用途：帮助蛋糕店、面包店、综合烘焙门店老板判断新店选址、投入、收入、成本和回本是否值得继续推进。

交付文件：

- `/store-diagnostic/index.html`
- `/store-diagnostic/README.md`
- `/store-diagnostic/coze-integration-spec.md`
- `/store-diagnostic/schema.json`
- `/store-diagnostic/sample-case.json`

## 模块二：会员运营诊断器

路径：`/member-diagnostic/index.html`

用途：帮助蛋糕店、面包店、综合烘焙门店老板自检会员基础、权益、积分、拉新、触达和活动复盘的健康度。

交付文件：

- `/member-diagnostic/index.html`
- `/member-diagnostic/README.md`
- `/member-diagnostic/coze-integration-spec.md`
- `/member-diagnostic/schema.json`
- `/member-diagnostic/sample-case.json`

## 统一交互约定

- 首页只展示模块标题、价值说明、开始按钮和示例按钮。
- 正式路径进入空白填写清单，用户提交后才展示结果。
- 示例路径直接进入结果页，顶部展示已填输入，下面展示结果输出。
- 结果页提供复制摘要和导出表格能力。

## Coze 集成建议

1. 最快方式：分别用 iframe 嵌入两个页面。
2. 工作流方式：参考各模块的 `schema.json` 配置输入字段，参考 `index.html` 中的计算逻辑实现函数节点。
3. 对话入口方式：Coze 负责选择模块和解释结果，网页模块负责收集、计算和导出。

