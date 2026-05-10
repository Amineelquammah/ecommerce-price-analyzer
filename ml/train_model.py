import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_csv("data/processed/jumia_clean.csv")

# -------------------------
# PREP DATA
# -------------------------
df["date"] = pd.to_datetime(df["date"])

# convertir date en nombre (timestamp)
df["date_num"] = df["date"].map(pd.Timestamp.toordinal)

# -------------------------
# TRAIN MODEL
# -------------------------
X = df[["date_num"]]
y = df["price"]

model = LinearRegression()
model.fit(X, y)

print("✅ Modèle entraîné")

# -------------------------
# PREDICTION FUTURE
# -------------------------
future_dates = pd.date_range(start=df["date"].max(), periods=5)

future_df = pd.DataFrame({
    "date": future_dates
})

future_df["date_num"] = future_df["date"].map(pd.Timestamp.toordinal)

future_df["predicted_price"] = model.predict(future_df[["date_num"]])

print("\n📊 Prédictions :")
print(future_df)

# -------------------------
# VISUALISATION
# -------------------------
plt.scatter(df["date"], df["price"], label="Real")
plt.plot(future_df["date"], future_df["predicted_price"], color="red", label="Prediction")

plt.legend()
plt.title("Price Prediction")
plt.show()