# Roblox Python External

to teach you skids the basics

## Requirements

- Python 3.7+
- Windows OS
- Roblox (RobloxPlayerBeta.exe)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/python-external-roblox.git
cd python-external-roblox
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

The project uses the following Python packages:

- `pymem==1.13.0`
- `psutil==5.9.6`
- `keyboard==0.13.5` 
- `mouse==0.7.1` 
- `PyQt5==5.15.10` 
- `pyautogui==0.9.54` 

## Usage

1. **Start Roblox**: Launch any Roblox game
2. **Run the tool**: Execute the main script
   ```bash
   python main.py
   ```
3. **Features**:
   - The tool will automatically detect and attach to Roblox
   - ESP overlay shows player positions as red dots
   - Use the GUI to toggle ESP on/off
   - Press `Insert` key to hide/show the GUI

## Project Structure

```
python-external-roblox/
├── main.py           # Main application entry point
├── memory.py         # Memory management and process handling
├── classes.py        # Core classes (instance, utils, scheduler)
├── offsets.json      # Memory offsets for Roblox structures
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```


