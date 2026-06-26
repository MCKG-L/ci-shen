# 次神：光之觉醒PC端助手

这是一个 Windows 桌面辅助工具。当前已完成“挖矿模块”，并预留“副本、召唤、菜园管理”的独立入口。

## 版权声明

开发所属工会：太虚殿（905662）。

本程序完全免费，仅供学习、研究与个人测试使用。禁止售卖，禁止以任何形式转售、收费分发或用于商业牟利。如果你通过付费方式获得本程序，请立即停止交易并要求退款。

## 下载使用

如果只是使用程序，请在右侧 Releases（发行版）中下载 setup 安装器，例如 `cishen-assistant-setup-1.0.0.exe`，或最新版本的 `cishen-assistant-setup-*.exe`。

安装步骤：

1. 下载 `cishen-assistant-setup-*.exe`。
2. 双击运行安装器，按提示完成安装。安装过程中会显示“选择安装位置”页面，可以保留默认路径，也可以点击“浏览”更改安装目录。
3. 安装完成后，从开始菜单启动“次神助手”。
4. 如果安装时勾选了桌面快捷方式，也可以从桌面启动。

请不要下载 `Source code (zip)` 或 `Source code (tar.gz)`，那是 GitHub 自动生成的源码包，不能直接运行。

### Windows 安全提示说明

由于本程序未购买商业代码签名证书，运行安装器或 `cishen-assistant.exe` 时 Windows 可能会弹出 **"Windows 已保护你的电脑"** 或显示 **"未知发布者"** 警告。这是 Windows SmartScreen 的正常行为，并非程序包含恶意代码。

解决方法：

1. 在弹出的警告窗口中点击 **"更多信息"**
2. 然后点击 **"仍要运行"**

> 本程序完全免费且开源，代码可于 [GitHub 仓库](https://github.com/MCKG-L/ci-shen) 审查。如仍有顾虑，可按下方"本地开发运行"方式从源码直接运行。

## 初次版本说明

这是 `CiShen Assistant` 的初次发布版本。

当前版本仅实现了挖矿模块，其他功能模块仍在预留和开发中。挖矿过程中会尝试识别“发现藏宝图”弹窗，只要检测到就自动点击确定。除藏宝图弹窗外，本版本暂未对游戏内各种特殊弹窗、异常提示、网络波动提示等情况做专门处理，如果运行过程中遇到弹窗遮挡，请先手动处理后再继续使用。

## 本地开发运行

```powershell
cd your\path\to\CISHEN
conda create -n cishen python=3.11 -y
conda activate cishen
python -m pip install -r requirements.txt
```

## 启动 GUI

```powershell
python -m cishen_clicker.gui
```

GUI 启动后会先进入系统首页，左侧显示功能模块入口，右侧显示版权声明和操作方式。点击某个模块后会进入该模块自己的页面；模块页提供返回首页、配置保存、开始、暂停、结束和日志区域。公共控制能力一次只会运行一个模块。

## 命令行运行

命令行会运行 `config.json` 当前选中的 `active_module`。如果要运行挖矿，请确认其值为 `mining`。

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
- `base_window`：矿区坐标对应的基准窗口大小，用于适配不同显示器和 DPI 缩放。
- `mine_area`：矿区相对窗口左上角的矩形坐标。
- `rows` / `cols`：矿区网格行列数。
- `active_start_row`：从第几行开始参与识别。
- `excluded_cells`：排除不参与点击的格子列表。
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

## 打包说明

如果要生成旧版 zip 压缩包，运行：

```powershell
.\pack.ps1
```

如果要生成 Windows setup 安装器，请先安装 Inno Setup 6。脚本会自动查找默认安装目录、PATH 和注册表中的自定义安装位置。然后运行：

```powershell
.\pack-setup.ps1
```

两个打包脚本都会使用 Python 3.7 和旧 Windows 兼容依赖。`pack.ps1` 会生成 `cishen-assistant.zip`，`pack-setup.ps1` 会先通过 PyInstaller 生成 `dist\cishen-assistant`，再调用 Inno Setup 生成 `dist-installer\cishen-assistant-setup-1.0.0.exe`。

如果别人运行安装后的程序时看到缺少 `api-ms-win-core-path-l1-1-0.dll`，说明之前的包大概率是用 Python 3.11 等较新的环境打出来的。请重新按上面的 `.\pack-setup.ps1` 生成安装器，不要从网上单独下载 DLL 放进程序目录。
