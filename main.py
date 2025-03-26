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
    cooldown_rest INTEGER
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
monstres_basiques = [
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

kolosse = {"nom": "Kolosse", "xp": 500, "image": "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c0260ac6-f0fa-4be7-a21d-ff98d393c58d/ded081s-a0b1d714-303a-4b0b-8838-6d2fec3f9f31.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcL2MwMjYwYWM2LWYwZmEtNGJlNy1hMjFkLWZmOThkMzkzYzU4ZFwvZGVkMDgxcy1hMGIxZDcxNC0zMDNhLTRiMGItODgzOC02ZDJmZWMzZjlmMzEucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.fYkOKEy9RggNoiX45K5_lq6iHtSYBZHjAm0pTTAbEJA"}

méduse = {"nom": "Méduse", "xp": 300, "image": "https://static.wikia.nocookie.net/codelyoko/images/3/3e/M%C3%A9duse.jpg/revision/latest?cb=20120105195726&path-prefix=fr"}

william = {"nom": "William", "xp": 400, "image": "https://pm1.aminoapps.com/6164/9348a6cce9fd07343464c2aa4c3c2af3ecaa6e8a_00.jpg"}

kalamar = {"nom": "Kalamar", "xp": 200, "image": "https://static.wikia.nocookie.net/codelyoko/images/9/98/Kalamar.jpg/revision/latest?cb=20120105195727&path-prefix=fr"}

probabilite_kolosse = 0.05  # 5% chance d'apparition du Kolosse
probabilite_william = 0.08  # 10% chance d'apparition de William
probabilite_méduse = 0.10  # 15% chance d'apparition de la Méduse
probabilite_kalamar = 0.15  # 20% chance d'apparition du Kalamar
probabilite_monstre = 1 - probabilite_kolosse - probabilite_méduse - probabilite_william - probabilite_kalamar  # 90% chance d'apparition d'un monstre basique


cooldown_spawn = 10  # Temps de rechargement entre chaque apparition de monstre (en secondes)

async def spawn_monstre():
    await bot.wait_until_ready()

    while not bot.is_closed():
        for guild in bot.guilds:
            server_id = guild.id
            cursor.execute("SELECT channel_id, current_monster, cooldown_rest FROM settings WHERE server_id = ?", (server_id,))
            result = cursor.fetchone()

            if result:
                channel_id, monstre_existant, cooldown_rest = result

                # Si un monstre est déjà actif, on vérifie si son cooldown est écoulé
                if monstre_existant:
                    continue
                    
                if cooldown_rest is None or time.time() < cooldown_rest:
                    continue

                # Sélection aléatoire du monstre
                if random.random() <= probabilite_kolosse:
                    monstre_actuel = kolosse
                elif random.random() <= probabilite_william:
                    monstre_actuel = william
                elif random.random() <= probabilite_méduse:
                    monstre_actuel = méduse
                elif random.random() <= probabilite_kalamar:
                    monstre_actuel = kalamar
                else:
                    monstre_actuel = random.choice(monstres_basiques)

                # Mettre à jour dans la base de données
                monstre_json = json.dumps(monstre_actuel)
                cursor.execute("UPDATE settings SET current_monster = ?,  cooldown_rest = ? WHERE server_id = ?", 
                               (monstre_json, time.time() + cooldown_spawn, server_id))  # Le cooldown est défini ici
                conn.commit()

                # Envoi du message dans le canal
                channel = discord.utils.get(guild.text_channels, id=channel_id)
                if channel:
                    titre = "⚠️ Attention !"
                    description = f"Le premier à taper `/kill` gagne {monstre_actuel['xp']} XP !"

                    if monstre_actuel == kolosse:
                        titre += f" Xana envoie le {monstre_actuel['nom']} !"
                        description = "Le Kolosse est très puissant ! " + description
                    elif monstre_actuel == william:
                        titre += f" Xana a envoyé {monstre_actuel['nom']} !"
                        description = "On dirait qu'il veut en découdre ! " + description
                    elif monstre_actuel == méduse:
                        titre += f" Xana a envoyé la {monstre_actuel['nom']} !"
                        description = "Attention à la xanatification ! " + description
                    elif monstre_actuel == kalamar:
                        titre += f" Xana a envoyé le {monstre_actuel['nom']} !"
                        description = "Attention au skid ! " + description
                    elif monstre_actuel['nom'] in ["Tarentule", "Manta"]:
                        titre += f" Une {monstre_actuel['nom']} est apparue !"
                    else:
                        titre += f" Un {monstre_actuel['nom']} est apparu !"

                    embed = discord.Embed(title=titre, description=description, color=discord.Color.red())
                    embed.set_image(url=monstre_actuel['image'])

                    await channel.send(embed=embed)

        await asyncio.sleep(1)

@bot.tree.command(name="nextmonstre", description="🕒 Affiche le temps restant avant qu'un monstre apparaisse.")
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
                       (server_id, None, cooldown_spawn))
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

        if nom_monstre == "Méduse":
            article = "la"
        elif nom_monstre in ["Kolosse", "Kalamar", "William"]:
            article = "le"
        elif nom_monstre in ["Manta", "Tarentule"]:
            article = "une"
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
        title="📊 Statistiques d'XP",
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
        description="Voici le top 10 des joueurs ayant le plus d'XP sur ce serveur !",
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
    embed.add_field(name="👾 **Monstres**", value=(
        "`/nextmonstre` - Indique quand le prochain monstre apparaîtra."
    ), inline=False)

    # Catégorie Gestion des rôles et du canal
    embed.add_field(name="🔧 **Gestion des Rôles & Canal**", value=(
        "`/set_role [niveau] @role` - Assigner un rôle de récompense aux joueurs après avoir atteint un certain niveau.\n"
        "`/set_channel #channel` - Indique le canal où les monstres apparaîtront."
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