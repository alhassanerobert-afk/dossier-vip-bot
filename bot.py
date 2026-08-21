import os
import sqlite3
from datetime import datetime, timezone

from telegram import Update, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]

PRICE_STARS = 100
SUBSCRIPTION_DAYS = 30
SUBSCRIPTION_SECONDS = 30 * 24 * 60 * 60

DB_FILE = "members.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            expires_at INTEGER
        )
    """)
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 Bienvenue sur Dossier VIP 🔞\n\n"
        "⭐ Accès au groupe privé\n"
        "⏳ Durée : 30 jours\n"
        "💰 Prix : 100 Telegram Stars\n\n"
        "Utilise /access pour acheter ton accès."
    )


async def access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = [LabeledPrice("Accès Dossier VIP — 30 jours", PRICE_STARS)]

    await update.message.reply_invoice(
        title="Dossier VIP 🔞",
        description="Accès au groupe privé pendant 30 jours.",
        payload="dossier_vip_30_days",
        currency="XTR",
        prices=prices,
        provider_token="",
        subscription_period=SUBSCRIPTION_SECONDS,
    )


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query

    if query.invoice_payload != "dossier_vip_30_days":
        await query.answer(ok=False, error_message="Paiement invalide.")
        return

    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user = update.effective_user

    expiration = payment.subscription_expiration_date

    if expiration is None:
        expiration = int(datetime.now(timezone.utc).timestamp()) + SUBSCRIPTION_SECONDS

    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        INSERT INTO members (user_id, username, expires_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            expires_at = excluded.expires_at
        """,
        (
            user.id,
            user.username or "",
            expiration,
        ),
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Paiement confirmé !\n\n"
        "⭐ Ton abonnement Dossier VIP est actif pendant 30 jours.\n\n"
        "🔐 L'accès au groupe sera envoyé dans la prochaine étape."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Aide Dossier VIP\n\n"
        "/start — Commencer\n"
        "/access — Acheter l'accès\n"
        "/help — Aide"
    )


def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("access", access))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(
        PreCheckoutQueryHandler(precheckout)
    )

    application.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
