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
    def __init__(self, api_key, model, token, command_prefix="/", max_messages=6):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tokenizer = tiktoken.encoding_for_model(model)
        self.conversation_history = [
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

    async def on_message(self, message):
        if message.author.bot:
            return  # Botからのメッセージは無視する

        base64_image = None
        if len(self.conversation_history) == self.max_messages:
            del self.conversation_history[0]

        print("***********************************************")
        print(f"Message from {message.author}: {message.content}")

        if message.attachments:
            for attachment in message.attachments:
                base64_image = self.get_image_base64(attachment.url)
                print(f"Attachment: {attachment.url}")
        print("***********************************************")

        user_message_content = [{"type": "text", "text": message.content}]
        if base64_image:
            user_message_content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            )

        self.conversation_history.append(
            {"role": "user", "content": user_message_content}
        )

        chatbot_response = self.client.chat.completions.create(
            model=self.model, messages=self.conversation_history
        )
        output_assistant_response = chatbot_response.choices[0].message.content

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": output_assistant_response}]
            }
        )

        num = math.ceil(len(output_assistant_response) / 2000)
        for i in range(num):
            if i == num - 1:
                await message.reply(output_assistant_response[2000*i:])
            else:
                await message.reply(output_assistant_response[2000*i:2000*(i+1)])

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
