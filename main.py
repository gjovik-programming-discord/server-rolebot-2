import discord
import os
import regex
from discord.utils import get
from discord.ext import commands

# Set intents for member management
intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="", intents=intents)

# Set up values
welcome_msg = """__Norwegian:__
Velkommen til Programmering i Gjøvik NTNU discord kanalen {name}!
Vennligst oppgi klassen din (eller staff hvis du er ansatt ved NTNU) og ditt fulle navn i {welcome} kanalen på følgende format:
`<klasse> <fullt navn>`
Eksempel:
`14HBSPA Ola Nordmann`
Vennligst les reglene i {rules} kanalen og ha et hyggelig opphold. Kontakt gjerne en @admin dersom du har noen spørsmål.

__English:__
Welcome to the programming discord for NTNU Gjøvik {name}!
Please state your class (or staff if you work at NTNU) and your full name in the {welcome} channel in the following format:
`<class> <full name>`
Example:
`14HBSPA Ola Nordmann`
Please read the rules in {rules} and enjoy your stay. Feel free to contact an @admin if you have any questions.
"""
class_regex = "(\d\d[A-Z]{5,8})|MACS|ALUMNI|INTERNATIONAL"
channelID_welcome = os.environ['channel_ID_welcome']
channelID_rules = os.environ['channel_ID_rules']

# Helper function spliting a string into 3 parts if regex part is found
# 1: Everything before the regex if found, everything otherwise
# 2: The regex if found, empty otherwise
# 3: Everything after the regex, empty otherwise
def regex_partition(content, separator):
  separator_match = regex.search(separator, content)
  if not separator_match:
    return content, '', ''
  
  matched_separator = separator_match.group(0)
  parts = regex.split(matched_separator, content, 1)
  return parts[0], matched_separator, parts[1]

# Message and @Admin in case anything goes wrong
async def something_went_wrong():
  msg = "Oops, something went wrong!\nAn <@&{roleID}> will be here shortly!"
  channel = await client.fetch_channel(channelID_welcome)
  roleID = get(channel.guild.roles, name="admin").id
  await channel.send(msg.format(roleID=roleID))

async def staff_call_admin():
  msg = "Hi staff!\nAn <@&{roleID}> will be here shortly!"
  channel = await client.fetch_channel(channelID_welcome)
  roleID = get(channel.guild.roles, name="admin").id
  await channel.send(msg.format(roleID=roleID))

# Edit the member's nickname and roles
async def edit_member_name_role(message):
  member_roles = message.author.roles
  is_unnamed = False

  for role in member_roles:
    if role.name == "Unnamed":
      is_unnamed = True
      member_roles.remove(role)

  # Return early if member role isn't Unnamed (has gotten a class)
  if not is_unnamed:
    return

  role_exist = False
  guild_roles = message.guild.roles
  split_string = regex_partition(message.content, class_regex)
  name_index = 0 if split_string[0] else 2

  # Check if the class exists as a roll
  for role in guild_roles:
    if split_string[1] == role.name:
      role_exist = True
      member_roles.append(role)
      break

  # If the class doesn't exist something went wrong
  if not role_exist:
    match = regex.search("staff", message.content, regex.IGNORECASE)
    if match:
      await staff_call_admin()
    else:
      await something_went_wrong()

    return

  # Try to edit the member with new role and nickname
  try:
    await message.author.edit(nick=split_string[name_index].lstrip(), roles=member_roles)
  except discord.Forbidden as e:
    print(e)
    await something_went_wrong()
  except discord.HTTPException as e:
    print(e)
    await something_went_wrong()
  
# Wait for member to join, set's role to "UNNAMED" and changes nickname
@client.event
async def on_member_join(member):
  member_roles = member.roles
  member_roles.append(get(member.guild.roles, name="Unnamed"))
  channel = await client.fetch_channel(channelID_welcome)
  welcome_mention = channel.mention
  rules_mention = (await client.fetch_channel(channelID_rules)).mention
  await channel.send(welcome_msg.format(name=member.mention, welcome=welcome_mention, rules=rules_mention))
  try:
    await member.edit(roles=member_roles)
  except discord.Forbidden as e:
    print(e)
    await something_went_wrong()
  except discord.HTTPException as e:
    print(e)
    await something_went_wrong()

# Wait for message in the welcome channel, returns early if not correct channel, DM or from bot
@client.event
async def on_message(message):
  if str(message.channel.id) != str(channelID_welcome):
    return
  if message.author.bot:
    return

  await edit_member_name_role(message)

@client.event
async def on_ready():
  print('BOT ready')

client.run(os.environ['TOKEN'])
