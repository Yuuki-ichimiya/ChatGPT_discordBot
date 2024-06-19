import os
import base64
import requests
from dotenv import load_dotenv
import disnake
from disnake.ext import commands
from openai import OpenAI
import tiktoken
import math

load_dotenv()


class ChatGPTDiscordBot:
    def __init__(self, api_key, model, token, command_prefix="/", max_messages=20):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tokenizer = tiktoken.encoding_for_model(model)
        self.conversationHistory = [
            {
                "role": "system",
                "content": "あなたはAIアシスタントです"
            }
        ]
        self.max_messages = max_messages

        intents = disnake.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=command_prefix, intents=intents)

        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)

    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name} (ID: {self.bot.user.id})')

    async def on_message(self, userMessage):
        if userMessage.author.bot:
            return  # Botからのメッセージは無視する

        # 最大入力数を超えないように履歴の一番古いものから削除
        while len(self.conversationHistory) > self.max_messages:
            del self.conversationHistory[0]

        # print("***********************************************")
        # print(f"Message from {userMessage.author}: {userMessage.content}")

        if userMessage.attachments:
            base64_image = None
            for attachment in userMessage.attachments:
                base64_image = self.get_image_base64(attachment.url)
                # print(f"Attachment: {attachment.url}")
                userMessageJSON = [
                    {"type": "text", "text": userMessage.content}]
                if base64_image:
                    userMessageJSON.append(
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"}}
                    )
                    self.conversationHistory.append(
                        {"role": "user", "content": userMessageJSON}
                    )
        else:
            self.conversationHistory.append(
                {"role": "user", "content": userMessage.content}
            )

        chatbot_response = self.client.chat.completions.create(
            model=self.model, messages=self.conversationHistory
        )
        output_assistant_response = chatbot_response.choices[0].message.content

        # ChatGPTからの返答を履歴に追加
        self.conversationHistory.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": output_assistant_response}]
            }
        )

        num = math.ceil(len(output_assistant_response) / 2000)
        for i in range(num):
            if i == num - 1:
                await userMessage.reply(output_assistant_response[2000*i:])
            else:
                await userMessage.reply(output_assistant_response[2000*i:2000*(i+1)])

    def get_image_base64(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            return encoded_image
        else:
            print(f"Failed to retrieve image: {response.status_code}")
            return None

    def run(self):
        try:
            self.bot.run(os.getenv('TOKEN'))
        except:
            os.system("kill")


if __name__ == "__main__":
    bot = ChatGPTDiscordBot(
        api_key=os.getenv('OPENAI_API'),
        model="gpt-4o",
        token=os.getenv('TOKEN')
    )
    bot.run()
