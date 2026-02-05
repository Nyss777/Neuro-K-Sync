# Neuro-K-Sync


## This is a tool made to update your Neuro karaoke songs with the latest metadata


This is a lightweight program that checks the metadata of your [Neuro Karaoke Archive](https://drive.google.com/drive/folders/1B1VaWp-mCKk15_7XpFnImsTdBJPOGx7a) files and syncs them with the [Metadata Repository](https://github.com/Nyss777/Neuro-Karaoke-Archive-Metadata). It is compatible with [DF-Customizer](https://github.com/gamerturuu/df-metadata-customizer/releases/latest) presets.

## How to use:

1. Run the executable;
2. Select the directory containing the karaoke files (The program will remember the chosen path after the first time);
3. Watch the terminal for progress;

To use a DF-Customizer preset, simply put the preset in the folder with the  `.exe`

>You may pass a directory as an `--path` argument. e.g.: `Neuro_K_Sync.exe --path "path/to/directory"`

## What this program does not do?

* It only updates songs, it doesn't download songs on it's own.
* For efficiency, this program mostly does not feature a GUI. 
* It doesn't verify songs for the given preset, it only formats the changed ones.
* It is currently not compatible with songs downloaded before 2025-12-13, they will not be detected.
