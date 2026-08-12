# Brand Tokens

## 色彩

```css
:root {
  --brand-ink: #0c0c0c;
  --brand-ink-raised: #171615;
  --brand-paper: #f4f1ea;
  --brand-paper-raised: #fffdf8;
  --brand-signal: #ff2442;
  --brand-text-on-dark: #f4f1ea;
  --brand-text-muted-dark: rgba(244, 241, 234, 0.66);
  --brand-text-on-light: #171615;
  --brand-text-muted-light: #625e57;
  --brand-line-dark: rgba(244, 241, 234, 0.14);
  --brand-line-light: rgba(23, 22, 21, 0.12);
}
```

信号红只用于主 CTA、关键数字、序号和焦点轮廓。普通正文不得使用低于可读对比度的浅灰。

## 字体

- 英文展示：Arial Black、Arial Narrow 或具有窄宽比例的无衬线展示字体。
- 中文标题：Noto Sans SC / 思源黑体，700–900。
- 中文正文：Noto Sans SC / Microsoft YaHei，400–600。
- 页面最多使用四档字重：400、600、800、900。

## 间距

基础单位 4px。常用间距：8、12、16、24、32、48、72、96px。禁止新增无规律的 18、26、28、30、34px，除非源于流式尺寸计算。

## 圆角

- 标签：999px
- 按钮：12px
- 内容卡片：16px
- 大型媒体容器：20px
- 页面框架：24px

胶囊只用于标签，不用于所有按钮和容器。

## 布局

- 内容最大宽度：1280px
- 正文最佳行宽：34–42 个中文字符
- 桌面区块垂直间距：96px
- 移动区块垂直间距：56px
- 移动首屏目标高度：680–740px

## 组件规则

- 一个区块只允许一个主 CTA。
- 图标与功能必须一致；菜单图标只能打开导航，登录入口使用锁形图标或明确文字。
- 项目卡片必须同时包含角色、问题、动作和结果中的至少三项。
- 标签不超过四个，且不得重复正文标题。

## 无障碍

- 正文对比度至少达到 WCAG AA。
- 交互目标最小 44 × 44px。
- 所有焦点状态使用信号红 3px 外轮廓。
- 减少动态模式保留必要的状态反馈，仅关闭装饰性动画。
