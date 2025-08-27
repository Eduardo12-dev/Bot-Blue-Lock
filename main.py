import discord

from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ui import View
import random
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

dono_id = 765241423003123773
ID_CANAL_LOGS = 1267656568451764259 

# ---------------- Persistência em JSON ----------------
ARQUIVO = "jogadores.json"

def carregar_dados():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_dados():
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=4)

jogadores = carregar_dados()

atributos_disponiveis = [
    "Finalizacao", "Drible", "Velocidade", "Fisico",
    "Passe", "Roubo", "Dominio", "Reflexo", "Agilidade", "Q.I"
]

# ---------------- Garantia de Estrutura ----------------
def get_jogador(user_id: str):
    if user_id not in jogadores:
        jogadores[user_id] = {
            "pontos": 0,
            "atributos": {attr: 0 for attr in atributos_disponiveis},
            "imagem": None,
            "cor": 0x1ABC9C
        }
    else:
        if "pontos" not in jogadores[user_id]:
            jogadores[user_id]["pontos"] = 0
        if "atributos" not in jogadores[user_id]:
            jogadores[user_id]["atributos"] = {attr: 0 for attr in atributos_disponiveis}
        else:
            for attr in atributos_disponiveis:
                jogadores[user_id]["atributos"].setdefault(attr, 0)
        if "imagem" not in jogadores[user_id]:
            jogadores[user_id]["imagem"] = None
        if "cor" not in jogadores[user_id]:
            jogadores[user_id]["cor"] = 0x1ABC9C

    return jogadores[user_id]

# ---------------- Função de Embed ----------------
def criar_embed_status(user):
    jogador = get_jogador(str(user.id))
    embed = discord.Embed(
        description=(
            "*__✦ ⎯⎯⎯⎯⎯⎯⎯⎯  ・純粋悪・⎯⎯⎯⎯⎯⎯⎯⎯⎯  ✦__*\n\n" +
            "\n".join([
                f" **__ıllı﹕界〘`{emoji}`〙{nome}__﹔ ﹒*`{jogador['atributos'].get(nome, 0)}`* **"
                for nome, emoji in zip(
                    atributos_disponiveis,
                    ["💥", "🪄", "⚡", "💪", "🥏", "🚫", "⚾", "👀", "🧤", "🧠"]
                )
            ]) + "\n\n"
            "ㅤ__**︶︶︶︶︶︶︶◜`🌿`◞︶︶︶︶︶︶︶**__\n"
            f"**੭ᶻz︐枝﹒__𝐏ontos 𝐃isponiveis:  `{jogador['pontos']}`__﹐໑ ` 🥀 `︐あৎ**\n"
            "*__✦ ⎯⎯⎯⎯⎯⎯⎯⎯  ・純粋悪・⎯⎯⎯⎯⎯⎯⎯⎯⎯  ✦__*"
        ),
        color=jogador.get("cor", 0x1ABC9C)
    )

    if jogador.get("imagem"):
        embed.set_image(url=jogador["imagem"])

    return embed

# ---------------- Dropdown ----------------
class AtributoDropdown(discord.ui.Select):
    def __init__(self, jogador_id):
        self.jogador_id = jogador_id
        options = [discord.SelectOption(label=attr, value=attr) for attr in atributos_disponiveis]
        super().__init__(placeholder="Selecione um atributo", options=options)

    async def callback(self, interaction: discord.Interaction):
        jogador = get_jogador(str(self.jogador_id))
        if jogador["pontos"] <= 0:
            await interaction.response.send_message("Você não tem pontos disponíveis!", ephemeral=True)
            return

        atributo = self.values[0]
        jogador["atributos"][atributo] += 1
        jogador["pontos"] -= 1
        salvar_dados()

        embed = criar_embed_status(interaction.user)
        await interaction.response.edit_message(embed=embed, view=StatusView(self.jogador_id))

# ---------------- Modal Imagem ----------------
class ImagemModal(discord.ui.Modal, title="Editar Imagem da Embed"):
    imagem = discord.ui.TextInput(label="URL da Imagem", style=discord.TextStyle.short)

    def __init__(self, jogador_id):
        super().__init__()
        self.jogador_id = jogador_id

    async def on_submit(self, interaction: discord.Interaction):
        jogadores[str(self.jogador_id)]["imagem"] = str(self.imagem)
        salvar_dados()
        embed = criar_embed_status(interaction.user)
        await interaction.response.edit_message(embed=embed, view=StatusView(self.jogador_id))

# ---------------- Modal Cor ----------------
class CorModal(discord.ui.Modal, title="Editar Cor da Faixa"):
    cor = discord.ui.TextInput(label="Cor em hexadecimal (ex: 0x1ABC9C)", style=discord.TextStyle.short)

    def __init__(self, jogador_id):
        super().__init__()
        self.jogador_id = jogador_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nova_cor = int(self.cor.value, 16)
            jogadores[str(self.jogador_id)]["cor"] = nova_cor
            salvar_dados()
            embed = criar_embed_status(interaction.user)
            await interaction.response.edit_message(embed=embed, view=StatusView(self.jogador_id))
        except:
            await interaction.response.send_message("Formato de cor inválido! Use o formato `0xHEXVALOR`", ephemeral=True)

# ---------------- View ----------------
class StatusView(discord.ui.View):
    def __init__(self, jogador_id):
        super().__init__(timeout=None)
        self.jogador_id = jogador_id
        self.add_item(AtributoDropdown(jogador_id))

    @discord.ui.button(label="Editar Imagem", style=discord.ButtonStyle.secondary, row=1)
    async def editar_imagem(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.jogador_id:
            await interaction.response.send_message("❌ Você não pode editar o status de outro jogador.", ephemeral=True)
            return
        await interaction.response.send_modal(ImagemModal(self.jogador_id))

    @discord.ui.button(label="Editar Cor", style=discord.ButtonStyle.secondary, row=1)
    async def editar_cor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.jogador_id:
            await interaction.response.send_message("❌ Você não pode editar o status de outro jogador.", ephemeral=True)
            return
        await interaction.response.send_modal(CorModal(self.jogador_id))

# ---------------- Comando STATUS ----------------
@bot.command()
async def status(ctx):
    user_id = str(ctx.author.id)
    get_jogador(user_id)
    salvar_dados()
    embed = criar_embed_status(ctx.author)
    await ctx.reply(embed=embed, view=StatusView(ctx.author.id))

# ---------------- Comando DISTRIBUIR ----------------
@bot.command()
async def distribuir(ctx, atributo: str, quantidade: int):
    user_id = str(ctx.author.id)
    jogador = get_jogador(user_id)

    atributo = atributo.capitalize()
    if atributo not in jogador["atributos"]:
        await ctx.reply("❌ Esse atributo não existe!")
        return

    if jogador['pontos'] < quantidade:
        await ctx.reply("❌ Você não tem pontos suficientes para distribuir.")
        return

    jogador["atributos"][atributo] += quantidade
    jogador['pontos'] -= quantidade
    salvar_dados()

    await ctx.reply(f"✅ Você adicionou **{quantidade} ponto(s)** em **{atributo}** com sucesso!")

# Função auxiliar para logar ações da staff
async def logar_acao(bot, mensagem):
    canal = bot.get_channel(ID_CANAL_LOGS)
    if canal:
        await canal.send(mensagem)

# ---------------- Comando ADICIONAR ----------------
@bot.command()
async def adicionar(ctx, membro: discord.Member, quantidade: int):
    if ctx.author.id != dono_id:
        await ctx.reply("❌ Apenas o dono do bot pode usar esse comando.")
        return

    jogador = get_jogador(str(membro.id))
    jogador["pontos"] += quantidade
    salvar_dados()

    await ctx.reply(f"✅ {quantidade} ponto(s) foram adicionados para {membro.mention}. Agora ele tem `{jogador['pontos']}` pontos disponíveis.")
    await logar_acao(bot, f"🟢 **{ctx.author}** adicionou **{quantidade} pontos** para {membro.mention}. Total agora: `{jogador['pontos']}`")

# ---------------- Comando REMOVER ----------------
@bot.command()
async def remover(ctx, membro: discord.Member, quantidade: int):
    if ctx.author.id != dono_id:
        await ctx.reply("❌ Apenas o dono do bot pode usar esse comando.")
        return

    jogador = get_jogador(str(membro.id))

    if jogador["pontos"] < quantidade:
        jogador["pontos"] = 0
    else:
        jogador["pontos"] -= quantidade

    salvar_dados()
    await ctx.reply(f"❌ {quantidade} ponto(s) foram removidos de {membro.mention}. Agora ele tem `{jogador['pontos']}` pontos disponíveis.")
    await logar_acao(bot, f"🔴 **{ctx.author}** removeu **{quantidade} pontos** de {membro.mention}. Total agora: `{jogador['pontos']}`")

# ---------------- Comando RESETAR ----------------
@bot.command()
async def resetar(ctx, membro: discord.Member):
    if ctx.author.id != dono_id:
        await ctx.reply("❌ Apenas o dono do bot pode usar esse comando.")
        return

    jogador = get_jogador(str(membro.id))

    # Soma todos os pontos investidos de volta
    pontos_totais = sum(jogador["atributos"].values())
    jogador["pontos"] += pontos_totais

    # Zera os atributos
    jogador["atributos"] = {attr: 0 for attr in atributos_disponiveis}
    salvar_dados()

    await ctx.reply(f"🔄 O status de {membro.mention} foi resetado. Ele agora tem `{jogador['pontos']}` pontos para redistribuir.")
    await logar_acao(bot, f"🟡 **{ctx.author}** resetou os atributos de {membro.mention}. Pontos devolvidos: `{pontos_totais}`")

@bot.event
async def on_ready():
    print("Bot inicializado com Sucesso")

@bot.command()
async def overall(ctx):
    jogador_id = ctx.author.id

    if jogador_id not in jogadores:
        await ctx.reply("❌ Você ainda não tem status criado. Use `!status` primeiro.")
        return

    status = jogadores[jogador_id]["atributos"]
    total = sum(status.values())
    overall_valor = total // 5

    if overall_valor >= 96:
        letra = "S"
        emoji = "🌟"
    elif overall_valor >= 85:
        letra = "A"
        emoji = "🔥"
    elif overall_valor >= 80:
        letra = "B"
        emoji = "💪"
    elif overall_valor >= 70:
        letra = "C"
        emoji = "⚽"
    elif overall_valor >= 60:
        letra = "D"
        emoji = "🌀"
    elif overall_valor >= 50:
        letra = "E"
        emoji = "📘"
    else:
        letra = "F"
        emoji = "💤"

    embed = discord.Embed(
        description=(
            f"## **「`📘`」Overall﹕利点﹕**"
            "_ _\n"
            "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n"
            f"**┃`📍`: Jogador: {ctx.author.mention}**\n"
            f"**┃`📊`: Overall: {overall_valor}**\n"
            f"**┃`🏆`: Categoria: {letra}**\n\n"
            "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n"
        ),
        color=0x1ABC9C
    )
    # Aqui você pode adicionar a imagem personalizada
    embed.set_image(url="https://media.discordapp.net/attachments/1267656568736972822/1391530695490539552/blue-lock-stats-v0-wzxfodh9cjee1.png?ex=686c3b73&is=686ae9f3&hm=52eaf02c716ff705fdd60d5520f5bda6ae4e05967314cad0e1126937ecabb5fa&=&format=webp&quality=lossless&width=552&height=412")  # Troque pelo link da imagem que você quer

    await ctx.reply(embed=embed)


@bot.command()
async def treinos(ctx: commands.Context):
    # Lista de desarmes com cor personalizada
    lista_treino = [
        {
            "title": "__*𑆠 ﹒︶꒡𝆹𝅥ﾞ﹑` 💪 `﹐Ꮺ﹒𝐓reinamento﹒︐﹒蓮﹑⾕*__",
            "barra" : "**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "*︶﹒`📖`ᝬ  一 説明,: O treino físico é uma parte essencial da preparação de qualquer jogador de futebol, especialmente para quem busca alto desempenho. Ele tem como objetivo melhorar a força, velocidade, resistência, explosão muscular e controle corporal habilidades indispensáveis para quem quer dominar dentro de campo.*⁠",
            "barra" : "**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "funcionamento" : "## ︐ lı__`✨`__৶﹕__𝐂__omo __𝐅__unciona? :﹑結﹒",
            "lista-treino" : '—﹒で﹒ `❗`  ꒱﹒ *Existem Diversos Tipos de Treino:*\n\n > ・ ``🎲``  ᝬ﹒ **!Treino_Leve** \n > ・ ``🎲``  ᝬ﹒ **!Treino_Dupla** \n > ・ ``🎲``  ᝬ﹒ **!Treino_Intenso** ',
            "imagem": "Bot/imagens/lista_treinos.jpg",
            "cor": 0x0a5dff  # Vermelho para erro
        },
    ]

    treinos = random.choice(lista_treino)

    # Usa a cor definida no dicionário
    minha_embed_treinos = discord.Embed(color=treinos['cor'])
    minha_embed_treinos.description = (
        f"{treinos['title']}"
        f"\n\n"
        f"{treinos['barra']}"
        f"\n\n"
        f"{treinos['info']} ๑﹕⁠﹒*"
        f"\n\n"
        f"{treinos['barra']}"
        f"\n\n"
        f"{treinos['funcionamento']}"
        f"\n\n"
        f"{treinos['lista-treino']}"
    )

    imagem = discord.File(treinos['imagem'], filename="treinos.jpg")
    minha_embed_treinos.set_image(url="attachment://treinos.jpg")

    await ctx.reply(embed=minha_embed_treinos, file=imagem)

@bot.command()
@commands.cooldown(1, 21600, BucketType.user)  # 6 horas
async def treino_leve(ctx: commands.Context):

    embed_1 = discord.Embed(
        title="# 𑆠 ﹒︶꒡𝆹𝅥ﾞ﹑` 😴 `﹐Ꮺ﹒𝐓reinamento 𝐋eve﹒︐﹒蓮﹑⾕",
        color=0xa20b44
    )

    treino_leve_lista = [
        {
            "barra": "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "funcionamento": "## ︐ lı__`✨`__৶﹕__𝐂__omo __𝐅__unciona? :﹑結﹒",
            "info": " —﹒で﹒ {Aviso}  ꒱﹒ *Realize uma Ação Simples de **__400 Caracteres.__***\n\n  —﹒で﹒ {Aviso}  ꒱﹒ *E em Seguida de um Lembrete do Treino com um tempo de 2 Horas.*⁠",
            "Recompensa": '## ︐ lı__`✨`__৶﹕__𝐑ecompensa__ :﹑結﹒',
            "imagem": "Bot/imagens/treino_leve.jpg",
            "cor": 0xa20b44
        },
    ]

    treino_leve = random.choice(treino_leve_lista)

    Aviso = "<a:Aviso:1386531866479300679>"
    info_formatada = treino_leve['info'].format(Aviso=Aviso)

    # Rolagem do dado (1d5)
    pontos_ganhos = random.randint(1, 5)

    minha_embed_treino_leve = discord.Embed(color=treino_leve['cor'])
    minha_embed_treino_leve.description = (
        f"{treino_leve['barra']}\n"
        f"{treino_leve['funcionamento']}\n\n"
        f"{info_formatada}\n\n"
        f"{treino_leve['barra']}\n"
        f"{treino_leve['Recompensa']}\n\n"
        f"—﹐ർ  ` ❗ `﹒ __**Recebeu {pontos_ganhos} Pontos.**__ **﹒⟡**"
    )

    imagem = discord.File(treino_leve['imagem'], filename="treinos.jpg")
    minha_embed_treino_leve.set_image(url="attachment://treinos.jpg")

    await ctx.reply(embeds=[embed_1, minha_embed_treino_leve], file=imagem)

@bot.command()
@commands.cooldown(1, 86400, BucketType.user)  # 1 vez por dia
async def treino_dupla(ctx: commands.Context):

    embed_1 = discord.Embed(
        title="# 𑆠 ﹒︶꒡𝆹𝅥ﾞ﹑` 🌟 `﹐Ꮺ﹒𝐓reinamento 𝗗upla﹒︐﹒蓮﹑⾕",
        color=0x76c2e3
    )

    # Lista de desarmes com cor personalizada
    treino_dupla_lista = [
        {
            "barra" : "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "funcionamento" : "## ︐ lı__`✨`__৶﹕__𝐂__omo __𝐅__unciona? :﹑結﹒",
            "info": " —﹒で﹒ {Aviso}  ꒱﹒ *Realize uma Ação Simples de **__600 Caracteres.__***\n\n  —﹒で﹒ :{Aviso}  ꒱﹒ *E em Seguida de um Lembrete do Treino com um tempo de 5 Horas.* \n\n ⁠—﹒で﹒ :{Aviso}  ꒱﹒ *Devem se realizar um treino 1v1 ou em times, e apos isso cada um de time devera dar o roll, e então irão soma-los para __cada equipe__*",
            "barra" : "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "Recompensa" : '## ︐ lı__`✨`__৶﹕__𝐑ecompensa__ :﹑結﹒',
            "Points" : '—﹐ർ  ` ❗ `﹒ __**Recebeu (1d5+1) Pontos**.__ **﹒⟡**',
            "imagem": "Bot/imagens/treino_dupla.jpg",
            "cor": 0x76c2e3  # Vermelho para erro
        },
    ]

    treino_dupla = random.choice(treino_dupla_lista)

    # Usa a cor definida no dicionário
    Aviso = "<a:Aviso:1386531866479300679>"
    info_formatada = treino_dupla['info'].format(Aviso=Aviso)

    minha_embed_treino_dupla = discord.Embed(color=treino_dupla['cor'])
    minha_embed_treino_dupla.description = (
        f"{treino_dupla['barra']}"
        f"\n"
        f"{treino_dupla['funcionamento']}"
        f"\n\n\n"
        f"{info_formatada}"
        f"\n\n"
        f"{treino_dupla['barra']}"
        f"\n"
        f"{treino_dupla['Recompensa']}"
        f"\n\n"
        f"{treino_dupla['Points']}"
    )

    imagem = discord.File(treino_dupla['imagem'], filename="treinos.jpg")
    minha_embed_treino_dupla.set_image(url="attachment://treinos.jpg")

    await ctx.reply(embeds=[embed_1,minha_embed_treino_dupla], file=imagem)

@bot.command()
@commands.cooldown(1, 28800, BucketType.user)  # 8 horas
async def treino_intenso(ctx: commands.Context):

    embed_1 = discord.Embed(
        title="# 𑆠 ﹒︶꒡𝆹𝅥ﾞ﹑` 🔥 `﹐Ꮺ﹒𝐓reinamento 𝐈ntenso﹒︐﹒蓮﹑⾕",
        color=0x119a97
    )

    # Lista de desarmes com cor personalizada
    treino_intenso_lista = [
        {
            "barra" : "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "funcionamento" : "## ︐ lı__`✨`__৶﹕__𝐂__omo __𝐅__unciona? :﹑結﹒",
            "info": " —﹒で﹒ {Aviso}  ꒱﹒ *Realize uma Ação Simples de **__600 Caracteres.__***\n\n  —﹒で﹒ :{Aviso}  ꒱﹒ *E em Seguida de um Lembrete do Treino com um tempo de 5 Horas.* \n\n ⁠—﹒で﹒ :{Aviso}  ꒱﹒ *Devem se realizar um treino 1v1 ou em times, e apos isso cada um de time devera dar o roll, e então irão soma-los para __cada equipe__*",
            "barra" : "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "requisitos" : "## ︐ lı__`❓`__৶﹕__𝐑__equisitos :﹑結﹒",
            "req" : "—﹒で﹒ {Aviso}  ꒱﹒ *Necessario ter Level **__40__*** \n\n —﹒で﹒ {Aviso}  ꒱﹒ *Estar no Arco **__Blue Lock x Sub-20__*** ",
            "barra" : "**₊★⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯๑ 〃ゆゆ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯★₊**",
            "Recompensa" : '## ︐ lı__`✨`__৶﹕__𝐑ecompensa__ :﹑結﹒',
            "Points" : '—﹐ർ  ` ❗ `﹒ __**Recebeu (1d6+3) Pontos**.__ **﹒⟡**',
            "imagem": "Bot/imagens/treino_intenso_nagi.jpg",
            "cor": 0x119a97  # Vermelho para erro
        },
    ]

    treino_intenso = random.choice(treino_intenso_lista)

    # Usa a cor definida no dicionário
    Aviso = "<a:Aviso:1386531866479300679>"
    info_formatada = treino_intenso['info'].format(Aviso=Aviso)
    req_formatada = treino_intenso['req'].format(Aviso=Aviso)

    minha_embed_treino_intenso = discord.Embed(color=treino_intenso['cor'])
    minha_embed_treino_intenso.description = (
        f"{treino_intenso['barra']}"
        f"\n"
        f"{treino_intenso['funcionamento']}"
        f"\n\n\n"
        f"{info_formatada}"
        f"\n\n"
        f"{treino_intenso['barra']}"
        f"\n"
        f"{treino_intenso['requisitos']}"
        f"\n\n"
        f"{req_formatada}"
        f"\n\n"
        f"{treino_intenso['barra']}"
        f"\n"
        f"{treino_intenso['Recompensa']}"
        f"\n\n"
        f"{treino_intenso['Points']}"
    )

    imagem = discord.File(treino_intenso['imagem'], filename="treinos.jpg")
    minha_embed_treino_intenso.set_image(url="attachment://treinos.jpg")

    await ctx.reply(embeds=[embed_1,minha_embed_treino_intenso], file=imagem)

@bot.command()
@commands.has_permissions(administrator=True)
async def remover_pontos(ctx, membro: discord.Member, quantidade: int):
    jogador = membro.id

    if jogador not in jogadores:
        await ctx.reply("❌ Este jogador ainda não possui um perfil de status.")
        return

    if jogadores[jogador]['pontos'] < quantidade:
        await ctx.reply("❌ O jogador não possui pontos suficientes para remover essa quantidade.")
        return

    jogadores[jogador]['pontos'] -= quantidade
    await ctx.reply(f"✅ Você removeu **{quantidade} pontos** de {membro.mention}.")

    dono = await bot.fetch_user(dono_id)
    await dono.send(f"❗ LOG | {ctx.author.mention} removeu **{quantidade} pontos** de {membro.mention} no servidor {ctx.guild.name}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def adicionar_pontos(ctx, membro: discord.Member, quantidade: int):
    jogador = membro.id

    if jogador not in jogadores:
        jogadores[jogador] = {
            "finalizacao": 0,
            "drible": 0,
            "velocidade": 0,
            "fisico": 0,
            "passe": 0,
            "roubo": 0,
            "defesa": 0,
            "pontos": 0,
            "imagem": None,
            "cor": 0x1ABC9C
        }

    jogadores[jogador]['pontos'] += quantidade
    await ctx.reply(f"✅ Você adicionou **{quantidade} pontos** para {membro.mention}.")

    dono = await bot.fetch_user(dono_id)
    await dono.send(f"✅ LOG | {ctx.author.mention} adicionou **{quantidade} pontos** para {membro.mention} no servidor {ctx.guild.name}.")


@bot.command()
async def formulas_defensivas(ctx: commands.Context):

    embed_1 = discord.Embed(
        title="# *** 𓂃 ͡ ﹐✨ , ⺌ Fórmulas Defensivas , 、カﾞ！***",
        color=0x652156
    )

    # Lista de desarmes com cor personalizada
    formulas_defensivas_lista = [
        {
            "barra" : "**⋘══════∗ {•『 `⚽` 』•} ∗══════ ⋙**",
            "especificacao" : "## **– ම│𝐒obre; Defensivas ꒰`🛡️`꒱** ,",
            "teto": "**╭-・ᘒﾟ`🧟` ⫘ ———————— ・⁐ ╮**",
            "formulas" : "**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n**┃ 一﹒オ﹔Snake Defense**\n",
            "faixa": "**╰┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈➤**",
            "barra" : "**⋘══════∗ {•『 `⚽` 』•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/formulas_defensivas.jpg",
            "cor": 0x652156  # Vermelho para erro
        },
    ]

    formulas_defensivas = random.choice(formulas_defensivas_lista)

    minha_embed_formula_defensiva = discord.Embed(color=formulas_defensivas['cor'])
    minha_embed_formula_defensiva.description = (
        f"{formulas_defensivas['barra']}"
        f"\n"
        f"{formulas_defensivas['especificacao']}"
        f"\n\n\n"
        f"{formulas_defensivas['teto']}"
        f"\n"
        f"{formulas_defensivas['formulas']}"
        f"\n"
        f"{formulas_defensivas['faixa']}"
        f"\n\n"
        f"{formulas_defensivas['barra']}"
    )

    imagem = discord.File(formulas_defensivas['imagem'], filename="formulas_defensivas.jpg")
    minha_embed_formula_defensiva.set_image(url="attachment://formulas_defensivas.jpg")

    await ctx.reply(embeds=[embed_1,minha_embed_formula_defensiva], file=imagem)

@bot.command()
async def Roll_Fam(ctx: commands.Context):

    # Lista de desarmes com cor personalizada
    familia_lista = [
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Rensuke Kunigami** ( Kunigami Rensuke ? )國くに神がみ 練れんvocêすけ é um jogador do Blue Lock que jogou como volante central no Bastard München da Alemanha durante a Neo Egoist League, Ele é um atacante impulsivo cujo principal objetivo é se tornar o melhor atacante do mundo e, consequentemente, um super-herói do futebol.  .___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Finalização** & **+3** em **Fisico**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Kunigami_rensuke_familia2.gif",
            "cor": 0xf6750f  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Ranze Kurona** ( Kurona Ranze ? )黒くろ名な 蘭らん世ぜ é um candidato ao Blue Lock Project , que jogou como lateral-direito do Bastard München da Alemanha durante a Neo Egoist League .___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Velocidade** & **+3** em **Passe**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Kurona_familia.jpg",
            "cor": 0xb71f67  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Kenyu Yukimiya** (雪ゆき宮みや剣けん優ゆう, Yukimiya Kenyu ? ) é um candidato ao Blue Lock Project , que atualmente joga como lateral-esquerdo do alemão Bastard München durante a Neo Egoist League. Yukimiya, um atacante teimoso e altamente motivado que está acorrentado por uma doença ocular conhecida como neuropatia óptica , está lutando com tudo o que tem para se tornar o melhor atacante do mundo antes que seu tempo acabe. Quando apresentado pela primeira vez, ele ficou em 5º lugar durante a Terceira Seleção e mais tarde jogou como ala esquerdo na partida entre o Blue Lock Eleven e a seleção sub-20 do Japão.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Dribles** & **+3** em **Velocidade**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/yukimiya_familia.gif",
            "cor": 0xcf924d  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Tabito Karasu** (烏からす旅たび vocêと, Karasu Tabito ? ) é um candidato ao Blue Lock , que atualmente joga como meio-campista central do Paris X Gen da França durante a Liga Neo Egoísta. Quando apresentado pela primeira vez, ele ficou em 3º lugar durante a Terceira Seleção e mais tarde jogou como meio-campista defensivo na partida entre o Blue Lock Eleven e a seleção sub-20 do Japão.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Fisico** & **+3** em **Passe**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Karasu_familia.gif",
            "cor": 0x1147a7  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Zantetsu Tsurugi** (剣つる城ぎ 斬ざん鉄てつ, Tsurugi Zantetsu ? ) é um candidato ao Blue Lock Project , que atualmente joga como ala direito do Paris X Gen da França durante a Liga Neo Egoísta. Zantetsu é um avanço simples, mas rápido. Ao chegar pela primeira vez na Blue Lock , ele era membro do Time V durante a Primeira Seleção. Ele é um dos candidatos restantes do Blue Lock após a Segunda Seleção.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Velocidade** & **+3** em **Finalização**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Zantetsu_familia.jpg",
            "cor": 0xafc1e0  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Gurimu Igarashi** ( Igarashi Gurimu ? )五十e嵐がらし 栗ぐり夢... é um candidato ao Blue Lock Project , que atualmente joga como lateral direito do Bastard München , da Alemanha .___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+2** em Todos os **Atributos**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/igarashi_familia.jpg",
            "cor": 0xafc1e0  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Eita Otoya** (おと夜や影えい汰た, Otoya Eita ? ) é um candidato ao Blue Lock , que atualmente joga como lateral direito do FC Barcha da Espanha durante a Liga Neo Egoísta. Quando apresentado pela primeira vez, ele ficou em 4º lugar durante a Terceira Seleção e mais tarde jogou como ala direito e lateral-direito na partida entre o Blue Lock Eleven e a seleção sub-20 do Japão.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Velocidade** & **+3** em **Dribles**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Otoya_familia.gif",
            "cor": 0x41a711  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Aoshi Tokimitsu** (とき光みつ 青あお志し, Tokimitsu Aoshi ? ) é um candidato ao Blue Lock Project , que atualmente joga como meio-campista do Paris X Gen da França durante a Neo Egoist League. Tokimitsu é um atacante introvertido que, quando apresentado pela primeira vez, foi classificado como o terceiro jogador na Segunda Seleção e é um dos contendores restantes do Blue Lock após a Segunda Seleção.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Fisico** & **+3** em **Velocidade**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/tokimitsu_familia.gif",
            "cor": 0x41a711  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Gin Gagamaru** ((S)我が¦がíquoまる ⁇ ≈ん Gin Gagamaru¡NÉ?(S) é um contendor de Fechadura Azul‚que atuou como goleiro do Germany´s Bastardo München durante o Liga Neo Egoísta, e atualmente o faz para o Japão Sub-20.O.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+6** em **Agilidade**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/gagamaru_familia.gif",
            "cor": 0xdde3ec  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Nijiro Nanase** ( Nanase Nijirō ? )七ななnão... eue郎ろう é um candidato do Blue Lock , que atualmente joga como ala esquerdo do Paris X Gen da França .___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Passe** & **+3** em **Domínio**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Nanase_familia.gif",
            "cor": 0x83aaf1  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Jyubei Aryu** (蟻あ生りゅう 十じゅう兵べ衛え, Aryū Jūbē ? ) é um candidato ao Blue Lock Project , que atualmente joga pelo Ubers da Itália durante a Neo Egoist League. Aryu é um atacante alto, estiloso e excêntrico que, quando apresentado pela primeira vez, foi classificado como o segundo jogador na Segunda Seleção e começou como zagueiro central do Blue Lock Eleven contra o Japão Sub-20___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Reflexo** & **+3** em **Domínio**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Aryu_familia.gif",
            "cor": 0xdde3ec  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Yo Hiori** (氷ひ織おり 羊よう, Hiori Yō ? ) é um candidato ao Blue Lock , que atualmente joga como lateral direito do Bastard München durante a Neo Egoist League.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Passe** & **+3** em **Reflexo**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Hiori_familia.jpg",
            "cor": 0x3bc3f8  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Charles Chevalier (シャルル・シュバリエ, Sharuru Shubarie ) é um meio-campista que joga pelo Paris X Gen e participa do Blue Lock durante a Neo Egoist League. Charles é descrito como o coração de PXG devido às suas habilidades de passe de alto nível que atendem aos estilos de jogo de Rin e Shido. Charles também é treinado para ser o passador de Julian Loki , para que os dois se tornem os melhores jogadores do mundo lado a lado.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Passe** & **+3** em **Dribles**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Charles_familia.jpg",
            "cor": 0xffd979  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Jin Kiyora** ( Kiyora Jin ? ) 清 きよ 羅 ら 刃 じん é um candidato do Blue Lock , que jogou como lateral-esquerdo do Bastard München da Alemanha durante a Neo Egoist League .___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Domínio** & **+3** em **Passe**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Kiyora_familia.jpg",
            "cor": 0x0f0e0b  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Oliver Aiku** (オリヴァ・愛空アイク, Oriva Aiku ? ) é o ex-capitão e zagueiro da seleção sub-20 do Japão. Atualmente, ele joga como zagueiro do Ubers da Itália durante a Liga Neo Egoísta. Quando Aiku era criança, ele queria se tornar o melhor atacante do mundo, mas seu treinador e outros adultos mancharam seu sonho com a filosofia de “jogar para os outros”. Ele perdeu a vontade de se tornar o melhor atacante do mundo com o tempo, mas decidiu de todo o coração se tornar o melhor zagueiro do mundo, para irritar todos os adultos e treinadores que lhe disseram para jogar para os outros e se recusaram a ajudá-lo a perseguir seus próprios objetivos.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Reflexo** & **+3** em **Roubo**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Oliver_familia.gif",
            "cor": 0x5dc70a  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Ikki Niko** (に子こ 一い揮っき, Niko Ikki ? ) é um concorrente do Blue Lock. Ao chegar pela primeira vez no Blue Lock, ele era membro do Time Y durante a Primeira Seleção, e estava determinado a sobreviver ao Blue Lock com as habilidades que já possuía, mas depois de perder para Yoichi Isagi na Primeira Seleção, ele decidiu deixar de ser com medo e mudar para melhorar para que ele pudesse sobreviver ao Blue Lock. Começou como zagueiro do Blue Lock Eleven contra o Japão Sub-20 e atualmente é volante do Ubers durante a Neo Egoist League.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Roubo** & **+3** em **Reflexo**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Ikki_familia.gif",
            "cor": 0xcfb3ba  # Vermelho para erro
        },
        {

            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___**Hyoma Chigiri** (千ち切ぎり 豹ひょう馬ま, Chigiri Hyōma ? ) é um candidato ao Blue Lock , que atualmente joga como ala esquerdo do Manshine City da Inglaterra durante a Liga Neo Egoísta.___* ❜❜",
            "buffs": "╭೨`📚`੭ ៸៸﹒  ﹙__𝐁uff__﹚・什",
            "info1" : "╰：❝ *___**+5** em **Velocidade** & **+3** em **Dribles**___* ❜❜",
            "info2" : "╭೨`🤼`੭ ៸៸﹒  ﹙__𝐅amilia-𝐂omuns__﹚・冬中",
            "info3" : "╰：",
            "canal_id": 1402019361929035806,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Chigiri_familia.gif",
            "cor": 0xec446c  # Vermelho para erro
        },
    ]

    familia_escolhida = random.choice(familia_lista)

    minha_embed_familia_escolhida = discord.Embed(color=familia_escolhida['cor'])
    minha_embed_familia_escolhida.description = (
        f"\n\n"
        f"{familia_escolhida['descricao']}"
        f"\n"
        f"{familia_escolhida['informação']}"
        f"\n\n"
        f"{familia_escolhida['buffs']}"
        f"\n"
        f"{familia_escolhida['info1']}"
        f"\n\n"
        f"{familia_escolhida['info2']}"
        f"\n"
        f"{familia_escolhida['info3']} ❝***<#{familia_escolhida['canal_id']}>***❜❜"
        f"\n"
        f"{familia_escolhida['barra3']}"
    )

    imagem = discord.File(familia_escolhida['imagem'], filename="familia.gif")
    minha_embed_familia_escolhida.set_image(url="attachment://familia.gif")

    await ctx.reply(embeds=[minha_embed_familia_escolhida], file=imagem)

@bot.command()
async def porte(ctx: commands.Context):

    # Lista de desarmes com cor personalizada
    porte_lista = [
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Você nasceu **`Alto`**, São imponentes fisicamente e costumam se destacar em jogadas aéreas, disputas físicas e presença de área. Ideal para funções como pivô, zagueiro fixo ou centroavante de referência. e graças à sua altura, muitas empresas, de moda ou até times de esporte, o querem.  .___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1268767370969616509,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Aryu_jyubei_porte.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
                {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Você Nasceu **`Baixo`**, O porte Baixo representa jogadores com estatura mais baixa que a média, geralmente mais ágeis e explosivos. Apesar da limitação no alcance físico, esse porte compensa com velocidade, imprevisibilidade e proximidade com o solo.___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1268767370969616509,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Ikki_Niko_porte.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Você nasceu **`Magro`**,  ou seja pessoas que tem um físico menos avantajado que o resto, essas pessoas tem mais facilidade em sua velocidade e agilidade, os permitindo fazer coisas que pessoas maiores não conseguem.  .___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1268767370969616509,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Kaiser_porte.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Você nasceu **`Forte`**, São imponentes fisicamente e costumam ou seja pessoas que tem um físico mais musculoso do que o resto, essas pessoas tem mais facilidade em erguer pesos, e conseguem se manter firme no local com mais tranquilidade.___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1268767370969616509,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Kunigami_rensuke_porte.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
    ]

    porte_escolhido = random.choice(porte_lista)

    minha_embed_porte_escolhido = discord.Embed(color=porte_escolhido['cor'])
    minha_embed_porte_escolhido.description = (
        f"{porte_escolhido['descricao']}"
        f"\n"
        f"{porte_escolhido['informação']}"
        f"\n\n"
        f"{porte_escolhido['buffs']}"
        f"\n"
        f"{porte_escolhido['info1']} ❝***__<#{porte_escolhido['canal_id']}>__***❜❜"
        f"\n"
        f"{porte_escolhido['barra3']}"
    )

    imagem = discord.File(porte_escolhido['imagem'], filename="porte.gif")
    minha_embed_porte_escolhido.set_image(url="attachment://porte.gif")

    await ctx.reply(embeds=[minha_embed_porte_escolhido], file=imagem)

@bot.command()
async def perna_dominante(ctx: commands.Context):

    # Lista de desarmes com cor personalizada
    perna_lista = [
        {
            "barra1" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿╭・ ────────── ・ஜ・──────────・",
            "especificacao" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ ﻿_ _ ━──────≪✷≫──────━",
            "titulo" : "## _ _ _ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ _ _ ﻿**・୭`❗️`︰  ⇆・꒰ __Perna Dominante__ ꒰・**╯",
            "quebra" : "\n\n",
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Um jogador com **perna dominante esquerda**, ou canhoto, possui um controle e precisão superiores com a perna esquerda. Essa dominância natural favorece ações como passes, dribles e finalizações realizadas com maior eficácia do lado esquerdo do campo. Canhotos têm facilidade em realizar jogadas em ângulos difíceis para jogadores destros, tornando-se imprevisíveis e difíceis de marcar. Essa característica permite que o jogador tenha maior confiança e precisão ao chutar, passar e conduzir a bola com a perna esquerda, fazendo com que explore melhor o flanco esquerdo e crie oportunidades únicas em campo.___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1407407066024247436,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Perna_canhota.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "barra1" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿╭・ ────────── ・ஜ・──────────・",
            "especificacao" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ ﻿_ _ ━──────≪✷≫──────━",
            "titulo" : "## _ _ _ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ _ _ ﻿**・୭`❗️`︰  ⇆・꒰ __Perna Dominante__ ꒰・**╯",
            "quebra" : "\n\n",
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Um jogador com **perna dominante esquerda**, ou canhoto, possui um controle e precisão superiores com a perna esquerda. Essa dominância natural favorece ações como passes, dribles e finalizações realizadas com maior eficácia do lado esquerdo do campo. Canhotos têm facilidade em realizar jogadas em ângulos difíceis para jogadores destros, tornando-se imprevisíveis e difíceis de marcar. Essa característica permite que o jogador tenha maior confiança e precisão ao chutar, passar e conduzir a bola com a perna esquerda, fazendo com que explore melhor o flanco esquerdo e crie oportunidades únicas em campo.___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1407407066024247436,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Perna_canhota.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "barra1" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿╭・ ────────── ・ஜ・──────────・",
            "especificacao" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ ﻿_ _ ━──────≪✷≫──────━",
            "titulo" : "## _ _ _ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ _ _ ﻿**・୭`❗️`︰  ⇆・꒰ __Perna Dominante__ ꒰・**╯",
            "quebra" : "\n\n",
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Um jogador com **perna dominante direita**, ou destro, possui um controle e precisão superiores com a perna direita. Tendo as mesmas funções de jogadores canhotos, mas sendo uma maior porcentagem de pessoas do mundo como destros. Tendo seu destaque do lado direito do campo, invadindo escondido e geralmente fazendo gols rápidos e fáceis, focando na objetividade___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1407407066024247436,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Perna_destra.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "barra1" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿╭・ ────────── ・ஜ・──────────・",
            "especificacao" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ ﻿_ _ ━──────≪✷≫──────━",
            "titulo" : "## _ _ _ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ _ _ ﻿**・୭`❗️`︰  ⇆・꒰ __Perna Dominante__ ꒰・**╯",
            "quebra" : "\n\n",
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ Um jogador com **perna dominante direita**, ou destro, possui um controle e precisão superiores com a perna direita. Tendo as mesmas funções de jogadores canhotos, mas sendo uma maior porcentagem de pessoas do mundo como destros. Tendo seu destaque do lado direito do campo, invadindo escondido e geralmente fazendo gols rápidos e fáceis, focando na objetividade___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1407407066024247436,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Perna_destra.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
        {
            "barra1" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿╭・ ────────── ・ஜ・──────────・",
            "especificacao" : "_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ ﻿_ _ ━──────≪✷≫──────━",
            "titulo" : "## _ _ _ _ ﻿_ _ ﻿_ _ ﻿_ _ _ _ _ _ ﻿**・୭`❗️`︰  ⇆・꒰ __Perna Dominante__ ꒰・**╯",
            "quebra" : "\n\n",
            "descricao": "╭೨`✍️`੭ ៸៸﹒  ﹙__𝐈nformação__﹚・広金",
            "informação" : "╰：❝ *___ A **“Ambidestria Natural”** é uma habilidade rara e extremamente valiosa no futebol, onde o jogador nasce com o domínio completo de ambas as pernas. Sem a necessidade de treinamento adicional para equilibrar sua técnica, o ambidestro natural possui uma fluidez impressionante ao alternar entre a perna direita e a esquerda, mantendo a mesma precisão em passes, chutes e dribles. Essa capacidade única torna o jogador imprevisível e extremamente versátil em qualquer posição do campo, capaz de adaptar-se rapidamente a diferentes situações de jogo. ___* ❜❜",
            "buffs": "╭೨`❓`੭ ៸៸﹒  ﹙__𝐈nfo__﹚・什",
            "info1" : "╰：",
            "canal_id": 1407407066024247436,
            "barra3" : "﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒﹒",
            "imagem": "Bot/imagens/Ambidestria.jpg",
            "cor": 0xa30707  # Vermelho para erro
        },
    ]

    perna_escolhida = random.choice(perna_lista)

    minha_embed_perna_escolhida = discord.Embed(color=perna_escolhida['cor'])
    minha_embed_perna_escolhida.description = (
        f"{perna_escolhida['barra1']}"
        f"\n"
        f"{perna_escolhida['especificacao']}"
        f"\n\n"
        f"{perna_escolhida['titulo']}{perna_escolhida['quebra']} "
        
        f"\n\n\n"
        f"{perna_escolhida['descricao']}"
        f"\n"
        f"{perna_escolhida['informação']}"
        f"\n\n"
        f"{perna_escolhida['buffs']}"
        f"\n"
        f"{perna_escolhida['info1']} ❝***__<#{perna_escolhida['canal_id']}>__***❜❜"
        f"\n"
        f"{perna_escolhida['barra3']}"
    )

    imagem = discord.File(perna_escolhida['imagem'], filename="porte.gif")
    minha_embed_perna_escolhida.set_image(url="attachment://porte.gif")

    await ctx.reply(embeds=[minha_embed_perna_escolhida], file=imagem)

@bot.command()
async def chute(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando chutamos e a bola sai dos limites do campo, isso é chamado de tiro de meta ou escanteio, dependendo de onde ela saiu e quem tocou por último. De forma geral, dizemos que a bola foi para fora. É uma interrupção do jogo, e a posse é dada ao time adversário.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando chutamos e a bola sai dos limites do campo, isso é chamado de tiro de meta ou escanteio, dependendo de onde ela saiu e quem tocou por último. De forma geral, dizemos que a bola foi para fora. É uma interrupção do jogo, e a posse é dada ao time adversário.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Chute ou finalização é basicamente quando o jogador tenta mandar a bola pro gol. Pode ser de longe, de perto, de primeira, com força ou colocada — o objetivo é sempre o mesmo: **fazer o gol.***⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Chute ou finalização é basicamente quando o jogador tenta mandar a bola pro gol. Pode ser de longe, de perto, de primeira, com força ou colocada — o objetivo é sempre o mesmo: **fazer o gol.***⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Chute ou finalização é basicamente quando o jogador tenta mandar a bola pro gol. Pode ser de longe, de perto, de primeira, com força ou colocada — o objetivo é sempre o mesmo: **fazer o gol.***⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def V_Chute(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Mesmo com sua facilidade para atingir ao gol, imprevistos ainda Podem acontecer ao finalizar até mesmo o minimo declinio pode levar um gol certeiro a um erro Fatal custando um gol, no qual foi nesse Momento aonde você finalizou com maestria, mas por algum declinio levou-se a um erro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Mesmo com sua facilidade para atingir ao gol, imprevistos ainda Podem acontecer ao finalizar até mesmo o minimo declinio pode levar um gol certeiro a um erro Fatal custando um gol, no qual foi nesse Momento aonde você finalizou com maestria, mas por algum declinio levou-se a um erro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Um chute mais calibrado e preciso do que chutes normais. Jogadores com essa maestria possuem um chute diferente dos que não possuem desta maestria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ao utilizar desse chute, Você tem uma facilidade maior para Gols tendo Chances a mais de **acertos** sobre o comando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Um chute mais calibrado e preciso do que chutes normais. Jogadores com essa maestria possuem um chute diferente dos que não possuem desta maestria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ao utilizar desse chute, Você tem uma facilidade maior para Gols tendo Chances a mais de **acertos** sobre o comando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Um chute mais calibrado e preciso do que chutes normais. Jogadores com essa maestria possuem um chute diferente dos que não possuem desta maestria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ao utilizar desse chute, Você tem uma facilidade maior para Gols tendo Chances a mais de **acertos** sobre o comando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Um chute mais calibrado e preciso do que chutes normais. Jogadores com essa maestria possuem um chute diferente dos que não possuem desta maestria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ao utilizar desse chute, Você tem uma facilidade maior para Gols tendo Chances a mais de **acertos** sobre o comando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/V-Chute_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Chute_Direto(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *você chegou atrasado para finalizar a bola, no momento em que você ia chutar você perdeu a oportunidade de Gol, com os Inimigos impedindo seu campo de visão e com a bola ja não estando mais tanto sobre o Ar, perdendo totalmente sua Potência fazendo assim você declinar seu Chute para fora*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_Direto_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *você chegou atrasado para finalizar a bola, no momento em que você ia chutar você perdeu a oportunidade de Gol, com os Inimigos impedindo seu campo de visão e com a bola ja não estando mais tanto sobre o Ar, perdendo totalmente sua Potência fazendo assim você declinar seu Chute para fora*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_Direto_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ponto Exato, Chute Exato, Você Conseguiu finalizar com um Chute Direto assim que ve a Bola quicando a sua frente realizando um Chute Potente sem dar chance de seus Inimigos o Acompanharem para desarma-lo, fazendo assim ela ir no Angulo Direto.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**.__\n\n ﹒ `❗`・⇢ __Caso não tenha a Arma **Direct-Shot** ou outra **Formula**, você recebera um debuff de **-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_Direto_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ponto Exato, Chute Exato, Você Conseguiu finalizar com um Chute Direto assim que ve a Bola quicando a sua frente realizando um Chute Potente sem dar chance de seus Inimigos o Acompanharem para desarma-lo, fazendo assim ela ir no Angulo Direto.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**.__\n\n ﹒ `❗`・⇢ __Caso não tenha a Arma **Direct-Shot** ou outra **Formula**, você recebera um debuff de **-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_Direto_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ponto Exato, Chute Exato, Você Conseguiu finalizar com um Chute Direto assim que ve a Bola quicando a sua frente realizando um Chute Potente sem dar chance de seus Inimigos o Acompanharem para desarma-lo, fazendo assim ela ir no Angulo Direto.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**.__\n\n ﹒ `❗`・⇢ __Caso não tenha a Arma **Direct-Shot** ou outra **Formula**, você recebera um debuff de **-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_Direto_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Cabeceio(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Infelizmente, você chegou atrasado e não conseguiu atingir a bola com seu cabeceio como queria, fazendo assim com que ela perdesse sua velocidade e não fosse para o Local exato que você queria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Cabeceio_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Infelizmente, você chegou atrasado e não conseguiu atingir a bola com seu cabeceio como queria, fazendo assim com que ela perdesse sua velocidade e não fosse para o Local exato que você queria.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Cabeceio_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *No Momento em que a mesma ficou a sua Frente, você conseguiu Pular com força dando uma cabeçada forte no centro da Bola fazendo ela ir com o Impacto para frente com Precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Cabeceou Bem, Invez de Utilizar o Roll de Finalização Você Utilizara o Roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** no seu Cabeceio.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Cabeceio_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *No Momento em que a mesma ficou a sua Frente, você conseguiu Pular com força dando uma cabeçada forte no centro da Bola fazendo ela ir com o Impacto para frente com Precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Cabeceou Bem, Invez de Utilizar o Roll de Finalização Você Utilizara o Roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** no seu Cabeceio.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Cabeceio_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *No Momento em que a mesma ficou a sua Frente, você conseguiu Pular com força dando uma cabeçada forte no centro da Bola fazendo ela ir com o Impacto para frente com Precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Cabeceou Bem, Invez de Utilizar o Roll de Finalização Você Utilizara o Roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** no seu Cabeceio.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Cabeceio_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Bike(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! ,Ele se posiciona, prepara o corpo e Salta Mas O tempo do chute não encaixa! erra completamente o contato com a bola assim Atingindo ela da forma Errada e atirando ela De forma Desajeitada, Uma chance dessas é bem Dificil de Conseguir de Novo*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! ,Ele se posiciona, prepara o corpo e Salta Mas O tempo do chute não encaixa! erra completamente o contato com a bola assim Atingindo ela da forma Errada e atirando ela De forma Desajeitada, Uma chance dessas é bem Dificil de Conseguir de Novo*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝Consegue! a Bola no Ar vem cortando o campo, viajando com precisão cirúrgica em sua direção! Ele se posiciona, seus olhos analisam cada detalhe do lance e então, com uma agilidade absurda, ele se lança no ar! Realizando um Chute de Bicicleta Espetacular!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝Consegue! a Bola no Ar vem cortando o campo, viajando com precisão cirúrgica em sua direção! Ele se posiciona, seus olhos analisam cada detalhe do lance e então, com uma agilidade absurda, ele se lança no ar! Realizando um Chute de Bicicleta Espetacular!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝Consegue! a Bola no Ar vem cortando o campo, viajando com precisão cirúrgica em sua direção! Ele se posiciona, seus olhos analisam cada detalhe do lance e então, com uma agilidade absurda, ele se lança no ar! Realizando um Chute de Bicicleta Espetacular!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Cavadinha(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! ,Ele se posiciona, prepara o corpo e Salta Mas O tempo do chute não encaixa! erra completamente o contato com a bola assim Atingindo ela da forma Errada e atirando ela De forma Desajeitada, Uma chance dessas é bem Dificil de Conseguir de Novo*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pessima Finalização, Agora tera de pegar o **Choose** para Decidir para aonde a sua Bola foi.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Bike_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue! a Bola no Ar vem cortando o campo, viajando com precisão cirúrgica em sua direção! Ele se posiciona, seus olhos analisam cada detalhe do lance e então, com uma agilidade absurda, ele se lança no ar! Realizando um Chute de Bicicleta Espetacular!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você Finalizou Bem, caso alguem tente Defender e Consiga, ambos devem roletar **Chute x Reflexo/Fisico**, o Roll maior **vence**__\n\n ﹒ `❗`・⇢ __Caso não tenha alguma **Formula** que impeça Isso, você tera um debuff de **_-5** na sua Finalização.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/cavadinha_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Chute_Clinico(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! A pessoa que esta o marcando o pressiona de mais, e Impede que você consiga achar uma brecha para uma finalização Precisa, com isso a Bola fica com o Jogador que o Marcou.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, por não ter conseguido achar uma brecha, a Bola fica com o **Jogador** que estava o **Marcando**__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! A pessoa que esta o marcando o pressiona de mais, e Impede que você consiga achar uma brecha para uma finalização Precisa, com isso a Bola fica com o Jogador que o Marcou.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, por não ter conseguido achar uma brecha, a Bola fica com o **Jogador** que estava o **Marcando**__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue! Chute estilo finalizador clínico é uma finalização precisa, rápida e sem desperdício de movimento, onde o jogador escolhe o canto certo e finaliza com eficiência e controle, mesmo estado marcado, demonstrado instinto matador.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pode chutar mesmo sendo marcado com **!Marcar**__\n\n ﹒ `❗`・⇢ __**(Outros Tipos de Marcação, anulam Essa Habilidade)**__ \n\n ﹒ `❗`・⇢ __Alem Disso você Fornece **-2** aos Jogadores que tentaram defender esse Chute.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue! Chute estilo finalizador clínico é uma finalização precisa, rápida e sem desperdício de movimento, onde o jogador escolhe o canto certo e finaliza com eficiência e controle, mesmo estado marcado, demonstrado instinto matador.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pode chutar mesmo sendo marcado com **!Marcar**__\n\n ﹒ `❗`・⇢ __**(Outros Tipos de Marcação, anulam Essa Habilidade)**__ \n\n ﹒ `❗`・⇢ __Alem Disso você Fornece **-2** aos Jogadores que tentaram defender esse Chute.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue! Chute estilo finalizador clínico é uma finalização precisa, rápida e sem desperdício de movimento, onde o jogador escolhe o canto certo e finaliza com eficiência e controle, mesmo estado marcado, demonstrado instinto matador.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pode chutar mesmo sendo marcado com **!Marcar**__\n\n ﹒ `❗`・⇢ __**(Outros Tipos de Marcação, anulam Essa Habilidade)**__ \n\n ﹒ `❗`・⇢ __Alem Disso você Fornece **-2** aos Jogadores que tentaram defender esse Chute.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue! Chute estilo finalizador clínico é uma finalização precisa, rápida e sem desperdício de movimento, onde o jogador escolhe o canto certo e finaliza com eficiência e controle, mesmo estado marcado, demonstrado instinto matador.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Pode chutar mesmo sendo marcado com **!Marcar**__\n\n ﹒ `❗`・⇢ __**(Outros Tipos de Marcação, anulam Essa Habilidade)**__ \n\n ﹒ `❗`・⇢ __Alem Disso você Fornece **-2** aos Jogadores que tentaram defender esse Chute.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Chute_clinico_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Passe(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele consegue! Você conseguiu enxergar seu companheiro totalmente livre de marcações, o que isso te facilita para realizar um lindo passe para ele, agora quem irá comandar a situação do jogo é ele. Parabéns, belo passe!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele consegue! Você conseguiu enxergar seu companheiro totalmente livre de marcações, o que isso te facilita para realizar um lindo passe para ele, agora quem irá comandar a situação do jogo é ele. Parabéns, belo passe!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele consegue! Você conseguiu enxergar seu companheiro totalmente livre de marcações, o que isso te facilita para realizar um lindo passe para ele, agora quem irá comandar a situação do jogo é ele. Parabéns, belo passe!*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Passe_Direto(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Direto_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Direto_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Só Pode ser usado caso **receba** um **Passe**.__\n\n ﹒ `❗`・⇢ __O Comando é mais Dificil que o passe Normal, alem disso pode ser Usado caso estiver **Marcando** algum jogador.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Direto_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Só Pode ser usado caso **receba** um **Passe**.__\n\n ﹒ `❗`・⇢ __O Comando é mais Dificil que o passe Normal, alem disso pode ser Usado caso estiver **Marcando** algum jogador.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Direto_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Lançamento(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Lançamento_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Lançamento_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **3 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Qualquer Jogador que esteja fora do setor do **Recebedor** ou do **Passador** não podera interceptar, so se estiverem mesmo setor.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Lançamento_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **3 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Qualquer Jogador que esteja fora do setor do **Recebedor** ou do **Passador** não podera interceptar, so se estiverem mesmo setor.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Lançamento_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **3 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Qualquer Jogador que esteja fora do setor do **Recebedor** ou do **Passador** não podera interceptar, so se estiverem mesmo setor.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Lançamento_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def PasseRQ(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou o Passe agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Alem de ser um Comando Facilitado, so podera usar esse Passe para seu Companheiro de Reação, alem disso você recebe **+3** no Passe, e seu Companheiro **+2** na **Proximo Embate** que ele fizer.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Alem de ser um Comando Facilitado, so podera usar esse Passe para seu Companheiro de Reação, alem disso você recebe **+3** no Passe, e seu Companheiro **+2** na **Proximo Embate** que ele fizer.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Alem de ser um Comando Facilitado, so podera usar esse Passe para seu Companheiro de Reação, alem disso você recebe **+3** no Passe, e seu Companheiro **+2** na **Proximo Embate** que ele fizer.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe só ultrapassa **2 setores**, além disso é totalmente proibido.__\n\n ﹒ `❗`・⇢ __Alem de ser um Comando Facilitado, so podera usar esse Passe para seu Companheiro de Reação, alem disso você recebe **+3** no Passe, e seu Companheiro **+2** na **Proximo Embate** que ele fizer.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/PasseRQ_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Trivela_Passe(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena?, Mesmo tendo errado estava tudo Planejado, você podera Decidir em qual **Setor** envolta de você a Bola Ira cair, aonde caso tenha um Companheiro ele podera Dominar.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena?, Mesmo tendo errado estava tudo Planejado, você podera Decidir em qual **Setor** envolta de você a Bola Ira cair, aonde caso tenha um Companheiro ele podera Dominar.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe vai até **3** Setores.__\n\n ﹒ `❗`・⇢ __Estava tudo Planejado, caso seu Companheiro erre o Domínio, você pode decidir em qual setor Envolta dele a Bola Ira cair, criando uma Segunda Chance para seu Time mesmo com o fracasso dele.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe vai até **3** Setores.__\n\n ﹒ `❗`・⇢ __Estava tudo Planejado, caso seu Companheiro erre o Domínio, você pode decidir em qual setor Envolta dele a Bola Ira cair, criando uma Segunda Chance para seu Time mesmo com o fracasso dele.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe vai até **3** Setores.__\n\n ﹒ `❗`・⇢ __Estava tudo Planejado, caso seu Companheiro erre o Domínio, você pode decidir em qual setor Envolta dele a Bola Ira cair, criando uma Segunda Chance para seu Time mesmo com o fracasso dele.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O passe vai até **3** Setores.__\n\n ﹒ `❗`・⇢ __Estava tudo Planejado, caso seu Companheiro erre o Domínio, você pode decidir em qual setor Envolta dele a Bola Ira cair, criando uma Segunda Chance para seu Time mesmo com o fracasso dele.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Passe_Trivela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Tabela_first(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou ou seja a Bola ficou **Automaticamente** com o Oponente que te desarmou.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, você errou ou seja a Bola ficou **Automaticamente** com o Oponente que te desarmou.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja sendo **Desarmado/Cercado**, e tenha um **Companheiro** em seu **setor**, você rapidamente faz uma Tabela com ele fazendo você rodar contra ele com seu roll de **Passe**, aonde caso ganhe avançaram **1** setor **Automaticamente**, e a pessoa na qual você fez essa Tabela ira ficar com a Bola e ganhar **Prioritaria**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja sendo **Desarmado/Cercado**, e tenha um **Companheiro** em seu **setor**, você rapidamente faz uma Tabela com ele fazendo você rodar contra ele com seu roll de **Passe**, aonde caso ganhe avançaram **1** setor **Automaticamente**, e a pessoa na qual você fez essa Tabela ira ficar com a Bola e ganhar **Prioritaria**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja sendo **Desarmado/Cercado**, e tenha um **Companheiro** em seu **setor**, você rapidamente faz uma Tabela com ele fazendo você rodar contra ele com seu roll de **Passe**, aonde caso ganhe avançaram **1** setor **Automaticamente**, e a pessoa na qual você fez essa Tabela ira ficar com a Bola e ganhar **Prioritaria**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja sendo **Desarmado/Cercado**, e tenha um **Companheiro** em seu **setor**, você rapidamente faz uma Tabela com ele fazendo você rodar contra ele com seu roll de **Passe**, aonde caso ganhe avançaram **1** setor **Automaticamente**, e a pessoa na qual você fez essa Tabela ira ficar com a Bola e ganhar **Prioritaria**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_first_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Tabela(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, vocês erraram a Tabela agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, vocês erraram a Tabela agora ira te que fazer um **Choose** para decidir aonde a Bola Caiu.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ambos Jogadores avançaram **2** Setores de forma **Instantânea**, a Bola ira ficar com o jogador que recebeu o Passe.__\n\n ﹒ `❗`・⇢ __Para acabar com a Tabela é necessario, que avancem para um dos **setores** que ambos vão passar, e tentarem **Marcar** algum dos jogadores ou realizar um **carrinho** na Bola__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ambos Jogadores avançaram **2** Setores de forma **Instantânea**, a Bola ira ficar com o jogador que recebeu o Passe.__\n\n ﹒ `❗`・⇢ __Para acabar com a Tabela é necessario, que avancem para um dos **setores** que ambos vão passar, e tentarem **Marcar** algum dos jogadores ou realizar um **carrinho** na Bola__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ambos Jogadores avançaram **2** Setores de forma **Instantânea**, a Bola ira ficar com o jogador que recebeu o Passe.__\n\n ﹒ `❗`・⇢ __Para acabar com a Tabela é necessario, que avancem para um dos **setores** que ambos vão passar, e tentarem **Marcar** algum dos jogadores ou realizar um **carrinho** na Bola__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tabela_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def desarme(ctx: commands.Context):
    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Erro de roubo é quando o jogador tenta desarmar o adversário, mas falha na tentativa.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, Você errou o Desarme, caso o jogador te drible, ele passara facilmente de Você.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/desarme_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Erro de roubo é quando o jogador tenta desarmar o adversário, mas falha na tentativa.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, Você errou o Desarme, caso o jogador te drible, ele passara facilmente de Você.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/desarme_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
                    "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Você chega no seu adversário e com reflexo rápido, consegue tirar a bola com precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Drible, ambos devem roletar **Roubo x Drible**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/desarme_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
            },
        {
                    "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Você chega no seu adversário e com reflexo rápido, consegue tirar a bola com precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Drible, ambos devem roletar **Roubo x Drible**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/desarme_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
            },
        {
                    "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Você chega no seu adversário e com reflexo rápido, consegue tirar a bola com precisão.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Drible, ambos devem roletar **Roubo x Drible**, o Roll maior **vence**...__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/desarme_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
            },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Carrinho(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Erro de carrinho é quando o jogador tenta desarmar deslizando, mas erra o tempo ou a direção, falha em tirar a bola e pode acabar cometendo falta ou deixando espaço para o adversário avançar.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, Você errou o carrinho, caso o jogador consiga te Driblar, você ficara **1 turno** sobre o Chão.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Carrinho_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Erro de carrinho é quando o jogador tenta desarmar deslizando, mas erra o tempo ou a direção, falha em tirar a bola e pode acabar cometendo falta ou deixando espaço para o adversário avançar.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena, Você errou o carrinho, caso o jogador consiga te Driblar, você ficara **1 turno** sobre o Chão.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Carrinho_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Carrinho é um desarme em que o jogador se lança deslizando no chão com uma ou ambas as pernas estendidas para tentar tirar a bola do adversário. É arriscado, mas pode ser muito eficaz se feito no tempo certo.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira disputar um desarme com seu Roll de **Reflexo** e fazendo a bola entrar em sobra **Automaticamente**, deve realizar um Choose para saber aonde ela caiu.__\n\n ﹒ `❗`・⇢ __Apos o Choose, você não podera ir atras da Bola, pois deve ficar **1 turno** sobre o chão, e fazer uma ação se Levantando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Carrinho_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Carrinho é um desarme em que o jogador se lança deslizando no chão com uma ou ambas as pernas estendidas para tentar tirar a bola do adversário. É arriscado, mas pode ser muito eficaz se feito no tempo certo.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira disputar um desarme com seu Roll de **Reflexo** e fazendo a bola entrar em sobra **Automaticamente**, deve realizar um Choose para saber aonde ela caiu.__\n\n ﹒ `❗`・⇢ __Apos o Choose, você não podera ir atras da Bola, pois deve ficar **1 turno** sobre o chão, e fazer uma ação se Levantando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Carrinho_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Carrinho é um desarme em que o jogador se lança deslizando no chão com uma ou ambas as pernas estendidas para tentar tirar a bola do adversário. É arriscado, mas pode ser muito eficaz se feito no tempo certo.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira disputar um desarme com seu Roll de **Reflexo** e fazendo a bola entrar em sobra **Automaticamente**, deve realizar um Choose para saber aonde ela caiu.__\n\n ﹒ `❗`・⇢ __Apos o Choose, você não podera ir atras da Bola, pois deve ficar **1 turno** sobre o chão, e fazer uma ação se Levantando.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Carrinho_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Defesa_cjog(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e não podera mais defender.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesacjog_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e não podera mais defender.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesacjog_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha nenhum tipo de Formula/Habilidade que impeça isso, você recebe **-5** de debuff.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesacjog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha nenhum tipo de Formula/Habilidade que impeça isso, você recebe **-5** de debuff.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesacjog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Fisico**.__\n\n ﹒ `❗`・⇢ __Caso não tenha nenhum tipo de Formula/Habilidade que impeça isso, você recebe **-5** de debuff.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesacjog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Defesa_jog(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e não podera mais defender.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesajog_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e não podera mais defender.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesajog_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesajog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesajog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesajog_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },

    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Interceptação(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e caiu com o Oponente, deixando você fora da proxima ação dele__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/interceptação_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e caiu com o Oponente, deixando você fora da proxima ação dele__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/interceptação_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Interceptação_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Interceptação_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Você ira defender Utilizando do roll de **Reflexo**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Interceptação_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Defesa_gk(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e possivelmente seu time levou um Gol.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesagk_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Ele Não Consegue! Ao realizar o Passe você utiliza a Potência ou Curva errada, fazendo errar o trajeto da Bola fazendo com que ela entrasse em sobra e não caisse sobre seu Companheiro.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou, Significa que a Bola passou de você e possivelmente seu time levou um Gol.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesagk_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ultima Salvação, Você ira defender Utilizando do roll de **Agilidade**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesagk_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ultima Salvação, Você ira defender Utilizando do roll de **Agilidade**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesagk_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Consegue!, Assim que a Bola chega em você, invez de Domina-la você se vira ganhando Posicionamento e passando diretamente com Passes Rapidos para seu Companheiro dando mais Chances Táticas pro seu Time*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Ultima Salvação, Você ira defender Utilizando do roll de **Agilidade**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Defesagk_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },

    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def Tromba(ctx: commands.Context):

    escolha_chute = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Não Conseguiu, Mesmo Trombando com seu Oponente você foi sem uma Postura para se Manter fazendo com que seu Oponente achasse brecha rapido e desviando da sua Trombada fazendo ele passar de você mantendo a Posse.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou Significa que **Automaticamente** o jogador ganha de você.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tromba_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Não Conseguiu, Mesmo Trombando com seu Oponente você foi sem uma Postura para se Manter fazendo com que seu Oponente achasse brecha rapido e desviando da sua Trombada fazendo ele passar de você mantendo a Posse.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Que Pena você errou Significa que **Automaticamente** o jogador ganha de você.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tromba_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Trombar é quando dois jogadores se chocam fisicamente durante uma disputa de bola, geralmente de forma intensa e direta, usando o corpo para ganhar espaço ou desequilibrar o adversário.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O adversário deve rodar **1d100**; **-55** ele solta a bola no setor devido ao impacto, onde todos tem que buscar a bola, caso ele Não Solte você tera que desarma-lo com seu **Fisico**.__\n\n ﹒ `❗`・⇢ __**Aviso:** Não sera permitido **SB**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tromba_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Trombar é quando dois jogadores se chocam fisicamente durante uma disputa de bola, geralmente de forma intensa e direta, usando o corpo para ganhar espaço ou desequilibrar o adversário.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O adversário deve rodar **1d100**; **-55** ele solta a bola no setor devido ao impacto, onde todos tem que buscar a bola, caso ele Não Solte você tera que desarma-lo com seu **Fisico**.__\n\n ﹒ `❗`・⇢ __**Aviso:** Não sera permitido **SB**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tromba_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Trombar é quando dois jogadores se chocam fisicamente durante uma disputa de bola, geralmente de forma intensa e direta, usando o corpo para ganhar espaço ou desequilibrar o adversário.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __O adversário deve rodar **1d100**; **-55** ele solta a bola no setor devido ao impacto, onde todos tem que buscar a bola, caso ele Não Solte você tera que desarma-lo com seu **Fisico**.__\n\n ﹒ `❗`・⇢ __**Aviso:** Não sera permitido **SB**.__",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Tromba_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    chute_escolhido = random.choice(escolha_chute)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_chute = discord.Embed(color=chute_escolhido['cor'])
    minha_embed_chute.description = (
        f"{chute_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
        f"\n\n"
        f"{chute_escolhido['info']}"
        f"\n\n"
        f"{chute_escolhido['barrinha']}"
        f"{chute_escolhido['especificar']}"
        f"{chute_escolhido['funcionamento']}"
        f"\n\n"
        f"{chute_escolhido['barra']}"
    )

    imagem = discord.File(chute_escolhido['imagem'], filename="Chute.jpg")
    minha_embed_chute.set_image(url="attachment://Chute.jpg")

    await ctx.reply(embeds=[minha_embed_chute], file=imagem)

@bot.command()
async def corte(ctx: commands.Context):

    escolha_pedalada = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/corte_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/corte_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Corte é um drible simples e eficiente em que o jogador muda rapidamente a direção da bola para escapar do marcador. Ele pode ser feito com o lado interno ou externo do pé, e é muito usado em jogadas de um contra um, tanto para avançar quanto para finalizar. É uma das fintas mais básicas do futebol, mas muito eficaz quando bem executada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/corte_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Corte é um drible simples e eficiente em que o jogador muda rapidamente a direção da bola para escapar do marcador. Ele pode ser feito com o lado interno ou externo do pé, e é muito usado em jogadas de um contra um, tanto para avançar quanto para finalizar. É uma das fintas mais básicas do futebol, mas muito eficaz quando bem executada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/corte_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Corte é um drible simples e eficiente em que o jogador muda rapidamente a direção da bola para escapar do marcador. Ele pode ser feito com o lado interno ou externo do pé, e é muito usado em jogadas de um contra um, tanto para avançar quanto para finalizar. É uma das fintas mais básicas do futebol, mas muito eficaz quando bem executada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/corte_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    pedalada_escolhido = random.choice(escolha_pedalada)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_pedalada = discord.Embed(color=pedalada_escolhido['cor'])
    minha_embed_pedalada.description = (
        f"{pedalada_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{pedalada_escolhido['barra']}"
        f"\n\n"
        f"{pedalada_escolhido['info']}"
        f"\n\n"
        f"{pedalada_escolhido.get('barrinha', '')}"
        f"{pedalada_escolhido.get('especificar', '')}"
        f"{pedalada_escolhido.get('funcionamento', '')}"
        f"{pedalada_escolhido['barra']}"
    )

    imagem = discord.File(pedalada_escolhido['imagem'], filename="pedalada.jpg")
    minha_embed_pedalada.set_image(url="attachment://pedalada.jpg")

    await ctx.reply(embed=minha_embed_pedalada, file=imagem)

@bot.command()
async def pedalada(ctx: commands.Context):

    escolha_pedalada = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/pedalada_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/pedalada_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/pedalada_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/pedalada_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/pedalada_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    pedalada_escolhido = random.choice(escolha_pedalada)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_pedalada = discord.Embed(color=pedalada_escolhido['cor'])
    minha_embed_pedalada.description = (
        f"{pedalada_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{pedalada_escolhido['barra']}"
        f"\n\n"
        f"{pedalada_escolhido['info']}"
        f"\n\n"
        f"{pedalada_escolhido.get('barrinha', '')}"
        f"{pedalada_escolhido.get('especificar', '')}"
        f"{pedalada_escolhido.get('funcionamento', '')}"
        f"{pedalada_escolhido['barra']}"
    )

    imagem = discord.File(pedalada_escolhido['imagem'], filename="pedalada.jpg")
    minha_embed_pedalada.set_image(url="attachment://pedalada.jpg")

    await ctx.reply(embed=minha_embed_pedalada, file=imagem)

@bot.command()
async def roleta(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/roleta_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/roleta_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def toque_duplo(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/toque_duplo_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/toque_duplo_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def Elastico(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Elastico_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Elastico_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def Chapeu(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/chapeu_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/chapeu_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def Caneta_L(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Canetacal_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso seu Oponente Tenha Acertado o Desarme, ambos devem roletar **Drible x Desarme**, o Roll maior **vence**...__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Canetacal_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def Dribbling_Speed(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Agora você tera de Driblar com seu roll de **Velocidade**, aonde caso você ganhe e **avance** um setor, e seja seguido pelo mesmo Oponente no qual você Driblou, **Seu Roll de velocidade sera o mesmo do qual você deu Drible**, caso seja um Outro Oponente, você necessitara dar Roll para ele.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Agora você tera de Driblar com seu roll de **Velocidade**, aonde caso você ganhe e **avance** um setor, e seja seguido pelo mesmo Oponente no qual você Driblou, **Seu Roll de velocidade sera o mesmo do qual você deu Drible**, caso seja um Outro Oponente, você necessitara dar Roll para ele.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Agora você tera de Driblar com seu roll de **Velocidade**, aonde caso você ganhe e **avance** um setor, e seja seguido pelo mesmo Oponente no qual você Driblou, **Seu Roll de velocidade sera o mesmo do qual você deu Drible**, caso seja um Outro Oponente, você necessitara dar Roll para ele.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Agora você tera de Driblar com seu roll de **Velocidade**, aonde caso você ganhe e **avance** um setor, e seja seguido pelo mesmo Oponente no qual você Driblou, **Seu Roll de velocidade sera o mesmo do qual você deu Drible**, caso seja um Outro Oponente, você necessitara dar Roll para ele.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_Speed_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def Dri_Marcar(ctx: commands.Context):

    escolha_roleta = [
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Drible_marcar_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ⸝⸝﹕❲`❌`❳ ***Ξ __{jogador} Errou__»***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *Quando você tenta avançar pedaladando, você erra o Posicionamento do seu pé enquanto tenta ser rapido fazendo a Bola Escapar para frente, antes que seu Oponente avance no Desarme dando uma vantagem para ele nesse confronto mano a mano*⁠",
            "especificar" : "",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Drible_marcar_erro.jpg",
            "cor": 0xE74C3C  # Vermelho para erro
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja marcado, você então consegue driblar seu Oponente passando por ele, utilizando qualquer um desses 3 atributos **Drible/Fisico/Velocidade** a decisão é sua.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Drible_marcar_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja marcado, você então consegue driblar seu Oponente passando por ele, utilizando qualquer um desses 3 atributos **Drible/Fisico/Velocidade** a decisão é sua.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Drible_marcar_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
        {
            "title": " ╰ㆍ﹕❲`✅`❳ ***Ξ __{jogador} Acertou__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "info": "︰ ``📖`` ・  ❝ *O jogador domina a bola com leveza e, sem perder o ritmo, manda uma pedalada rápida, confundindo o marcador. Com um toque ágil, ele avança, deixando o adversário para trás, pronto para criar a jogada!.*⁠",
            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",
            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `❗`・⇢ __Caso esteja marcado, você então consegue driblar seu Oponente passando por ele, utilizando qualquer um desses 3 atributos **Drible/Fisico/Velocidade** a decisão é sua.__\n\n",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Drible_marcar_acerto.jpg",
            "cor": 0x2ECC71  # Verde para acerto
        },
    ]

    roleta_escolhido = random.choice(escolha_roleta)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_roleta = discord.Embed(color=roleta_escolhido['cor'])
    minha_embed_roleta.description = (
        f"{roleta_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{roleta_escolhido['barra']}"
        f"\n\n"
        f"{roleta_escolhido['info']}"
        f"\n\n"
        f"{roleta_escolhido.get('barrinha', '')}"
        f"{roleta_escolhido.get('especificar', '')}"
        f"{roleta_escolhido.get('funcionamento', '')}"
        f"{roleta_escolhido['barra']}"
    )

    imagem = discord.File(roleta_escolhido['imagem'], filename="roleta.jpg")
    minha_embed_roleta.set_image(url="attachment://roleta.jpg")

    await ctx.reply(embed=minha_embed_roleta, file=imagem)

@bot.command()
async def dribbling_fact(ctx: commands.Context):

    escolha_dribbling = [
        {
            "title": " ╰ㆍ﹕❲`💫`❳ ***Ξ __{jogador} Usou o Olfato de Drible...__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",

            "info": "︰ ``📖`` ・  ❝ *Estando tão Imerso em seus Dribles, você consegue pressentir o proximo Drible que deve fazer para realizar para vencer seu Oponente no Mano a Mano, Não pense Muito, apenas confie nos seus Istintos e Reflexos e no seu Ego.*⁠",

            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",

            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `🌟`・⇢ __Você pode realizar esse Comando antes de todo Drible em que for fazer, para saber qual seu Istinto Indica qual deve ser o proximo Drible, caso tu utilize o Drible que o Comando falou e vença seu Oponente, você ira receber **+1** no proximo drible, acumlando ate **+3**__\n\n",

            "Habilidade": "ㅤ**__—__ㅤㅤSeu Proximo Drible é...**\n",
            "drible": "ㅤㅤ`❓ ⦁` *Uma **Pedalada**.*\n\n",

            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_fact.jpg",
            "cor": 0xece303
        },
        {
            "title": " ╰ㆍ﹕❲`💫`❳ ***Ξ __{jogador} Usou o Olfato de Drible...__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",

            "info": "︰ ``📖`` ・  ❝ *Estando tão Imerso em seus Dribles, você consegue pressentir o proximo Drible que deve fazer para realizar para vencer seu Oponente no Mano a Mano, Não pense Muito, apenas confie nos seus Istintos e Reflexos e no seu Ego.*⁠",

            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",

            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `🌟`・⇢ __Você pode realizar esse Comando antes de todo Drible em que for fazer, para saber qual seu Istinto Indica qual deve ser o proximo Drible, caso tu utilize o Drible que o Comando falou e vença seu Oponente, você ira receber **+1** no proximo drible, acumlando ate **+3**__\n\n",

            "Habilidade": "ㅤ**__—__ㅤㅤSeu Proximo Drible é...**\n",
            "drible": "ㅤㅤ`❓ ⦁` *Um **Corte**.*\n\n",

            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_fact.jpg",
            "cor": 0xece303
        },
        {
            "title": " ╰ㆍ﹕❲`💫`❳ ***Ξ __{jogador} Usou o Olfato de Drible...__ »***",
            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",

            "info": "︰ ``📖`` ・  ❝ *Estando tão Imerso em seus Dribles, você consegue pressentir o proximo Drible que deve fazer para realizar para vencer seu Oponente no Mano a Mano, Não pense Muito, apenas confie nos seus Istintos e Reflexos e no seu Ego.*⁠",

            "barrinha": "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n",

            "especificar": "ㅤ**__—__ㅤㅤFuncionamento**\n",
            "funcionamento": "﹒ `🌟`・⇢ __Você pode realizar esse Comando antes de todo Drible em que for fazer, para saber qual seu Istinto Indica qual deve ser o proximo Drible, caso tu utilize o Drible que o Comando falou e vença seu Oponente, você ira receber **+1** no proximo drible, acumlando ate **+3**__\n\n",

            "Habilidade": "ㅤ**__—__ㅤㅤ Habilidade Especial, Seu Proximo Drible é...**\n",
            "drible": 'ㅤㅤ`❓ ⦁` *É com tu meu "fih" cava uma falta que é gol, pode escolher o proximo Drible as chances são tão grandes de vencer, Pode "Ginga e balança", que é desse jeito que nois encanta.*\n\n',

            "barra" : "ㅤㅤ**⋘══════∗ {•*『 `   ⚽   `&』*•} ∗══════ ⋙**",
            "imagem": "Bot/imagens/Dribbling_special.jpg",
            "cor": 0xece303
        },
    ]

    dribbling_escolhido = random.choice(escolha_dribbling)
    jogador = ctx.author.mention

    # Usa a cor definida no dicionário
    minha_embed_dribbling = discord.Embed(color=dribbling_escolhido['cor'])
    minha_embed_dribbling.description = (
        f"{dribbling_escolhido['title'].format(jogador=jogador)}"
        f"\n\n"
        f"{dribbling_escolhido['barra']}"
        f"\n\n"
        f"{dribbling_escolhido['info']}"
        f"\n\n"
        f"{dribbling_escolhido['barrinha']}"
        f"{dribbling_escolhido['especificar']}"
        f"{dribbling_escolhido['funcionamento']}"
        f"{dribbling_escolhido['Habilidade']}"
        f"{dribbling_escolhido['drible']}"
        f"{dribbling_escolhido['barra']}"
    )

    imagem = discord.File(dribbling_escolhido['imagem'], filename="dribbling.jpg")
    minha_embed_dribbling.set_image(url="attachment://dribbling.jpg")

    await ctx.reply(embed=minha_embed_dribbling, file=imagem)

# 📖 Lista de embeds personalizáveis
embed_pages = [
    discord.Embed(
        description="## **__`ᨳ ˖ ་ 📘 𖦆 ﹗(Diretrizes das Regras)`__**\n\n"
                    "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n"
                    "> ⚽ **Siga a posição do seu personagem** em campo, respeitando tática e limite de ações.\n\n"
                    "> 🔁 Evite ações fora do contexto e respeite o turno de cada jogador.",
        color=0x1abc9c
    ).set_image(url="https://i.pinimg.com/736x/fb/4d/05/fb4d05ae9b45f750a928f099fd228cfe.jpg"),

    discord.Embed(
        description="## **__`ᨳ ˖ ་ 📘 𖦆 ﹗(Diretrizes das Regras)`__**\n\n"
                    "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n"
                    "> ⚽ **Siga a posição do seu personagem** em campo, respeitando tática e limite de ações.\n\n"
                    "> 🔁 Evite ações fora do contexto e respeite o turno de cada jogador.",
        color=0x3498db
    ).set_image(url="https://i.pinimg.com/736x/e4/67/d9/e467d9e526c5ef9bf790cc861943b8a3.jpg"),

    discord.Embed(
        description="## **__`ᨳ ˖ ་ 📘 𖦆 ﹗(Diretrizes das Regras)`__**\n\n"
                    "```‹ ㅤ  ㅤ ㅤ ㅤ📚 ㅤ  ㅤ ㅤ ㅤ ›```\n"
                    "> ⚽ **Siga a posição do seu personagem** em campo, respeitando tática e limite de ações.\n\n"
                    "> 🔁 Evite ações fora do contexto e respeite o turno de cada jogador.",
        color=0xe67e22)
        .set_image(url="https://i.pinimg.com/736x/aa/0d/48/aa0d481cbfe560de730420b57c48edee.jpg")
]

class PaginacaoView(View):
    def __init__(self, ctx, paginas):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.paginas = paginas
        self.atual = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.blurple)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.atual > 0:
            self.atual -= 1
            await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)

    @discord.ui.button(label="...", style=discord.ButtonStyle.gray, disabled=True)
    async def meio(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.blurple)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.atual < len(self.paginas) - 1:
            self.atual += 1
            await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)

# 🔐 Comando com permissão de administrador
@bot.command()
@commands.has_permissions(administrator=True)
async def livro_de_regras(ctx):
    view = PaginacaoView(ctx, embed_pages)
    await ctx.send(embed=embed_pages[0], view=view)

# ❌ Se não for administrador
@livro_de_regras.error
async def livro_de_regras_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando. Apenas administradores podem acessá-lo.")

@bot.event
async def on_thread_create(thread):
    # Substitua pelo ID do canal de fórum desejado
    forum_id = 1346963431005224972 

    if thread.parent.id == forum_id:
        embed = discord.Embed(
            title="📘 Regras Blue Lock",
            description="Essas são as regras oficiais. Leia com atenção!",
            color=discord.Color.blue()
        )
        embed.set_image(url="URL_DA_IMAGEM")
        await thread.send(embed=embed)


bot.run(TOKEN)
