# -*- coding: utf-8 -*-
"""插件骨架 —— 复制这个文件夹，改掉 metadata.json 和下面的逻辑就行。

完整文档（ctx 能力全表、容易踩的坑）：见仓库根目录的 README.md

调试：把文件夹丢进 Nekoe 的 data/plugins/ 下，
      管理界面「插件」页点右上角「重新加载」，不用重启。

几条最重要的约定：
  · 只跟 setup(ctx) 打交道，**不要 import 主程序**（打包成 exe 后模块名会变）
  · 模块顶层别碰数据库 —— 核心就绪后才会调用 setup()，那时才能用 ctx.db_*
  · 命令和消息钩子的处理函数记得 return True，否则消息会继续往下走
  · 配置项、表名、页面里的 JS 函数名都加上你的插件前缀，避免跟别人撞车
"""


def setup(ctx):
    """插件入口。核心（数据库 / AI）就绪后调用一次。"""

    # ---- 自己的表自己建（表名加插件前缀）----
    # ctx.db_exec("""CREATE TABLE IF NOT EXISTS myplugin_log(
    #     user_id INTEGER, group_id INTEGER, ts TEXT,
    #     PRIMARY KEY (user_id, group_id, ts))""")

    # ---- 读配置（metadata.json 的 defaults，或用户在配置小窗里改的值）----
    reply = ctx.cfg("my_reply", "默认回复内容")

    @ctx.command("测试命令", "被 @ 且内容正好是「测试命令」时触发")
    async def on_cmd(event, cmd):
        await ctx.send_group(event.group_id, reply)
        ctx.log(f"在群 {event.group_id} 回应了 {event.user_id}")
        return True          # True = 已处理，不再走内置逻辑

    # 想要多个别名就多注册几个，指向同一个处理函数：
    # for kw in ("测试命令", "测试", "test"):
    #     ctx.command(kw, "说明")(on_cmd)

    # ---- 可选：消息钩子（每条消息都过一遍）----
    # @ctx.on_message()
    # async def on_msg(event, text):
    #     if "广告" in text:
    #         return True      # 吞掉这条消息
    #     return False

    # ---- 可选：@某人 / 发图片 ----
    # await ctx.send_group(event.group_id, [
    #     ctx.mention(event.user_id), " 你好\n",
    #     ctx.image("https://example.com/a.jpg"),
    # ])

    # ---- 可选：调外部接口（用 ctx.http_get，别自己 import httpx）----
    # r = await ctx.http_get("https://api.example.com/x", params={"q": "1"})
    # data = r.json()

    # ---- 可选：让 AI 写点东西（失败返回空串，不会抛异常）----
    # text = await ctx.ai("用一句话形容今天的天气")

    # ---- 声明配置项 ----
    # 这些不会混进「系统配置」页，而是在**本插件自己的配置小窗**里：
    # 管理界面「插件 → 已安装」的卡片上点「配置」。
    ctx.register_config("我的插件", [
        ["my_reply", "回复内容", "text"],
        # ["my_enabled", "开启", "bool"],
        # ["my_limit", "次数上限", "number"],
    ])

    # ---- 可选：插件自带管理页（html 里的 <script> 会执行）----
    # 注意脚本跑在全局作用域，函数名加前缀（mypluginFoo 而不是 foo）
    # ctx.register_page("my_plugin", "我的插件", """
    # <div class="card">
    #   <div class="card-h"><h3>我的插件</h3><span class="en">My Plugin</span></div>
    #   <div class="api-result" id="mp-res">等待请求…</div>
    # </div>
    # <script>
    # async function mypluginPing(){
    #   var b=document.getElementById("mp-res");
    #   var r=await api("/admin/api/plugins/my_plugin/ping");
    #   b.textContent=JSON.stringify(r,null,2);
    # }
    # </script>
    # """)

    # ---- 可选：管理接口（会自动带 token 校验）----
    # async def _ping(request, body):
    #     q = request.query_params.get("x")     # 查询参数
    #     b = body or {}                        # POST 的 JSON body
    #     return {"ok": True, "echo": q or b.get("x")}
    # ctx.register_api("/admin/api/plugins/my_plugin/ping", _ping,
    #                  methods=("GET", "POST"))

    ctx.log("我的插件已就绪")
