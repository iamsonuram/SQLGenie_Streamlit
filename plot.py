import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import matplotlib.pyplot as plt

for filename in os.listdir("static/plots"):
    os.remove(os.path.join("static/plots", filename))

df = pd.read_csv("generated_data.csv")

plt.figure(figsize=(8, 5))
plt.bar(df["DepartmentName"], df["total_salary"], color="skyblue")
plt.xlabel("Department")
plt.ylabel("Total Salary")
plt.title("Total Salary by Department")
plt.savefig("static/plots/plot_1.png")