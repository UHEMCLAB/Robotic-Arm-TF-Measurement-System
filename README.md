# Robotic-Arm-TF-Measurement-System
Source code and instruction to robotic arm transfer function measurement system developed by Dr. Ji Chen's lab at University of Houston

# Installation Instructions for the Curved Trajectory TF Measurement System Application GUI (version 2.5)

**Disclaimer:**  
The mention of commercial products, their sources, or their use in connection with material reported herein is not to be construed as either an actual or implied endorsement of such products by the Department of Health and Human Services.

This document provides installation instructions for the application that provides a graphical interface (GUI) for controlling an XArm robotic system and visualizing data using a PyQt5-based GUI. The application allows you to manage, analyze, and plot data from connected instruments using libraries like NumPy, pandas, and qwt.

**This code (python code – see ‘armsystem.py’) has only been tested under Ubuntu 20.04/22.04 LTS version; it is not guaranteed to operate on any other environment.**

## Features
- **GUI Interface:** Built using PyQt5 for intuitive user interaction.
- **Data Visualization:** Uses Qwt for plotting data (e.g., magnitude and phase plots).
- **Robotic Arm Control:** Supports control of an XArm robotic system via the `xarm` Python wrapper.
- **Instrument Communication:** Interacts with instruments through pyVISA.
- **Data Handling:** Processes and stores data using NumPy and pandas.

## Requirements
- A compatible robotic arm (this code is tested on model XArm 6 from UFactory).
    - [XArm 6 Product Page](https://www.ufactory.cc/product-page/ufactory-xarm-6/)
- A visa-compatible vector network analyzer (VNA) (this code is tested on Copper Mountain TR1300 VNA).
    - [Copper Mountain TR1300 VNA Product Page](https://coppermountaintech.com/vna/tr1300-1-2-port-1-3-ghz-analyzer/)
- Python 3.x.
    - [Download Python](https://www.python.org/downloads/)
- PyQt5: PyQt5 is a set of Python bindings for the Qt application framework used for creating graphical user interfaces (GUIs).
    - [PyQt5 Documentation](https://pypi.org/project/PyQt5/)
- Qwt: Provides widgets for plotting and other scientific purposes.
    - [Qwt Documentation](https://pypi.org/project/PythonQwt/)
- XArm Python SDK: Provides the necessary functions to communicate with and control the XArm 6 robotic arm.
    - [XArm SDK GitHub Repository](https://github.com/xArm-Developer/xArm-Python-SDK)
- pyVISA: Used for communicating with instruments like oscilloscopes, spectrum analyzers, and VNAs.
    - [pyVISA Documentation](https://pyvisa.readthedocs.io/en/latest/)
- NumPy: Handles numerical data and enables mathematical operations and data processing.
    - [NumPy Documentation](https://numpy.org/install/)
- pandas: Manages data logs and processes the measured data from instruments.
    - [pandas Documentation](https://pandas.pydata.org/getting_started.html)

## Installation

1. Set up the Linux environment and Python running environment. Connect both VNA and robotic arm to the Linux environment. In the testing environment, the VNA is connected via USB, and the robotic arm is connected via LAN. Extra permission on mounted devices may be needed to allow the code to read and write data to devices. The devices' name or address in this code may need to be changed to allow the code to find the devices.

2. Install the dependencies:
    - PyQt5
    - Qwt
    - XArm SDK
    - pyVISA
    - NumPy
    - pandas

3. Use any Python compiler (VS Code is recommended for its ease of use). Import this code into VS Code. Once all dependencies are installed, you can run the application. This will launch the graphical interface, allowing you to interact with the robotic system and visualize the data.

## Troubleshooting
If you encounter issues related to dependencies, ensure that all required libraries are installed and that your environment is properly configured. You can also try reinstalling the dependencies or refer to the devices' programming guides.
