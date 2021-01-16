import discord
import asyncio

async def etb(emb):
    emb_str = "```md\n"
    emb_list = []
    if emb.author:
        emb_str += f"<{emb.author.name}>\n\n"
    if emb.title:
        emb_str += f"<{emb.title}>\n"
    if emb.description:
        if len(f"{emb_str}{emb.description}\n```")>2000:
            emb_str += "```"
            emb_list.append(emb_str)
            emb_str = "```md\n"
        emb_str += f"{emb.description}\n"
    if emb.fields:
        for field in emb.fields:
            if len(f"{emb_str}#{field.name}\n{field.value}\n```")>2000:
                emb_str += "```"
                emb_list.append(emb_str)
                emb_str = "```md\n"
            emb_str += f"#{field.name}\n{field.value}\n"
    if emb.footer:
        if len(f"{emb_str}\n{emb.footer.text}\n```")>2000:
            emb_str += "```"
            emb_list.append(emb_str)
            emb_str = "```md\n"
        emb_str += f"\n{emb.footer.text}\n"
    if emb.timestamp:
        if len("{}\n{}\n```".format(emb_str, str(emb.timestamp)))>2000:
            emb_str += "```"
            emb_list.append(emb_str)
            emb_str = "```md\n"
        emb_str += "\n{}".format(str(emb.timestamp))
    emb_str += "```"
    if emb_str != "```md\n```":
        emb_list.append(emb_str)
    return emb_list