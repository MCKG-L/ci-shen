# 模块化助手框架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前单一挖矿助手拆成可切换的模块框架，让 GUI 和启动入口都能按 `active_module` 运行对应功能，并为后续新模块提供统一注册入口。

**Architecture:** 引入 workspace 级配置 `active_module + modules[...]` 和模块注册表。每个模块暴露自己的字段定义、默认配置、运行态工厂与单步执行函数；GUI 通过当前模块的字段集动态生成表单，CLI 根据 `active_module` 选择对应模块运行。现有挖矿逻辑尽量保留，只迁移到矿工模块包装中；自动打副本先作为独立模块骨架接入，后续再补完整流程。

**Tech Stack:** Python 3.11, `tkinter`, `unittest`, existing OpenCV / keyboard / pyautogui dependencies.

---

### Task 1: Workspace Config And Module Registry

**Files:**
- Create: `cishen_clicker/workspace_config.py`
- Create: `cishen_clicker/modules/__init__.py`
- Create: `cishen_clicker/modules/base.py`
- Create: `cishen_clicker/modules/mining.py`
- Create: `cishen_clicker/modules/dungeon.py`
- Test: `tests/test_workspace_config.py`
- Test: `tests/test_module_registry.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_load_workspace_config_migrates_legacy_flat_mining_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "window_title": "game",
                "mine_area": {"x": 1, "y": 2, "width": 3, "height": 4},
                "rows": 7,
                "cols": 6,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cfg = load_workspace_config(path)

    assert cfg.active_module == "mining"
    assert cfg.modules["mining"]["window_title"] == "game"
```

```python
def test_module_registry_exposes_mining_and_dungeon():
    assert list_module_keys() == ["mining", "dungeon"]
    assert get_module_spec("mining").label == "挖矿"
    assert get_module_spec("dungeon").label == "自动打副本"
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:
```powershell
python -m unittest tests.test_workspace_config tests.test_module_registry
```

Expected: fail because the workspace loader and registry do not exist yet.

- [ ] **Step 3: Implement minimal config loading and registry**

```python
@dataclass(frozen=True)
class WorkspaceConfig:
    active_module: str
    modules: dict[str, dict[str, Any]]

def load_workspace_config(path: Path) -> WorkspaceConfig:
    raw = load_raw_config(path)
    if "modules" not in raw:
        return WorkspaceConfig(active_module="mining", modules={"mining": _legacy_mining_module(raw)})
    return WorkspaceConfig(
        active_module=str(raw.get("active_module", "mining")),
        modules={key: value for key, value in raw["modules"].items() if isinstance(value, dict)},
    )
```

```python
@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    fields: tuple[ConfigField, ...]
    create_runtime: Callable[[dict[str, Any], Path], Any]
    run_cycle: Callable[..., list[Any]]
```

- [ ] **Step 4: Re-run the tests**

Run:
```powershell
python -m unittest tests.test_workspace_config tests.test_module_registry
```

Expected: PASS.

---

### Task 2: Mining Module Extraction

**Files:**
- Modify: `cishen_clicker/__main__.py`
- Modify: `cishen_clicker/config.py`
- Modify: `cishen_clicker/tool_usage.py`
- Modify: `cishen_clicker/strategy.py` if runtime state needs a small helper
- Use: `cishen_clicker/modules/mining.py`
- Test: `tests/test_tools.py`
- Test: `tests/test_login_conflict.py`
- Test: `tests/test_click_timing.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_mining_runtime_uses_existing_tool_and_strategy_state():
    runtime = build_mining_runtime(raw_module_config, config_path.parent)
    assert runtime.config.tool_interval_loops == 4
    assert runtime.strategy is not None
    assert runtime.tool_state is not None
```

```python
def test_run_once_dispatches_to_mining_module_when_active_module_is_mining():
    workspace = WorkspaceConfig(active_module="mining", modules={"mining": mining_raw})
    result = run_once(workspace, templates=[], live=False, debug=False, ...)
    assert result == []
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:
```powershell
python -m unittest tests.test_tools tests.test_login_conflict tests.test_click_timing
```

Expected: fail because mining runtime has not been separated from the CLI entrypoint.

- [ ] **Step 3: Move the existing mining loop into the mining module**

```python
@dataclass
class MiningRuntime:
    config: MiningConfig
    strategy: MiningStrategy
    tool_state: ToolUsageState

def build_runtime(raw_module: dict[str, Any], config_dir: Path) -> MiningRuntime:
    config = load_mining_config(raw_module, config_dir)
    return MiningRuntime(
        config=config,
        strategy=MiningStrategy(),
        tool_state=ToolUsageState(interval_loops=config.tool_interval_loops),
    )
```

```python
def run_cycle(runtime: MiningRuntime, templates: list, live: bool, debug: bool, control, logger=print):
    # current mining run_once logic, including tool clicks and debug screenshots
    ...
```

- [ ] **Step 4: Re-run the mining tests**

Run:
```powershell
python -m unittest tests.test_tools tests.test_login_conflict tests.test_click_timing
```

Expected: PASS.

---

### Task 3: Dynamic GUI Module Selector

**Files:**
- Modify: `cishen_clicker/gui.py`
- Modify: `cishen_clicker/gui_config.py`
- Test: `tests/test_gui_config.py`
- Test: `tests/test_gui_window.py`
- Test: `tests/test_gui_start.py`

- [ ] **Step 1: Write the failing GUI tests**

```python
def test_gui_shows_module_selector_and_selected_module_fields():
    gui = MiningGui(root)
    assert gui.module_var.get() == "mining"
    assert "dungeon" in gui.module_options
    assert list(gui.field_vars.keys()) == [field.key for field in mining_fields]
```

```python
def test_gui_save_preserves_inactive_module_data():
    # save mining values, switch to dungeon, save again, and ensure mining config is still present
    ...
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:
```powershell
python -m unittest tests.test_gui_config tests.test_gui_window tests.test_gui_start
```

Expected: fail because the GUI still renders one flat parameter list.

- [ ] **Step 3: Rebuild the GUI around the selected module**

```python
self.module_var = tk.StringVar(value=workspace.active_module)
self.module_menu = ttk.Combobox(..., values=[spec.key for spec in MODULE_SPECS], state="readonly")

def _render_module_fields(self, module_spec):
    # destroy previous field widgets, rebuild using module_spec.fields
```

```python
values = extract_gui_values(module_raw, module_spec.fields)
updated_module_raw = apply_gui_values(module_raw, values, module_spec.fields)
```

- [ ] **Step 4: Re-run the GUI tests**

Run:
```powershell
python -m unittest tests.test_gui_config tests.test_gui_window tests.test_gui_start
```

Expected: PASS.

---

### Task 4: CLI Dispatch And Config Migration

**Files:**
- Modify: `cishen_clicker/__main__.py`
- Modify: `config.json`
- Modify: `README.md`
- Test: `tests/test_module_dispatch.py`
- Update: `tests/test_packaging.py` only if packaging text changes

- [ ] **Step 1: Write the failing dispatch test**

```python
def test_main_dispatches_to_active_module_runner(monkeypatch):
    workspace = WorkspaceConfig(active_module="dungeon", modules={"dungeon": dungeon_raw})
    monkeypatch.setattr("cishen_clicker.__main__.load_workspace_config", lambda path: workspace)
    monkeypatch.setattr("cishen_clicker.__main__.get_module_spec", fake_spec)
    assert main() == 0
```

- [ ] **Step 2: Run the dispatch test and confirm it fails**

Run:
```powershell
python -m unittest tests.test_module_dispatch
```

Expected: fail because `__main__.py` still assumes the mining module directly.

- [ ] **Step 3: Route the CLI through the module registry**

```python
workspace = load_workspace_config(Path(args.config))
module_spec = get_module_spec(workspace.active_module)
runtime = module_spec.create_runtime(workspace.modules[workspace.active_module], Path(args.config).parent)
```

- [ ] **Step 4: Update the sample config and docs**

```json
{
  "active_module": "mining",
  "modules": {
    "mining": { "...": "..." },
    "dungeon": { "...": "..." }
  }
}
```

- [ ] **Step 5: Run the full test suite**

Run:
```powershell
python -m unittest discover -s tests
python -m py_compile cishen_clicker\\__main__.py cishen_clicker\\gui.py cishen_clicker\\workspace_config.py
```

Expected: PASS.

---

### Task 5: Packaging And README Polish

**Files:**
- Modify: `pack.ps1` only if the new config shape needs packaging changes
- Modify: `README.md`
- Modify: `NOTICE.txt` only if the module list needs a note

- [ ] **Step 1: Verify packaging still includes the new config and module files**
- [ ] **Step 2: Update README run instructions for module selection**
- [ ] **Step 3: Confirm packaged zip still omits generated artifacts and passes the existing packaging tests**

