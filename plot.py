import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

for filename in os.listdir("static/plots"):
    os.remove(os.path.join("static/plots", filename))

df = pd.read_csv("generated_data.csv")

plt.figure(figsize=(8, 5))
plt.bar(df["FirstName"], df["Salary"], color="skyblue")
plt.xlabel("First Name")
plt.ylabel("Salary")
plt.title("Salary by Employee")
plt.savefig("static/plots/plot_1.png")

plt.figure(figsize=(8, 5))
sns.boxplot(x="LastName", y="Salary", data=df)
plt.xlabel("Last Name")
plt.ylabel("Salary")
plt.title("Salary Distribution by Last Name")
plt.savefig("static/plots/plot_2.png")