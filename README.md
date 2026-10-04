# Nekoe 插件市场

这是 [Nekoe](https://github.com/Mario9800/nekoe) 的插件注册表。

机器人管理界面里的「**插件 → 插件市场**」会拉这个仓库的 [`index.json`](./index.json)，
显示有哪些插件可以装，点一下就能装。

> **自己写的插件也可以不收录**，直接在「已安装」页底部贴 GitHub 仓库地址就能装。

---

## 目录

- [装插件](#装插件)
- [5 分钟写一个插件](#5-分钟写一个插件)
- [`metadata.json` 字段](#metadatajson-字段)
- [`ctx` 能力全表](#ctx-能力全表)
- [完整例子](#完整例子)
- [本地测试](#本地测试)
- [提交收录](#提交收录)
- [容易踩的坑](#容易踩的坑)

---

## 装插件

管理界面 **插件 → 插件市场 → 找到想要的 → 安装**。

装好之后去「**已安装**」标签管理它：**停用 / 启用**、**配置**、**卸载**。

市场里只有「安装」和「更新」，管理都在「已安装」页。

---

## 5 分钟写一个插件

一个插件就是一个文件夹，最少两个文件：

```
my_plugin/
├── metadata.json    插件信息
└── main.py          入口，里面的 setup(ctx) 会在加载时调用一次
```

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

**`main.py`**

```python
def setup(ctx):
    """插件入口。核心就绪后调用一次。"""

    @ctx.command("你好", "打个招呼")
    async def hello(event, cmd):
        # event 是 OneBot 事件，event.group_id / event.user_id 最常用
        await ctx.send_group(event.group_id, "你也好呀")
        return True          # True = 已处理，不再走内置命令逻辑

    ctx.register_config("我的插件", [
        ["my_setting", "设置项", "text"],
    ])
```

**关键约定：插件只跟 `setup(ctx)` 打交道，不要 `import` 主程序。**

主程序打包成 exe 之后模块名会变，`import bot` 这类写法必然失效。
你需要的所有东西都在 `ctx` 上。

---

## `metadata.json` 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 插件标识。只能用字母数字 `_ - .`，**别跟别人重名**（它是唯一键） |
| `display_name` | | 界面上显示的名字，不填就用 `name` |
| `version` | | `1.2.3` 这种。**升级时一定要改大**，否则不会提示更新 |
| `author` | | 作者 |
| `description` | | 一句话说明 |
| `entry` | | 入口文件，默认 `main.py` |
| `tags` | | 标签数组，会显示成小徽章 |
| `defaults` | | 配置项默认值。`ctx.cfg()` 读不到时会用这里 |

---

## `ctx` 能力全表

### 注册东西

| 能力 | 用法 |
|---|---|
| 群命令 | `@ctx.command("关键词", "说明")` → `handler(event, cmd)`，返回 `True` 表示已处理 |
| 消息钩子 | `@ctx.on_message()` → `handler(event, text)`，每条消息都过一遍，返回 `True` 吞掉 |
| 配置项 | `ctx.register_config("分组标题", [[键, 标签, 类型], ...])` |
| 管理页 | `ctx.register_page("id", "标题", html)` |
| 管理接口 | `ctx.register_api("/admin/api/plugins/xx/yy", handler, methods=("GET",))` |

命令是**精确匹配**被 @ 后的原文。想要多个别名（比如「签到」和「打卡」），
就多注册几个，指向同一个处理函数：

```python
for kw in ("签到", "打卡"):
    ctx.command(kw, "每日签到")(same_handler)
```

### 收发消息

| 能力 | 用法 |
|---|---|
| 发群 | `await ctx.send_group(gid, "文本")` |
| 发私聊 | `await ctx.send_private(uid, "文本")` |
| @某人 | `ctx.mention(uid)` —— 放进列表里 |
| 发图片 | `ctx.image(url)` —— 放进列表里 |

`send_group` / `send_private` 的第二个参数可以是字符串，也可以是列表，
把文字和 `mention` / `image` 片段混着放：

```python
await ctx.send_group(gid, [
    ctx.mention(uid), " 恭喜中奖！\n",
    ctx.image("https://example.com/a.jpg"),
])
```

### 读写数据

| 能力 | 用法 |
|---|---|
| 执行写语句 | `ctx.db_exec(sql, params)` → 影响行数 |
| 查询 | `ctx.db_query(sql, params)` → `[{列: 值}, ...]` |
| 键值存储 | `ctx.kv_get(键, 默认值)` / `ctx.kv_set(键, 值)` |
| 活跃成员 | `ctx.act_recent(gid, days=7)` |
| 日发言榜 | `ctx.daily_rank(gid, "2026-10-04", limit=10)` |
| 日汇总 | `ctx.daily_summary(gid, "2026-10-04")` → `{"users": n, "total": n}` |

**自己的表自己建**，建表语句放在 `setup()` 开头就行。表名请加插件名前缀，
避免跟别人的插件（或主程序）撞车：

```python
ctx.db_exec("""CREATE TABLE IF NOT EXISTS myplugin_hits(
    user_id INTEGER, group_id INTEGER, n INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, group_id))""")
```

`act_recent` 返回的字段是
`{user_id, group_id, last_active, msg_count, nickname}`（注意是 `msg_count`）。
`daily_rank` 返回 `{user_id, nickname, msg_count}`。

### 积分（签到插件提供的数据）

`points` 表是主程序的数据层，签到/抽奖/老婆这些插件共用。你可以直接用：

| 能力 | 用法 |
|---|---|
| 签到 | `ctx.sign_do(uid, gid, nick, base, bonus_per, bonus_cap, today)` |
| 查积分 | `ctx.sign_get(uid, gid)` → `{points, sign_count, streak, ...}` 或 `None` |
| 积分榜 | `ctx.sign_rank(gid, limit=10)` |
| 扣积分 | `ctx.points_spend(uid, gid, amount)` → `(成功?, 剩余)` |
| 退积分 | `ctx.points_refund(uid, gid, amount)` |

**扣分要成对用**：先扣，失败/异常时退。参考 `wife` 插件的写法。

### 网络 / AI / 其它

| 能力 | 用法 |
|---|---|
| GET 请求 | `await ctx.http_get(url, params={...}, timeout=15)` |
| AI 生成 | `await ctx.ai("提示词", timeout=15)` → 字符串，失败返回 `""`（不抛异常） |
| 群名 | `await ctx.group_name(gid)` |
| 机器人 QQ | `ctx.self_id()` |
| 打日志 | `ctx.log("...")`（青色）/ `ctx.warn("...")`（黄色） |

**网络请求请用 `ctx.http_get`，别自己 `import httpx`。**
主程序的共享客户端对本机地址（localhost / 127.0.0.1）强制直连 ——
系统代理开着的时候，自己建的客户端会把连本机服务的请求也发给代理，直接 502。

---

## 完整例子

一个「关键词自动回复 + 命中统计」插件，演示了大部分能力。

**`metadata.json`**

```json
{
  "name": "autoreply",
  "display_name": "关键词回复",
  "version": "1.0.0",
  "author": "你的名字",
  "description": "关键词自动回复，带命中统计。",
  "tags": ["工具", "群管"],
  "defaults": {
    "ar_enabled": true,
    "ar_pairs": "帮助=发送「帮助」看用法\n群规=请先看群公告",
    "ar_cooldown": 5
  }
}
```

**`main.py`**

```python
import time

TABLE = "autoreply_hits"
PAIR_SEP = "="


def setup(ctx):
    # 自己的表自己建
    ctx.db_exec(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
        user_id INTEGER, group_id INTEGER, n INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, group_id))""")

    _last = {}

    def _bool(key, d):
        v = ctx.cfg(key, d)
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes", "on", "开启")

    def _int(key, d):
        try:
            return int(float(ctx.cfg(key, d)))
        except Exception:
            return d

    def pairs():
        """把配置里的 "关键词=回复" 多行文本解析成字典。"""
        out = {}
        raw = str(ctx.cfg("ar_pairs", "") or "")
        for line in raw.splitlines():
            line = line.strip()
            if not line or PAIR_SEP not in line:
                continue
            k, v = line.split(PAIR_SEP, 1)
            k, v = k.strip(), v.strip()
            if k and v:
                out[k] = v
        return out

    @ctx.on_message()
    async def on_msg(event, text):
        if not _bool("ar_enabled", True):
            return False
        if not getattr(event, "group_id", None):
            return False          # 只管群消息
        text = (text or "").strip()
        if not text or text in ("", " "):
            return False

        rules = pairs()
        hit = None
        for k in rules:
            if text == k:
                hit = k
                break
        if hit is None:
            return False

        # 冷却按 (群, 关键词) 各算各的 —— 按整群算的话，
        # 同一群里连发两个不同关键词，第二个会被误吞。
        cd = _int("ar_cooldown", 5)
        gid = int(event.group_id)
        now = time.time()
        ck = (gid, hit)
        if cd > 0 and now - _last.get(ck, 0) < cd:
            return True
        _last[ck] = now

        # 记一次命中
        try:
            ctx.db_exec(f"""INSERT INTO {TABLE}(user_id, group_id, n) VALUES(?,?,1)
                            ON CONFLICT(user_id,group_id) DO UPDATE SET n=n+1""",
                        (int(event.user_id), gid))
        except Exception as e:
            ctx.warn(f"记命中失败：{type(e).__name__}: {e}")

        await ctx.send_group(gid, rules[hit])
        ctx.log(f"群 {gid} 命中「{hit}」")
        return True

    # ---------------- 管理接口 ----------------
    async def _stats(request, body):
        rows = ctx.db_query(
            f"SELECT group_id, SUM(n) AS total, COUNT(*) AS users "
            f"FROM {TABLE} GROUP BY group_id ORDER BY total DESC")
        return {"ok": True, "groups": rows}

    async def _clear(request, body):
        gid = request.query_params.get("group_id") or (body or {}).get("group_id")
        if not gid:
            return {"ok": False, "error": "缺少 group_id"}
        n = ctx.db_exec(f"DELETE FROM {TABLE} WHERE group_id=?", (int(gid),))
        ctx.log(f"清空群 {gid} 的命中统计（{n} 行）")
        return {"ok": True, "deleted": n}

    ctx.register_api("/admin/api/plugins/autoreply/stats", _stats, methods=("GET",))
    ctx.register_api("/admin/api/plugins/autoreply/clear", _clear,
                     methods=("GET", "POST"))

    # ---------------- 配置项（会出现在这个插件自己的配置小窗里）----------------
    ctx.register_config("关键词回复", [
        ["ar_enabled", "开启", "bool"],
        ["ar_pairs", "规则（每行一条：关键词=回复）", "text"],
        ["ar_cooldown", "同群冷却（秒）", "number"],
    ])

    # ---------------- 插件自带页面 ----------------
    ctx.register_page("autoreply", "关键词回复", """
<div class="card">
  <div class="card-h"><h3>关键词回复</h3><span class="en">Auto Reply</span></div>
  <div class="page-desc">
    规则在「插件 → 已安装 → 关键词回复 → 配置」里改，每行一条：<code>关键词=回复</code>。
  </div>
  <div class="form-grid">
    <div class="form-row"><label>群号</label>
      <input id="ar-gid" class="inp" placeholder="例如 100000000"></div>
  </div>
  <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">
    <button class="btn primary" onclick="arStats()">看统计</button>
    <button class="btn danger" onclick="arClear()">清空本群</button>
  </div>
  <div class="api-result" id="ar-res">等待请求…</div>
</div>
<script>
// 脚本跑在全局作用域，函数名一定要加自己的前缀
async function arStats(){
  var b=document.getElementById("ar-res");
  b.textContent="查询中…";
  var r=await api("/admin/api/plugins/autoreply/stats");
  b.textContent=JSON.stringify(r,null,2);
}
async function arClear(){
  var g=document.getElementById("ar-gid");
  var b=document.getElementById("ar-res");
  if(!g.value){b.textContent="请填群号";return;}
  var r=await api("/admin/api/plugins/autoreply/clear?group_id="
                  +encodeURIComponent(g.value),{method:"POST"});
  b.textContent=JSON.stringify(r,null,2);
}
</script>
""")

    ctx.log("关键词回复插件已就绪")
```

---

## 本地测试

把插件文件夹丢进 Nekoe 的 `data/plugins/` 下，管理界面「插件」页点
右上角「**重新加载**」就能看到效果，**不用重启程序**。

改完代码再点一次「重新加载」即可 —— 它会连插件挂的管理接口一起换新的。

调试时可以看「概览 → 实时日志」，插件打的日志都带插件名。

---

## 提交收录

改本仓库的 [`index.json`](./index.json)，在 `plugins` 数组里加一项：

```json
{
  "name": "autoreply",
  "display_name": "关键词回复",
  "version": "1.0.0",
  "author": "你的名字",
  "description": "关键词自动回复，带命中统计。",
  "repo": "https://github.com/你/nekoe-plugin-autoreply",
  "tags": ["工具", "群管"],
  "verified": false
}
```

然后提 PR。合并之后所有 Nekoe 用户都能在市场里看到它。

插件跟别的插件放在同一个仓库里的话，用 `path` 指明子目录：

```json
"repo": "https://github.com/你/插件合集",
"path": "plugins/autoreply"
```

（本仓库自己的 `plugins/hello`、`plugins/lottery` 等就是这么组织的。）

---

## 容易踩的坑

**一定要 `return True`**
命令和消息钩子的处理函数返回 `True` 才算「我处理了」。
返回 `False` 或不返回，消息会继续往下走（可能被 AI 对话接走）。

**插件在没有数据库的时候就会 import**
主程序**先扫描插件（只 import 模块读 metadata），等数据库和 AI 都建好之后才调用
`setup(ctx)`**。所以：

- 模块顶层（`setup` 外面）**别碰 `ctx`、别查数据库**
- 建表、读配置这类事都写进 `setup(ctx)` 里，那时一切都就绪了

**插件页里的 `<script>` 是全局作用域**
函数名、变量名都可能跟别的插件或主程序撞车。加插件名前缀，例如
`autoreplyStats()` 而不是 `stats()`。
（如果整个脚本里有重复声明，浏览器会直接不执行这段 —— 表现是"页面上的按钮点了没反应"。）

**配置项的键要加前缀**
`ctx.cfg("enabled")` 这种通用名迟早会跟别的插件撞。用 `autoreply_enabled`。

**网络请求用 `ctx.http_get`**
它走主程序的共享客户端，本机地址会自动直连。自己 `import httpx` 建的客户端
在开了系统代理的机器上会把 `127.0.0.1` 的请求也发给代理，直接失败。

**扣积分别忘了退**
`ctx.points_spend()` 扣完，后面任何一步失败（网络挂了、API 返回异常）都要
`ctx.points_refund()` 退回去，否则用户白扣分。

---

## 收录标准

不复杂，就几条：

- 能装上、能跑起来（`metadata.json` 合法、入口存在、`setup(ctx)` 不抛异常）
- **别干坏事** —— 偷 API Key、往外发用户数据、当后门的一律不收
- `description` 写清楚干什么，别只写「一个插件」
- 别跟已有插件重名

收录了也不代表我给它背书 ——
**装第三方插件等于让陌生人的代码在你电脑上跑，自己想清楚再装。**

---

## 目录结构

```
index.json          插件清单（市场读这个）
plugins/            官方插件源码
  hello/            最小示例
  lottery/          抽奖
  report/           群报
  sign/             签到积分
  wife/             今日老婆
template/           新插件骨架，复制就能用
```

---

## 许可

跟主程序一样，GPL-3.0。
