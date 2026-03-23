# 🖥️ DisplayTuner 

![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**LuminaCtrl** 是一款专为 Windows 多屏用户打造的现代化显示器控制中心。它打破了原生系统的限制，不仅支持对外接显示器的硬件亮度进行独立调节，还创新性地加入了**分屏独立护眼模式**。配合极具现代感的无边框暗黑 UI 与系统托盘常驻功能，为你带来沉浸式的屏幕管理体验。

---

## ✨ 核心特性 (Features)

- ☀️ **硬件级亮度控制**：基于 DDC/CI 协议，精准、独立地调节每一块外接显示器的真实物理亮度。
- 🌙 **独立护眼模式 (夜间色温)**：调用 Windows 底层 Gamma API，支持对**特定屏幕**单独开启去蓝光护眼模式，多屏互不干扰（完美解决系统原生夜间模式在扩展屏下失效或强制全局生效的痛点）。
- 🖥️ **一键投影切换**：内嵌 Windows 原生投影控制（仅电脑屏幕 / 复制 / 扩展 / 仅外接屏幕），一键高效切换办公状态。
- 🎨 **现代化纯平 UI**：采用无边框 (Frameless)、全局圆角、高级阴影和线性渐变设计的 Fluent Design 风格暗黑界面，告别传统理工男审美。
- 🛸 **无感托盘常驻**：点击关闭自动隐入系统托盘。支持右键唤出多级快捷菜单，提供 0%-100% 五档预设一键调节，且完美实现托盘与主界面的状态双向同步。


---

## 🛠️ 技术栈 (Tech Stack)

- **核心语言**: Python 3
- **GUI 框架**: PyQt5
- **底层驱动**: `screen_brightness_control` (DDC/CI), `ctypes` (Windows GDI32 API)
- **打包工具**: PyInstaller

---

## 🚀 快速开始 (Getting Started)

### 1. 克隆项目
```bash
git clone [https://github.com/你的用户名/LuminaCtrl.git](https://github.com/你的用户名/LuminaCtrl.git)
cd LuminaCtrl
