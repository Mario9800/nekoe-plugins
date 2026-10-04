# -*- coding: utf-8 -*-
"""插件骨架：复制这个文件夹，改掉 metadata.json 和下面的逻辑就行。

调试：丢进 Nekoe 的 data/plugins/ 下，管理界面「插件」页点「重新加载」。
"""


def setup(ctx):
    """插件入口，加载时调用一次。只依赖 setup(ctx) 这个约定 —— 
    不需要 import 主程序任何东西，所以打包成 exe 后也能加载。"""

    # 读配置（metadata.json 的 defaults 或用户在界面上改的值）
    reply = ctx.cfg("my_reply", "默认回复内容")

    @ctx.command("测试命令", "被 @ 且内容是这个时触发")
    async def on_cmd(event, cmd):
        await ctx.send_group(event.group_id, reply)
        ctx.log(f"在群 {event.group_id} 回应了 {event.user_id}")
        return True          # True = 已处理，不再走内置逻辑

    # 配置项会出现在管理界面「系统配置」页的最后
    ctx.register_config("我的插件", [
        ["my_reply", "回复内容", "text"],
    ])

    ctx.log("我的插件已就绪")
