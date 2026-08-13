# 测试

- `fixtures/`：脱敏截图和人工确认的数据；
- `browser/`：使用真实 Chromium 解码和操作本地网页；
- `js/`：直接提取网页算法执行图片回归；
- `python/`：计算函数和 OpenCV 工具的单元测试。

完整测试命令：

```powershell
npm test
```

首次运行浏览器测试前，需要安装 Chromium：

```powershell
python -m playwright install chromium
```

修改识别算法时，应至少加入一个能够先失败、修改后通过的回归断言。
