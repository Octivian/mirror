# 烘焙门店诊断模块包

这不是本地 `file://` 交付，而是一个可部署的静态模块包。把整个目录上传到任意静态服务后，同事即可拿到可访问 URL，用于 Coze 页面嵌入或前端集成。

## 包内模块

- `modules/store-diagnostic/index.html`：单店模型诊断器
- `modules/member-diagnostic/index.html`：会员运营诊断器
- `index.html`：模块选择入口页
- `integration-manifest.json`：模块清单和推荐嵌入路径

## 推荐部署方式

任选一种：

- 放到团队现有官网或后台静态目录。
- 上传到对象存储/CDN，例如阿里云 OSS、腾讯云 COS、七牛云。
- 部署到 Vercel、Netlify、GitHub Pages。
- 如果 Coze 支持网页组件或 iframe，直接嵌入部署后的模块 URL。

## 部署后的 URL 示例

假设同事把整个目录部署到：

`https://your-domain.com/bakery-diagnostic/`

则两个模块地址为：

- `https://your-domain.com/bakery-diagnostic/modules/store-diagnostic/index.html`
- `https://your-domain.com/bakery-diagnostic/modules/member-diagnostic/index.html`

Coze iframe 示例：

```html
<iframe
  src="https://your-domain.com/bakery-diagnostic/modules/store-diagnostic/index.html"
  title="单店模型诊断器"
  style="width:100%;height:900px;border:0;"
></iframe>
```

```html
<iframe
  src="https://your-domain.com/bakery-diagnostic/modules/member-diagnostic/index.html"
  title="会员运营诊断器"
  style="width:100%;height:900px;border:0;"
></iframe>
```

## 集成注意

- 两个模块都是纯前端页面，不需要接口。
- 正式填写路径默认空白，不会带示例数据。
- 示例路径会先展示已填示例输入，再展示结果输出。
- 如果 iframe 高度不够，建议移动端改为新页面打开。

