# 工单查询页面 UI 设计规范

---

## 一、需求概述

基于 PRD 文档，设计工单查询页面，为管理员提供多条件查询、分页浏览和详情查看功能。

### 功能定位
- **用户角色**：管理员
- **使用频率**：低频（偶尔查看）
- **核心功能**：工单列表查询、详情弹窗展示

---

## 二、设计风格

### 2.1 色彩方案

| 颜色类型 | 色值 | 用途 |
|----------|------|------|
| 主色调 | #1890ff | 按钮、链接、强调元素 |
| 成功色 | #52c41a | 成功状态、操作成功提示 |
| 警告色 | #faad14 | 警告状态、提示信息 |
| 错误色 | #f5222d | 错误状态、危险操作 |
| 中性色-50 | #fafafa | 页面背景 |
| 中性色-100 | #f5f5f5 | 卡片背景 |
| 中性色-200 | #e8e8e8 | 边框颜色 |
| 中性色-600 | #595959 | 次要文字 |
| 中性色-800 | #333333 | 主要文字 |

### 2.2 字体规范

| 类型 | 字体 | 大小 | 行高 | 字重 |
|------|------|------|------|------|
| 标题1 | Inter | 20px | 1.5 | 600 |
| 标题2 | Inter | 16px | 1.5 | 500 |
| 正文 | Inter | 14px | 1.6 | 400 |
| 小字 | Inter | 12px | 1.5 | 400 |

### 2.3 间距规范

| 类型 | 间距 | 用途 |
|------|------|------|
| 页面边距 | 24px | 页面内容与边缘距离 |
| 卡片间距 | 16px | 卡片之间距离 |
| 组件间距 | 8px | 组件内部元素间距 |
| 按钮间距 | 8px | 按钮之间距离 |

---

## 三、页面布局

### 3.1 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│  顶部导航栏 (64px)                                          │
│  ┌──────────────┐    ┌───────────────────────┐             │
│  │ Logo/标题    │    │           │ 用户信息  │             │
│  └──────────────┘    └───────────┴───────────┘             │
├─────────────────────────────────────────────────────────────┤
│  侧边栏 (200px)                                              │
│  ┌─────────────────────────────────────┐                    │
│  │ 菜单项                              │                    │
│  │  ├─ 首页                           │                    │
│  │  ├─ 工单管理 ✓                      │                    │
│  │  └─ 系统设置                        │                    │
│  └─────────────────────────────────────┘                    │
├─────────────────────────────────────────────────────────────┤
│  主内容区                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 工单查询                                           │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ 查询条件面板                                        │    │
│  │ 搜索框 + 筛选器 + 日期选择器                        │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ 数据表格                                           │    │
│  │ 工单列表（支持分页）                                │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ 分页器                                             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 响应式适配

| 屏幕尺寸 | 布局调整 |
|----------|----------|
| < 768px | 侧边栏折叠为抽屉菜单 |
| 768-1200px | 保持三栏布局 |
| > 1200px | 加宽主内容区至 1200px |

---

## 四、组件设计

### 4.1 搜索框组件

**样式规范：**
- 边框：1px solid #e8e8e8
- 聚焦边框：1px solid #1890ff
- 圆角：4px
- 高度：36px
- 内边距：0 12px
- 占位符颜色：#bfbfbf

**状态规范：**
| 状态 | 边框色 | 背景色 |
|------|--------|--------|
| 默认 | #e8e8e8 | #fff |
| 聚焦 | #1890ff | #fff |
| 错误 | #f5222d | #fff2f0 |

### 4.2 按钮组件

**样式规范：**

| 类型 | 背景色 | 文字色 | 边框 | 圆角 | 高度 |
|------|--------|--------|------|------|------|
| 主按钮 | #1890ff | #fff | none | 4px | 36px |
| 次按钮 | #fff | #595959 | 1px solid #d9d9d9 | 4px | 36px |
| 危险按钮 | #f5222d | #fff | none | 4px | 36px |

**状态规范：**

| 状态 | 主按钮 | 次按钮 |
|------|--------|--------|
| 默认 | #1890ff | #fff |
| 悬停 | #40a9ff | #fafafa |
| 点击 | #096dd9 | #f5f5f5 |
| 禁用 | #d9d9d9 | #f5f5f5 |

### 4.3 日期选择器组件

**样式规范：**
- 输入框样式同搜索框
- 弹出日历面板：白色背景，阴影效果
- 选中日期：蓝色背景，白色文字
- 今日高亮：蓝色边框

### 4.4 数据表格组件

**样式规范：**
- 表头背景：#fafafa
- 表头文字：#595959，14px，500 字重
- 表格边框：1px solid #e8e8e8
- 单元格内边距：12px 16px
- 行悬停背景：#fafafa
- 斑马纹：偶数行背景 #fafafa

### 4.5 分页器组件

**样式规范：**
- 当前页码：蓝色背景，白色文字
- 其他页码：白色背景，灰色文字
- 禁用状态：灰色，不可点击
- 按钮尺寸：32px x 32px
- 圆角：4px

### 4.6 详情弹窗组件

**样式规范：**
- 遮罩层：rgba(0, 0, 0, 0.5)
- 弹窗背景：#fff
- 圆角：8px
- 阴影：0 4px 12px rgba(0, 0, 0, 0.15)
- 宽度：520px（最大）

---

## 五、交互设计

### 5.1 页面加载

- 初始加载：显示骨架屏
- 数据加载：显示加载动画（居中旋转图标）
- 加载失败：显示错误提示和重试按钮

### 5.2 搜索交互

- 输入搜索条件后，点击搜索按钮或按 Enter 键触发搜索
- 搜索按钮点击后显示加载状态
- 搜索结果为空时显示"暂无数据"提示

### 5.3 表格交互

- 鼠标悬停在表格行上显示手型指针
- 点击表格行打开详情弹窗
- 支持点击表头排序（升序/降序切换）

### 5.4 弹窗交互

- 弹窗出现：淡入动画（0.2s），遮罩层渐显
- 弹窗关闭：淡出动画（0.2s），点击遮罩层或关闭按钮可关闭
- 操作按钮：确认按钮高亮，取消按钮次要

### 5.5 分页交互

- 点击页码跳转到对应页
- 点击上一页/下一页切换
- 显示当前页码和总页数

---

## 六、切图标注

### 6.1 图标规范

| 类型 | 尺寸 | 格式 | 颜色 |
|------|------|------|------|
| 搜索图标 | 16px | SVG | #8c8c8c |
| 日历图标 | 16px | SVG | #8c8c8c |
| 关闭图标 | 16px | SVG | #8c8c8c |
| 箭头图标 | 12px | SVG | #8c8c8c |

### 6.2 图片规范

- 图片格式：WebP（优先）、PNG
- 图片压缩：确保加载性能
- 响应式图片：根据屏幕尺寸提供不同分辨率

---

## 七、前端代码输出

### 7.1 Tailwind CSS 示例

```html
<!-- 查询条件区域 -->
<div class="bg-white rounded-lg shadow-sm p-4 mb-4">
  <div class="flex flex-wrap gap-4">
    <!-- 工单编号输入 -->
    <div class="flex items-center gap-2">
      <label class="text-sm text-gray-600">工单编号</label>
      <input 
        type="text" 
        class="w-48 px-3 py-2 border border-gray-200 rounded-md focus:border-blue-500 focus:outline-none"
        placeholder="请输入工单编号"
      />
    </div>
    
    <!-- 创建人输入 -->
    <div class="flex items-center gap-2">
      <label class="text-sm text-gray-600">创建人</label>
      <input 
        type="text" 
        class="w-48 px-3 py-2 border border-gray-200 rounded-md focus:border-blue-500 focus:outline-none"
        placeholder="请输入创建人姓名"
      />
    </div>
    
    <!-- 日期范围选择 -->
    <div class="flex items-center gap-2">
      <label class="text-sm text-gray-600">创建时间</label>
      <input 
        type="date" 
        class="px-3 py-2 border border-gray-200 rounded-md focus:border-blue-500 focus:outline-none"
      />
      <span class="text-gray-400">至</span>
      <input 
        type="date" 
        class="px-3 py-2 border border-gray-200 rounded-md focus:border-blue-500 focus:outline-none"
      />
    </div>
    
    <!-- 操作按钮 -->
    <div class="flex items-center gap-2 ml-auto">
      <button class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
        查询
      </button>
      <button class="px-4 py-2 border border-gray-300 text-gray-600 rounded-md hover:bg-gray-50 transition-colors">
        重置
      </button>
    </div>
  </div>
</div>

<!-- 数据表格 -->
<div class="bg-white rounded-lg shadow-sm overflow-hidden">
  <table class="w-full">
    <thead class="bg-gray-50">
      <tr>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">工单编号</th>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">标题</th>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">状态</th>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">创建人</th>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">创建时间</th>
        <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">更新时间</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-200">
      <tr class="hover:bg-gray-50 cursor-pointer">
        <td class="px-4 py-3 text-sm text-gray-800">W001</td>
        <td class="px-4 py-3 text-sm text-gray-800">服务器异常问题</td>
        <td class="px-4 py-3">
          <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">处理中</span>
        </td>
        <td class="px-4 py-3 text-sm text-gray-600">张*丰</td>
        <td class="px-4 py-3 text-sm text-gray-600">2025-06-10 10:00:00</td>
        <td class="px-4 py-3 text-sm text-gray-600">2025-06-10 14:30:00</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- 分页器 -->
<div class="flex items-center justify-between mt-4">
  <span class="text-sm text-gray-600">共 45 条，第 1/3 页</span>
  <div class="flex items-center gap-1">
    <button class="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50" disabled>上一页</button>
    <button class="px-3 py-1 text-sm bg-blue-500 text-white rounded">1</button>
    <button class="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">2</button>
    <button class="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">3</button>
    <button class="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">下一页</button>
  </div>
</div>

<!-- 详情弹窗 -->
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
  <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
    <div class="flex items-center justify-between px-4 py-3 border-b">
      <h3 class="text-lg font-medium text-gray-800">工单详情</h3>
      <button class="text-gray-400 hover:text-gray-600">&times;</button>
    </div>
    <div class="p-4 space-y-3">
      <div class="flex justify-between">
        <span class="text-gray-600">工单编号</span>
        <span class="text-gray-800 font-medium">W001</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-600">标题</span>
        <span class="text-gray-800">服务器异常问题</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-600">状态</span>
        <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">处理中</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-600">创建人</span>
        <span class="text-gray-800">张三</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-600">创建时间</span>
        <span class="text-gray-800">2025-06-10 10:00:00</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-600">更新时间</span>
        <span class="text-gray-800">2025-06-10 14:30:00</span>
      </div>
      <div class="pt-2 border-t">
        <span class="text-gray-600">描述</span>
        <p class="mt-1 text-gray-800 text-sm">服务器在运行过程中出现异常，需要及时排查处理。</p>
      </div>
    </div>
    <div class="flex justify-end gap-2 px-4 py-3 border-t">
      <button class="px-4 py-2 border border-gray-300 text-gray-600 rounded-md hover:bg-gray-50">关闭</button>
    </div>
  </div>
</div>
```

---

## 八、相关文档

| 文档类型 | 路径 |
|----------|------|
| PRD 文档 | `docs/prd/workorder/20250610_query_workorder_v1.md` |
| 全局技术规范 | `docs/specs/全局技术规范.md` |

---

**版本**: v1.0  
**日期**: 2025-06-11  
**作者**: UI/UX Pro Max
