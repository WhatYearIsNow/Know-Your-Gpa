# Know Your GPA

一个在浏览器本地运行的微北洋 GPA 雷达图识别工具。导入截图后，它会尝试还原课程数量、成绩和学分，并计算加权成绩、平均 GPA 与总学分。

如果你不熟悉代码，想先了解项目背景和 Vibe Coding 开发过程，请阅读 [项目介绍](docs/PROJECT_OVERVIEW.md)。

> [!IMPORTANT]
> 本项目不是学校官方工具。识别结果仅供整理和参考，正式成绩请以学校系统为准。

## 功能

- 选择、拖入或粘贴 GPA 截图；
- 自动识别课程轴、成绩折线和学分扇形；
- 计算加权成绩、平均 GPA 和总学分；
- 手动调整成绩点、学分点、圆心与外圆；
- 直接编辑课程名称、成绩、学分和课程数量；
- 复制汇总或导出 CSV；
- 对裁剪、涂鸦等低可信截图给出核对提示；
- 图片仅在本机处理，不会上传。

## 快速开始

Windows 下双击 `雷达图GPA.bat`，也可以直接用浏览器打开 `radar_gpa.html`。

打开页面后，拖入、选择或按 `Ctrl + V` 粘贴截图。识别顺序从雷达图正右方开始，按顺时针排列。

普通使用不需要安装 Node.js 或 Python。

## 开发与测试

Node.js 和 Python 依赖仅用于测试及旧版诊断工具。

```powershell
npm ci
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
npm test
```

也可以分别运行：

```powershell
npm run test:js
npm run test:browser
python -m pytest
```

运行旧版 OpenCV 诊断工具：

```powershell
python radar_auto_detect.py "tests\fixtures\synthetic-16axes.jpg" "tests\fixtures\synthetic-16axes.txt"
```

## 仓库结构

```text
.
├─ .github/               GitHub Actions、Issue 与 PR 模板
├─ docs/                  面向读者的项目文档
├─ experiments/           早期视觉算法实验，不参与正式测试
├─ references/            微北洋雷达图绘制参考源码
├─ tests/
│  ├─ fixtures/           回归测试截图和对应数据
│  ├─ browser/            真实 Chromium 页面回归
│  ├─ js/                 浏览器算法的 JavaScript 回归测试
│  └─ python/             Python 单元测试
├─ radar_gpa.html         主程序，离线网页与识别算法
├─ 雷达图GPA.bat          Windows 启动入口
├─ radar_gpa.py           早期手动标点工具和计算函数
├─ radar_gpa_gui.py       早期图形界面工具
└─ radar_auto_detect.py   OpenCV 诊断工具
```

各目录的具体用途可查看目录内的 README。

## 参与改进

提交问题或修改前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全和隐私问题请参考 [SECURITY.md](SECURITY.md)。新增识别规则时，应同时加入能够复现问题的脱敏截图和回归断言，避免只修好一张图片却影响其他样本。

## 隐私与局限

- 截图可能包含个人成绩，公开提交测试图片前请先脱敏；
- 当前回归素材仍包含真实课程名称、课程代码和成绩，公开仓库前应由项目所有者再次确认；
- 项目针对微北洋 GPA 雷达图设计，不是通用成绩单 OCR；
- 不同主题、压缩方式和大面积遮挡可能影响识别；
- 低置信度结果应结合页面标记进行人工核对。

## 许可证

仓库目前尚未选择开源许可证。在许可证明确前，默认保留全部权利；如果准备向公众开放修改和再分发，建议由项目所有者单独选择合适的许可证。
