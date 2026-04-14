# portal-front

这是 `portal-front`，也是 `MyPortal` 的 Vue 3 聊天界面，使用 `Vite + TypeScript` 构建。

## 功能

- 创建聊天会话
- 调用 `MyPortal` 后端聊天接口发送消息
- 展示会话历史
- 展示最近 traces
- 展示最近一轮工具调用结果

## 配置

复制 `portal-front/.env.example` 为 `portal-front/.env`，按需修改：

```env
VITE_API_BASE_URL=http://127.0.0.1:8080
```

## 启动

```bash
npm install
npm run dev
```

默认开发地址通常是 [http://127.0.0.1:5173](http://127.0.0.1:5173)。
