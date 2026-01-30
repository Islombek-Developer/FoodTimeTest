# 🚀 Telegram Botni 24/7 Ishlatish - Render + UptimeRobot

Bu yo'riqnoma sizning Fast Food botingizni Render platformasida bepul host qilish va UptimeRobot yordamida 24/7 ishlatib turish uchun to'liq qo'llanma.

---

## 📋 Kerakli Fayllar

Botni Render ga deploy qilish uchun quyidagi fayllar kerak:

1. ✅ `bot.py` - Asosiy bot kodi (yangilangan)
2. ✅ `requirements.txt` - Python kutubxonalar ro'yxati
3. ✅ `Procfile` - Render uchun ishga tushirish buyrug'i
4. ✅ `runtime.txt` - Python versiyasi
5. ✅ `.env.example` - Environment variables namunasi

---

## 🔧 1-BOSQICH: GitHub Repository Yaratish

### 1.1 GitHub Account Yaratish
- https://github.com ga o'ting
- "Sign up" tugmasini bosing
- Email, parol va username kiriting
- Emailni tasdiqlang

### 1.2 Yangi Repository Yaratish
1. GitHub da "+" tugmasini bosing → "New repository"
2. Repository nomi: `fastfood-telegram-bot`
3. Description: "Fast Food Delivery Telegram Bot"
4. ✅ Public yoki Private tanlang (Public tavsiya qilinadi)
5. **IMPORTANT:** ❌ "Add a README file" ni TANLANG (README qo'shing)
6. "Create repository" tugmasini bosing

### 1.3 Fayllarni GitHub ga Yuklash

#### Variant A: GitHub Web Interface orqali (Oson)
1. Repository ochilgandan keyin, "Add file" → "Upload files" ni bosing
2. Quyidagi fayllarni tortib tashlang:
   - `bot.py`
   - `requirements.txt`
   - `Procfile`
   - `runtime.txt`
3. Commit message yozing: "Initial commit"
4. "Commit changes" tugmasini bosing

#### Variant B: Git orqali (Terminal/CMD)
```bash
# Git o'rnatilgan bo'lishi kerak

# Loyihangiz papkasiga o'ting
cd /path/to/your/bot/folder

# Git repository yaratish
git init

# Barcha fayllarni qo'shish
git add .

# Commit qilish
git commit -m "Initial commit"

# GitHub repository ga ulash (SIZNING_USERNAME va REPO_NAME ni o'zgartiring)
git remote add origin https://github.com/SIZNING_USERNAME/fastfood-telegram-bot.git

# GitHub ga push qilish
git branch -M main
git push -u origin main
```

**Eslatma:** `.env` faylini GitHub ga yuklamang! Maxfiy ma'lumotlar Render da Environment Variables sifatida qo'shiladi.

---

## ☁️ 2-BOSQICH: Render da Bot Yaratish

### 2.1 Render Account Yaratish
1. https://render.com ga o'ting
2. "Get Started" yoki "Sign Up" tugmasini bosing
3. **GitHub bilan kirish tavsiya qilinadi** (osonroq integratsiya)
4. Emailni tasdiqlang

### 2.2 Web Service Yaratish
1. Render dashboard ga o'ting
2. "New +" tugmasini bosing
3. "Web Service" ni tanlang

### 2.3 Repository Ulash
1. "Connect a repository" bo'limida GitHub ni tanlang
2. Agar birinchi marta bo'lsa, "Connect GitHub" tugmasini bosing
3. Render ga GitHub repository larga ruxsat bering
4. `fastfood-telegram-bot` repository ni tanlang
5. "Connect" tugmasini bosing

### 2.4 Service Sozlamalari

Quyidagi sozlamalarni kiriting:

**Basic Settings:**
- **Name:** `fastfood-bot` (yoki istalgan nom)
- **Region:** `Frankfurt (EU Central)` yoki yaqin region
- **Branch:** `main`
- **Root Directory:** (bo'sh qoldiring)
- **Environment:** `Python 3`
- **Build Command:** (bo'sh qoldiring yoki `pip install -r requirements.txt`)
- **Start Command:** `python bot.py`

**Instance Type:**
- ✅ **Free** ni tanlang (bepul)

### 2.5 Environment Variables Qo'shish

"Environment" bo'limiga o'ting va quyidagi o'zgaruvchilarni qo'shing:

| Key | Value | Izoh |
|-----|-------|------|
| `BOT_TOKEN` | `7673962223:AAHAE0HRRwTcFG_lFtkKz_1HkF7ThWJ2_34` | BotFather dan olingan token |
| `ADMIN_ID` | `6965587290` | Sizning Telegram ID |
| `COURIER_IDS` | `6168822836` | Kuryer ID lari (vergul bilan) |

**O'z ma'lumotlaringizni kiriting!**

### 2.6 Deploy Qilish
1. Barcha sozlamalarni to'g'ri kiritganingizdan amin bo'ling
2. Pastdagi **"Create Web Service"** tugmasini bosing
3. Deploy boshlanadi (2-5 daqiqa davom etadi)
4. "Build successful" ko'ringuncha kuting

### 2.7 Service URL Olish
Deploy tugagandan keyin:
1. Service dashboard ga o'ting
2. Yuqori qismda **Service URL** ko'rinadi
3. Masalan: `https://fastfood-bot.onrender.com`
4. **Bu URL ni saqlang** - UptimeRobot uchun kerak bo'ladi

---

## 🔄 3-BOSQICH: UptimeRobot Sozlash (24/7 Ishlashi Uchun)

### Nima uchun UptimeRobot kerak?

Render ning bepul rejasi **15 daqiqa faoliyat bo'lmasa avtomatik o'chadi**. UptimeRobot har 5 daqiqada botga ping yuboradi va uni doim aktiv holatda saqlaydi.

### 3.1 UptimeRobot Account Yaratish
1. https://uptimerobot.com ga o'ting
2. "Free Sign Up" tugmasini bosing
3. Email va parol kiriting
4. Emailni tasdiqlang
5. Dashboard ga o'ting

### 3.2 Monitor Qo'shish
1. Dashboard da "+ Add New Monitor" tugmasini bosing
2. Quyidagi sozlamalarni kiriting:

**Monitor Type:** `HTTP(s)`

**Friendly Name:** `FastFood Bot Monitor`

**URL (or IP):** 
```
https://fastfood-bot.onrender.com
```
**IMPORTANT:** Sizning Render service URL ni kiriting!

**Monitoring Interval:** `5 minutes` (bepul rejada eng kam interval)

**Monitor Timeout:** `30 seconds`

**HTTP Method:** `GET`

**Alert Contacts:** Email manzil (xatoliklar haqida xabar olish uchun)

3. "Create Monitor" tugmasini bosing

### 3.3 Monitor Ishlashini Tekshirish
- 5 daqiqadan keyin dashboard ni yangilang
- "Status" ustunida ✅ **UP** ko'rinishi kerak
- "Response Time" ko'rsatiladi
- Agar 🔴 **DOWN** bo'lsa, Render da xatolik bor

---

## 🎯 4-BOSQICH: Botni Tekshirish

### 4.1 Telegram da Tekshirish
1. Telegram da botingizni oching
2. `/start` buyrug'ini yuboring
3. Bot javob berishi kerak

### 4.2 Render Logs Tekshirish
1. Render dashboard ga o'ting
2. "Logs" tab ni oching
3. Quyidagi xabar ko'rinishi kerak:
```
✅ Bot ishga tushdi!
Admin ID: 6965587290
Kuryerlar: [6168822836]
```

### 4.3 UptimeRobot Statistika
- UptimeRobot dashboard da "Uptime Ratio" ni tekshiring
- 99-100% bo'lishi kerak

---

## 🔧 5-BOSQICH: Kelajakda O'zgartirish Qilish

### GitHub orqali Kod O'zgartirish

#### Variant A: GitHub Web da (Oson)
1. GitHub repository ga o'ting
2. `bot.py` faylini oching
3. ✏️ (Pen) belgisini bosing
4. Kodni tahrirlang
5. "Commit changes" tugmasini bosing
6. Render avtomatik yangi versiyani deploy qiladi (2-3 daqiqa)

#### Variant B: Git orqali (Terminal)
```bash
# O'zgarishlarni qilish
# bot.py faylini taxrirlang

# Commit qilish
git add .
git commit -m "Updated bot code"
git push origin main

# Render avtomatik deploy qiladi
```

### Environment Variables O'zgartirish
1. Render dashboard ga o'ting
2. "Environment" tabiga o'ting
3. O'zgaruvchini tahrirlang
4. "Save Changes" tugmasini bosing
5. Service avtomatik qayta ishga tushadi

---

## 📊 6-BOSQICH: Monitoring va Troubleshooting

### Render Logs Tekshirish
```
Render Dashboard → Logs tab → Real-time logs
```

Qidirilayotgan xabarlar:
- ✅ `Bot ishga tushdi!`
- ✅ `Database initialized successfully`
- ❌ `Error:` - xatolik yuz bergan

### Tez-tez uchraydigan Xatolar

#### 1. Bot ishga tushmayapti
**Sabab:** Environment variables noto'g'ri
**Yechim:** 
- Render da `BOT_TOKEN` to'g'ri kiritilganini tekshiring
- BotFather da tokenni yangilang

#### 2. Database xatoliklari
**Sabab:** `fastfood.db` faylini yo'qotish
**Yechim:** 
- Render free plan da database tez-tez reset bo'ladi
- PostgreSQL/SQLite persistent storage sozlang (keyingi versiyada)

#### 3. Bot 15 daqiqada o'chib qolyapti
**Sabab:** UptimeRobot ishlamayapti
**Yechim:**
- UptimeRobot monitorni tekshiring
- Render URL to'g'ri kiritilganini tasdiqlang

#### 4. Yangi kodlar deploy bo'lmayapti
**Sabab:** GitHub push qilinmagan
**Yechim:**
```bash
git push origin main
```

---

## 💡 Qo'shimcha Maslahatlar

### 1. Database Backup
Render bepul rejada database har safar restart bo'lganda o'chadi. Muntazam backup oling:
- SQLite faylni yuklab oling
- Yoki PostgreSQL ga o'ting (Render Postgres bepul)

### 2. Logs Saqlash
Muhim xatolarni monitor qiling:
- Render logs 7 kun saqlanadi
- External log service ishlating (Logtail, Papertrail)

### 3. Performance Optimization
- Kod optimizatsiya qiling
- Database query larini kamaytiring
- Async/await to'g'ri ishlating

### 4. Security
- ❌ `.env` faylini GitHub ga yuklamang
- ✅ Bot tokenni sir saqlang
- ✅ Admin/Kuryer ID larni to'g'ri kiriting

---

## 🎉 Yakuniy Tekshirish

### ✅ Barcha Narsalar To'g'ri Ishlayaptimi?

- [ ] GitHub da kod yuklangan
- [ ] Render da service ishga tushgan
- [ ] Environment variables to'g'ri kiritilgan
- [ ] Bot `/start` ga javob beryapti
- [ ] UptimeRobot monitor faol
- [ ] Uptime 99%+ ko'rsatyapti
- [ ] Logs da xatolik yo'q

---

## 📞 Yordam Kerakmi?

### Render Support
- Dashboard → Help → Submit a ticket

### UptimeRobot Support
- https://uptimerobot.com/contact

### Telegram Bot API
- https://core.telegram.org/bots/api

---

## 🚀 Keyingi Qadamlar (Ixtiyoriy)

1. **PostgreSQL ga O'tish:** SQLite o'rniga Render Postgres
2. **Custom Domain:** Bot uchun shaxsiy domen
3. **Monitoring Dashboard:** Grafana, Prometheus
4. **CI/CD Pipeline:** GitHub Actions orqali avtomatik test va deploy
5. **Load Balancing:** Ko'p foydalanuvchi uchun

---

## 🔗 Foydali Linklar

- **Render Documentation:** https://render.com/docs
- **UptimeRobot Guide:** https://uptimerobot.com/kb/
- **Telegram Bot API:** https://core.telegram.org/bots
- **Python Aiogram:** https://docs.aiogram.dev/

---

## ✨ Muaffaqiyat!

Sizning botingiz endi 24/7 ishlamoqda! 🎉

Savollar bo'lsa, Render yoki UptimeRobot support ga murojaat qiling.
