from enum import Enum, auto
import discord
import re


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()

    # Beginning of Custom States
    Phishing_and_Malware_Related_Scams_Category = auto()
    Social_Engineering_Scams = auto()
    Trade_and_Transaction_Scams = auto()
    Fake_Service_and_Site_Scams = auto()
    Other_Scams = auto()
    Prompt_Additional_Description = auto()
    Received_Additional_Description = auto()
    Awaiting_User_Acknowledgement = auto()
    Awaiting_Block = auto()
    

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    report_reasons = ["Phishing and Malware-Related Scams", "Social Engineering Scams", "Trade and Transaction Scams", "Fake Service and Site Scams", "Other"]
    phishing_and_malware_categories = ["Phishing Email or Message", "Link to Malware Download", "Fake Steam Code Generator", "Other"]
    social_engineering_categories = ["Impersonation or False Identity", "Fraudulent Giveaway or Sweepstakes", "Middleman Scams", "False Skin Inspection", "Other"]
    trade_and_transaction_categories = ["False Trade Offers", "Real Currency Transaction Scams", "False Market Listing", "Non-Human Transaction", "Chargeback Scam", "Other"]
    fake_service_and_site_categories = ["Betting Scams", "Gift Card Scams", "False Skin Upgrade Offers", "False Trading Site", "Other"]

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.report = {}

    REPORT_CHANNEL_ID = 1103033286760091721

    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply = "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."

            # Store the reporter's id
            self.report["reporter"] = message.author.id

            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```. How do you want to classify this message? We can support the following: \n"
                    + str(self.report_reasons)]
            
        # Continue with identifying the reason
        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content == "Phishing and Malware-Related Scams":
                self.state = State.Phishing_and_Malware_Related_Scams_Category
            elif message.content == "Social Engineering Scams":
                self.state = State.Social_Engineering_Scams
            elif message.content == "Trade and Transaction Scams":
                self.state = State.Trade_and_Transaction_Scams
            elif message.content == "Fake Service and Site Scams":
                self.state = State.Fake_Service_and_Site_Scams
            else:
                self.state = State.Other_Scams

            self.report["Report Reason"] = message.content.copy()
            
            if self.state == State.Phishing_and_Malware_Related_Scams_Category:
                reply = "Thank you for reporting under the Phishing and Malware Related Scams Category. \n"
                reply += "Please select the type of phishing or malware content that this report falls under: \n"
                reply += str(self.phishing_and_malware_categories)

                self.state = State.Prompt_Additional_Description
                return [reply]
            
            if self.state == State.Social_Engineering_Scams:
                reply = "Thank you for reporting under the Social Engineering Scams Category. \n"
                reply += "Please select the type of social engineering content that this report falls under: \n"
                reply += str(self.social_engineering_categories)

                self.state = State.Prompt_Additional_Description
                return [reply]
            
            if self.state == State.Trade_and_Transaction_Scams:
                reply = "Thank you for reporting under the Trade and Transaction Scams Category. \n"
                reply += "Please select the type of trade and transaction scam content that this report falls under: \n"
                reply += str(self.trade_and_transaction_categories)

                self.state = State.Prompt_Additional_Description
                return [reply]

            if self.state == State.Fake_Service_and_Site_Scams:
                reply = "Thank you for reporting under the Fake Service and Site Scams Category. \n"
                reply += "Please select the type of fake service and site scam content that this report falls under: \n"
                reply += str(self.fake_service_and_site_categories)

                self.state = State.Prompt_Additional_Description
                return [reply]

            if self.state == State.Other_Scams:
                reply = "Thank you for reporting under the Other Scams Category. \n"
                reply += ("Please provide any additional descriptions or supporting material of the abuse (Screenshots, Text Messages, URLs, etc.) This will significantly improve"
                    "our ability to review the report and provide corrective action")
                self.state = State.Received_Additional_Description
                return [reply]

        reply = ""
        if self.state == State.Prompt_Additional_Description: 
            reply = ("Please provide any additional descriptions or supporting material of the abuse (Screenshots, Text Messages, URLs, etc.) This will significantly improve"
                    "our ability to review the report and provide corrective action")
            self.report["Category"] = message.content
            self.state = State.Received_Additional_Description

        if self.state == State.Received_Additional_Description:
            reply = ("Thank you for your report! \n Our abuse moderation team will review your case and decide on appropriate action. Please note that under no circumstances"
            " will transactions be reversed or restored, per our User Policy. \n To complete the report, please type `I understand` to acknowledge the report conditions")
            self.report["Additional Description"] = message.content
            self.state = State.Awaiting_User_Acknowledgement
            return [reply]
        
        if self.state == State.Awaiting_User_Acknowledgement:
            if message.content.lower() == "i understand":
                reply = ("Thank you for acknowledging that. Would you like to block this user to prevent them from sending you more "
                "messages in the future? Please type 'yes' or 'no'")

                self.state = State.Awaiting_Block
            else:
                reply = "Sorry. I'm unable to continue without acknowledgement of our trade policy"
                self.state = State.Received_Additional_Description
            return [reply]
        
        if self.state == State.Awaiting_Block:
            if message.content == "Yes" or message.content == "yes":
                reply = "I've gone ahead and blocked the user from interacting with you. Future accounts created by the user will be blocked from you as well."
            elif message.content == "No" or message.content == "no":
                reply = "Sounds good. I'll go ahead and forward the information to a specialized team who can decide future action"
            self.report["Blocked"] = (message.content.lower() == "yes")
            self.state = State.REPORT_COMPLETE
            return [reply]

        if self.state == State.REPORT_COMPLETE:
            report_channel = self.client.get_channel(self.REPORT_CHANNEL_ID)
            report_message = f"Report by {message.author.name}:\n\n"
            for key, value in self.report.items():
                report_message += f"{key}: {value}\n"
            await report_channel.send(report_message)
            return ["Report complete. The moderators have been notified."]

        return

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

