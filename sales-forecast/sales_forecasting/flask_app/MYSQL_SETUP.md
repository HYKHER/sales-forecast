# RetailIQ — MySQL Edition Setup Guide

## 1. Install MySQL (if not already installed)

### Ubuntu/Debian:
```bash
sudo apt update && sudo apt install mysql-server -y
sudo systemctl start mysql
sudo mysql_secure_installation
```

### macOS (Homebrew):
```bash
brew install mysql
brew services start mysql
```

### Windows:
Download MySQL installer from https://dev.mysql.com/downloads/installer/

---

## 2. Create the Database and User

Log into MySQL as root:
```bash
mysql -u root -p
```

Then run:
```sql
CREATE DATABASE retailiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'retailiq'@'localhost' IDENTIFIED BY 'StrongPass123!';
GRANT ALL PRIVILEGES ON retailiq.* TO 'retailiq'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 3. Set Environment Variables

### Linux/macOS (in your terminal or .env file):
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=retailiq
export MYSQL_PASSWORD=StrongPass123!
export MYSQL_DB=retailiq
export SECRET_KEY=your-random-secret-key-here
```

### Windows (Command Prompt):
```cmd
set MYSQL_HOST=localhost
set MYSQL_USER=retailiq
set MYSQL_PASSWORD=StrongPass123!
set MYSQL_DB=retailiq
```

---

## 4. Install Python Dependencies

```bash
cd sales_forecasting/flask_app
pip install -r requirements_flask.txt
```

---

## 5. Run the App

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

---

## MySQL Tables Created Automatically

| Table              | Description                                   |
|--------------------|-----------------------------------------------|
| `users`            | User accounts (email, password hash, plan)    |
| `prediction_logs`  | Every prediction result logged here            |
| `sales_records`    | Sales data entered via the web form            |

## Useful MySQL Queries

```sql
-- View all sales records
SELECT * FROM retailiq.sales_records ORDER BY date DESC LIMIT 50;

-- View recent predictions
SELECT pl.*, u.email FROM retailiq.prediction_logs pl
JOIN retailiq.users u ON pl.user_id = u.id
ORDER BY pl.created_at DESC LIMIT 20;

-- Category summary
SELECT category, COUNT(*) as count, AVG(units_sold) as avg_units
FROM retailiq.sales_records GROUP BY category;

-- Today's prediction count per user
SELECT u.email, COUNT(*) as preds_today
FROM retailiq.prediction_logs pl
JOIN retailiq.users u ON pl.user_id = u.id
WHERE DATE(pl.created_at) = CURDATE()
GROUP BY u.email;
```

---

## Environment Variable Reference

| Variable         | Default       | Description                    |
|------------------|---------------|--------------------------------|
| `MYSQL_HOST`     | `localhost`   | MySQL server hostname          |
| `MYSQL_PORT`     | `3306`        | MySQL port                     |
| `MYSQL_USER`     | `root`        | MySQL username                 |
| `MYSQL_PASSWORD` | `password`    | MySQL password                 |
| `MYSQL_DB`       | `retailiq`    | Database name                  |
| `SECRET_KEY`     | dev key       | Flask session secret key       |
