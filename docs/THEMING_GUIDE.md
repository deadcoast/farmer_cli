# Farmer CLI Theming Guide

## Overview

Farmer CLI features a sophisticated theming system that provides beautiful, customizable terminal interfaces. The theming system supports multiple color schemes, border styles, and visual elements to enhance your terminal experience.

## Available Themes

### 1. **Default**

- **Description**: Classic terminal aesthetic with vibrant colors
- **Border Style**: Double-line borders (╔═╗)
- **Color Palette**: Magenta borders, cyan titles, yellow highlights
- **Best For**: General use with good contrast

### 2. **Dark Mode**

- **Description**: Sleek dark theme for reduced eye strain
- **Border Style**: Single-line borders (┌─┐)
- **Color Palette**: White borders, green titles, cyan highlights
- **Best For**: Extended use in dark environments

### 3. **Light Mode**

- **Description**: Clean and bright theme for well-lit environments
- **Border Style**: Rounded borders (╭─╮)
- **Color Palette**: Black borders, blue titles, magenta highlights
- **Best For**: Bright environments or users who prefer light themes

### 4. **High Contrast**

- **Description**: Maximum contrast for accessibility
- **Border Style**: Heavy borders (┏━┓)
- **Color Palette**: Bright white borders, yellow titles, cyan on black highlights
- **Best For**: Users requiring maximum visibility

### 5. **Ocean**

- **Description**: Calming blue and teal palette
- **Border Style**: Rounded borders (╭─╮)
- **Color Palette**: Cyan borders, turquoise accents, sea green success
- **Best For**: Users who prefer blue-toned interfaces

### 6. **Forest**

- **Description**: Natural green tones inspired by nature
- **Border Style**: Single-line borders (┌─┐)
- **Color Palette**: Green borders, chartreuse accents, earth tones
- **Best For**: Users who prefer nature-inspired colors

### 7. **Neon**

- **Description**: Vibrant cyberpunk-inspired theme
- **Border Style**: Double-line borders (╔═╗)
- **Color Palette**: Hot pink titles, cyan accents, purple backgrounds
- **Best For**: Users who enjoy bold, futuristic aesthetics

### 8. **Monochrome**

- **Description**: Elegant grayscale theme
- **Border Style**: Single-line borders (┌─┐)
- **Color Palette**: White on black with gray accents
- **Best For**: Minimalist users or monochrome displays

### 9. **Retro**

- **Description**: Classic amber/green phosphor terminal
- **Border Style**: ASCII borders (+--+)
- **Color Palette**: Amber/yellow text on black
- **Best For**: Nostalgic users or retro terminal enthusiasts

## Theme Components

Each theme defines the following visual elements:

### Colors

- **border_style**: Color of frames and borders
- **title_style**: Main headings and titles
- **subtitle_style**: Secondary headings
- **option_style**: Menu options and choices
- **highlight_style**: Selected or emphasized items
- **success_style**: Success messages
- **error_style**: Error messages
- **warning_style**: Warning messages
- **info_style**: Information messages
- **prompt_style**: User input prompts

### UI Elements

- **header_style**: Top bars and headers
- **footer_style**: Bottom bars and footers
- **table_header_style**: Table column headers
- **table_row_style**: Table data rows
- **progress_bar_complete**: Filled progress sections
- **progress_bar_incomplete**: Empty progress sections

### Border Characters

- Single line: ┌─┐│└┘
- Double line: ╔═╗║╚╝
- Rounded: ╭─╮│╰╯
- Heavy: ┏━┓┃┗┛
- ASCII: +--+|++

## Visual Elements

The theming system includes various visual elements:

### Progress Indicators

- Filled: █
- Empty: ░
- Partial: ▒

### Status Indicators

- Bullet: •
- Check: ✓
- Cross: ✗
- Star: ★

### Arrows

- Right: →
- Left: ←
- Up: ↑
- Down: ↓

## Changing Themes

To change your theme:

```bash
1. From the main menu, select [3] Configuration
2. Select [1] Select Theme
3. Choose your desired theme from the list
4. The theme will be applied immediately and saved to your preferences
```

## Creating Custom Themes

To add a custom theme, edit the `src/themes.py` file and add your theme to the `THEMES` dictionary:

```python
"my_custom_theme": {
    "name": "My Custom Theme",
    "description": "A beautiful custom theme",
    "border_style": "bold blue",
    "border_chars": SINGLE_LINE,
    "title_style": "bold cyan",
    "subtitle_style": "cyan",
    # ... other style definitions
}
```

## Theme Showcase

To see all themes in action:

```bash
1. From the main menu, select [3] Configuration
2. Select [2] Theme Showcase
3. Follow the interactive demonstration of each theme
```

## Best Practices

1. **Consider Your Environment**: Choose themes based on your terminal background and lighting
2. **Accessibility**: Use High Contrast theme if you have visibility concerns
3. **Terminal Compatibility**: ASCII borders work best in limited terminals
4. **Performance**: All themes perform equally well
5. **Consistency**: Theme preferences are saved and persist between sessions

## Technical Details

The theming system uses:

- **Rich library**: For terminal styling and colors
- **Unicode characters**: For borders and visual elements
- **256-color support**: For extended color palettes
- **Fallback options**: ASCII alternatives for limited terminals

## Troubleshooting

### Borders Not Displaying Correctly

- Ensure your terminal supports Unicode
- Try switching to ASCII border theme (Retro)
- Check terminal font supports box-drawing characters

### Colors Not Showing

- Verify terminal supports 256 colors
- Check TERM environment variable
- Try a different terminal emulator

### Theme Not Persisting

- Check write permissions for preferences.json
- Ensure data directory exists
- Verify no syntax errors in theme definition
