# Nekoe 插件市场

这是 [Nekoe](https://github.com/Mario9800/nekoe) 的插件注册表。

机器人管理界面里的「**插件 → 市场**」会拉这个仓库的 [`index.json`](./index.json)，
显示有哪些插件可以装。点一下就能装。

---

## 怎么装插件

在 Nekoe 管理界面：**插件 → 市场 → 找到想要的 → 安装**

也可以**直接贴一个 GitHub 仓库地址**装，不用等收录进市场。

---

## 怎么发布自己的插件

### 1. 写插件

新建一个 GitHub 仓库，里面至少两个文件：

**`metadata.json`**
```json
{
  "name": "my_plugin",
  "display_name": "我的插件",
  "version": "1.0.0",
  "author": "你的名字",
  "description": "一句话说明它干什么",
  "entry": "main.py",
  "tags": ["工具"],
  "defaults": {
    "my_setting": "默认值"
  }
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 插件标识，只能用字母数字 `_ - .`，48 字以内，**别跟别人重名** |
| `display_name` | | 界面上显示的名字 |
| `version` | | 版本号，`1.2.3` 这种。**升级时要改大**，否则不会提示更新 |
| `author` | | 作者 |
| `description` | | 一句话说明 |
| `entry` | | 入口文件，默认 `main.py` |
| `tags` | | 标签数组 |
| `defaults` | | 配置项默认值，`ctx.cfg()` 读不到时会用这里 |

**`main.py`**
```python
def setup(ctx):
    """插件入口。加载时调用一次。"""

    @ctx.command("命令词", "说明")
    async def handler(event, cmd):
        await ctx.send_group(event.group_id, "回一句")
        return True          # True = 已处理，不再走内置逻辑

    ctx.register_config("我的插件", [
        ["my_setting", "设置项", "text"],
    ])
```

**关键：插件只依赖 `setup(ctx)` 这个约定**，不需要 import 主程序任何东西。
这样打包成 exe 之后也能正常加载。

### 2. `ctx` 能干什么

| 能力 | 用法 |
|---|---|
| 注册命令 | `@ctx.command("关键词", "说明")` → 被 @ 且内容匹配时触发 |
| 消息钩子 | `@ctx.on_message()` → 每条消息都过一遍，返回 True 吞掉 |
| 声明配置 | `ctx.register_config(标题, [[键, 标签, 类型], ...])` |
| 声明管理页 | `ctx.register_page("id", "标题", html)` |
| 声明接口 | `ctx.register_api("/admin/api/xxx", handler)` |
| 读配置 | `ctx.cfg("键", 默认值)` |
| 写配置 | `ctx.set_cfg("键", 值)` |
| 发群消息 | `await ctx.send_group(gid, 文本)` |
| 发私聊 | `await ctx.send_private(uid, 文本)` |
| 查活跃成员 | `ctx.act_recent(gid, days=7)` → `[{user_id, nickname, count}, ...]` |
| 群名 | `await ctx.group_name(gid)` |
| 数据库 | `ctx.db()` → sqlite3 连接（自己的表自己建，加插件名前缀） |
| 键值存储 | `ctx.kv_get(键)` / `ctx.kv_set(键, 值)` |
| 打日志 | `ctx.log("...")` / `ctx.warn("...")` |
| 当前 bot | `ctx.self_id()` |

配置项的 `类型` 跟主程序一样：`bool` / `number` / `text` / `backend`。

### 3. 本地测试

把插件文件夹丢进 Nekoe 的 `data/plugins/` 下，
在管理界面「插件」页点「重新加载」就能看到效果，**不用重启程序**。

### 4. 提交收录

改本仓库的 [`index.json`](./index.json)，在 `plugins` 数组里加一项：

```json
{
  "name": "my_plugin",
  "display_name": "我的插件",
  "version": "1.0.0",
  "author": "你的名字",
  "description": "一句话说明",
  "repo": "https://github.com/你/my-plugin",
  "tags": ["工具"]
}
```

然后提 PR。合并之后所有 Nekoe 用户就都能在市场里看到它了。

> 如果你的插件跟别的插件放在同一个仓库里，用 `path` 指明子目录：
> ```json
> "repo": "https://github.com/你/插件合集",
> "path": "plugins/my_plugin"
> ```

---

## 收录标准

不复杂，就几条：

- 能装上、能跑起来（`metadata.json` 合法、入口存在）
- **别干坏事** —— 偷 API Key、往外发用户数据、当后门的一律不收
- `description` 写清楚干什么，别只写「一个插件」
- 别跟已有插件重名

收录了也不代表我给它背书 —— **装第三方插件等于让陌生人的代码在你电脑上跑，自己想清楚**。

---

## 目录结构

```
index.json          插件清单（市场读这个）
plugins/            官方示例插件源码
  hello/            打招呼示例
template/           新插件骨架，复制就能用
```

---

## 许可

跟主程序一样，GPL-3.0。
