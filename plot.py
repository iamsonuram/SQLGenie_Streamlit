import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import matplotlib.pyplot as plt

for filename in os.listdir("static/plots"):
    os.remove(os.path.join("static/plots", filename))

df = pd.read_csv("generated_data.csv")

plt.figure(figsize=(8, 5))
plt.pie(df["total\_salary\_expenditure"], labels=df["DepartmentName"], autopct="%1.1f%%")
plt.axis("equal")
plt.title("Total Salary Expenditure by Department")
plt.savefig("static/plots/plot_1.png")

plt.figure(figsize=(8, 5))
plt.bar(df["DepartmentName"], df["total\_salary\_expenditure"], color="orange")
plt.xlabel("Department")
plt.ylabel("Total Salary Expenditure")
plt.title("Total Salary Expenditure by Department")
plt.savefig("static/plots/plot_2.png")