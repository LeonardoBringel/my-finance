<h1 align="center">
  💰 My Finance 💰
</h1>

## 📌 About
Track income and expenses, plan monthly cash flow, and visualize your financial health through an intuitive dashboard. Sensitive data is encrypted at rest using Fernet symmetric encryption.

## ✨ Main Features
- **Dashboard** — KPIs and charts summarizing income, expenses, and balance
- **Transactions** — Record, filter, and manage financial entries by category
- **Cash Flow** — Monthly planning using reusable templates
- **Categories** — Custom income/expense categories per user
- **User Management** — Admin panel for managing users
- **Encryption** — Sensitive fields encrypted before persisting to the database
- **Fail2Ban** - Fail2Ban integration for deployed environments

## 🚀 Technologies Used

| Layer | Technology |
|---|---|
| Language | Python |
| Framework | Streamlit|
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Encryption | cryptography (Fernet) |
| Auth | bcrypt + PyJWT |
| Charts | Plotly |

## 🎨 Preview
TODO

## 🚚 Getting Started

### Prerequisites
- Python 3.13+
- PostgreSQL running locally or remotely
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### Setup
1. **Clone the repository**
```bash
git clone https://github.com/LeonardoBringel/my-finance
cd my-finance
```

2. **Install dependencies**
```bash
uv sync
```

3. **Configure environment variables**
Create a `.env` file at the project root:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=my_finance

FERNET_KEY=your_fernet_key   # generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

ENABLE_FAIL2BAN_LOGGING=false # enable this to add fail2ban integration
FAIL2BAN_LOG_PATH=/var/log/my-finance/auth.log
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the application**
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.
