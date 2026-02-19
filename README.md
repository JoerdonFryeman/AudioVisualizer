# ЭЛЕКТРОНИКА 54 (AudioVisualizer)

A simple console audio visualization.

<img width="621" height="274" alt="AudioVisualizer" src="https://github.com/user-attachments/assets/49ff0c28-4613-49e1-bd30-38e2365480e8" />

## Startup
Download [latest release](https://github.com/JoerdonFryeman/AudioVisualizer/releases/tag/AudioVisualizer_v1.0.1).

In Linux, run ```AudioVisualizer_v1.0.1``` in the terminal with the command:
```console
cd /home/your_directories.../AudioVisualizer_v1.0.1/Linux/ && ./AudioVisualizer_v1.0.1
```

## Requirements

- Python: >= 3.14
- numpy: >= 2.4.2
- sounddevice: >= 0.5.5
- pulsectl: >= 24.12.0
- The application was developed for Arch Linux with the KDE Plasma desktop environment, but should work in other distributions.

## Installation

Download the project

``` console
git clone https://github.com/JoerdonFryeman/AudioVisualizer
cd AudioVisualizer
```

### For Linux

Create and activate a virtual environment:

``` console
python -m venv venv && source venv/bin/activate
```

Install the requirements and run the script in your console:

``` console
pip install --upgrade pip && pip install -r requirements.txt
python main.py
```

## Stop

Just press Enter or try any other key.

## Settings

Some program settings can be specified in the preset.json file.

- You can change the number of your audio device.
- Each time it is launched, the application logs the current audio devices, so device listings are available in the application log.
- Change the channels_number, samples_number, maxsize, bands_levels or the bands values.

The default settings can be restored by deleting the preset.json file and restarting the program.

## License

This project is being developed under the MIT license.

## Support with Bitcoin

bc1qewfgtrrg2gqgtvzl5d2pr9pte685pp5n3g6scy
