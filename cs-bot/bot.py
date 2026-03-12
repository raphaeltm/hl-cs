import discord
from discord.ext import commands, tasks
from datetime import timedelta
import torch
from torch import nn, optim
import os
import random
import time
from pathlib import Path
from PIL import Image, ImageDraw
from svgpathtools import parse_path
import requests

intent = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intent)

intent.members = True
intent.message_content = True
intent.moderation = True
intent.guilds = True

admin_ids = [1353315975319126047, 990248306544377876]

class CSReactor(nn.Module):
    def __init__(self, vs=128, hidden=384):
        super().__init__()
        self.lstm = nn.LSTM(128, hidden, 2, dropout=0.4, batch_first=True)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden, vs)
    def forward(self, x, hidden=None):
        out, hidden = self.lstm(x, hidden)
        out = self.dropout(out)
        out = self.fc(out)
        return out, hidden
    
def time_parser(time):
    unit = time[-1]
    amount = int(time[:-1])
    if unit == "s":
        return timedelta(seconds=amount)
    elif unit == "m":
        return timedelta(minutes=amount)
    elif unit == "h":
        return timedelta(hours=amount)
    elif unit == "d":
        return timedelta(days=amount)
    else:
        raise ValueError("Invalid time format. Use 's' for seconds, 'm' for minutes, 'h' for hours, or 'd' for days.")

model_case = "CS_Reactor.pt"
if os.path.exists(model_case):
    model = torch.load(model_case, map_location="cpu", weights_only=False)
    print("Loaded")
else:
    model = CSReactor()
    torch.save(model, model_case)
    print("Created a new servo")

optimizer = optim.Adam(model.parameters(), lr=0.003)
criterion = nn.CrossEntropyLoss()

samps = [
    ("what's going on here?", "Looks like u wound up in the wrong server bro. We don't accept lost causes XD"),
    ("I failed the test", "Bro just got the fattest L of the week"),
    ("good morning guys", "good morning son"),
    ("send private shit", "FBI open up, we got a brave one here"),
    ("i'm bored", "same bro, existence alone is a pain"),
]

snipes = {}
edits = {}
ts = {}
def fs():
    url = "https://kejvhvxbsugbsmmbunlh.supabase.co/functions/v1/scrape-competitor"
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtlanZodnhic3VnYnNtbWJ1bmxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYwMzI2NTUsImV4cCI6MjA2MTYwODY1NX0.-_Iqos5xvnQ712RhfMQibuBN08QKGu2GskqodEkTgoE"}
    res = requests.get(url, headers=headers).json()
    global ts
    in_stock_items = [item for item in res.get('items', []) if item.get('inStock', False)]
    sorted_items = sorted(in_stock_items, key=lambda x: x['value'], reverse=True)
    stock = {}
    print(sorted_items)
    for item in sorted_items:
        name = item.get('name', 'Unknown Item')
        value = item.get('value', 0)
        stock[name] = value
    if stock == ts:
        print("Stock unchanged")
        return
    ts = stock
    print(ts)
    return ts 
     
    
@bot.event
async def on_ready():
    await bot.tree.sync()
    continuous_fetch.start()
    for guild in bot.guilds:
        print(guild.name)
        general = discord.utils.get(guild.channels, name="general")
        if guild.name == "CS Tutorials":
            welcome = discord.utils.get(guild.channels, name="welcome-and-rules")
            if not welcome:
                welcome = guild.create_text_channel(name="welcome-and-rules")
            async for message in welcome.history(limit=40):
                text = "n peace"
                if message.author == bot.user:
                    return
                else:
                    await welcome.send(content=f"__**Welcome to CS**__\n In order to maintain peace in this server, there are a list of rules which everyone is expected to follow\n1. **Be Respectful**: Treat everyone with respect. No harrassment, hate speech, or personal attacks. Be patient with begsinners--everyone is learning👍\n2. **Stay on topic**: Keep discussions related to programming, technology, and learning. Off-topic chats should go in designated channels like #off-topic")

@tasks.loop(minutes=30)
async def continuous_fetch():
    stock = fs()
    if stock is None:
        print("No stock update")
        return
    for guild in bot.guilds:
        
        # if not channel:
        #     with open(f"{guild.name}/sv_data.npthy", "r") as r:
        #         lines = r.readlines()
        #         for i, li in enumerate(lines):
        #             if li.startswith("bfa"):
        #                 value = li.split("--")[1].split("[]")[0]
        #                 if value == "fs":
        #                     return
        #                 channel = await guild.create_text_channel(name="blox-fruits-stock")
        #                 channel.set_permissions(guild.default_role, read_messages=True, send_messages=False, add_reactions=True)
        #                 continue
        if guild.name == "His Excellency and Co.":
            channel = discord.utils.get(guild.channels, name="blox-fruits-stock")
            try:
                result = "Name | Price\n"
                for name, value in stock.items():
                    result += f"**{name}**: {value}\n"
                embed = discord.Embed(title="Blox Fruits Stock Update\n", description=result, color=0x00ff00, timestamp=discord.utils.utcnow())
                embed.set_footer(text="Stock resets every 4 hours")
                return await channel.send(embed=embed)
            except Exception as e:
                print(f"Error occurred while sending embed: {e}")
@bot.event
async def on_message_delete(message: discord.Message):
    print(f"{message.author} deleted the message {message.content} in {message.channel}--{message.guild}")
    snipes[message.channel.id] = message
@bot.event
async def on_message(message: discord.Message):
    print(f"{message.author}--{message.content}")
    if message.author == bot.user:
        return
    referral = message.reference
    if referral:
        print("has referral")
        ref_msg = await message.channel.fetch_message(message.reference.message_id)
        if ref_msg.author == bot.user:
            return
        texts = ["Commando Servo", "commando", "cs_bot", "CS Bot", "cs bot", "servo", "neal pathways"]
        for text in texts:
            if text in message.content.lower():
                if not message.author.guild_permissions.manage_messages:
                    await message.channel.send("You do not have permission to use this command.")
                    break
                print("has keyword")
                if "insult" in message.content.lower():
                    insults = [
                        "You're as useless as the 'ueue' in 'queue'.",
                        "I'd explain it to you, but I left my English-to-Dingbat dictionary at home.",
                        "You're not stupid; you just have bad luck when it comes to thinking.",
                        "If I wanted to hear from an idiot, I'd just watch reality TV.",
                        "You're like a cloud. When you disappear, it's a beautiful day."
                        "You fool. Do you have any idea who you're talking to?",
                        "I'd agree with you, but then we'd both be wrong.",
                    ]
                    print("issuing insult")
                    insult = random.choice(insults)
                    await ref_msg.reply(insult)
                    return await message.delete()
                elif "respond" in message.content.lower():
                    arg = message.content.lower().split(" ")[2:]
                    prompt = " ".join(arg)
                    await ref_msg.reply(prompt)
                    return await message.delete()
                
@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    print(f"{before.author} edited the message {before.content} to {after.content} in {before.channel}--{before.guild}")
    if before.content == after.content:
        return
    edits[after.id] = (before, after)
@bot.tree.command(name="clear", description="Clear a specific amount of messzages from a channel")
async def clear(interaction: discord.Interaction, count: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You do not have permission to use this command")
        return
    if count > 50:
        await interaction.response.send_message("You cannot delete more than 50 messages at once")
        return
    await interaction.response.defer(ephemeral=True)
    deleted_messages = await interaction.channel.purge(limit=count)
    await interaction.followup.send(f"{len(deleted_messages)} messages have been deleted", ephemeral=True)
@bot.tree.command(name="verify", description="Verify your account in order to have access")
async def verify(interaction: discord.Interaction):
    await interaction.response.send_message("You are being verified")

@bot.tree.command(name="mute", description="A command used by the elites of the server to temporarily punish users for their wromgdoings")
async def mute(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer()
    if not interaction.user.guild_permissions.mute_members:
        return await interaction.followup.send(content="You do not have permission to use this command.", ephemeral=True)
    muted_role = discord.utils.get(interaction.guild.roles, name="muted")
    if not muted_role:
        muted_role = await interaction.guild.create_role(name="muted")
        mr_perms = discord.PermissionOverwrite(send_messages=False, speak=False, read_message_history=True, read_messages=True, manage_messages=False, administrator=False)
        for channel in interaction.guild.channels:
            await channel.set_permissions(muted_role, overwrite=mr_perms)
    with open(f"{user.name}-data.npthwy", "a+") as r:
        text = ", ".join(role.name for role in user.roles)
        translated = "".join(format(ord(char), "08b") for char in text)
        r.write(translated + "\n")
    await user.edit(roles=[muted_role])
    await interaction.followup.send(f"{user.name} has been muted")

@bot.tree.command(name="rp", description="Reply the referral message")
async def rp(interaction: discord.Interaction, mi: str, me: str):
    try:
        ref_msg = await interaction.channel.fetch_message(int(mi))
        await ref_msg.reply(me)
        await interaction.response.send_message("Replied successfully :smirk:.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("Message not found.", ephemeral=True)
        return
@bot.tree.command(name="sp", description="Gm")
async def sp(interaction: discord.Interaction, me: str):
    # await interaction.response.defer()
    if not interaction.user.guild_permissions.manage_messages or interaction.user.id not in admin_ids:
        return await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
    await interaction.channel.send(me)
    await interaction.response.send_message("Message sent successfully :smirk:.", ephemeral=True)

@bot.tree.command(name="react", description="React to the referral message with an emoji")
async def react(interaction: discord.Interaction, mi: str, emoji: str):
    await interaction.response.defer()
    try:
        ref_msg = await interaction.channel.fetch_message(int(mi))
        await ref_msg.add_reaction(emoji)
        await interaction.response.send_message("Replied successfully :smirk:.", ephemeral=True)
    except discord.NotFound:
        await interaction.followup.send("Message not found.", ephemeral=True)
        return

@bot.tree.command(name="kick", description="Kick a user from the guild")
async def kick(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    await user.kick()
    return await interaction.response.send_message(f"{user.name} has been kicked from the guild", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a user from the guild")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    await user.ban(reason=reason)
    return await interaction.response.send_message(f"{user.name} has been banned from the guild", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user from the guild")
async def unban(interaction: discord.Interaction, user: discord.User, reason: str):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    await interaction.guild.unban(user, reason=reason)
    return await interaction.response.send_message(f"{user.name} has been unbanned from the guild", ephemeral=True)

@bot.tree.command(name="nick", description="Change a user's nickname")
async def nick(interaction: discord.Interaction, user: discord.Member, nickname: str):
    if not interaction.user.guild_permissions.manage_nicknames:
        return await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
    await user.edit(nick=nickname)
    return await interaction.response.send_message(f"{user.name}'s nickname has been changed to {nickname} :smirk:", ephemeral=True)
@bot.tree.command(name="tmt", description="Timeout a user for a specific amount of time")
async def tmt(interaction: discord.Interaction, user: discord.Member, duration: str, reason:str):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    d_time = time_parser(duration)
    await user.timeout(d_time, reason=reason)
    return await interaction.response.send_message(f"{user.name} has been timed out for {d_time.total_seconds()} seconds", ephemeral=True)

@bot.tree.command(name="ufetch", description="fetch a user's data")
async def ufetch(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    try:
        with open(f"{interaction.guild.name}/users/{user.name}.npthy", "r") as r:
            data = r.read()
            with open(f"temp-{user.name}.txt", "w") as w:
                w.write(data)
    except FileNotFoundError:
        return await interaction.response.send_message(content="User data not found", ephemeral=True)
    await interaction.response.send_message(content=f"Data for {user.name} has been fetched", file=discord.File(f"temp-{user.name}.txt"), ephemeral=True)
    time.sleep(5)
    os.remove(f"temp-{user.name}.txt")

@bot.tree.command(name="audit", description="audit a server")
async def audit(interaction: discord.Interaction):
    await interaction.response.defer()
    sv_dir = Path(f"{interaction.guild.name}")
    if sv_dir.exists() and sv_dir.is_dir():
        os.remove(sv_dir)
    Path(f"{interaction.guild.name}/users").mkdir(parents=True, exist_ok=True)
    members = [m async for m in interaction.guild.fetch_members(limit=None)]
    for user in members:
        with open(f"{interaction.guild.name}/users/{user.name}.npthy", "a+") as a:
            a.seek(0)
            a.write(f"name--{user.name}[]\ndisplay--{user.display_name}[]\njoined--{user.joined_at}[]\nroles--{', '.join(role.name for role in user.roles)}[]\nstatus--{user.client_status}[]\nflags--{user.public_flags}\nID--{", ".join(format(ord(char), "08b") for char in str(user.id))}[]\npermissions--{", ".join(str(perm) for perm in user.guild_permissions)}\n {f"count--0[]" if user.guild_permissions.manage_channels or user.guild_permissions.manage_messages else ""}\n")
    with open(f"{interaction.guild.name}/sv_data.npthy", "a+") as ab:
        ab.seek(0)
        ab.write(f"name--{interaction.guild.name}[]\ndescription--{interaction.guild.description}[]\nID--{", ".join(format(ord(char), "08b") for char in str(interaction.guild.id))}[]\nowner--{interaction.guild.owner.name if interaction.guild.owner else 'Unknown'}[]\nowner_id--{", ".join(format(ord(char), "08b") for char in str(interaction.guild.owner_id))}[]\nmembers--{interaction.guild.member_count}[]\ncreated--{interaction.guild.created_at}[]\nverification_level--{interaction.guild.verification_level}[]\nboosts--{interaction.guild.premium_subscription_count}[]\nboost level--{interaction.guild.premium_tier}[]\nhc--{len([m for m in interaction.guild.members if not m.bot])}[]\nbc--{len([m for m in interaction.guild.members if m.bot])}[]\nchannels--{len(interaction.guild.channels)}[]\nroles--{len(interaction.guild.roles)}[]\nemojis--{len(interaction.guild.emojis)}[]\nstickers--{len(interaction.guild.stickers)}[]\nbfa--fs[]\nvc--{len(interaction.guild.voice_channels)}[]\nfeatures--{", ".join(ft for ft in interaction.guild.features)}\nverification-level--{interaction.guild.verification_level}[]")
    return await interaction.followup.send(content="Audit completed. Use the fetch commands to retrieve user data.", ephemeral=True)
@bot.tree.command(name="dm", description="Send a direct message to a user")
async def dm(interaction: discord.Interaction, user: discord.Member, message: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    await user.send(message)
    return await interaction.response.send_message(content=f"Message sent to {user.name} successfully. Dw they won't find out :smirk:", ephemeral=True)
@bot.tree.command(name="draw", description="Draw simple vector images")
async def draw(interaction: discord.Interaction, width: int, height: int, shape_width: int, color: str, bg_color: str, private: bool, shape: str):
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    svg_path = shape
    path = parse_path(svg_path)
    points = [
        (int(p.real), int(p.imag))
        for p in [path.point(t/100) for t in range(101)]
    ]
    draw.line(points, fill=color, width=shape_width)
    img.save(f"{interaction.user.name}-output.png")
    await interaction.response.send_message(content="Image drawn successfully", file=discord.File(f"{interaction.user.name}-output.png"), ephemeral=True if private else False)
    time.sleep(5)
    os.remove(f"{interaction.user.name}-output.png")

@bot.tree.command(name="snipe", description="Snipe the last deleted message in the channel")
async def snipe(interaction: discord.Interaction):
    if interaction.channel.id not in snipes:
        return await interaction.response.send_message(content="There are no recently deleted messages in this channel", ephemeral=True)
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    message = snipes[interaction.channel.id]
    embed = discord.Embed(description=message.content, timestamp=message.created_at)
    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
    await interaction.response.send_message(embed=embed, ephemeral=True)
@bot.tree.command(name="retrieve", description="Retrieve original messages (meant to be usede by admins ONLY)")
async def retrieve(interaction: discord.Interaction, message_id: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    data = edits.get(int(message_id))
    if not data:
        with open(f"{interaction.guild.name}/users/{interaction.user.name}.npthy", "a+") as ro:
            lines = ro.readlines()
            for i, li, in enumerate(lines):
                if li.startswith("count--"):
                    count = int(li.split("--")[1].split("[]")[0])
                    lines[i] = f"count--{count + 1}[]"
                    ro.seek(0)
                    ro.writelines(lines)
        return await interaction.response.send_message(content="This message was never edited :unamused:. Continue like this and you'll lose access to these commands", ephemeral=True)
    
    (before, after) = data
    embed = discord.Embed(title=f"{before.author}'s message", description=f"**Before:** {before.content}\n**After:** {after.content}", timestamp=after.created_at)
    return await interaction.response.send_message(embed=embed, ephemeral=True)
@bot.tree.command(name="rescou", description="Reset an admin's offense count")
async def rescou(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(content="You do not have permission to use this command", ephemeral=True)
    with open(f"{interaction.guild.name}/users/{interaction.user.name}.npthy", "r") as r:
        lines = r.readlines()
        for i, li, in enumerate(lines):
            if li.startswith("count--"):
                count = int(li.split("--")[1].split("[]")[0])
                if count >= 3:
                    return await interaction.response.send_message(content=f"You cannot use this command, as you have too many offenses yourself", ephemeral=True)
    if user.name == interaction.user.name:
        return await interaction.response.send_message(content="You cannot reset your own offense count :unamused:", ephemeral=True)            
    with open(f"{interaction.guild.name}/users/{user.name}.npthy", "a+") as ro:
        lines = ro.readlines()
        for i, li, in enumerate(lines):
            if li.startswith("count--"):
                lines[i] = f"count--0[]"
                ro.seek(0)
                ro.writelines(lines)
    return await interaction.response.send_message(content=f"{user.name}'s offense count has been reset", ephemeral=True)
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(str(token))