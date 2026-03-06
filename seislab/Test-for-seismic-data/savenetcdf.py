from netCDF4 import Dataset
import matplotlib.pyplot as plt

# Open dataset
ds = Dataset("output.nc")

print(ds)

# Load seismic cube
samples = ds.variables["Samples"][:]

print("Data shape:", samples.shape)

# -----------------------------
# 1. Plot a single seismic trace
# -----------------------------
trace = samples[0, 0, :]

plt.figure()
plt.plot(trace)
plt.title("Seismic Trace")
plt.xlabel("Time Sample")
plt.ylabel("Amplitude")
plt.show()

# -----------------------------
# 2. Plot shot gather
# -----------------------------
shot = samples[10, :, :]

plt.figure()
plt.imshow(shot.T, aspect="auto", cmap="gray")
plt.title("Shot Gather")
plt.xlabel("Receiver")
plt.ylabel("Time")
plt.show()

# -----------------------------
# 3. Plot time slice
# -----------------------------
t = samples.shape[2] // 2   # middle time slice

time_slice = samples[:, :, t]

plt.figure()
plt.imshow(time_slice, cmap="seismic", aspect="auto")
plt.title(f"Time Slice (sample {t})")
plt.xlabel("Receiver")
plt.ylabel("Field Record")
plt.show()