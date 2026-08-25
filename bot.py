import os
import asyncio
from aiohttp import web
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8761444347:AAHN5kk1IX6S_CWqcJ1yJ79a398ADUpmtp8"
API_BASE_URL = "/api/anime/oploverz-search"
API_KEY = "/api/anime/oploverz-download"
# =======================================================

BASE_URL = API_BASE_URL.rstrip("/")

# --- Dummy HTTP Server to Satisfy Render Port Binding & Keep Alive ---
async def handle_ping(request):
    return web.Response(text="Bot is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render assigns the port dynamically via the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server listening on port {port}")

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to the Velvet Anime Bot!**\n\n"
        "Commands:\n"
        "• `/search <anime title>` - Search anime on Oploverz\n"
        "• `/dl <link or url>` - Fetch download links"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def oploverz_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/search <anime title>`", parse_mode="Markdown")
        return

    query = " ".join(context.args)
    endpoint = f"{BASE_URL}/api/anime/oploverz-search"
    params = {"q": query}
    if API_KEY:
        params["apikey"] = API_KEY

    status_msg = await update.message.reply_text("🔍 Searching Oploverz...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint, params=params) as resp:
                if resp.status != 200:
                    await status_msg.edit_text(f"⚠️ API error: Status `{resp.status}`.", parse_mode="Markdown")
                    return
                data = await resp.json()
        except Exception as e:
            await status_msg.edit_text(f"❌ Connection failed: `{e}`", parse_mode="Markdown")
            return

    results = data.get("result") or data.get("data") or data.get("results") or []
    if not results:
        await status_msg.edit_text("❌ No anime found matching your query.")
        return

    msg = "🍿 **Search Results:**\n\n"
    for idx, item in enumerate(results[:8], 1):
        title = item.get("title") or item.get("name") or "Unknown Title"
        link = item.get("link") or item.get("url") or "No link"
        msg += f"{idx}. *{title}*\n🔗 `{link}`\n\n"

    msg += "👉 Copy the link and run: `/dl <link>`"
    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def oploverz_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/dl <link or url>`", parse_mode="Markdown")
        return

    target_url = context.args[0]
    endpoint = f"{BASE_URL}/api/anime/oploverz-download"
    params = {"url": target_url}
    if API_KEY:
        params["apikey"] = API_KEY

    status_msg = await update.message.reply_text("⚡ Fetching download links...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint, params=params) as resp:
                if resp.status != 200:
                    await status_msg.edit_text(f"⚠️ API error: Status `{resp.status}`.", parse_mode="Markdown")
                    return
                data = await resp.json()
        except Exception as e:
            await status_msg.edit_text(f"❌ Connection failed: `{e}`", parse_mode="Markdown")
            return

    result = data.get("result") or data.get("data") or data

    msg = "📥 **Download Links:**\n\n"
    if isinstance(result, dict):
        for key, val in result.items():
            if isinstance(val, list):
                msg += f"**{key.upper()}:**\n"
                for entry in val:
                    srv = entry.get("server") or entry.get("name") or "Server Link"
                    lnk = entry.get("link") or entry.get("url") or "#"
                    msg += f"• [{srv}]({lnk})\n"
                msg += "\n"
            else:
                msg += f"• **{key}:** {val}\n"
    elif isinstance(result, list):
        for entry in result:
            srv = entry.get("server") or entry.get("quality") or "Download"
            lnk = entry.get("link") or entry.get("url") or "#"
            msg += f"• [{srv}]({lnk})\n"
    else:
        msg += str(result)

    await status_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def main():
    if BOT_TOKEN == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise ValueError("Please replace BOT_TOKEN with your actual token.")

    # 1. Start Web Server
    await start_web_server()

    # 2. Start Telegram Polling
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", oploverz_search))
    app.add_handler(CommandHandler("dl", oploverz_download))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print("Bot is running...")
    
    # Keep the event loop running forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())

