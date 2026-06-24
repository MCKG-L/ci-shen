# CISHEN Windows Click Helper

这是第一版授权测试脚本：在 Windows 桌面上定位微信小程序窗口，截取窗口画面，按固定矿区网格识别候选矿物，并点击第一个候选格。

默认是 dry-run，不会点击。只有加 `--live` 才会真实点击。

## 版权声明

开发所属工会：太虚殿。

本程序完全免费，仅供学习、研究与个人测试使用。

禁止售卖，禁止以任何形式转售、收费分发或用于商业牟利。如你通过付费方式获得本程序，请立即停止交易并要求退款。

## 安装

```powershell
cd C:\path\to\CISHEN
py -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 打包给别人使用

如果要生成带 `CISHEN.exe` 的压缩包，推荐直接运行：

```powershell
.\pack.ps1
```

打包脚本会使用 Python 3.7 和旧 Windows 兼容依赖生成 `CISHEN.zip`。如果别人运行时看到缺少 `api-ms-win-core-path-l1-1-0.dll`，说明之前的包大概率是用 Python 3.11 等较新的环境打出来的，请重新运行 `.\pack.ps1` 生成压缩包。不要从网上单独下载 DLL 放进程序目录。

## 调整配置

编辑 `config.json`：

- `window_title`：窗口标题关键字，能匹配到微信小程序窗口即可。
- `mine_area`：矿区相对窗口左上角的矩形坐标。
- `rows` / `cols`：矿区网格行列数。
- `thresholds`：识别阈值，误点多就提高 `min_score`，漏点多就降低。

当前 `mine_area` 是按你发的截图估算的，实际窗口大小不同就需要重新标定。

## 先跑一次识别

```powershell
python -m cishen_clicker --once --debug
```

输出会显示目标格子的行列、分数和屏幕坐标。`debug` 目录会保存带框截图：绿色代表会被点击的候选格，红色代表跳过。

## 开始点击

确认 debug 图没有明显误判后再运行：

```powershell
python -m cishen_clicker --live
```

停止脚本用 `Ctrl+C`。

## 提升识别准确率

第一版不用模板也能跑，但建议把矿物小图放进 `templates/` 目录，例如：

- `red_ore.png`
- `yellow_ore.png`
- `stone.png`

模板越干净，误判越少。模板应只包含矿物主体，别截太多背景。
