# 🍕 FastFood Telegram Bot

Professional Fast Food Delivery Telegram Bot with complete order management system.

## 📋 Features

### 👥 For Customers
- 🍽 **Menu Browsing** - View delicious food items with photos
- 🛒 **Shopping Cart** - Add/remove items easily
- 📦 **Order Tracking** - Track your order status in real-time
- 💳 **Multiple Payment Methods** - Cash, Payme, Click
- 📞 **Contact Info** - Get delivery information
- 📱 **Order History** - View your past orders

### 👨‍💼 For Admins
- 📊 **Order Management** - Accept, assign, cancel orders
- 🍽 **Product Management** - Add, edit, delete menu items
- 👥 **Courier Management** - Assign couriers to orders
- 📈 **Statistics** - View business metrics
- 🔔 **Real-time Notifications** - Get notified of new orders

### 🚚 For Couriers
- 📋 **Active Orders** - View orders assigned to you
- ✅ **Delivery Confirmation** - Mark orders as delivered
- 📞 **Customer Contact** - Quick access to customer phone
- 📊 **Personal Statistics** - Track your deliveries
- 🎉 **Delivery History** - View completed deliveries

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Your Telegram User ID

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/fastfood-telegram-bot.git
cd fastfood-telegram-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
COURIER_IDS=courier1_id,courier2_id
```

5. Run the bot:
```bash
python bot.py
```

## ☁️ Deploy to Render (24/7 Hosting)

See detailed guide in [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)

Quick steps:
1. Push code to GitHub
2. Create Web Service on Render
3. Set Environment Variables
4. Setup UptimeRobot monitoring

## 📱 Bot Commands

- `/start` - Start the bot and show main menu

## 🗂 Project Structure

```
fastfood-telegram-bot/
├── bot.py                 # Main bot file
├── requirements.txt       # Python dependencies
├── Procfile              # Render start command
├── runtime.txt           # Python version
├── .env.example          # Environment variables example
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── DEPLOY_GUIDE.md       # Deployment guide
```

## 🛠 Technology Stack

- **Framework:** [Aiogram 3.x](https://docs.aiogram.dev/)
- **Database:** SQLite3
- **Hosting:** Render
- **Monitoring:** UptimeRobot
- **Language:** Python 3.11

## 📊 Database Schema

### Orders Table
- Order details, status, timestamps
- Customer information
- Courier assignment

### Couriers Table
- Courier profiles
- Statistics and activity status

### Products Table
- Menu items with emoji, price, description
- Photos and availability status

## 🔐 Security

- Bot token stored in environment variables
- No sensitive data in code
- Admin/Courier ID verification
- `.env` excluded from Git

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

Created with ❤️ for learning purposes

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact via Telegram

## 🙏 Acknowledgments

- Aiogram framework developers
- Telegram Bot API team
- Render and UptimeRobot services

---

**Note:** This bot is for educational purposes. Customize it according to your needs.

## 🎯 Roadmap

- [ ] PostgreSQL migration
- [ ] Admin web dashboard
- [ ] Payment gateway integration
- [ ] Multi-language support
- [ ] Customer reviews system
- [ ] Promo codes & discounts
- [ ] Geolocation tracking
- [ ] Push notifications

---

Made with 🍕 and ☕
