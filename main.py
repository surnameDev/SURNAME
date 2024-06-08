import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import config
from config import TOKEN

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=',', help_command=None, intents=intents)

# ID роли для бана
ban_role_id = YOU_ID

# Словарь для хранения временных мутов
temporary_mutes = {}

# Список ID разрешенных ролей и их соответствующих команд
allowed_roles = {
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban", "unban", "permban", "unpermban", "addrole", "delrole", "kick"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban", "unban", "permban", "unpermban", "addrole", "delrole", "kick"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban", "unban", "permban", "unpermban", "addrole", "delrole", "kick"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban", "unban", "permban", "unpermban", "addrole", "delrole", "kick"],
    YOU_ID: ["clear", "mute", "unmute", "addnick", "ban", "unban", "permban","kick", "unpermban"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban", "unban"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban",],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick", "ban"],
    YOU_ID: ["clear", "mute", "unmute", "delnick", "addnick"]
}

def has_allowed_role(command):
    async def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False  # Команда не может быть использована в личных сообщениях

        allowed_commands = allowed_roles.get(ctx.author.top_role.id, [])
        if command in allowed_commands:
            return True
        else:
            return False

    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'Вошел в систему как {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="В разработке..."))
    check_temp_bans.start()
    check_temp_mutes.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Ошибка",
            description="Команда не найдена. Используйте `,help` для списка доступных команд.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        # Если ошибка не CommandNotFound, пробрасываем ее дальше для стандартной обработки
        raise error

@tasks.loop(minutes=1)
async def check_temp_bans():
    current_time = datetime.now()
    for member_id, unban_time in list(temporary_bans.items()):
        if unban_time is not None and current_time >= unban_time:
            guild_id, role_ids = roles_before_ban.get(member_id, (None, []))
            if guild_id is None:
                continue
            guild = bot.get_guild(guild_id)
            if guild is None:
                continue
            member = guild.get_member(member_id)
            if member:
                roles = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]
                await member.edit(roles=roles, reason="Автоматический разбан")
            del temporary_bans[member_id]
            del roles_before_ban[member_id]

@tasks.loop(minutes=1)
async def check_temp_mutes():
    current_time = datetime.now()
    for member_id, unmute_time in list(temporary_mutes.items()):
        if current_time >= unmute_time[1]:
            guild = bot.get_guild(unmute_time[0])
            member = guild.get_member(member_id)
            if member:
                await member.edit(timed_out_until=None, reason="Автоматический размут")
            del temporary_mutes[member_id]

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member = None, role: discord.Role = None):
    if member is None:
        await ctx.send("Вы не указали пользователя.")
        return
    if role is None:
        await ctx.send("Вы не указали роль.")
        return

    await member.add_roles(role)
    await ctx.send(f"Роль {role.name} успешно добавлена пользователю {member.mention}.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def delrole(ctx, member: discord.Member = None, role: discord.Role = None):
    if member is None:
        await ctx.send("Вы не указали пользователя.")
        return
    if role is None:
        await ctx.send("Вы не указали роль.")
        return

    await member.remove_roles(role)
    await ctx.send(f"Роль {role.name} успешно удалена у пользователя {member.mention}.")

@bot.command(name='help')
async def commands_list(ctx):
    user_role_id = ctx.author.top_role.id
    allowed_commands = allowed_roles.get(user_role_id, [])

    if not allowed_commands:
        embed = discord.Embed(
            title="Недостаточно прав",
            description="У вас нет разрешенных команд.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="Список команд",
        description="Доступные команды и их описание",
        color=0x00ff00,
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
    embed.set_footer(text="Используйте команды ответственно", icon_url=ctx.author.avatar.url)

    command_descriptions = {
        "ban": "@user Время в минутах Причина | Временно банит пользователя.",
        "permban": "@user Причина | Банит пользователя навсегда.",
        "unban": "@user | Снимает бан пользователю.",
        "unpermban": "@user | Снимает вечный бан с пользователя.",
        "mute": "@user Время в минутах Причина | Временно мутит пользователя.",
        "unmute": "@user | Снимает мут пользователю.",
        "clear": "Очищает указанное количество сообщений, или одно сообщение по ID.",
        "addnick": "@user Ник | Устанавливает пользователю никнейм.",
        "delnick": "@user Ник | Убирает никнейм пользователю.",
        "addrole": "@user @роль | Добавляет роль пользователю.",
        "delrole": "@user @role | Удаляет роль у пользователя.",
        "kick": "@user Причина | Исключает пользователя.",
        "help": "Отображает данный список"
    }
    
    for command in allowed_commands:
        embed.add_field(name=command, value=command_descriptions.get(command, "Описание отсутствует."), inline=False)

    await ctx.send(embed=embed)

@bot.command()
@has_allowed_role("ping")
async def ping(ctx):
    embed = discord.Embed(
            title="Pong",
            color=discord.Color.green()
        )
    await ctx.send(embed=embed)

#kick
@bot.command()
@has_allowed_role("kick")
async def kick(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы должны указать причину для кика.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if member.top_role.position >= ctx.author.top_role.position or member.top_role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не можете кикнуть пользователя с ролью, которая находится выше вашей или бота в иерархии.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        await member.kick(reason=f"{reason} (Модератор: {ctx.author})")
        embed = discord.Embed(
            title="Успешно",
            description=f'{member.mention} был кикнут по причине: {reason}',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="Ошибка",
            description="У меня недостаточно прав для кика этого пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            title="Ошибка",
            description=f"Произошла ошибка при попытке кика: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
# Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="Исключен пользователь",
            description=f"Пользователь {member.mention} был исключен по причине: {reason}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

# Глобальные словари для хранения данных о временных банах
temporary_bans = {}  # Хранение информации о временных банах (user_id: unban_time)
banned_users = {}  # Хранение информации о банах (user_id: (guild_id, role_ids))
roles_before_ban = {}  

@bot.command()
@has_allowed_role("ban")  # Проверяем, есть ли у пользователя роль "ban"
async def ban(ctx, member: discord.Member = None, duration: int = None, *, reason=None):
    # Проверка наличия аргументов
    if member is None or duration is None or reason is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не указали все необходимые аргументы: пользователя, продолжительность бана и причину.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Проверка иерархии ролей
    if member.top_role.position >= ctx.author.top_role.position or member.top_role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не можете забанить пользователя с ролью, которая находится выше вашей или бота в иерархии.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Сохраняем текущие роли и ID гильдии
    roles_before_ban[member.id] = (ctx.guild.id, [role.id for role in member.roles])
    
    # Удаляем все роли у пользователя
    await member.edit(roles=[], reason=f"{reason} (Модератор: {ctx.author})")
    
    # Добавляем роль бана
    ban_role = ctx.guild.get_role(ban_role_id)
    await member.add_roles(ban_role, reason=f"{reason} (Модератор: {ctx.author})")

    # Устанавливаем время для разбана
    unban_time = datetime.now() + timedelta(minutes=duration)
    temporary_bans[member.id] = unban_time

    embed = discord.Embed(
        title="Успешно",
        description=f'{member.mention} был забанен на {duration} минут по причине: {reason}',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)  # ID вашего лог-канала
    if log_channel:
        log_embed = discord.Embed(
            title="Пользователь забанен",
            description=f"Пользователь {member.mention} был забанен на {duration} минут по причине: {reason}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("permban")  # Проверяем, есть ли у пользователя роль "permban"
async def permban(ctx, member: discord.Member = None, *, reason=None):
    # Проверка наличия аргументов
    if member is None or reason is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не указали все необходимые аргументы: пользователя и причину.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Проверка иерархии ролей
    if member.top_role.position >= ctx.author.top_role.position or member.top_role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не можете забанить пользователя с ролью, которая находится выше вашей или бота в иерархии.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Добавляем пользователя в список заблокированных
    banned_users.add(member.id)

    # Сохраняем текущие роли и ID гильдии
    roles_before_ban[member.id] = (ctx.guild.id, [role.id for role in member.roles])
    
    # Удаляем все роли у пользователя
    await member.edit(roles=[], reason=f"{reason} (Модератор: {ctx.author})")
    
    # Добавляем роль бана
    ban_role = ctx.guild.get_role(ban_role_id)
    await member.add_roles(ban_role, reason=f"{reason} (Модератор: {ctx.author})")

    embed = discord.Embed(
        title="Успешно",
        description=f'{member.mention} был забанен навсегда по причине: {reason}',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)  # ID вашего лог-канала
    if log_channel:
        log_embed = discord.Embed(
            title="Пользователь забанен",
            description=f"Пользователь {member.mention} был забанен навсегда по причине: {reason}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("unban")  # Проверяем, есть ли у пользователя роль "unban"
async def unban(ctx, member: discord.Member = None):
    log_channel = bot.get_channel(YOU_ID)  # ID вашего лог-канала

    if member is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не указали пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        if log_channel:
            log_embed = discord.Embed(
                title="Ошибка команды",
                description=f"Пользователь {ctx.author.mention} попытался разбанить без указания пользователя.",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log_embed)
        return

    # Проверка наличия пользователя в забаненных
    if member.id not in temporary_bans:
        embed = discord.Embed(
            title="Ошибка",
            description="Этот пользователь не обнаружен в списке заблокированых.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        if log_channel:
            log_embed = discord.Embed(
                title="Ошибка команды",
                description=f"Пользователь {ctx.author.mention} попытался разбанить пользователя {member.mention}, который не забанен или был забанен не этой командой.",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log_embed)
        return

    # Снимаем роль бана
    ban_role = ctx.guild.get_role(ban_role_id)
    await member.remove_roles(ban_role, reason="Разбан")

    # Восстанавливаем роли пользователя
    guild_id, role_ids = roles_before_ban.get(member.id, (None, []))
    if guild_id is not None:
        guild = bot.get_guild(guild_id)
        if guild:
            member = guild.get_member(member.id)
            if member:
                roles = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]
                await member.edit(roles=roles, reason="Разбан")

    # Удаляем пользователя из временных банов
    del roles_before_ban[member.id]

    embed = discord.Embed(
        title="Успешно",
        description=f'{member.mention} был разбанен.',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Отправляем сообщение в лог-канал
    if log_channel:
        log_embed = discord.Embed(
            title="Пользователь разбанен",
            description=f"Пользователь {member.mention} был разбанен.",
            color=discord.Color.green()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("unpermban")  # Проверяем, есть ли у пользователя роль "unban"
async def unpermban(ctx, member: discord.Member = None):
    log_channel = bot.get_channel(YOU_ID)  # ID вашего лог-канала

    if member is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не указали пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        if log_channel:
            log_embed = discord.Embed(
                title="Ошибка команды",
                description=f"Пользователь {ctx.author.mention} попытался разбанить без указания пользователя.",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log_embed)
        return

    # Проверяем, был ли пользователь постоянно заблокирован
    if member.id in banned_users:
        # Снимаем постоянный бан
        try:
            await member.unban(reason="Разбан")
            embed = discord.Embed(
                title="Успешно",
                description=f'{member.mention} был разбанен.',
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Ошибка",
                description="У меня недостаточно прав для разбана этого пользователя.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при попытке разбана: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        # Отправляем сообщение в лог-канал
        if log_channel:
            log_embed = discord.Embed(
                title="Пользователь разбанен",
                description=f"Пользователь {member.mention} был разбанен.",
                color=discord.Color.green()
            )
            await log_channel.send(embed=log_embed)
    else:
        embed = discord.Embed(
            title="Ошибка",
            description="Этот пользователь не обнаружен в списке заблокированых.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        if log_channel:
            log_embed = discord.Embed(
                title="Ошибка команды",
                description=f"Пользователь {ctx.author.mention} попытался разбанить пользователя {member.mention}, который не забанен или был забанен не этой командой.",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("mute")
async def mute(ctx, member: discord.Member = None, duration: str = None, *, reason: str = None):
    if member is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не упомянули пользователя, которому нужно выдать наказание.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if duration is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не указали длительность мута.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        duration = int(duration)
    except ValueError:
        embed = discord.Embed(
            title="Ошибка",
            description="Продолжительность мута должна быть числом.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if duration <= 0:
        embed = discord.Embed(
            title="Ошибка",
            description="Продолжительность мута должна быть положительным числом.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if reason is None:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы должны указать причину для мута.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if member.top_role.position >= ctx.author.top_role.position or member.top_role.position >= ctx.guild.me.top_role.position:
        embed = discord.Embed(
            title="Ошибка",
            description="Вы не можете выдать мут пользователю с ролью, которая находится выше вашей или бота в иерархии.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if member.id in temporary_mutes:
        embed = discord.Embed(
            title="Ошибка",
            description="Этот пользователь уже имеет мут.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Проверяем права бота
    if not ctx.guild.me.guild_permissions.manage_roles:
        embed = discord.Embed(
            title="Ошибка",
            description="У бота нет прав для управления ролями.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if not ctx.guild.me.guild_permissions.moderate_members:
        embed = discord.Embed(
            title="Ошибка",
            description="У бота нет прав для управления тайм-аутами пользователей.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Выдаем мут пользователю (тайм-аут)
    timeout_duration = timedelta(minutes=duration)
    unmute_time = datetime.now() + timeout_duration

    try:
        await member.edit(timed_out_until=unmute_time, reason=f"{reason} (Модератор: {ctx.author})")
        temporary_mutes[member.id] = (ctx.guild.id, unmute_time)
        embed = discord.Embed(
            title="Успешно",
            description=f'{member.mention} был замучен на {duration} минут по причине: {reason}',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="Ошибка",
            description="У меня недостаточно прав для мута этого пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            title="Ошибка",
            description=f"Произошла ошибка при попытке мута: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="Пользователю выдан мут",
            description=f"Пользователю {member.mention} был выдан мут на {duration} минут по причине: {reason}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("clear")
async def clear(ctx, amount: Optional[int] = 1, message_id: Optional[int] = None):
    if message_id:
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.delete()
            embed = discord.Embed(
                title="Успешно",
                description=f"Сообщение с ID {message_id} было удалено.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.NotFound:
            embed = discord.Embed(
                title="Ошибка",
                description="Сообщение с указанным ID не найдено.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Ошибка",
                description="У меня недостаточно прав для удаления этого сообщения.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при попытке удаления сообщения: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    else:
        try:
            deleted = await ctx.channel.purge(limit=amount)
            embed = discord.Embed(
                title="Успешно",
                description=f"Удалено {len(deleted)} сообщений.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Ошибка",
                description="У меня недостаточно прав для удаления сообщений.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при попытке удаления сообщений: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

# Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="Сообщения удалины",
            description=f"Администратор {ctx.author.mention} очистил сообщение.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("addnick")
async def addnick(ctx, member: discord.Member, *, nickname: str):
    try:
        await member.edit(nick=nickname, reason=f"Изменение ника по запросу {ctx.author}")
        embed = discord.Embed(
            title="Успешно",
            description=f"Никнейм пользователя {member.mention} был изменен на {nickname}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="Ошибка",
                        description="У меня недостаточно прав для изменения никнейма этого пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            title="Ошибка",
            description=f"Произошла ошибка при попытке изменения никнейма: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
# Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="Изменен ник",
            description=f"Администратор {ctx.author.mention} изменил ник пользователю {member.mention}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

@bot.command()
@has_allowed_role("delnick")
async def delnick(ctx, member: discord.Member):
    try:
        await member.edit(nick=None, reason=f"Удаление ника по запросу {ctx.author}")
        embed = discord.Embed(
            title="Успешно",
            description=f"Никнейм пользователя {member.mention} был сброшен.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="Ошибка",
            description="У меня недостаточно прав для удаления никнейма этого пользователя.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            title="Ошибка",
            description=f"Произошла ошибка при попытке удаления никнейма: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Отправляем сообщение в лог-канал
    log_channel = bot.get_channel(YOU_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="Изменен ник",
            description=f"Администратор {ctx.author.mention} удалил ник пользователю {member.mention}.",
            color=discord.Color.red()
        )
        await log_channel.send(embed=log_embed)

# Загрузка токена бота из файла конфигурации или переменной окружения
bot.run(TOKEN)