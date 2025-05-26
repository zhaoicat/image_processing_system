# 图像处理系统前端

基于 Vue 3 + Vite 构建的图像处理系统前端应用。

## 环境配置

### 1. 环境变量设置

项目支持通过环境变量配置后端服务地址，避免硬编码：

```bash
# 复制环境变量示例文件
cp env.example .env.local

# 编辑 .env.local 文件，设置后端地址
VITE_BACKEND_HOST=http://localhost:8000
```

### 2. 不同环境配置示例

**开发环境：**
```
VITE_BACKEND_HOST=http://localhost:8000
```

**生产环境：**
```
VITE_BACKEND_HOST=https://api.yourdomain.com
```

**Docker环境：**
```
VITE_BACKEND_HOST=http://backend:8000
```

## 开发指南

### 安装依赖
```bash
npm install
```

### 开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 跨域配置

项目已配置开发环境代理和生产环境nginx反向代理，无需担心跨域问题：

- **开发环境**：通过 Vite 代理配置解决跨域
- **生产环境**：通过 nginx 反向代理解决跨域

## 技术栈

- Vue 3 (Composition API)
- Vite
- Element Plus
- Axios
- Vue Router
- Pinia

# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).
