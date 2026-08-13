# 参与贡献

感谢你愿意改进 Know Your GPA。这个项目由 Vibe Coding 推动，也欢迎不熟悉代码的使用者通过截图、正确结果和复现步骤参与测试。

## 报告识别问题

请优先使用 GitHub 的 Bug 模板，并提供：

- 截图类型、尺寸和主题；
- 实际识别结果；
- 你确认过的正确结果；
- 是否存在裁剪、压缩、文字或贴纸遮挡；
- 可以复现问题的脱敏图片。

成绩截图属于个人信息。上传前请移除姓名、学号及其他不希望公开的内容。

课程代码、课程名称和成绩组合也可能形成间接身份信息；不能确认安全时，请使用合成数据。

## 本地开发

```powershell
npm ci
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
npm test
```

网页本身不依赖构建步骤。修改 `radar_gpa.html` 后可以直接刷新浏览器检查。

## 目录约定

- 正式网页代码保留在 `radar_gpa.html`；
- 自动化测试放在 `tests/js/` 或 `tests/python/`；
- 真实页面回归放在 `tests/browser/`；
- 脱敏测试图片放在 `tests/fixtures/`；
- 一次性算法探索放在 `experiments/`；
- 外部绘图逻辑参考放在 `references/`；
- 面向使用者的长文档放在 `docs/`。

不要把 `node_modules/`、缓存、导出的 CSV 或诊断图片提交到仓库。

## 提交修改

1. 一个修改尽量只解决一个问题；
2. 先说明错误表现和预期结果；
3. 修改识别算法时补充回归测试；
4. 运行 `npm test`；
5. 在 Pull Request 中说明测试结果和仍然存在的限制。

提交信息应说明修改的原因，例如：`避免遮挡文字被当作成绩折线`。
