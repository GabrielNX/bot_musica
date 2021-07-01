import asyncio
import youtube_dl
import pafy
import discord
from discord.ext import commands
import ctypes
import ctypes.util
 
print("ctypes - Find opus:")
a = ctypes.util.find_library('opus')
print(a)
 
print("Discord - Load Opus:")
b = discord.opus.load_opus(a)
print(b)
 
print("Discord - Is loaded:")
c = discord.opus.is_loaded()
print(c)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="#", intents=intents, description="~")

#Status do bot no console
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'| #ajuda'))

    print(f"{bot.user.name} On-line!.")

#Classe, config os comandos.
class BotMusica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:   #setando a fila em uma lista. limitar em 10 músicas.
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            ctx.voice_client.stop()
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])   #Checar a fila.
            self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):    #Procurar as músicas
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        url = pafy.new(song).getbestaudio().url    #Tocar a música e setar o recurso do volume.
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5
    
    #Comandos: ajuda. Priorizar: Entrar, sair, play, procurar, fila, skip. Arrumar volume? talves...

    @commands.command()
    async def ajuda(self, ctx):
        self.embed = discord.Embed(title="GAMER'S MUSIC | 🤖",description="🔹🔹 LISTA DE COMANDOS 🔹🔹", color=0xeee657)
        self.embed.add_field(name='DIGITE: join',value='**EX: join** `O bot ira entrar no canal de voz.` ```OBS: Antes de fazer o comando, você deve está no canal primeiro!```', inline=False)
        self.embed.add_field(name='DIGITE: play',value='**EX: play <nome da música>** `O bot ira tocar a música.` ```OBS: Veja se o nome música foi digitada corretamente.```', inline=False)
        self.embed.add_field(name='DIGITE: sair',value='**EX: sair** `O bot ira se desconectar do canal de voz.` ```OBS: Não existe o comando stop, sair faz com que ele saia do canal de voz.```', inline=False)
        self.embed.add_field(name='DIGITE: procurar',value='**EX: procurar <link da música>** `Essa é uma alternativa para procurar músicas específicas.` ```OBS: O link tem que ser somente o do youtube!```', inline=False)
        self.embed.add_field(name='DIGITE: fila',value='**EX: fila** `O bot mostra a fileira de música.` ```OBS: O bot pode enfileirar até 10 músicas!```', inline=False)
        self.embed.add_field(name='DIGITE: skip',value='**EX: skip** `O bot ira pular a música atual para a próxima música da fila` ```OBS: Uma votação é feita e ela dura 15 segundos!```', inline=False)
        self.embed.add_field(name='DIGITE: volume',value='**EX: volume** `O bot ira setar o volume definido.` ```OBS: O volume tem o limite entre 0 a 100.```', inline=False)

        await ctx.message.delete()
        await ctx.send(embed=self.embed)

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("Você precisa está em um canal de voz! depois digite #join")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.author.voice.channel.connect()

    @commands.command()
    async def sair(self, ctx):
        if ctx.voice_client is not None:
            await ctx.send("Okay, bot de música desconectado.")
            return await ctx.voice_client.disconnect()
            
        await ctx.send("Não estou conectado em um canal de voz.")

    @commands.command()
    async def play(self, ctx, *, song=None):

        if song is None:
            return await ctx.send("Você deve incluir uma música para tocar.")

        if ctx.voice_client is None:
            return await ctx.send("Devo estar em um canal de voz para tocar uma música.")

        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Procurando música, isso pode levar alguns segundos.")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Não consegui encontrar a música fornecida, tente usar meu comando de pesquisa. Digite !procurar.")

            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"No momento, estou reproduzindo uma música, esta música foi adicionada à fila na posição: {queue_len+1}.")

            else:
                return await ctx.send("Desculpe, só posso enfileirar até 10 músicas, aguarde a música atual terminar.")

        await self.play_song(ctx, song)
        await ctx.send(f"Tocando agora: {song}")

    @commands.command()  #Comando procurar, caso a pesquisa de música no play não seja de primeira.
    async def procurar(self, ctx, *, song=None):
        
        if song is None: return await ctx.send("Você se esqueceu de incluir uma música para pesquisar.")

        await ctx.send("Procurando música, isso pode levar alguns segundos.")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Resultados para '{song}':", description="*Você pode usar estes URLs para tocar uma música exata se a que você deseja não for o primeiro resultado.*\n", colour=discord.Colour.red())
        
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Exibindo o primeiro {amount} resultado.")
        await ctx.send(embed=embed)

    @commands.command()
    async def fila(self, ctx):

        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("Atualmente não há músicas na fila.")

        embed = discord.Embed(title="Fila de músicas", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text=f"Musicas na fila agora: {i}, obs: A que está tocando também conta. :D")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):

        if ctx.voice_client is None:
            return await ctx.send("Eu não estou tocando nenhuma música.")

        if ctx.author.voice is None:
            return await ctx.send("Você não está conectado a nenhum canal de voz.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("Atualmente não estou tocando nenhuma música para você.")

        poll = discord.Embed(title=f"Vote para pular música de - {ctx.author.name}#{ctx.author.discriminator}", description="**80% do canal de voz deve votar para pular para que passe para proxima música.**", colour=discord.Colour.blue())
        poll.add_field(name="Pular", value=":white_check_mark:")
        poll.add_field(name="Manter", value=":no_entry_sign:")
        poll.set_footer(text="A votação termina em 15 segundos.")

        poll_msg = await ctx.send(embed=poll)
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705")
        await poll_msg.add_reaction(u"\U0001F6AB")
        
        await asyncio.sleep(15)

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% dos que estão na call
                skip = True
                embed = discord.Embed(title="skip bem sucedido", description="***A votação para pular a música atual foi bem-sucedida, pulando agora.***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Falha ao pular música", description="*A votação para pular a música atual falhou.*\n\n**A votação falhou, a votação requer pelo menos 80% dos membros para pular.**", colour=discord.Colour.red())

        embed.set_footer(text="A votação acabou.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)
    
    @commands.command()
    async def volume(self, ctx, volume:int):

        if ctx.voice_client is None:
            return await ctx.send("Eu preciso está no canal de voz para usar o comando volume.")
        
        if volume < 0 or volume > 100:
            return await ctx.send("Defina um volume entre 0 a 100.")
        
        ctx.voice_client.source.volume = volume/100
        await ctx.send(f"Volume definido para: {volume}")

async def setup():  #Buffering
    await bot.wait_until_ready() 
    bot.add_cog(BotMusica(bot))

bot.loop.create_task(setup()) #Loops e tarefas
bot.run("ODU3MDMxMTg4MzkxOTE5NjI3.YNJqfg.Ky6OAjzLH7WUZNYW5kYPDGNZtks")
