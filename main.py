import os
import re
import io
import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = (
        f"👋 Hoş Geldin, {user.first_name}! 🤖\n\n"
        "🌐 Web Site HTML İndirme Botu hizmetinizdedir.\n\n"
        "🚀 **Nasıl Kullanılır?**\n"
        "İncelemek istediğiniz web sitesinin bağlantısını (`https://example.com` şeklinde) "
        "bana göndermeniz yeterlidir. Sitenin tüm HTML kodlarını tam kapsamlı bir şekilde "
        "çekip size bir .txt dosyası olarak göndereceğim.\n\n"
        "✨ Hemen bir bağlantı göndererek başlayabilirsiniz!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def fetch_html(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    if not url_pattern.match(url):
        await update.message.reply_text("❌ Geçersiz URL! Lütfen doğru bir web adresi gönderin.", parse_mode="Markdown")
        return

    status_message = await update.message.reply_text("⏳ **Web sitesinin kodları çekiliyor, lütfen bekleyin...**", parse_mode="Markdown")

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        response.encoding = response.apparent_encoding or "utf-8"
        html_content = response.text

        domain_name = url.split("//")[-1].split("/")[0].replace("www.", "")
        filename = f"{domain_name}_source.txt"

        file_stream = io.BytesIO(html_content.encode("utf-8"))
        file_stream.name = filename

        await update.message.reply_document(
            document=file_stream,
            filename=filename,
            caption=(
                f"✅ **HTML Kodları Başarıyla Çekildi!**\n\n"
                f"🌐 Site: `{url}`\n"
                f"📁 Dosya: `{filename}`"
            ),
            parse_mode="Markdown"
        )

        await status_message.delete()

    except requests.exceptions.RequestException as e:
        await status_message.edit_text(f"⚠️ **Siteye erişirken bir hata oluştu:**\n`{str(e)}`", parse_mode="Markdown")
    except Exception as e:
        await status_message.edit_text(f"❌ **Beklenmeyen bir hata oluştu:**\n`{str(e)}`", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("HATA: BOT_TOKEN bulunamadı!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_html))

    print("Bot çalışıyor...")
    app.run_polling()

if name == "__main__":
    main()
