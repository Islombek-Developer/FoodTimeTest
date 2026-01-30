# ⚡ Tez Deploy Qo'llanmasi (5 daqiqa)

## 1️⃣ GitHub (2 daqiqa)

```bash
# 1. GitHub da yangi repo yarating: fastfood-telegram-bot
# 2. Terminal da:

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/fastfood-telegram-bot.git
git push -u origin main
```

## 2️⃣ Render (2 daqiqa)

1. https://render.com → Sign Up (GitHub bilan)
2. "New +" → "Web Service"
3. Repository tanlang: `fastfood-telegram-bot`
4. Sozlamalar:
   - **Name:** `fastfood-bot`
   - **Start Command:** `python bot.py`
   - **Instance:** Free
5. Environment Variables qo'shing:
   ```
   BOT_TOKEN = 7673962223:AAHAE0HRRwTcFG_lFtkKz_1HkF7ThWJ2_34
   ADMIN_ID = 6965587290
   COURIER_IDS = 6168822836
   ```
6. "Create Web Service" → Kutish (2-3 daqiqa)
7. URL ni saqlang: `https://fastfood-bot.onrender.com`

## 3️⃣ UptimeRobot (1 daqiqa)

1. https://uptimerobot.com → Sign Up
2. "+ Add New Monitor"
3. Sozlamalar:
   - **Type:** HTTP(s)
   - **Name:** FastFood Bot
   - **URL:** `https://fastfood-bot.onrender.com`
   - **Interval:** 5 minutes
4. "Create Monitor"

## ✅ Tugadi!

Bot 24/7 ishlamoqda. Telegram da `/start` ni sinab ko'ring!

## 🔧 Keyingi O'zgarishlar

```bash
# Kodni o'zgartirasiz
# Git orqali push qilasiz:

git add .
git commit -m "Updated bot"
git push origin main

# Render avtomatik deploy qiladi (2-3 daqiqa)
```

## 📊 Tekshirish

- ✅ Render Logs: Bot ishga tushdi!
- ✅ Telegram: /start javob beryapti
- ✅ UptimeRobot: Status UP

## ⚠️ Tez-tez Xatolar

1. **Bot javob bermayapti** → Render da Environment Variables tekshiring
2. **15 daqiqada o'chyapti** → UptimeRobot URL to'g'rimi?
3. **Deploy bo'lmayapti** → `git push origin main` qildingizmi?

---

Batafsil ma'lumot: [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
