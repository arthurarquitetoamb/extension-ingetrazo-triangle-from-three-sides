# Triangle from Three Sides

**An IngeTrazo extension that builds a triangle from its three side lengths.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![IngeTrazo](https://img.shields.io/badge/IngeTrazo-0.6.1-blue)](https://github.com/ingelibre/ingetrazo)
![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)

Enter three lengths, check the live area / perimeter / angle summary, and press
**Construct triangle**. The extension adds a real, editable face to the model —
one undoable step, using the document's own units.

## Features

- **SSS construction** — three side lengths define the triangle.
- **Document units everywhere** — metres, centimetres, millimetres, decimal
  feet, feet-and-inches and fractional feet-and-inches.
- **Typed units accepted** — write `3 m`, `118"`, `9'10"` or `250 cm` in any
  field; the value is converted to the model's metres behind the scenes.
- **Live summary** — area, perimeter and the three interior angles, in the
  document's area and angle units.
- **Triangle validation** — impossible or degenerate sets are refused with a
  clear explanation.
- **Editable result** — one group named `Triangle`, one flat face in the
  ground plane, centred on the model origin, on the current layer.
- **One undo step** — `Ctrl+Z` removes the whole object.
- **No dependencies** beyond IngeTrazo and its PySide6 runtime.

## Improved Precision Through Triangulation

Dividing a quadrilateral into two triangles improves precision in surveying and geometry because triangles are mathematically rigid shapes.
<img width="3151" height="1893" alt="triangle" src="https://github.com/user-attachments/assets/8211b34b-6507-45b0-99af-f772a9dee40a" />


## Installation

### Manual

Copy `triangle_from_three_sides.py` into the per-user plugins folder and
restart IngeTrazo:

| System | Plugins folder |
|---|---|
| Windows | `%APPDATA%\ingetrazo\plugins\` |
| Linux | `~/.local/share/ingetrazo/plugins/` (or `$XDG_DATA_HOME/ingetrazo/plugins/`) |
| macOS | `~/Library/Application Support/ingetrazo/plugins/` |

You can also use **Extensions → Open plugins folder** inside IngeTrazo, drop
the file there, and restart the application.

### From the ZIP

Download `triangle_from_three_sides-1.0.0.zip` from the latest release and
install it with **Extensions → Manage extensions…**, or unpack it into the
plugins folder. The package contains the plugin and this README.

After restarting, the command appears at:

**Extensions → Triangle from three sides…**

## Usage

1. Open **Extensions → Triangle from three sides…**.
2. Type the three side lengths.

   The dialog starts with a 3–4–5 triangle: 3 m / 4 m / 5 m in a metric
   document, or 3 ft / 4 ft / 5 ft in an imperial one.

3. Read the live summary:

   ```text
   Area: 6.00 m²    Perimeter: 12.00 m
   Angles A–B–C: 36.9° · 53.1° · 90.0°    (right triangle)
   ```

4. Press **Construct triangle**.

The result is a group named **Triangle** containing one face. It is selected
when created, so it can be moved, painted, grouped or Push/Pulled immediately.

## Units

The fields use the same `core.units` layer as every IngeTrazo tool. What you
see and what you type follow the document:

| Document units | Field shows | Examples of valid input |
|---|---|---|
| Metres | `3.00 m` | `3`, `2.5 m`, `250 cm` |
| Centimetres | `300.00 cm` | `300`, `3 m`, `2500 mm` |
| Millimetres | `3000 mm` | `3000`, `3 m`, `250 cm` |
| Decimal feet | `9.84'` | `9.84'`, `3 m` |
| Feet and inches | `9'10"` | `9'10"`, `118"`, `3 m` |
| Fractional feet and inches | `9'10 1/16"` | `9'10"`, `118"`, `3 m` |

The displayed text is only a view. The value behind every field is always
**metres**, IngeTrazo's model unit, so the code that creates the geometry never
converts anything.

## Validation

The extension refuses a set of lengths that cannot close a triangle and says
why in the dialog:

- **Side zero or negative** — every side must be longer than zero.
- **Triangle inequality** — the longest side must be shorter than the other
  two added together. For example, `1`, `1` and `2.1` do not close.
- **Degenerate** — lengths that only describe a flat line are rejected.
- **Non-finite values** — `NaN` and infinity are rejected.

The check uses a small relative tolerance so rounding in the fields cannot
turn a valid triangle into an error.

## What gets created

| Property | Value |
|---|---|
| Object | One group named `Triangle` |
| Geometry | One face in the ground plane (`Z = 0`), facing up |
| Position | Centred on the model origin |
| Layer | The document's active layer |
| Parameters | `group.ext["triangle_from_three_sides"] = {"a": …, "b": …, "c": …}` |
| Undo | One step through `core.history.SnapshotImport` |

The face is not a solid. Use **Push/Pull** if you need a triangular prism.

## How it works

With side `c` as the base, the apex is found with the law of cosines:

```text
x = (b² + c² − a²) / (2c)
h = √(b² − x²)
```

So the vertices are:

```text
A = (0, 0)
B = (c, 0)
C = (x, h)
```

The triangle is then translated so its centroid sits at the model origin.
Area and angles are computed from the original lengths, not measured back from
the mesh, so the summary describes the intended construction.

Everything goes through IngeTrazo's command layer (`SnapshotImport`), which
means the document is marked unsaved normally and the whole operation is a
single undo step.

## Compatibility

- Developed and tested with **IngeTrazo 0.6.1** (extension API 2).
- Uses `views.length_field.LengthSpinBox` when available. Older 0.x builds that
  do not provide it fall back to a metres-only field.
- Requires no extra Python packages.
- The interface is in **English**.

## Troubleshooting

**The menu entry does not appear.**
Restart IngeTrazo after copying the file. Check the plugin folder path and use
**Extensions → Manage extensions…** to see whether the extension failed to
load; the error and log folder are shown there.

**The lengths show the wrong unit.**
The dialog follows the open document's units, not the application's default.
Check the document units in the units panel or Preferences.

**The triangle is not visible.**
It is created at the model origin, in the ground plane. Select the `Triangle`
group in the Browser, or use **Zoom Extents**.

**Undo removed more than the triangle.**
The construction is one undo step by design. If you made other edits after it,
each of those is a separate step.

Contributions and issue reports are welcome.

## License

This extension is released under the **GNU General Public License v3.0 or
later** (GPL-3.0-or-later), the same license as IngeTrazo.

You are free to use, study, share and modify it. If you distribute a modified
version, it must remain under the same license.
