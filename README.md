# Nekoe 插件开发

写给想给 [Nekoe](https://github.com/Mario9800/nekoe) 写插件的人。

**这份文档的重点是「出错了怎么办」** —— 前半部分是快速上手，
后半部分按**你在哪里看到报错**来查问题。

---

## 目录

- [五分钟跑通一个插件](#五分钟跑通一个插件)
- [**出错了？先看这里**](#出错了先看这里)
  - [三层失败：你会先在哪看到](#三层失败你会先在哪看到)
  - [报错对照表（按报错原文查）](#报错对照表按报错原文查)
  - [**完全不报错的坑**](#完全不报错的坑) ← 最容易耗时间
  - [怎么调试](#怎么调试)
- [`metadata.json` 完整字段](#metadatajson-完整字段)
- [`ctx` 能力全表](#ctx-能力全表)
- [完整例子](#完整例子)
- [本地测试与发布](#本地测试与发布)

---

## 五分钟跑通一个插件

一个插件就是一个文件夹，最少两个文件：

```
my_plugin/
├── metadata.json    插件信息
└── main.py          入口，里面必须有 def setup(ctx)
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
    "my_reply": "默认回复"
  }
}
```

**`main.py`**

```python
def setup(ctx):
    """插件入口。核心就绪后会被调用一次。"""

    @ctx.command("你好", "打个招呼")
    async def hello(event, cmd):
        await ctx.send_group(event.group_id, "你也好呀")
        return True          # ← 千万别忘了这个

    ctx.register_config("我的插件", [
        ["my_reply", "回复内容", "text"],
    ])
```

丢进 Nekoe 的 `data/plugins/` 下，管理界面「插件」页点右上角**「重新加载」**，
不用重启程序。

**三条铁律**（下面所有报错基本都是违反了这三条）：

1. **只跟 `setup(ctx)` 打交道，不要 `import` 主程序**
2. **模块顶层别碰 `ctx` 和数据库** —— 那时核心还没准备好
3. **命令和消息钩子的处理函数必须 `return True`**

---

## 出错了？先看这里

### 三层失败：你会先在哪看到

插件出错时，**报错会出现在三个完全不同的地方**。先确定你遇到的是哪一层，
能省掉一半排查时间。

```
① 插件列表里根本没这个插件
   └─ metadata.json 有问题。Nekoe 直接跳过它，
      只有「概览 → 实时日志」里有一行 "跳过 xxx：..."

② 有卡片，但标着红色「加载失败」
   └─ 入口文件 / 语法 / setup() 的问题。
      鼠标停在红标上能看到具体错误。

③ 卡片正常（绿色「运行中」），但功能没反应
   └─ 处理函数的问题。界面上完全看不出来，
      必须去「概览 → 实时日志」看。
```

**排查第一步永远是**：打开「概览 → 实时日志」，用日志框上面的筛选看 `插件` 分类。
插件报的错都带插件名，形如：

```
[插件] 我的插件 处理「你好」出错：TypeError: ...
[插件] 我的插件 消息钩子出错：KeyError: 'foo'
```

---

### 报错对照表（按报错原文查）

#### ① 插件压根不出现 → 看日志里的「跳过」

| 日志原文 | 原因 | 改法 |
|---|---|---|
| `跳过 my_plugin：缺少 metadata.json` | 文件夹里没有 `metadata.json` | 补上。文件名必须**正好**是这个 |
| `跳过 my_plugin：metadata.json 解析失败：Expecting property name enclosed in double quotes: line 1 column 17` | JSON 写坏了 | 多半是：多了个逗号、用了单引号、写了注释。**JSON 不允许注释和尾逗号** |
| `跳过 my_plugin：metadata.json 根节点必须是对象` | 最外层写成了数组 | 最外层必须是 `{}` |

> **为什么没有卡片？** 因为 Nekoe 连这个插件叫什么都不知道，没法显示。
> 这是最容易卡住的一层 —— 界面上一片空白，人会以为是程序没扫描到。

#### ② 卡片标红「加载失败」

鼠标停在红标上，或看日志，报错是这几种之一：

| 报错原文 | 原因 | 改法 |
|---|---|---|
| `找不到入口文件 run.py` | `metadata.json` 里的 `entry` 指向的文件不存在 | 检查文件名大小写、是不是放在子目录里了 |
| `导入失败：SyntaxError: expected ':' (main.py, line 1)` | `main.py` 有 Python 语法错误 | 看括号里给的**文件名和行号**，去改那一行 |
| `导入失败：ModuleNotFoundError: No module named 'xxx'` | `main.py` 顶层 import 了没装的库，或 `import bot` | ① 装那个库；② **不要 `import bot`**（见下面「不报错的坑」） |
| `入口文件里没有 setup(ctx) 函数` | 函数名不是 `setup`，或 `setup` 不是函数 | 必须是 `def setup(ctx):`，参数名随意但**必须收一个参数** |
| `setup() 抛异常：AttributeError: 'PluginContext' object has no attribute 'register_typo'` | `setup()` 里调了 `ctx` 上不存在的方法（多半是打错字） | 对照下面 [ctx 能力全表](#ctx-能力全表) |
| `setup() 抛异常：NameError: name 'DB' is not defined` | `setup()` 里用了不存在的变量 | 只能通过 `ctx` 取东西，不能直接用主程序的变量 |
| `setup() 抛异常：sqlite3.OperationalError: ...` | 建表 SQL 写错了 | `ctx.db_exec()` 的 SQL 得自己保证正确 |

#### ③ 卡片正常但功能没反应

这些**只在日志里**：

| 日志原文 | 原因 | 改法 |
|---|---|---|
| `我的插件 处理「你好」出错：TypeError: h() takes 1 positional argument but 2 were given` | 处理函数参数个数不对 | 必须是 `async def h(event, cmd):` **两个参数** |
| `我的插件 处理「你好」出错：ValueError: ...` | 你的代码抛异常了 | 看异常类型和消息，是自己逻辑的问题 |
| `我的插件 消息钩子出错：...` | `@ctx.on_message()` 的钩子里抛异常 | 同上 |
| `我的插件 的接口 /admin/api/xxx 与已有路由冲突，跳过` | 你注册的接口路径跟内置的（或别的插件的）撞了 | 换成 `/admin/api/plugins/<你的插件名>/xxx` |
| `我的插件 接口 /admin/api/xxx 挂载失败：...` | `register_api` 的 handler 不是函数 | 传函数对象本身，别传字符串 |
| 什么都没打印，消息也没回 | **十有八九是忘了 `return True`** | 见下面 |

---

### 完全不报错的坑

这些是最耗时间的 —— **程序认为一切正常，但功能就是不对**。

#### 坑 1：忘了 `return True`（最高频）

```python
@ctx.command("你好", "打个招呼")
async def hello(event, cmd):
    await ctx.send_group(event.group_id, "你也好呀")
    # ← 这里没有 return True
```

结果：**消息可能发出去了，但 Nekoe 认为"这个命令没人处理"**，
于是继续往下走 —— 可能被内置逻辑接走，或者触发 AI 对话，重复回一遍。

**规则**：处理函数返回 `True` = "我处理了，别再往下传"。
返回 `False` / `None` / 不返回 = "我没处理"。

```python
@ctx.command("你好", "...")
async def hello(event, cmd):
    if not some_condition:
        return False         # 这次我不处理，让别人来
    await ctx.send_group(event.group_id, "你也好呀")
    return True              # 处理完了
```

#### 坑 2：`import bot` —— 开发时正常，装到桌面版必炸

```python
import bot                    # ← 千万别这么写
def setup(ctx):
    bot.DB.something()
```

在源码环境里 `import bot` 能跑（因为 `bot.py` 就在旁边），
但**装到桌面版（exe）里会 `ModuleNotFoundError`** —— 主程序被打进 exe 了，
不是磁盘上那个 `.py` 文件。

**你需要的所有东西都在 `ctx` 上**，不需要 import 主程序。

#### 坑 3：模块顶层碰 `ctx`

```python
def setup(ctx):
    global REPLY
    REPLY = ctx.cfg("reply", "默认")     # ✓ 这样没问题

REPLY = ctx.cfg("reply", "默认")          # ✗ 顶层根本拿不到 ctx
```

Nekoe **先扫描插件（只 import 模块读 metadata），等数据库和 AI 都建好之后
才调用 `setup(ctx)`**。所以：

- ✅ `setup()` 里面：随便用 `ctx`
- ❌ `setup()` 外面：没有 `ctx`，也没有数据库

建表、读配置这类事**都写进 `setup()` 里**。

#### 坑 4：两个插件用了同一个 `name`

```
data/plugins/my-plugin-a/metadata.json   → "name": "hello"
data/plugins/my-plugin-b/metadata.json   → "name": "hello"
```

结果：**后扫描到的那个被静默吞掉**，命令全都不生效。
日志只说「扫描完成：N 个可用」，N 比你实际的目录数少 —— 不仔细看发现不了。

**`name` 是唯一键**，起个不会撞的（加你自己的前缀）。

#### 坑 5：插件页面里的 `<script>` 有语法错误

```python
ctx.register_page("myplugin", "标题", """
<div><button onclick="mypluginGo()">点我</button></div>
<script>
function mypluginGo( {          ← 多了个括号
  ...
}
</script>
""")
```

插件**加载完全成功**，卡片是绿的。但打开页面后：

- 按钮点了没反应
- 那个页面的**所有**函数都不可用（JS 是一整块，一处语法错整块不执行）

**排查**：浏览器按 F12 打开控制台，会看到 `Uncaught SyntaxError`。
这个错误**不会**出现在 Nekoe 的日志里 —— 日志只管 Python 那边。

> 另外：页面脚本跑在**全局作用域**，函数名加插件前缀
> （`mypluginGo` 而不是 `go`），否则可能跟主程序或别的插件撞名。
> 撞名同样会导致**整块脚本不执行**。

#### 坑 6：配置项的值不会自动转换类型

```python
ctx.register_config("我的插件", [["my_limit", "次数上限", "number"]])
```

界面上是一个数字输入框，但 `ctx.cfg("my_limit", 3)` 拿到的
**可能是字符串 `"3"` 而不是整数 `3`**（取决于值从哪来）。

**自己转**：

```python
def _int(key, default):
    try:
        v = ctx.cfg(key, default)
        return default if v is None or v == "" else int(float(v))
    except Exception:
        return default

def _bool(key, default):
    v = ctx.cfg(key, default)
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on", "开启")

def _str(key, default):
    v = ctx.cfg(key, default)
    return default if v is None else str(v)
```

这三个小工具几乎每个官方插件里都有，直接抄。

#### 坑 7：`ctx.db_exec` 的 SQL 错误会抛异常

`ctx.db_exec()` / `ctx.db_query()` **不吞异常**，SQL 写错会往上抛，
在你没加 `try` 的地方中断整个处理函数。

```python
try:
    ctx.db_exec("INSERT INTO myplugin_log(user_id, n) VALUES(?, 1)", (uid,))
except Exception as e:
    ctx.warn(f"写库失败：{type(e).__name__}: {e}")   # 记一笔，别让整个命令挂掉
```

**哪些 `ctx` 方法会吞异常、哪些不会** —— 见下面能力表里的「失败时」一列。

#### 坑 8：网页请求自己 `import httpx`

```python
import httpx                                   # ✗
r = httpx.get("http://127.0.0.1:7861/...")
```

开了系统代理（Clash / v2ray）的机器上，`httpx` 会把连**本机服务**的请求
也发给代理，代理不转发 localhost，直接 502。

用 `ctx.http_get()` —— 它走主程序的共享客户端，本机地址强制直连：

```python
r = await ctx.http_get("http://127.0.0.1:7861/x", timeout=10)
data = r.json()
```

---

### 怎么调试

**唯一的工具是日志。** 「概览 → 实时日志」里筛选「插件」，只看插件相关的。

自己打的日志也在这里：

```python
ctx.log("正常信息，青色")      # → [插件] 我的插件：正常信息
ctx.warn("警告，黄色")         # → 同样带插件名，好找
```

**推荐的调试节奏：**

1. 改完代码 → 点「重新加载」（**不用重启**）
2. 看「插件」页卡片有没有变红 → 有 → 查上面的 ① ② 表
3. 卡片绿了 → 去群里 @机器人 发命令
4. 没反应 → 回日志看有没有 `处理「xxx」出错`
5. 日志也没东西 → 九成是**忘了 `return True`**，或者命令词跟实际发的不一致

**命令词是精确匹配的。** 注册了 `"你好"`，群里发「你好啊」「你好！」都**不触发**。
要多个别名就多注册几个：

```python
for kw in ("你好", "您好", "hi"):
    ctx.command(kw, "打招呼")(hello_handler)
```

---

## `metadata.json` 完整字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 插件唯一标识。**只能用字母、数字、`_` `-` `.`，48 字以内**。用中文或空格的话，本地能加载，但装到别人机器上会被拒（市场安装有校验） |
| `display_name` | | 界面上显示的名字，不填就用 `name` |
| `version` | | `1.2.3` 这种。**升级时必须改大**，否则市场不会提示更新 |
| `author` | | 作者 |
| `description` | | 一句话说明 |
| `entry` | | 入口文件，默认 `main.py`。只能是插件文件夹里的相对路径 |
| `tags` | | 字符串数组，显示成小徽章 |
| `defaults` | | 配置项默认值。`ctx.cfg()` 读不到时会用这里 |

**`name` 的合法格式**：

```
✅ my_plugin    autoreply    nekoe.tools    my-plugin
❌ 我的插件       my plugin     my/plugin      （中文 / 空格 / 斜杠都不行）
```

**`version` 必须能被解析**，不然市场比不出新旧：

```
✅ 1.0.0    1.2.3    2.0.0.1    0.1.0
❌ v1.0      最新版    abc
```

---

## `ctx` 能力全表

「失败时」一列很关键 —— **标"会抛异常"的方法，你不加 `try` 就可能中断整个处理函数**。

### 注册东西

| 方法 | 说明 |
|---|---|
| `ctx.command(命令词, 说明="")` | 装饰器。`async def h(event, cmd)` → 返回 `True` 表示已处理 |
| `ctx.on_message()` | 装饰器。`async def h(event, text)` → 返回 `True` 吞掉这条消息 |
| `ctx.register_config(标题, fields)` | 声明配置项。`fields` = `[[键, 标签, 类型], ...]`，类型：`bool` / `number` / `text` |
| `ctx.register_page(id, 标题, html="")` | 插件自带管理页。页内 `<script>` 会执行 |
| `ctx.register_api(路径, handler, methods=("GET",))` | 注册管理接口。handler 签名 `(request, body)`，可 async |

### 收发消息

| 方法 | 失败时 | 说明 |
|---|---|---|
| `await ctx.send_group(gid, 内容)` | 吞异常，返回 `True`/`False` | 内容可以是字符串或列表 |
| `await ctx.send_private(uid, 内容)` | 吞异常，返回 `True`/`False` | 同上 |
| `ctx.mention(uid)` | — | @某人的片段，放进列表里 |
| `ctx.image(url)` | — | 图片片段，放进列表里 |

```python
await ctx.send_group(event.group_id, [
    ctx.mention(event.user_id), " 恭喜中奖！\n",
    ctx.image("https://example.com/a.jpg"),
])
```

### 读写数据

| 方法 | 失败时 | 说明 |
|---|---|---|
| `ctx.db_exec(sql, params=())` | **会抛异常** | 写语句，返回影响行数 |
| `ctx.db_query(sql, params=())` | **会抛异常** | 查询，返回 `[{列: 值}, ...]` |
| `ctx.kv_get(键, 默认值=None)` | 吞异常 | 插件私有键值存储 |
| `ctx.kv_set(键, 值)` | 吞异常，返回 `True`/`False` | 适合存少量状态 |
| `ctx.act_recent(gid, days=7)` | 吞异常，返回 `[]` | 最近 N 天活跃成员 |
| `ctx.daily_rank(gid, 日期串, limit=10)` | 吞异常，返回 `[]` | 某天发言榜 |
| `ctx.daily_summary(gid, 日期串)` | 吞异常，返回 `{users:0,total:0}` | 某天汇总 |

**返回的字段名**（很容易记错）：

```python
ctx.act_recent(gid, days=7)
# → [{"user_id":111, "group_id":1, "last_active":"2026-10-04 12:00:00",
#     "msg_count":9, "nickname":"小明"}, ...]
#                        ↑ 是 msg_count，不是 count

ctx.daily_rank(gid, "2026-10-04", limit=10)
# → [{"user_id":111, "nickname":"小明", "msg_count":12}, ...]

ctx.daily_summary(gid, "2026-10-04")
# → {"users": 3, "total": 22}
```

**自己的表自己建**，建表语句放在 `setup()` 开头。**表名一定要加插件名前缀**，
否则会跟别的插件或主程序撞：

```python
def setup(ctx):
    ctx.db_exec("""CREATE TABLE IF NOT EXISTS myplugin_hits(
        user_id INTEGER, group_id INTEGER, n INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, group_id))""")
```

### 积分（签到插件提供的数据）

`points` 表由主程序托管，签到 / 抽奖 / 老婆这些插件共用。

| 方法 | 失败时 | 说明 |
|---|---|---|
| `ctx.sign_do(uid, gid, nick, base, bonus_per, bonus_cap, today)` | **会抛异常** | 原子签到，返回 dict |
| `ctx.sign_get(uid, gid)` | **会抛异常** | 返回 `{points, sign_count, streak, ...}` 或 `None` |
| `ctx.sign_rank(gid, limit=10)` | 吞异常，返回 `[]` | 本群积分榜 |
| `ctx.sign_rank_all()` | 吞异常，返回 `[]` | 所有群汇总 |
| `ctx.sign_clear_group(gid)` | **会抛异常** | 清空某群积分 |
| `ctx.points_spend(uid, gid, 数量)` | **会抛异常** | 扣分，返回 `(成功?, 剩余)` |
| `ctx.points_refund(uid, gid, 数量)` | **会抛异常** | 退分 |

**扣分要成对用** —— 扣完后面任何一步失败都要退，否则用户白扣：

```python
ok, left = ctx.points_spend(uid, gid, cost)
if not ok:
    return {"ok": False, "error": f"积分不够，需要 {cost}，你只有 {left}"}
spent = cost
try:
    # ... 干活 ...
except Exception:
    ctx.points_refund(uid, gid, spent)     # 出事了退回去
    raise
```

### 网络 / AI / 其它

| 方法 | 失败时 | 说明 |
|---|---|---|
| `await ctx.http_get(url, params=None, timeout=15.0, headers=None)` | **会抛异常** | 返回 httpx 的 Response，自己 `.json()` |
| `await ctx.ai(提示词, timeout=15.0)` | 吞异常，返回 `""` | 让 AI 生成文字，没启用或失败都返回空串 |
| `await ctx.group_name(gid)` | 吞异常，返回 `f"群{gid}"` | 群名 |
| `ctx.self_id()` | 吞异常，返回 `""` | 机器人 QQ |
| `ctx.log(消息)` / `ctx.warn(消息)` | — | 打日志，都带插件名 |
| `ctx.cfg(键, 默认值=None)` | 吞异常 | 读配置 |
| `ctx.set_cfg(键, 值)` | **可能抛异常** | 写配置（会落盘） |

**`ctx.ai` 超时**是返回 `""` 而不是抛异常，所以 `if not text:` 就够了，不用 try。

---

## 完整例子

「关键词自动回复 + 命中统计」，用到了大部分能力。

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

    # ---- 配置类型转换（配置值可能是字符串）----
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
        """把 "关键词=回复" 的多行文本解析成字典。"""
        out = {}
        for line in str(ctx.cfg("ar_pairs", "") or "").splitlines():
            line = line.strip()
            if not line or PAIR_SEP not in line:
                continue
            k, v = line.split(PAIR_SEP, 1)
            k, v = k.strip(), v.strip()
            if k and v:
                out[k] = v
        return out

    # ---- 消息钩子 ----
    @ctx.on_message()
    async def on_msg(event, text):
        if not _bool("ar_enabled", True):
            return False
        if not getattr(event, "group_id", None):
            return False              # 只管群消息
        text = (text or "").strip()
        if not text:
            return False

        rules = pairs()
        if text not in rules:
            return False              # 不是关键词，交给别人

        # 冷却按 (群, 关键词) 各算各的 —— 按整群算的话，
        # 同一群里连发两个不同关键词，第二个会被误吞
        cd = _int("ar_cooldown", 5)
        gid = int(event.group_id)
        now = time.time()
        ck = (gid, text)
        if cd > 0 and now - _last.get(ck, 0) < cd:
            return True               # 冷却中，静默吞掉
        _last[ck] = now

        # 记一次命中（写库会抛异常，自己兜住）
        try:
            ctx.db_exec(f"INSERT INTO {TABLE}(user_id, group_id, n) VALUES(?,?,1) "
                        f"ON CONFLICT(user_id,group_id) DO UPDATE SET n=n+1",
                        (int(event.user_id), gid))
        except Exception as e:
            ctx.warn(f"记命中失败：{type(e).__name__}: {e}")

        await ctx.send_group(gid, rules[text])
        ctx.log(f"群 {gid} 命中「{text}」")
        return True                   # 处理完了

    # ---- 管理接口 ----
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
        return {"ok": True, "deleted": n}

    ctx.register_api("/admin/api/plugins/autoreply/stats", _stats, methods=("GET",))
    ctx.register_api("/admin/api/plugins/autoreply/clear", _clear,
                     methods=("GET", "POST"))

    # ---- 配置项（出现在本插件自己的配置小窗里）----
    ctx.register_config("关键词回复", [
        ["ar_enabled", "开启", "bool"],
        ["ar_pairs", "规则（每行一条：关键词=回复）", "text"],
        ["ar_cooldown", "同群冷却（秒）", "number"],
    ])

    # ---- 插件自带页面 ----
    ctx.register_page("autoreply", "关键词回复", """
<div class="card">
  <div class="card-h"><h3>关键词回复</h3><span class="en">Auto Reply</span></div>
  <div class="form-grid">
    <div class="form-row"><label>群号</label>
      <input id="ar-gid" class="inp" placeholder="例如 100000000"></div>
  </div>
  <div style="margin-top:14px">
    <button class="btn primary" onclick="autoreplyStats()">看统计</button>
  </div>
  <div class="api-result" id="ar-res">等待请求…</div>
</div>
<script>
// 函数名加插件前缀 —— 脚本跑在全局作用域，撞名会让整块不执行
async function autoreplyStats(){
  var b=document.getElementById("ar-res");
  b.textContent="查询中…";
  var r=await api("/admin/api/plugins/autoreply/stats");
  b.textContent=JSON.stringify(r,null,2);
}
</script>
""")

    ctx.log("关键词回复插件已就绪")
```

这个例子就是市场里的 [`autoreply`](plugins/autoreply) 插件，装上去就能跑。

---

## 本地测试与发布

### 本地测试

1. 把插件文件夹丢进 `data/plugins/`
2. 管理界面「插件」页点右上角**「重新加载」**
3. 看卡片是不是绿的 → 不是就查[报错对照表](#报错对照表按报错原文查)
4. 去群里发命令试试
5. 没反应 → 看「概览 → 实时日志」

**改完代码点一次「重新加载」就行，不用重启程序。**
它会把插件挂的管理接口也一起换成新的。

### 发布

**方式一：不收录，别人也能装**

把插件推到自己的 GitHub 仓库，别人在「插件 → 已安装」页底部
贴上仓库地址就能装。

**方式二：收录进市场**

改本仓库的 [`index.json`](index.json)，在 `plugins` 数组里加一项：

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

然后提 PR。

插件跟别的插件放在同一个仓库里的话，用 `path` 指明子目录：

```json
"repo": "https://github.com/你/插件合集",
"path": "plugins/autoreply"
```

（本仓库的 `plugins/hello`、`plugins/lottery` 等就是这么组织的。）

### 收录标准

- 能装上、能跑起来（`metadata.json` 合法、入口存在、`setup()` 不抛异常）
- **别干坏事** —— 偷 API Key、往外发用户数据、当后门的一律不收
- `description` 写清楚干什么
- `name` 别跟已有的重名

收录不代表背书 —— **装第三方插件等于让陌生人的代码在你电脑上跑**。

---

## 目录结构

```
index.json          插件清单（市场读这个）
plugins/            官方插件源码
  hello/            最小示例
  autoreply/        完整示例（关键词回复）
  lottery/          抽奖
  report/           群报
  sign/             签到积分
  wife/             今日老婆
template/           新插件骨架，复制就能改
```

---

## 许可

主程序和官方插件：GPL-3.0。
你自己的插件不受这个约束。
