import nextcord
from nextcord.ext import commands
import datetime
import humanfriendly
import nextwave


intents = nextcord.Intents.all()
intents.members = True
command_prefix = '!'

bot = commands.Bot(command_prefix, intents = intents)
bot.remove_command('help')

class ControlPanel(nextcord.ui.View):
    def __init__(self, vc, ctx):
        super().__init__()
        self.vc = vc
        self.ctx = ctx

    @nextcord.ui.button(label="Продолжить/Пауза", style=nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("Введи команду, чтобы использовать конпки", ephemeral=True)
        for child in self.children:
            child.disabled = False
        if self.vc.is_paused:
            await self.vc.resume()
            await interaction.message.edit(content="Продолжаю", view=self)
        else:
            await self.vc.pause()
            await interaction.message.edit(content="Пауза", view=self)

    @nextcord.ui.button(label="Плейлист", style=nextcord.ButtonStyle.blurple)
    async def queue(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("Введи команду, чтобы использовать конпки", ephemeral=True)
        for child in self.children:
            child.disabled = False
        button.disabled = True
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("Плейлист пустой", ephemeral=True)
    
        em = nextcord.Embed(title="Плейлист")
        queue = self.vc.queue.copy()
        song_count = 0

        for song in queue:
            song_count += 1
            em.add_field(name = f"Песня номер {song_count}", value=f"'{song.title}'")
        await interaction.message.edit(embed=em, view=self)
    
    @nextcord.ui.button(label="Скип", style=nextcord.ButtonStyle.blurple)
    async def skip(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("Введи команду, чтобы использовать конпки", ephemeral=True)
        for child in self.children:
            child.disabled = False
        button.disabled = True
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("Плейлист пустой", ephemeral=True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            await interaction.message.edit(content=f"Сейчас играет '{next_song}'", view=self)
        except Exception:
            return await interaction.response.send_message("Плейлист пустой", ephemeral=True)

    @nextcord.ui.button(label="Дисконект", style=nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("Введи команду, чтобы использовать конпки", ephemeral=True)
        for child in self.children:
            child.disabled = True
        
        await self.vc.disconnect()
        await interaction.message.edit(content="Я ушел за пивом", view=self)

@bot.event
async def on_ready():
    print("Бот включён")
    bot.loop.create_task(node_connect())

@bot.event
async def nextwave_ready(node:nextwave.Node):
    print(f"Node {node.identifier} готов")
async def node_connect():
    await bot.wait_until_ready()
    await nextwave.NodePool.create_node(bot=bot, host='n1.lavalink.milrato.com', port=3350, password='discord.gg/milrato')

@bot.event
async def track_end(player: nextwave.Player, track: nextwave.Track, reason):
    ctx = player.ctx
    vc: player = ctx.voice_client

    if vc.loop:
        return await vc.play(track)

    next_song = vc.queue.get()
    await vc.play(next_song)
    await ctx.send(f"Сейчас я поставил {next_song.title}")

@bot.command()
async def hello(ctx):
    await ctx.send("Салам Олейкум братишка как ты, че ты, где ты?")

@bot.command()
async def info(ctx):
    await ctx.send("Привет я бот Bavlin, я могу управлять музыкой и не только. \n А если у тебя роль 'админ', или выше, то с моей помощью ты можешь даже наказывать людей :D")

@bot.command()
async def help(ctx):
    await ctx.send("Мои команды: \n\n !hello - приветсвие \n !info - информация обо мне \n !play - музыка \n !pause - пауза \n !resume - продолжить \n !stop - прекращения проигрывания \n !disconnect - отключение из войса \n !loop - повтор трека \n !queue - плейлист \n !skip - пропуск текущей песни \n !panel - панель управления музыкой \n !adminhelp - список доп.команд(только для админов)")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def adminhelp(ctx):
    await ctx.send("Команды для админов: \n\n !timeout - наказание \n !untimeout - снять наказание")

@bot.command()
async def panel(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я буду управлять тем, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    if not vc.is_playing():
        return await ctx.send("Сначала включи какой нибудь трек")
    
    em = nextcord.Embed(title="Панель управления", description="Управляй ботом с помощью конопок ниже")
    view = ControlPanel(vc, ctx)
    await ctx.send(embed=em, view=view)
    
@bot.command()
async def play(ctx: commands.Context, *, search:nextwave.YouTubeMusicTrack):
    if not ctx.voice_client:
        vc: nextwave.Player = await ctx.author.voice.channel.connect(cls=nextwave.Player)
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    elif not ctx.author.voice == ctx.me.voice:
        return await ctx.send("Ну ты еще на другой сервер уйди блять")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    if vc.queue.is_empty and vc.is_playing:
        await vc.play(search)
        await ctx.send(f"Сейчас я поставил {search.title}")
    else:
        await vc.play.put_wait(search)
        await ctx.send(f"Добавил {search.title} в плейлист")
    
    vc.ctx = ctx
    setattr(vc, "loop", False)

@bot.command()
async def pause(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    await vc.pause()
    await ctx.send("Пауза нахуй")

@bot.command()
async def resume(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    await vc.resume()
    await ctx.send("Пауза идет нахуй")

@bot.command()
async def skip(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    try:
        vc.queue.get()
    except nextwave.QueueEmpty:
        return await ctx.send("Как я по твоему должен пропустить трек, если его нет блять?")
    
    await vc.stop()
    await ctx.send("Застопил музыку")

@bot.command()
async def stop(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    await vc.stop()
    await ctx.send("Все ебать, застопил музыку")

@bot.command()
async def disconnect(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    await vc.disconnect()
    await ctx.send("Я ушел за пивом")

@bot.command()
async def loop(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    vc: nextwave.Player = ctx.voice_client  
    if not vc.is_playing():
        return await ctx.send("Ну ты совсем дебил? Как я повторю то, чего нет?")
    try:
        vc.loop *= True
    except:
        setattr(vc, "loop", False)
    if vc.loop:
        return await ctx.send("Режим попугая включен")
    else:
        return await ctx.send("Режим попугая выключен")

@bot.command()
async def queue(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("Ты шо дядя, ёбу дал? Как я остановлю то, чего нет?")
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.send("Ты блять, хуйло кожаное, в войсе никого нет, кому я буду музыку ставить?")
    elif not ctx.autor.voice == ctx.me.voice:
        return await ctx.send("Ну ты еще на другой сервер уйди блять")
    else:
        vc :nextwave.Player = ctx.voice_client
    
    if vc.queue.is_empty:
        return await ctx.send("Плейлист пустой")
    
    em = nextcord.Embed(title="Плейлист")
    queue = vc.queue.copy()
    song_count = 0
    for song in queue:
        song_count += 1
        em.add_field(name = f"Песня номер {song_count}", value=f"'{song.title}'")
    
    return await ctx.send(embed=em)


@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: nextcord.Member, time, *, reason):
    time = humanfriendly.parse_timespan(time)
    await member.edit(timeout=nextcord.utils.utcnow()+datetime.timedelta(seconds=time))
    await ctx.send(f"{member.mention} наказан на {time} секунд потому, что {reason}")

@bot.command()
async def untimeout(ctx, member: nextcord.Member, *, reason):
    await member.edit(timeout=None)
    await ctx.send(f"Наказание с {member.mention} снято потому, что {reason}")


bot.run('MTAzNTY1OTE0NzI2MzM0NDY2MA.GvV66P.I-iGDkUf_6XOeG1JmJ3O54NrjKsmQvBG-Nzsn4')
