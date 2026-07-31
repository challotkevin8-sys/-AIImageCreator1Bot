import os
import io
import logging
import base64

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")

client = OpenAI(api_key=OPENAI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your AI Image Creator bot.\n\n"
        "Just send me a text description and I'll generate an image for it.\n\n"
        "Example: a cyberpunk city skyline at sunset, cinematic lighting\n\n"
        "Commands:\n"
        "/start - show this message\n"
        "/help - how to use the bot"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me any text prompt and I'll turn it into an image.\n"
        "Tips for better results:\n"
        "- Be descriptive (style, lighting, mood, colors)\n"
        "- Mention 'photo', 'illustration', '3D render', etc. for style\n"
        "- Keep prompts under ~1000 characters"
    )


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = update.message.text.strip()

    if not prompt:
        await update.message.reply_text("Please send a text description to generate an image.")
        return

    if len(prompt) > 1000:
        await update.message.reply_text("That prompt is a bit long — please keep it under 1000 characters.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text("Generating your image... this can take up to ~20 seconds.")

    try:
        result = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size=IMAGE_SIZE,
            n=1,
        )

        image_b64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)
        image_file = io.BytesIO(image_bytes)
        image_file.name = "image.png"

        await update.message.reply_photo(photo=image_file, caption=f'"{prompt}"')
        await status_msg.delete()

    except Exception as e:
        logger.exception("Image generation failed")
        await status_msg.edit_text(
            "Sorry, something went wrong generating that image. "
            "Please try again with a different prompt."
        )


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    logger.info("Bot starting (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
