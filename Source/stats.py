import sys
import psutil
import pyqtgraph as pg
import numpy as np
import soundcard as sc
from pyqtgraph.Qt import QtWidgets, QtCore
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetUtilizationRates, nvmlDeviceGetTemperature, NVML_TEMPERATURE_GPU

nvmlInit() #Initialize nvidia device stats
gpu_handle = nvmlDeviceGetHandleByIndex(0) #Assuming only 1 gpu

app = QtWidgets.QApplication([])

# Create the main window layout
win = pg.GraphicsLayoutWidget(title="Real-Time GPU, CPU, and Audio Monitoring")
win.resize(800, 700)
win.setWindowTitle("Real-Time GPU, CPU, and Audio Monitoring")

# Add plots to the layout
p1 = win.addPlot(title="GPU Usage (%)")
p2 = win.addPlot(title="GPU Temp (°C)")
win.nextRow()
p3 = win.addPlot(title="CPU Clock Speed (MHz)")
p4 = win.addPlot(title="CPU Usage (%)")
win.nextRow()

# Set labels for y-axes of main plots for consistent alignment
p1.setLabel('left', 'GPU Usage (%)')
p2.setLabel('left', 'GPU Temp (°C)')
p3.setLabel('left', 'CPU Clock (MHz)')
p4.setLabel('left', 'CPU Usage (%)')

# Create a horizontal bar graph for audio output at the bottom
audio_plot = win.addPlot(title="Audio Output Level")
audio_plot.setXRange(0, 1)  # Normalize the audio level to range between 0 and 1
audio_plot.setYRange(0, 0.5)  # Fixed height for horizontal bar visualization
audio_plot.setMaximumHeight(100)  # Set maximum height to make it shorter than other plots

# Hide y-axis and adjust left margin of audio_plot to align with other plots
audio_plot.hideAxis('left')

audio_bar = pg.BarGraphItem(x=[0], width=0, height=0.5, brush='b')
audio_plot.addItem(audio_bar)


# Set y-axis limits for GPU and CPU utilization
p1.setYRange(0, 100)  # GPU Usage (%)
p4.setYRange(0, 100)  # CPU Usage (%)

# Initialize curves for real-time updating
gpu_usage_curve = p1.plot(pen='y')
gpu_temp_curve = p2.plot(pen='r')
cpu_clock_curve = p3.plot(pen='g')
cpu_usage_curve = p4.plot(pen='b')

# Create TextItems for displaying current values with specified anchors and colors
gpu_usage_text = pg.TextItem(anchor=(1, 1), color="w")
gpu_temp_text = pg.TextItem(anchor=(1, 1), color="w")
cpu_clock_text = pg.TextItem(anchor=(1, 1), color="w")
cpu_usage_text = pg.TextItem(anchor=(1, 1), color="w")

# Position the text boxes at a visible location within each plot
p1.addItem(gpu_usage_text)
gpu_usage_text.setPos(90, 90)  # Position near the top right

p2.addItem(gpu_temp_text)
gpu_temp_text.setPos(90, 90)

p3.addItem(cpu_clock_text)
cpu_clock_text.setPos(90, 4500)  # Adjusted for CPU clock range

p4.addItem(cpu_usage_text)
cpu_usage_text.setPos(90, 90)

# Initialize data lists for storing the latest data
data = {
    "gpu_usage": [],
    "gpu_temp": [],
    "cpu_clock": [],
    "cpu_usage": [],
    "audio_level": [0]
}

# Set up the default speaker for audio capture
default_speaker = sc.default_speaker()

def get_audio_peak():
    """Capture audio from the default speaker and compute its volume peak."""
    try:
        with sc.get_microphone(id=str(default_speaker.name), include_loopback=True).recorder(samplerate=44100, blocksize=4096) as mic: #Getting microphone as input, but enable loopback to hear system output
            audio_data = mic.record(numframes=1024)
            # Take the absolute value to remove negative peaks
            peak_volume = np.max(np.abs(audio_data))  # Detect absolute peak volume
            return min(peak_volume, 1.0)  # Normalize to 1.0 as max
    except Exception as e:
        print("Error capturing audio:", e)
        return 0

# Maximum number of points to display
max_points = 100

# Set y-axis range and limits for each plot, and disable y-axis zoom/pan
p1.setYRange(0, 100)  # GPU Usage (%)
p1.setLimits(xMin=0, xMax=max_points, yMin=0, yMax=100)
p1.setMouseEnabled(y=False)  # Disable y-axis zoom and pan

p2.setYRange(0, 100)  # GPU Temp (°C)
p2.setLimits(xMin=0, xMax=max_points, yMin=0, yMax=100)
p2.setMouseEnabled(y=False)

p3.setYRange(0, 5000)  # Initial range for CPU Clock Speed
p3.setLimits(xMin=0, xMax=max_points, yMin=0, yMax=5000)
p3.setMouseEnabled(y=False)

p4.setYRange(0, 100)  # CPU Usage (%)
p4.setLimits(xMin=0, xMax=max_points, yMin=0, yMax=100)
p4.setMouseEnabled(y=False)

# Configure the audio plot to have a fixed y-axis as well
audio_plot.setXRange(0, 1)  # Normalize the audio level range
audio_plot.setYRange(0, 0.5)
audio_plot.setLimits(xMin=0, xMax=1, yMin=0, yMax=1)
audio_plot.setMouseEnabled(y=False)
audio_plot.setMouseEnabled(x=False)

def update():
    # Capture GPU, CPU data
    gpu_util = nvmlDeviceGetUtilizationRates(gpu_handle).gpu
    gpu_temp = nvmlDeviceGetTemperature(gpu_handle, NVML_TEMPERATURE_GPU)
    cpu_clock = psutil.cpu_freq().current
    cpu_usage = psutil.cpu_percent()

    # Append data to lists and limit to max_points
    data["gpu_usage"].append(gpu_util)
    data["gpu_usage"] = data["gpu_usage"][-max_points:]

    data["gpu_temp"].append(gpu_temp)
    data["gpu_temp"] = data["gpu_temp"][-max_points:]

    data["cpu_clock"].append(cpu_clock)
    data["cpu_clock"] = data["cpu_clock"][-max_points:]

    data["cpu_usage"].append(cpu_usage)
    data["cpu_usage"] = data["cpu_usage"][-max_points:]

    # Update plots with fixed range for recent data
    gpu_usage_curve.setData(data["gpu_usage"])
    gpu_temp_curve.setData(data["gpu_temp"])
    cpu_clock_curve.setData(data["cpu_clock"])
    cpu_usage_curve.setData(data["cpu_usage"])

    # Capture audio level and limit to max_points
    current_audio_level = get_audio_peak()
    data["audio_level"].append(current_audio_level)
    data["audio_level"] = data["audio_level"][-max_points:]
    audio_bar.setOpts(width=current_audio_level)

    # Update the text boxes with the current values
    gpu_usage_text.setText(f"{gpu_util:.1f}%")
    gpu_temp_text.setText(f"{gpu_temp:.1f}°C")
    cpu_clock_text.setText(f"{cpu_clock:.1f} MHz")
    cpu_usage_text.setText(f"{cpu_usage:.1f}%")


# Start the update timer
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(100)

# Display the window
win.show()
if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()
