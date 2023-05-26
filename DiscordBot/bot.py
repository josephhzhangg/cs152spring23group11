# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
import pdb

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.reports = {}  # Map from user IDs to the state of their report

        self.vote_cache = {}  # For voting on the outcomes
        self.required_votes = 2  # CHANGE NUMBER OF REQUIRED VOTES

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.user.id:  # check if the reaction was made by the bot
            return
        channel_ids = [channel.id for channel in self.mod_channels.values()]
        if payload.channel_id in channel_ids:
            emoji_map = {
                "1️⃣": "No action taken.",
                "2️⃣": "Fraudulent site warning.",
                "3️⃣": "Warning to the abuser.",
                "4️⃣": "User Suspension or Ban.",
                "5️⃣": "Shadow ban.",
            }

            # lookup the outcome based on the emoji
            outcome = emoji_map.get(str(payload.emoji), None)
            if outcome:
                if payload.message_id not in self.vote_cache:
                    # initialize the vote count for this message
                    self.vote_cache[payload.message_id] = {emoji: 0 for emoji in emoji_map.keys()}
                # increment the vote count for the chosen emoji
                if payload.user_id != self.user.id:
                    self.vote_cache[payload.message_id][str(payload.emoji)] += 1
                # check if the required number of votes has been reached
                if self.vote_cache[payload.message_id][str(payload.emoji)] >= self.required_votes:
                    channel = self.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    # get the reporter's id and abuser's id from the message content
                    reporter_id, abuser_id = self.extract_ids_from_message(message.content)
                    reported_message, report_reason = self.extract_report_from_message(message.content)
                    if reporter_id is not None and abuser_id is not None:
                        await self.notify_report_outcome(reporter_id, abuser_id, outcome, reported_message, report_reason, payload)
                    if outcome == "User Suspension or Ban.":
                        await self.send_suspension_duration_vote(channel, abuser_id)
                    del self.vote_cache[payload.message_id]  # delete this message from vote cache

    async def send_suspension_duration_vote(self, channel, abuser_id):
        emoji_map = {
            "1️⃣": "1 Hour",
            "2️⃣": "24 Hours",
            "3️⃣": "1 Week",
            "4️⃣": "1 Month",
            "5️⃣": "1 Year",
            "🔴": "Permanent Ban",
        }
        vote_message = await channel.send(
            "Please vote on the suspension duration for user {}:\n\n".format(abuser_id) + "\n".join(
                ["{}: {}".format(emoji, duration) for emoji, duration in emoji_map.items()]))
        # add reactions to the vote message
        for emoji in emoji_map.keys():
            await vote_message.add_reaction(emoji)
        # initialize the vote count for this message
        self.vote_cache[vote_message.id] = {emoji: 0 for emoji in emoji_map.keys()}

    def extract_ids_from_message(self, content):
        # The abuser_id follows at the beginning and the reporter_id follows "reported by "
        match = re.search('(\d+) reported by (\d+):', content)
        if match:
            return int(match.group(2)), int(match.group(1))  # returns a tuple of (reporter_id, abuser_id)
        else:
            print(f"Failed to extract reporter_id and abuser_id from message: {content}")
            return None, None

    def extract_report_from_message(self, content):
        # The reported message and reason are located after "Reported Message: " and "Report Reason: " respectively
        match = re.search('Reported Message: (.+)\nReport Reason: (.+)', content)
        if match:
            return match.group(1), match.group(2)  # returns a tuple of (reported_message, report_reason)
        else:
            print(f"Failed to extract reported message and reason from message: {content}")
            return None, None

    async def notify_report_outcome(self, reporter_id: int, abuser_id: int, outcome: str, reported_message: str,
                                    report_reason: str, payload):
        # Send the outcome to the reporter
        reporter = await self.fetch_user(reporter_id)
        if reporter:
            await reporter.send(f"Your report has been processed. Outcome: {outcome}")

        # If the outcome is a warning or suspension/ban, notify the abuser
        if outcome in ["Warning to the abuser.", "User Suspension or Ban."]:
            abuser = await self.fetch_user(abuser_id)
            if abuser:
                await abuser.send(
                    f"Your message:\n\n{reported_message}\n\nwas reported for the following reason: {report_reason}\n\nOutcome: {outcome}")
                # If the outcome is a suspension or ban, include the duration
                if outcome == "User Suspension or Ban.":
                    duration = self.vote_cache[payload.message_id][str(payload.emoji)]
                    await abuser.send(f"You have been suspended for {duration}.")

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply = "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to us
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            self.reports.pop(author_id)

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel

        """
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        scores = self.eval_text(message.content)
        await mod_channel.send(self.code_format(scores))
        """
    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text + "'"


client = ModBot()
client.run(discord_token)
