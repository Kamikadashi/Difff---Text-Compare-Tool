# Difff - Text Compare Tool

**Difff** is a lightweight web-based text comparison tool inspired by the [meso-cacase' difff](https://github.com/meso-cacase/difff). It allows you to compare two texts line-by-line and character-by-character, highlighting differences in an intuitive and visually appealing way.

## Features
- **Side-by-Side Comparison**: View differences between two texts in a side-by-side layout.
- **Character-Level Highlighting**: Differences are highlighted at the character level for precise comparison.
- **Persistent Settings**: Save your preferred theme (Dark, Light, Sepia) and layout (side-by-side or stacked) across sessions.
- **Text Statistics**: Get detailed statistics for each text, including word count, character count, spaces, and linefeeds.
- **Customizable Highlight Color**: Choose your preferred highlight color for differences.

## How It Works
The tool uses Python's `difflib` library to compare texts and generates an HTML-based interface for visualization. It runs a local HTTP server to serve the comparison results in your browser.

## Usage
1. Clone the repository:
   ```bash
   git clone https://github.com/Kamikadashi/Difff---Text-Compare-Tool.git
   cd Difff---Text-Compare-Tool
   ```
2. Run the script:
   ```bash
   python difff.py
   ```
3. Open your browser and navigate to `http://localhost:8004`.
4. Enter your texts in the provided text areas and click "Compare" to see the differences.

## Dependencies
- Python 3.x
- `difflib` (standard library)
- `http.server` (standard library)
- `webbrowser` (standard library)

## Acknowledgments
This project was inspired by the [meso-cacase' difff](https://github.com/meso-cacase/difff). Special thanks to the original creators!

## License
This project is open-source and available under the MIT License. Feel free to use, modify, and distribute it as needed.
