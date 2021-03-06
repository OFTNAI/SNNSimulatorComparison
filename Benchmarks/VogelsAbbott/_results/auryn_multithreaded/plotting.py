import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
#plt.style.use('ggplot')
plt.style.use('seaborn-paper')


SpikeBenchmarkPath = "../timestep_8_delay/Spike.dat"
with open(SpikeBenchmarkPath, 'r') as f:
        SpikeBenchmark = f.read()
SpikeBenchmark = float(SpikeBenchmark) / 100.0


AurynBenchmarks = []
AurynBenchmarkCores = [1, 2, 4, 8]

for numCores in AurynBenchmarkCores:
    with open(str(numCores) + ".dat", 'r') as f:
        time = f.read()
        AurynBenchmarks.append(float(time) / 100.0)

print(AurynBenchmarkCores, AurynBenchmarks)

# Fitting a line
points = np.linspace(1, 8, 100)

def expfunc(x, a, b, c):
    return a * np.exp(-b *x) + c

popt, pcov = curve_fit(expfunc, AurynBenchmarkCores, AurynBenchmarks)
#plt.plot(points, expfunc(points, *popt))



# Plotting single timestep results
fig, ax = plt.subplots()
#ax.set_title("Multi-Threaded Vogels Abbott Benchmark Comparison\nauryn vs Spike", size=12)
ax.scatter(AurynBenchmarkCores, AurynBenchmarks, color='k', zorder=2, s=50)
ax.scatter([1], [SpikeBenchmark], color='r', zorder=2, s=50)
ax.plot([1, 8], [SpikeBenchmark, SpikeBenchmark], color='r', linewidth = 3, alpha=0.75, zorder=1, label="Spike", linestyle='--')
ax.plot(points, expfunc(points, *popt), color='k', linewidth = 3, alpha=0.75, zorder=1, label="Auryn")
ax.legend(frameon=False)
ax.yaxis.set_tick_params(labelsize=11)
ax.xaxis.set_tick_params(labelsize=11)
ax.set_xticks(AurynBenchmarkCores)
ax.set_xlabel("Number of CPU Cores", size=12)
ax.set_ylabel("Simulation Run Time (Normalized)", size=12)
ax.set_ylim([10.0**-2, 10.0**0])
ax.set_yscale('log')
fig.subplots_adjust(bottom=0.15, top=0.975)
fig.savefig('multithreaded_comparison.png', dpi=300)
#plt.show()
