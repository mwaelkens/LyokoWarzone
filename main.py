import os
import discord
import asyncio
import random
import sqlite3
import typing
import time
import json
from discord.ext import commands  
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
token = os.getenv('TOKEN_BOT_DISCORD')

# Connexion à la base de données SQLite
conn = sqlite3.connect("lyoko_rpg.db")
cursor = conn.cursor()

# Création de la table pour stocker l'XP (par serveur et par utilisateur)
cursor.execute("""
CREATE TABLE IF NOT EXISTS xp (
    user_id INTEGER,
    server_id INTEGER,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, server_id)
)
""")
conn.commit()

# Création de la table pour stocker les paramètres du serveur (canal de message)
cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    server_id INTEGER PRIMARY KEY,
    channel_id INTEGER NULL,
    current_monster TEXT,
    cooldown_rest INTEGER,
    cooldown_rest_zone INTEGER,
    current_zone TEXT
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    server_id INTEGER,
    level INTEGER,
    role_id INTEGER,
    PRIMARY KEY (server_id, level)
)
""")
conn.commit()

# Liste des monstres avec leur XP et image
monstres_basiques_xana = [
    {"nom": "Kankrelat", "xp": 10, "image": "https://static.wikia.nocookie.net/codelyoko/images/0/01/Kankrelat.jpg/revision/latest?cb=20120105195635&path-prefix=fr"},
    {"nom": "Krabe", "xp": 30, "image": "https://static.wikia.nocookie.net/codelyoko/images/2/2e/Krabe.jpg/revision/latest/scale-to-width-down/432?cb=20120105195635&path-prefix=fr"},
    {"nom": "Blok", "xp": 20, "image": "https://i.pinimg.com/736x/70/e8/fa/70e8fa947c4fe1d7fbf5c496ba5238f0.jpg"},
    {"nom": "Mégatank", "xp": 50, "image": "https://static.wikia.nocookie.net/codelyoko/images/5/54/M%C3%A9gatank.jpg/revision/latest?cb=20120105195636&path-prefix=fr"},
    {"nom": "Tarentule", "xp": 40, "image":"https://static.wikia.nocookie.net/codelyoko/images/a/a8/Tarentule.jpg/revision/latest?cb=20120105195637&path-prefix=fr"},
    {"nom": "Rampant", "xp": 60, "image":"https://static.wikia.nocookie.net/codelyoko/images/2/25/Rampant.jpg/revision/latest?cb=20120105195638&path-prefix=fr"},
    {"nom": "Frôlion", "xp": 25, "image":"https://static.wikia.nocookie.net/codelyoko/images/0/04/Fr%C3%B4lion.jpg/revision/latest/scale-to-width-down/432?cb=20120105195633&path-prefix=fr"},
    {"nom": "Manta", "xp": 70, "image":"https://static.wikia.nocookie.net/codelyoko/images/c/c1/Manta.jpg/revision/latest?cb=20120105195638&path-prefix=fr"},
    {"nom": "Kongre", "xp": 35, "image":"https://static.wikia.nocookie.net/codelyoko/images/3/3e/Kongre.jpg/revision/latest?cb=20120105195728&path-prefix=fr"},
    {"nom": "Rekin", "xp": 45, "image":"https://static.wikia.nocookie.net/codelyoko/images/3/31/Rekin.jpg/revision/latest?cb=20120105195727&path-prefix=fr"},
     
]

monstres_boss_xana = [
    {"nom": "Infinite", "xp": 1500, "image": "https://pm1.aminoapps.com/6164/9348a6cce9fd07343464c2aa4c3c2af3ecaa6e8a_00.jpg"},
    {"nom": "Kolosse", "xp": 500, "image": "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c0260ac6-f0fa-4be7-a21d-ff98d393c58d/ded081s-a0b1d714-303a-4b0b-8838-6d2fec3f9f31.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcL2MwMjYwYWM2LWYwZmEtNGJlNy1hMjFkLWZmOThkMzkzYzU4ZFwvZGVkMDgxcy1hMGIxZDcxNC0zMDNhLTRiMGItODgzOC02ZDJmZWMzZjlmMzEucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.fYkOKEy9RggNoiX45K5_lq6iHtSYBZHjAm0pTTAbEJA"},
    {"nom": "William", "xp": 450, "image": "https://static.wikia.nocookie.net/codelyoko/images/3/3e/M%C3%A9duse.jpg/revision/latest?cb=20120105195726&path-prefix=fr"},
    {"nom": "Méduse", "xp": 400, "image": "https://pm1.aminoapps.com/6164/9348a6cce9fd07343464c2aa4c3c2af3ecaa6e8a_00.jpg"},
    {"nom": "Kalamar", "xp": 350, "image": "https://static.wikia.nocookie.net/codelyoko/images/9/98/Kalamar.jpg/revision/latest?cb=20120105195727&path-prefix=fr"},
]

ocs_xana = [
    {"nom": "Aiko", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889906269028353/069c5a28-25d2-4b21-8d46-9313141309ca.png?ex=68163a3f&is=6814e8bf&hm=59ecd2ebd6ac681158424c96cfffb458f293c76706aceef83261030b6687d528&"},
    {"nom": "Inaya", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889906822680617/49b66e45f88e935bae8e5dbee9286cd5.png?ex=68163a3f&is=6814e8bf&hm=ae62aeb6a3250dba42438ada7aefd59031df764b17b5761276ba6a09b160fd09&"},
    {"nom": "Nightmare", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367898606807416893/80f8d784fcdb87fd1485218fdf85a810.png?ex=6816425a&is=6814f0da&hm=fb4d06753ed37e30e4feb33cd6fcc6051a7336e9d016abbbc31fc1fa425aecc8&"},
    {"nom": "Anna", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889907980308674/Anna_creation_de_XANA.png?ex=68163a40&is=6814e8c0&hm=27342a59ef683547b37fb24c6f14dedfd72181b2bc1f3c5c7629970bf8606eb4&"},
    {"nom": "Flora", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889904666935356/Screenshot_20240814_124457_Google.png?ex=68163a3f&is=6814e8bf&hm=9147550c71c48c21e78bbb979ea81e52e749538f0cbcacc721fba26f0db20bf5&"},
]

monstres_basiques_kage = [
    {"nom": "Arachnobot", "xp":"15", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367885662560194712/Arachnobot.png?ex=6816364c&is=6814e4cc&hm=b1f5aab4f54ce5d68fc0e5ba5140fba0d23446baab1fd2288a8f3e889bde2e7a&"},
    {"nom": "Vipertron", "xp":"25", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887301782405321/Vipertron.png?ex=681637d2&is=6814e652&hm=316a8c8d0f667451722006333a87834d7f0c7bb580c617dc65cbd1a2da041f71&"},
    {"nom": "Draconique", "xp":"35", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887300020801628/Draconique.png?ex=681637d2&is=6814e652&hm=32f0ae683cf83aa2a5cb552ff630dfe629afa5478d6e215175b97db80f1e2a6c&"},
    {"nom": "Screechwings", "xp":"50", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887301060984902/Screechwings.png?ex=681637d2&is=6814e652&hm=b72a633c4fb7a849ba21aa54876046d23bbca830318fd5774752862c03f3f0c6&"},
    {"nom": "Corvale", "xp":"70", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887299672801321/Corvale.png?ex=681637d2&is=6814e652&hm=966f8ff5706a1002275a7e3e1528fb31b8cf279f6e8b7a2d02131543074ee240&"},
    {"nom": "Hippovortex", "xp":"40", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887300398284941/Hippovortex.png?ex=681637d2&is=6814e652&hm=c9391252ad2b5a6b5b3a25592d5f8778360f143bc2cbe7fde21820f3f520d293&"},
    {"nom": "Seastalker", "xp":"45", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887301455118486/Seastalker.png?ex=681637d2&is=6814e652&hm=5c9928f3b02c8e237b5bc489aaa5dcf1e891fbef5c14408a25c9095bd51b0364&"},
]

monstres_boss_kage = [
    {"nom": "Nébulys", "xp": 400, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367887300700410026/Nebulys.jpg?ex=681637d2&is=6814e652&hm=701b5ecf57126c61fb54b14062dfee82cb46f07e6d1c10c0acbc76338e0f59aa&"},
]

ocs_kage = [
    {"nom": "Nathaniel", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889905048490134/3de8780d9a1cf0e5b302f748cadd7fd0.png?ex=68163a3f&is=6814e8bf&hm=a36165297f184dd480fc510ff551f82399c78199b22f03cb8a844086b6aa1658&"},
    {"nom": "Clarissa", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889905585492039/Screenshot_20241101_180711_Gallery.png?ex=68163a3f&is=6814e8bf&hm=f331cae53ecf1bdf5a92cffa506649245f5bdb0a885f7e2a9c5976685854e812&"},
    {"nom": "Wyvern", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889907233591317/OIG1.png?ex=68163a40&is=6814e8c0&hm=557043f2cfa19ac5b1b290d40f50471db248bf1e44bad0fbb76498085fbec53e&"},
]

monstres_basiques_hades = [
    {"nom": "Kankrelat obscur", "xp": 10, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888667301117992/Screenshot_20241002_095441_Discord.png?ex=68163918&is=6814e798&hm=a8fef8c3be0384bf5b1dddd750c4406d21e372e1ba9f0562264024c9f0fe40db&"},
    {"nom": "Krabe obscur", "xp": 30, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888666537754634/Screenshot_20241002_095452_Discord.png?ex=68163918&is=6814e798&hm=397097c4cb099054302070de285c6fa9a69fc91a62eb006a0ae63144225873a7&"},
    {"nom": "Blok obscur", "xp": 20, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888666944475288/Screenshot_20241002_095447_Discord.png?ex=68163918&is=6814e798&hm=1e02a89ac2b502a651da2f9ac1b67bf77fce29b905e26413c7dc64a9330923d2&"},
    {"nom": "Mégatank obscur", "xp": 50, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888665828655144/Screenshot_20241002_095501_Discord.png?ex=68163918&is=6814e798&hm=9a72b6205cfb37abb1cd7b5b1d9e597e274e05a9a55108d6fb28ba21250bd502&"},
    {"nom": "Tarentule obscure", "xp": 40, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888667716223137/Screenshot_20241001_210900_Discord.png?ex=68163918&is=6814e798&hm=66d3970ab57879a5c87b9afbd18cab479dce01e277e446ec820f996a7be81288&"},
    {"nom": "Rampant obscur", "xp": 60, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888665451429918/Screenshot_20241002_095514_Discord.png?ex=68163917&is=6814e797&hm=856a82285cfe2eebeac9072ed7b103e9538e7ad46ca35d72f7bfad85711ee8e2&"},
    {"nom": "Frôlion obscur", "xp": 25, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888666168397944/Screenshot_20241002_095457_Discord.png?ex=68163918&is=6814e798&hm=0baf89456a93622b73af9936e63ea66bb3479c47d127342b7e880a9c442422e3&"},
    {"nom": "Manta obscure", "xp": 70, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888665119821844/Screenshot_20241002_095524_Discord.png?ex=68163917&is=6814e797&hm=7e5f3558076b46850260ecacdaa0e929d0084c43bbd14b4af5e7ac155aa770dd&"},
    {"nom": "Kongre obscur", "xp": 35, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888664767627325/Screenshot_20241002_095529_Discord.png?ex=68163917&is=6814e797&hm=ea45154b3f04ef603e0842bc50610d658b6d6b1ac3ac3f4025f5dce021fd1ff4&"},
    {"nom": "Rekin obscur", "xp": 45, "image":"https://cdn.discordapp.com/attachments/1367885614053331094/1367888772158722188/Rekin_HADES.webp?ex=68163931&is=6814e7b1&hm=84625288c13ee170b1e596ca7091b1cc1b2ea17862008e6e9bd9e0c3b5acbee4&"},
]

monstres_boss_hades = [
    {"nom": "Black", "xp": 1500, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367903280193343609/20230315_152336.png?ex=681646b4&is=6814f534&hm=074b2b8265a37b5ac66966deb6d16fa238b3ac93a02744208029ec36b74790f6&"},
    {"nom": "Kolosse obscur", "xp": 500, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888712184238141/Screenshot_20241002_095718_Discord.png?ex=68163923&is=6814e7a3&hm=232b30d576ba4b4fb4d3ab5b31d02bf67860feeef72eace909d5d8e602cf08c5&"},
    {"nom": "Méduse obscure", "xp": 400, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888711609749635/Screenshot_20241002_095519_Discord.png?ex=68163922&is=6814e7a2&hm=b68ebb15c42b3eba59e06fefc15226e1edf91060cb7660476fa8f04ec15cd536&"},
    {"nom": "Kalamar obscur", "xp": 350, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367888664440602704/Screenshot_20241002_095709_Discord.png?ex=68163917&is=6814e797&hm=b93952f70c7d0004df36d0fc71697ad2250d108d1f668dead5f47216a08a886c&"},
]

ocs_hades = [
    {"nom": "Yuna", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367889907627982890/ninja_girl.png?ex=68163a40&is=6814e8c0&hm=5ac10004f499c0401bd66ea0e1569b9a4a29b8afa402aff792133042207515f9&"},
    {"nom": "Corrax", "xp": 300, "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1367890046358655016/Corrax_HADES.webp?ex=68163a61&is=6814e8e1&hm=a7e75773e328d3235cb7b396824c86ad19290cf48a7967086994b5936c040412&"},
]

logos_camps = [
    {"nom": "Xana", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1368142739463602237/XANA.png?ex=681725b7&is=6815d437&hm=561ccc31cf63b85f25fe126dd5255511946e743ca837c89e47dc60f9708afe48&"},
    {"nom": "Kage", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1368142739195035718/KAGE.png?ex=681725b7&is=6815d437&hm=1f7cb2c615f79654c9e2167ed3febe6dd3184ad3d5c480dc41ef5d6db66a8fa2&"},
    {"nom": "Hades", "image": "https://cdn.discordapp.com/attachments/1367885614053331094/1368142738943639613/HADES.png?ex=681725b7&is=6815d437&hm=963a51358f70992fc733bb937ed61c0a04794a5b38056da3e5793079a9ea9a61&"},
]

cooldown_spawn = 300  # Temps de rechargement entre chaque apparition de monstre (en secondes)
cooldown_zone = 3600 #Temps avant la prochaine zone

async def spawn_monstre():
    await bot.wait_until_ready()

    while not bot.is_closed():
        for guild in bot.guilds:
            server_id = guild.id
            cursor.execute("SELECT channel_id, current_monster, cooldown_rest, cooldown_rest_zone, current_zone FROM settings WHERE server_id = ?", (server_id,))
            result = cursor.fetchone()

            if result:
                channel_id, monstre_existant, cooldown_rest, cooldown_rest_zone, current_zone = result

                
                if cooldown_rest_zone is None or time.time() > cooldown_rest_zone:
                    titre = "⚠️ Attention !"
                    if current_zone is None or current_zone == "HADES":
                        new_zone = "XANA"
                        logo = logos_camps[0]
                        titre += f" Vous voilà dans la zone de {logo['nom']} !"
                        color = discord.Color.red()
                    elif current_zone == "XANA":
                        new_zone = "KAGE"
                        logo = logos_camps[1]
                        titre += f" Vous voici dans la zone de {logo['nom']} !"
                        color = discord.Color.yellow()
                    else:
                        new_zone = "HADES"
                        logo = logos_camps[2]
                        titre += f" Vous voici dans la zone d'{logo['nom']} !"
                        color = discord.Color.purple()

                    cursor.execute("UPDATE settings SET cooldown_rest_zone = ?,  current_zone = ? WHERE server_id = ?", 
                               (time.time() + cooldown_zone, new_zone, server_id))  # Le cooldown est défini ici
                    conn.commit()

                    channel = discord.utils.get(guild.text_channels, id=channel_id)
                    embed = discord.Embed(
                        title=titre,
                        color=color
                    )
                    embed.set_image(url=logo['image'])
                    await channel.send(embed=embed)

                    

                # Si un monstre est déjà actif, on vérifie si son cooldown est écoulé
                if monstre_existant:
                    continue
                    
                if cooldown_rest is None or time.time() < cooldown_rest:
                    continue

                # Sélection aléatoire du monstre
                selection = random.random()
                if current_zone == "XANA":

                    if selection > 0.1:
                        monstre_actuel = random.choice(monstres_basiques_xana)
                    elif selection > 0.05:
                        monstre_actuel = random.choice(ocs_xana)
                    else:
                        potentiel_infinite = random.random()
                        if potentiel_infinite == 0.01:
                            monstre_actuel = monstres_boss_xana[0]
                        else:
                            if selection >= 0.04:
                                monstre_actuel = monstres_boss_xana[3]
                            elif selection == 0.03:
                                monstre_actuel = monstres_boss_xana[2]
                            else:
                                monstre_actuel = monstres_boss_xana[1]                       
                elif current_zone == "KAGE":

                    if selection > 0.1:
                        monstre_actuel = random.choice(monstres_basiques_kage)
                    elif selection > 0.05:
                        monstre_actuel = random.choice(ocs_kage)
                    else:
                            if selection == 0.03:
                                monstre_actuel = monstres_boss_kage[0]
                else:

                    if selection > 0.1:
                        monstre_actuel = random.choice(monstres_basiques_hades)
                    elif selection > 0.05:
                        monstre_actuel = random.choice(ocs_hades)
                    else:
                        potentiel_black = random.random()
                        if potentiel_black == 0.01:
                            monstre_actuel = monstres_boss_hades[0]
                        else:
                            if selection >= 0.04:
                                monstre_actuel = monstres_boss_hades[3]
                            elif selection == 0.03:
                                monstre_actuel = monstres_boss_hades[2]
                            else:
                                monstre_actuel = monstres_boss_hades[1]

                # Mettre à jour dans la base de données
                monstre_json = json.dumps(monstre_actuel)
                cursor.execute("UPDATE settings SET current_monster = ?,  cooldown_rest = ? WHERE server_id = ?", 
                               (monstre_json, time.time() + cooldown_spawn, server_id))  # Le cooldown est défini ici
                conn.commit()

                # Envoi du message dans le canal
                channel = discord.utils.get(guild.text_channels, id=channel_id)
                if channel:
                    if current_zone == "XANA":
                        color= discord.Color.red()
                        titre = "⚠️ Attention ! Xana"
                        description = f"Le premier à taper `/kill` gagne {monstre_actuel['xp']} XP !"

                        if monstre_actuel['nom'] == monstres_boss_xana[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Quoi ?! Mais qu'est ce qu'il fait ici ?! " + description
                        elif monstre_actuel['nom'] == monstres_boss_xana[1]['nom']:
                            titre += f" envoie le {monstre_actuel['nom']} !"
                            description = "Le Kolosse est très puissant ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_xana[2]['nom']:
                            titre += f" a envoyé {monstre_actuel['nom']} !"
                            description = "On dirait qu'il veut en découdre ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_xana[3]['nom']:
                            titre += f" a envoyé la {monstre_actuel['nom']} !"
                            description = "Attention à la xanatification ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_xana[4]['nom']:
                            titre += f" a envoyé le {monstre_actuel['nom']} !"
                            description = "Attention au skid ! " + description
                        elif monstre_actuel['nom'] == ocs_xana[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Mei ! Vient calmer ton frère ! " + description
                        elif monstre_actuel['nom'] == ocs_xana[1]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Prenez garde à son hypnose si vous voulez pas devenir son pantin ! " + description
                        elif monstre_actuel['nom'] == ocs_xana[2]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Le narrateur des descriptions a fui de peur, désolé... (Maxou) " + description
                        elif monstre_actuel['nom'] == ocs_xana[3]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "N'espérez aucune pitié de sa part, vous êtes déjà morts ! " + description
                        elif monstre_actuel['nom'] == ocs_xana[4]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "La météo s'annonce instable, prévoyez un parapluie ! " + description 
                        elif monstre_actuel['nom'] in ["Tarentule", "Manta"]:
                            titre = f"⚠️ Attention ! Une {monstre_actuel['nom']} est apparue !"   
                        else:
                            titre = f"⚠️ Attention ! Un {monstre_actuel['nom']} est apparu !"
                    elif current_zone == "KAGE":
                        color = discord.Color.yellow()
                        titre = "⚠️ Attention ! Kage"
                        description = f"Le premier à taper `/kill` gagne {monstre_actuel['xp']} XP !"

                        if monstre_actuel['nom'] == monstres_boss_kage[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Attention à la Kagefication ! " + description
                        elif monstre_actuel['nom'] == ocs_kage[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Il est l'équivalent de William chez Kage, vous allez en baver ! " + description
                        elif monstre_actuel['nom'] == ocs_kage[1]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Elle ne connait pas la défaite ! Bon courage... " + description
                        elif monstre_actuel['nom'] == ocs_kage[2]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "La fidèle IA de Kage ! Elle désintègre n'importe qui en une seconde !  " + description   
                        else:
                            titre = f"⚠️ Attention ! Un {monstre_actuel['nom']} est apparu !"
                    else:
                        color= discord.Color.purple()
                        titre = "⚠️ Attention ! Hades"
                        description = f"Le premier à taper `/kill` gagne {monstre_actuel['xp']} XP !"

                        if monstre_actuel['nom'] == monstres_boss_hades[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Zarius a encore mal tourné ! Planquez vous ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_hades[1]['nom']:
                            titre += f" envoie le {monstre_actuel['nom']} !"
                            description = "Le Kolosse obscur détruit tout sur son passage ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_hades[2]['nom']:
                            titre += f" envoie la {monstre_actuel['nom']} !"
                            description = "Attention à la Hadesification ! " + description
                        elif monstre_actuel['nom'] == monstres_boss_hades[3]['nom']:
                            titre += f" envoie le {monstre_actuel['nom']} !"
                            description = "Le Skid n'a qu'à bien se tenir ! " + description
                        elif monstre_actuel['nom'] == ocs_hades[0]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Bras droit de Ziggurat, elle éliminera tout les gêneurs de son maitre ! " + description
                        elif monstre_actuel['nom'] == ocs_hades[1]['nom']:
                            titre += f" envoie {monstre_actuel['nom']} !"
                            description = "Le cauchemar de Xana ! Il rapportera toutes ses données à son maitre ! " + description  
                        elif monstre_actuel['nom'] in ["Tarentule obscure", "Manta obscure"]:
                            titre = f"⚠️ Attention ! Une {monstre_actuel['nom']} est apparue !" 
                        else:
                            titre = f"⚠️ Attention ! Un {monstre_actuel['nom']} est apparu !"   
                    embed = discord.Embed(title=titre, description=description, color=color)
                    embed.set_image(url=monstre_actuel['image'])

                    await channel.send(embed=embed)

        await asyncio.sleep(1)

@bot.tree.command(name="next_monster", description="🕒 Affiche le temps restant avant qu'un monstre apparaisse.")
async def nextmonstre(interaction: discord.Interaction):
    server_id = interaction.guild.id

    # Récupérer les données spécifiques à ce serveur : current_monster, cooldown_rest
    cursor.execute("SELECT current_monster, cooldown_rest FROM settings WHERE server_id = ?", (server_id,))
    result = cursor.fetchone()

    if result:
        monstre_actuel, cooldown_rest = result

        # Si un monstre est déjà actif
        if monstre_actuel:
            embed = discord.Embed(
                title="👾 Un monstre est déjà présent !",
                description="Tuez-le d'abord avec `/kill` avant qu'un autre n'apparaisse.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calcul du cooldown si nécessaire
        if cooldown_rest is None:
            # Si jamais la valeur de cooldown_rest est None, on initialise un premier spawn
            cooldown_rest = time.time() + cooldown_spawn
            cursor.execute("UPDATE settings SET cooldown_rest = ? WHERE server_id = ?", (cooldown_rest, server_id))
            conn.commit()
            temps_restant = cooldown_rest - time.time()
            minutes = int(temps_restant // 60)
            secondes = int(temps_restant % 60)
            description = f"Le **prochain monstre** apparaîtra dans **{minutes} min {secondes} sec**."
            couleur = discord.Color.orange()
        else:
            temps_restant = max(0, cooldown_rest - time.time())  # Le cooldown ne peut pas être négatif

            if temps_restant <= 0:
                description = "🔥 Un **nouveau monstre** peut apparaître **à tout moment** !"
                couleur = discord.Color.green()
            else:
                minutes = int(temps_restant // 60)
                secondes = int(temps_restant % 60)
                description = f"Le **prochain monstre** apparaîtra dans **{minutes} min {secondes} sec**."
                couleur = discord.Color.orange()

            # Mise à jour du cooldown dans la base de données pour ce serveur
            cursor.execute("UPDATE settings SET cooldown_rest = ? WHERE server_id = ?", (temps_restant + time.time(), server_id))
            conn.commit()

        embed = discord.Embed(
            title="⏳ Prochain Monstre",
            description=description,
            color=couleur
        )
        await interaction.response.send_message(embed=embed)

    else:
        # Si aucune donnée trouvée pour ce serveur, initialiser les valeurs
        cursor.execute("INSERT INTO settings (server_id, current_monster, cooldown_rest) VALUES (?, ?, ?)",
                       (server_id, None, time.time() + cooldown_spawn))
        conn.commit()
        embed = discord.Embed(
            title="❌ Aucune donnée trouvée pour ce serveur !",
            description="Aucun spawn n'a encore eu lieu. Le cooldown est initialisé.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="next_zone", description="🕒 Affiche le temps restant avant que la zone change.")
async def nextzone(interaction: discord.Interaction):
    server_id = interaction.guild.id

    # Récupérer les données spécifiques à ce serveur : current_monster, cooldown_rest
    cursor.execute("SELECT cooldown_rest_zone FROM settings WHERE server_id = ?", (server_id,))
    result = cursor.fetchone()

    if result:
        cooldown_rest_zone = result[0]

        # Calcul du cooldown si nécessaire
        if cooldown_rest_zone is None:
            # Si jamais la valeur de cooldown_rest est None, on initialise un premier spawn
            cooldown_rest_zone = time.time() + cooldown_zone
            cursor.execute("UPDATE settings SET cooldown_rest = ? WHERE server_id = ?", (cooldown_rest_zone, server_id))
            conn.commit()
            temps_restant = cooldown_rest_zone - time.time()
            minutes = int(temps_restant // 60)
            secondes = int(temps_restant % 60)
            description = f"Le **prochain monstre** apparaîtra dans **{minutes} min {secondes} sec**."
            couleur = discord.Color.orange()
        else:
            temps_restant = max(0, cooldown_rest_zone - time.time())  # Le cooldown ne peut pas être négatif
            print(temps_restant)
            if temps_restant <= 0:
                description = "🔥 La **zone** peut changer **à tout moment** !"
                couleur = discord.Color.green()
            else:
                minutes = int(temps_restant // 60)
                secondes = int(temps_restant % 60)
                description = f"Le **prochain monstre** apparaîtra dans **{minutes} min {secondes} sec**."
                couleur = discord.Color.orange()

            # Mise à jour du cooldown dans la base de données pour ce serveur
            cursor.execute("UPDATE settings SET cooldown_rest_zone = ? WHERE server_id = ?", (temps_restant + time.time(), server_id))
            conn.commit()

        embed = discord.Embed(
            title="⏳ Prochaine zone",
            description=description,
            color=couleur
        )
        await interaction.response.send_message(embed=embed)

    else:
        # Si aucune donnée trouvée pour ce serveur, initialiser les valeurs
        cursor.execute("INSERT INTO settings (server_id, cooldown_rest_zone) VALUES (?, ?, ?)",
                       (server_id, time.time() + cooldown_rest_zone))
        conn.commit()
        embed = discord.Embed(
            title="❌ Aucune donnée trouvée pour ce serveur !",
            description="Aucun spawn n'a encore eu lieu. Le cooldown est initialisé.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)   

@bot.tree.command(name="kill", description="⚔️ Permet d'attaquer le monstre actuellement apparu dans le salon.")
async def kill(interaction: discord.Interaction):
    server_id = interaction.guild.id
    user_id = interaction.user.id
    channel_id = interaction.channel.id

     # Récupérer le salon autorisé depuis la base de données
    cursor.execute("SELECT channel_id FROM settings WHERE server_id = ?", (server_id,))
    result = cursor.fetchone()

    if result and result[0]:  # Si un salon est défini
        monster_channel_id = result[0]
        if channel_id != monster_channel_id:  # Vérifie si l'utilisateur est dans le bon salon
            embed = discord.Embed(
                title="❌ Mauvais salon !",
                description=f"Tu dois utiliser cette commande dans <#{monster_channel_id}>.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)  # Message visible seulement par l'utilisateur
            return

    # Récupérer le monstre en cours
    cursor.execute("SELECT current_monster FROM settings WHERE server_id = ?", (server_id,))
    result = cursor.fetchone()

    if result and result[0]:
        monstre_actuel = json.loads(result[0])
        xp_gagnee = monstre_actuel['xp']

        # Ajouter l'XP à l'utilisateur
        cursor.execute(
            """
            INSERT INTO xp (user_id, server_id, xp) VALUES (?, ?, ?)
            ON CONFLICT(user_id, server_id) DO UPDATE SET xp = xp + ?
            """,
            (user_id, server_id, xp_gagnee, xp_gagnee)
        )
        conn.commit()

        # Mettre à jour le cooldown
        cooldown_timestamp = time.time() + cooldown_spawn
        cursor.execute("UPDATE settings SET current_monster = NULL, cooldown_rest = ? WHERE server_id = ?", 
                       (cooldown_timestamp, server_id))
        conn.commit()

        # Définition du titre et de la description du message de victoire
        nom_monstre = monstre_actuel['nom']

        if nom_monstre in ["Méduse" "Méduse obscure"]:
            article = "la"
        elif nom_monstre in ["Kolosse", "Kalamar", "Kolosse obscur", "Kalamar obscure"]:
            article = "le"
        elif nom_monstre in ["Manta", "Tarentule", "Manta obscure", "Tarentule obscure"]:
            article = "une"
        elif nom_monstre in ["William", "Infinite", "Aiko", "Inaya", "Nightmare", "Anna", "Flora", "Nathaniel", "Clarissa", "Wyvern", "Black", "Yuna", "Corrax"]:
            article = ""
        else:
            article = "un"

        description = f"Félicitations {interaction.user.mention} ! Tu as vaincu {article} {nom_monstre} ! **{xp_gagnee} XP** ont été ajoutés."

        # Création de l'embed
        embed = discord.Embed(description=description, color=discord.Color.green())
        embed.set_thumbnail(url=monstre_actuel["image"])

        # Envoi du message
        await interaction.response.send_message(embed=embed)

        await check_level_up(interaction, user_id, server_id)
    else:
        embed = discord.Embed(
            title="❌ Aucun monstre ici !",
            description="Il n'y a **aucun monstre** à combattre dans ce canal.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Réponse visible uniquement par l'utilisateur

async def check_level_up(interaction, user_id, server_id):
    # Récupérer l'XP et le niveau actuel de l'utilisateur
    cursor.execute("SELECT xp, level FROM xp WHERE user_id = ? AND server_id = ?", (user_id, server_id))
    result = cursor.fetchone()

    if not result:
        return  # L'utilisateur n'a pas encore d'XP enregistrée

    user_xp, current_level = result

    # Vérifier si l'utilisateur atteint un nouveau niveau
    new_level = current_level
    level_threshold = round(get_xp_required(current_level))

    while user_xp >= level_threshold:  # Vérifier s'il peut monter plusieurs niveaux d'un coup
        new_level += 1
        level_threshold = round(get_xp_required(new_level))  # Mettre à jour le palier suivant

    if new_level > current_level:
        # Mettre à jour le niveau de l'utilisateur
        cursor.execute("UPDATE xp SET level = ? WHERE user_id = ? AND server_id = ?", (new_level, user_id, server_id))
        conn.commit()

        embed = discord.Embed(
            title="🎉 Félicitations !",
            description=f"{interaction.user.mention} a atteint le **niveau {new_level}** ! 🎊",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)  # Envoyer un embed pour la montée de niveau

    # Récupérer les rôles associés aux niveaux pour ce serveur
    cursor.execute("SELECT level, role_id FROM roles WHERE server_id = ? ORDER BY level ASC", (server_id,))
    level_roles = cursor.fetchall()

    if not level_roles:
        return  # Aucun rôle défini sur ce serveur, donc pas besoin d’aller plus loin

    # Vérifier si un rôle doit être attribué
    guild = interaction.guild
    member = guild.get_member(user_id)
    if not member:
        return  # L'utilisateur n'est pas sur le serveur

    roles_to_remove = []
    role_to_assign = None

    for lvl, role_id in level_roles:
        if lvl <= new_level:  # Si l'utilisateur a dépassé ou atteint le niveau requis
            role_to_assign = role_id
            roles_to_remove.append(role_id)  # On stocke les anciens rôles

    # Vérifier si l'utilisateur a déjà le rôle à attribuer avant de l'ajouter
    if role_to_assign:
        role = guild.get_role(role_to_assign)
        if role and role not in member.roles:  # Si l'utilisateur n'a pas déjà ce rôle
            # Supprimer les anciens rôles et attribuer le nouveau
            if roles_to_remove:
                roles = [guild.get_role(rid) for rid in roles_to_remove if guild.get_role(rid)]
                await member.remove_roles(*roles)  # Supprimer les rôles précédents

            await member.add_roles(role)  # Ajouter le nouveau rôle
            embed_role = discord.Embed(
                title="🏅 Nouveau Rôle Débloqué !",
                description=f"{interaction.user.mention} a obtenu le rôle {role.mention} ! 👑",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed_role)  # Envoyer un embed pour l'attribution du rôle

def get_xp_required(level: int, base_xp: int = 100, growth_factor: float = 1.5):
    """
    Calculer l'XP nécessaire pour atteindre un niveau donné avec une difficulté croissante.
    La difficulté augmente progressivement avec un facteur de croissance.
    """
    xp_required = base_xp * ((level + 1) ** growth_factor)  # Facteur de croissance exponentielle
    return int(xp_required)


# Commande pour voir l'XP d'un joueur
@bot.tree.command(name="level", description="📊 Affiche votre niveau et votre XP ou ceux du joueur mentionné.")
async def level(interaction: discord.Interaction, member: typing.Optional[discord.Member] = None):
    if member is None:
        member = interaction.user
      
    # Vérification pour éviter les erreurs
    if not isinstance(member, discord.Member):
        await interaction.response.send_message("❌ Erreur : Impossible de récupérer les informations de l'utilisateur.", ephemeral=True)
        return
      
    cursor.execute("SELECT xp, level FROM xp WHERE user_id = ? AND server_id = ?", (member.id, interaction.guild.id))
    result = cursor.fetchone()

    if result is None:
        xp = 0
        level = 1
    else:
        xp = result[0]
        level = result[1]

    # Création de l'embed
    embed = discord.Embed(
        title="📊 Statistiques de joueur",
        description=f"{member.mention} est **niveau {level}** avec **{xp} XP** !",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)



@bot.tree.command(name="leaderboard", description="🏆 Affiche le classement des 10 meilleurs joueurs en XP sur ce serveur.")
async def leaderboard(interaction: discord.Interaction):
    # Récupérer les 10 meilleurs joueurs par XP et leur niveau pour ce serveur
    cursor.execute("SELECT user_id, xp, level FROM xp WHERE server_id = ? ORDER BY xp DESC LIMIT 10", (interaction.guild.id,))
    top_players = cursor.fetchall()

    # Si aucun joueur n'a encore gagné d'XP
    if not top_players:
        await interaction.response.send_message("❌ Aucun joueur n'a encore gagné d'XP sur ce serveur.", ephemeral=True)
        return

    # Création de l'embed
    embed = discord.Embed(
        title="🏆 Classement des meilleurs joueurs 🏆",
        description="Voici le top 10 des joueurs de ce serveur !",
        color=discord.Color.gold()
    )

    # Construire le classement
    for rank, (user_id, xp, level) in enumerate(top_players, 1):
        # Récupérer le membre
        member = interaction.guild.get_member(user_id)

        # Vérifier si le membre existe
        if member:
            embed.add_field(name=f"#{rank} - {member.name}", value=f"**XP**: {xp} | **Niveau**: {level}", inline=False)
        else:
            embed.add_field(name=f"#{rank} - Utilisateur inconnu (ID: {user_id})", value=f"**XP**: {xp} | **Niveau**: {level}", inline=False)

    # Envoyer l'embed
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="set_channel", description="📢 Définit le salon actuel comme celui où les monstres apparaîtront. Administrateurs uniquement.")
@commands.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Définit le salon où le bot postera ses messages."""

    server_id = interaction.guild.id

    # Mettre à jour la base de données
    cursor.execute(
        "INSERT OR REPLACE INTO settings (server_id, channel_id, cooldown_rest) VALUES (?, ?, ?)",
        (server_id, channel.id, time.time() + cooldown_spawn)
    )
    conn.commit()
    cursor.execute("UPDATE settings SET current_monster = NULL WHERE server_id = ?", (server_id,))
    conn.commit()

    # Création de l'embed
    embed = discord.Embed(
        title="✅ Salon défini",
        description=f"Le salon {channel.mention} a été défini comme salon d'apparition des monstres et des messages.",
        color=discord.Color.green()
    )

    # Envoyer l'embed
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="view_channel", description="👁️ Affiche le salon d'apparition actuel des monstres. Administrateurs uniquement.")
@commands.has_permissions(administrator=True)
async def voir_channel(interaction: discord.Interaction):
    """Affiche le salon défini pour l'apparition des monstres."""
    
    server_id = interaction.guild.id

    cursor.execute("SELECT channel_id FROM settings WHERE server_id = ?", (server_id,))
    result = cursor.fetchone()

    if result and result[0]:
        salon = interaction.guild.get_channel(result[0])
        if salon:
            description = f"Les monstres apparaissent actuellement dans le salon {salon.mention}."
        else:
            description = "⚠️ Le salon défini n'existe plus ou le bot n'y a pas accès."
    else:
        description = "❌ Aucun salon n'a été défini pour l'apparition des monstres."

    embed = discord.Embed(
        title="📍 Salon d'apparition",
        description=description,
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="set_role", description="🏅 Associe un rôle spécifique à un niveau donné. Administrateurs uniquement.")
@commands.has_permissions(administrator=True)
async def set_role(interaction: discord.Interaction, level: int, role: discord.Role):
    """Définit le rôle à attribuer à un joueur lorsqu'il atteint un certain niveau."""

    server_id = interaction.guild.id

    # Enregistrement du rôle dans la base de données pour le niveau donné
    cursor.execute(
        "INSERT INTO roles (server_id, level, role_id) VALUES (?, ?, ?) "
        "ON CONFLICT(server_id, level) DO UPDATE SET role_id = ?",
        (server_id, level, role.id, role.id)
    )
    conn.commit()

    # Création de l'embed
    embed = discord.Embed(
        title="✅ Rôle défini avec succès",
        description=f"Le rôle {role.mention} sera attribué aux joueurs qui atteindront le niveau {level}.",
        color=discord.Color.green()
    )

    # Envoi de l'embed
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="view_roles", description="📜 Affiche les rôles associés aux niveaux. Administrateurs uniquement.")
@commands.has_permissions(administrator=True)
async def view_roles(interaction: discord.Interaction):
    """Affiche les rôles associés aux niveaux pour le serveur."""  

    server_id = interaction.guild.id

    # Récupérer tous les rôles associés aux niveaux pour ce serveur
    cursor.execute("SELECT level, role_id FROM roles WHERE server_id = ?", (server_id,))
    roles = cursor.fetchall()

    if roles:
        description = "Voici les rôles associés aux niveaux :\n"
        for level, role_id in roles:
            role = interaction.guild.get_role(role_id)
            if role:
                description += f"**Niveau {level}** : {role.mention}\n"
            else:
                description += f"**Niveau {level}** : Rôle supprimé\n"
        
        embed = discord.Embed(
            title="📜 Rôles associés aux niveaux",
            description=description,
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="❌ Aucun rôle trouvé",
            description="Aucun rôle n'a été associé à un niveau dans ce serveur.",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove_role", description="❌ Supprime un rôle associé à un niveau. Administrateurs uniquement.")
@commands.has_permissions(administrator=True)
async def remove_role(interaction: discord.Interaction, level: int):
    """Supprime le rôle associé à un niveau donné."""  

    server_id = interaction.guild.id

    # Vérifier si le rôle existe pour ce niveau
    cursor.execute("SELECT role_id FROM roles WHERE server_id = ? AND level = ?", (server_id, level))
    result = cursor.fetchone()

    if result:
        role_id = result[0]
        cursor.execute("DELETE FROM roles WHERE server_id = ? AND level = ?", (server_id, level))
        conn.commit()

        embed = discord.Embed(
            title="✅ Rôle supprimé avec succès",
            description=f"Le rôle associé au niveau {level} a été supprimé.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="❌ Aucun rôle associé à ce niveau",
            description=f"Aucun rôle n'est associé au niveau {level}.",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="infos", description="📜 Affiche la liste des commandes disponibles du bot.")
async def infos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Liste des Commandes",
        description="Voici toutes les commandes disponibles pour le bot !",
        color=discord.Color.blue()
    )

    # Catégorie XP et Niveau
    embed.add_field(name="🆙 **XP & Niveau**", value=(
        "`/kill` - Tue le monstre actuel et gagne de l'XP.\n"
        "`/level [@joueur]` - Affiche le niveau et l'xp d'un joueur ou ceux du joueur mentionné.\n"
        "`/leaderboard` - Affiche le classement des joueurs par XP."
    ), inline=False)

    # Catégorie Monstres
    embed.add_field(name="👾 **Monstres et zones**", value=(
        "`/next_monster` - Indique quand le prochain monstre apparaîtra. \n"
        "`/next_zone` - Indique quand la zone changera. \n"
    ), inline=False)

    # Catégorie Gestion des rôles et du canal
    embed.add_field(name="🔧 **Gestion des Rôles & Canal**", value=(
        "`/set_role [niveau] @role` - Assigne un rôle de récompense aux joueurs après avoir atteint un certain niveau. Administrateurs uniquement.\n"
        "`/remove_role [niveau]` - Supprime le rôle associé à un niveau. Administrateurs uniquement.\n"
        "`/view_roles` - Affiche les rôles associés aux niveaux. Administrateurs uniquement.\n"
        "`/set_channel #channel` - Indique le canal où les monstres apparaîtront. Administrateurs uniquement.\n"
        "`/view_channel` - Affiche le salon d'apparition actuel des monstres. Administrateurs uniquement."
    ), inline=False)

    # Catégorie Divers
    embed.add_field(name="⚙ **Autres**", value=(
        "`/infos` - Affiche cette liste de commandes.\n"
    ), inline=False)

    # Ajouter un pied de page
    embed.set_footer(text="Lyoko Warzone Bot • Créé par Maxou", icon_url=interaction.client.user.avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est connecté et prêt"""
    print(f"{bot.user} est maintenant connecté !")

    # Vérifier chaque serveur et initialiser s'il n'a pas été configuré
    for guild in bot.guilds:
        cursor.execute("SELECT server_id FROM settings WHERE server_id = ?", (guild.id,))
        result = cursor.fetchone()

        if not result:
            # Si le serveur n'a pas encore d'entrée dans la base de données, on l'initialise
            channel_id = None 
            init_server(guild.id, channel_id)
    # Synchronisation des commandes slash
    await bot.tree.sync()

    # Lancer la boucle de spawn de monstre après l'initialisation
    bot.loop.create_task(spawn_monstre())

# Fonction appelée lors de l'ajout du bot à un serveur
@bot.event
async def on_guild_join(guild):
    """Événement déclenché lorsqu'un serveur rejoint le bot"""
    print(f"{bot.user} a rejoint le serveur {guild.name} ({guild.id})")

    # Vérifier si le serveur est déjà dans la base de données
    cursor.execute("SELECT server_id FROM settings WHERE server_id = ?", (guild.id,))
    result = cursor.fetchone()

    if not result:
        # Si le serveur n'a pas encore d'entrée dans la base de données
        # On initialise le canal à None pour éviter d'envoyer des messages par erreur
        channel_id = None
        init_server(guild.id, channel_id)

    # Ajoute une pause pour éviter de surcharger l'API
    await asyncio.sleep(1)  # Délai d'une seconde entre les actions

def init_server(server_id, channel_id):
    """Initialiser un serveur dans la base de données avec ses paramètres"""
    cursor.execute("INSERT INTO settings (server_id, channel_id) VALUES (?, ?)", (server_id, channel_id))
    conn.commit()

# Lancer le bot
bot.run(token)