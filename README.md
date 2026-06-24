# CISHEN Windows 助手

这是一个 Windows 桌面辅助工具。当前已完成“挖矿模块”，并预留“副本、召唤、菜园管理”的独立入口；GUI 和命令行都会根据 `config.json` 中的 `active_module` 运行当前选择的模块。

## 版权声明

开发所属工会：太虚殿。

本程序完全免费，仅供学习、研究与个人测试使用。禁止售卖，禁止以任何形式转售、收费分发或用于商业牟利。如果你通过付费方式获得本程序，请立即停止交易并要求退款。

## 安装

```powershell
cd D:\Develop\project\CISHEN
py -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 启动 GUI

```powershell
python -m cishen_clicker.gui
```

GUI 启动后会先进入系统首页，左侧显示功能模块入口，右侧显示版权声明。点击某个模块后会进入该模块自己的页面；模块页提供返回首页、配置保存、开始、暂停、结束和日志区域。公共控制能力一次只会运行一个模块。

## 命令行运行

先只检查当前模块的一次识别/执行结果，不真实点击：

```powershell
python -m cishen_clicker --once --debug
```

确认 debug 图没有明显误判后，再真实运行：

```powershell
python -m cishen_clicker --live
```

## 模块化配置

`config.json` 顶层使用模块结构：

```json
{
  "active_module": "mining",
  "modules": {
    "mining": {},
    "dungeon": {},
    "summon": {},
    "garden": {}
  }
}
```

- `active_module`：当前运行模块。现在可选 `mining`、`dungeon`、`summon` 和 `garden`。
- `modules.mining`：挖矿模块配置。
- `modules.dungeon`：副本模块配置入口，目前是骨架，后续可以继续实现。
- `modules.summon`：召唤模块配置入口，目前是骨架，后续可以继续实现。
- `modules.garden`：菜园管理模块配置入口，目前是骨架，后续可以继续实现。

旧版扁平配置仍可读取；通过 GUI 保存后会自动写成新的模块化结构。

## 挖矿模块参数

挖矿参数位于 `modules.mining`：

- `window_title`：窗口标题关键字，能匹配到游戏窗口即可。
- `mine_area`：矿区相对窗口左上角的矩形坐标。
- `rows` / `cols`：矿区网格行列数。
- `click_hold_seconds`：窗口消息点击时，按下到抬起之间的保持时间；点击无效时可适当调大。
- `click_delay_seconds`：两次点击之间的等待时间；点击过快导致无效时可适当调大。
- `loop_interval_seconds`：每轮循环之间的等待时间。
- `max_targets_per_round`：每轮最多点击的价值矿目标数。
- `max_runtime_minutes`：本次启动后允许运行的最大分钟数，`-1` 表示不限制；暂停期间不计入运行时间。
- `max_pickaxe_clicks`：本次启动后允许消耗的最大镐头数，`-1` 表示不限制；每次点击矿格按 1 个镐头计算。
- `use_drill` / `use_bomb`：是否使用钻头、炸药道具，GUI 中可以勾选。
- `tool_interval_loops`：每隔多少次底部兜底循环尝试使用一次道具。
- `drill_button_ratio` / `bomb_button_ratio`：道具按钮在窗口内的相对位置。
- `thresholds`：识别阈值，误点多就提高 `min_score`，漏点多就降低。

启用两个道具时会交替使用。使用道具后，程序会额外点击当前兜底矿 5 次，用来降低爆炸动画对下一轮价值矿识别的干扰。

## 打包给别人使用

如果要生成带 `CISHEN.exe` 的压缩包，推荐直接运行：

```powershell
.\pack.ps1
```

打包脚本会使用 Python 3.7 和旧 Windows 兼容依赖生成 `CISHEN.zip`。如果别人运行时看到缺少 `api-ms-win-core-path-l1-1-0.dll`，说明之前的包大概率是用 Python 3.11 等较新的环境打出来的，请重新运行 `.\pack.ps1` 生成压缩包。不要从网上单独下载 DLL 放进程序目录。
