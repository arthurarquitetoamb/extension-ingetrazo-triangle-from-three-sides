# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IngeTrazo contributors.
"""Triangle from three sides — an IngeTrazo extension.

Builds a planar triangle from its three side lengths (SSS), the classical
ruler-and-compass construction: side ``c`` lies along the X axis, side ``b``
closes the triangle at the apex, and side ``a`` is the triangle inequality's
third condition -- if any two sides added together are not longer than the
third, there is no triangle and the extension says so.

Everything a field shows or reads goes through ``core.units``: a document in
metres shows and takes metres, a millimetre document shows and takes
millimetres, and an imperial document shows feet-and-inches
(``1'6 1/2"``) and also reads a typed ``18"`` or ``1.5'``. The value behind
the field is always metres, the model's unit.

The triangle is one undoable step: a group named "Triangle" holding a single
face in the ground plane, centred on the model origin, in the current layer.
Select it and move it like anything else. ``Ctrl+Z`` takes it away.

Install: copy this file into the plugins folder (Extensions ▸ Open plugins
folder) and restart IngeTrazo. It appears as **Extensions ▸ Triangle from
three sides…**.
"""
from __future__ import annotations

import math

from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from core import units
from core.group import Group
from core.history import SnapshotImport
from core.mesh import Mesh
from tools.base import Tool

#: The key this extension uses for its own parameters in ``group.ext``.
KEY = "triangle_from_three_sides"

#: A side may be this long, at most (metres): the field's range, not a
#: geometric limit of the construction.
MAX_SIDE = 10_000.0

#: The smallest side taken (metres): one millimetre, so a millimetre
#: document can still draw a real triangle.
MIN_SIDE = 0.001


# ---------------------------------------------------------------------------
# The geometry
# ---------------------------------------------------------------------------

def _clamp_unit(value: float) -> float:
    """Keep an arccosine argument inside [-1, 1] despite rounding."""
    return max(-1.0, min(1.0, value))


def triangle_geometry(a: float, b: float, c: float) -> dict:
    """Everything the dialog and the mesh need for sides ``a``, ``b``, ``c``.

    Returns ``{"points", "area", "perimeter", "angles", "right"}``:

    - ``points`` are three ``(x, y, z)`` tuples on the ground plane, already
      centred on their centroid so the new triangle appears around the
      model origin;
    - ``area`` is in square metres, ``perimeter`` in metres;
    - ``angles`` maps ``"A"``, ``"B"``, ``"C"`` to radians, each opposite the
      side of the same lowercase letter;
    - ``right`` says whether one of them is a right angle.

    Raises ``ValueError`` when the three lengths cannot close a triangle.
    """
    try:
        a, b, c = float(a), float(b), float(c)
    except (TypeError, ValueError) as exc:
        raise ValueError("Enter three numeric side lengths.") from exc

    if not all(math.isfinite(v) for v in (a, b, c)):
        raise ValueError("The side lengths must be finite numbers.")
    if min(a, b, c) <= 0.0:
        raise ValueError("Every side must be longer than zero.")

    longest = max(a, b, c)
    tolerance = 1e-9 * longest
    if (a + b <= c + tolerance
            or a + c <= b + tolerance
            or b + c <= a + tolerance):
        other = sorted((a, b, c))[:2]
        raise ValueError(
            "These three lengths do not close a triangle: the longest side "
            f"({units.fmt_len(longest)}) must be shorter than the other two "
            f"added together ({units.fmt_len(other[0] + other[1])}).")

    # Classical construction: A at the origin, B on +X at distance c, and C
    # where the circle of radius b around A meets the circle of radius a
    # around B. Its x is the law of cosines; its height follows Pythagoras.
    x = (b * b + c * c - a * a) / (2.0 * c)
    height_squared = b * b - x * x
    if height_squared <= 0.0:
        raise ValueError("These three lengths describe a flat line, not a "
                         "triangle.")
    height = math.sqrt(height_squared)

    points = [(0.0, 0.0, 0.0), (c, 0.0, 0.0), (x, height, 0.0)]
    cx = (points[0][0] + points[1][0] + points[2][0]) / 3.0
    cy = (points[0][1] + points[1][1] + points[2][1]) / 3.0
    points = [(px - cx, py - cy, pz) for px, py, pz in points]

    def angle(opposite: float, first: float, second: float) -> float:
        return math.acos(_clamp_unit(
            (first * first + second * second - opposite * opposite)
            / (2.0 * first * second)))

    angles = {
        "A": angle(a, b, c),
        "B": angle(b, a, c),
        "C": angle(c, a, b),
    }
    right = any(abs(value - math.pi / 2.0) < 1e-6
                for value in angles.values())
    return {
        "points": points,
        "area": 0.5 * c * height,
        "perimeter": a + b + c,
        "angles": angles,
        "right": right,
    }


def create_triangle(scene, a: float, b: float, c: float) -> Group:
    """Add the triangle to ``scene`` as one group and select it.

    The mesh, the group and its parameters are created here; the caller is
    expected to run this inside :class:`SnapshotImport`, so the whole thing
    is one undo step.
    """
    from core.layers import active_layer

    geometry = triangle_geometry(a, b, c)
    mesh = Mesh()
    mesh.add_face([QVector3D(*point) for point in geometry["points"]])

    group = Group(mesh, name="Triangle")
    group.layer = active_layer(scene)
    group.ext = {KEY: {
        "a": float(a),
        "b": float(b),
        "c": float(c),
    }}
    scene.groups.append(group)
    scene.selection.clear()
    scene.selection.add(group)
    return group


# ---------------------------------------------------------------------------
# Length fields in the document's units
# ---------------------------------------------------------------------------

try:                                    # IngeTrazo 0.5.8 and later
    from views.length_field import LengthSpinBox
except Exception:                       # an older IngeTrazo: metres only
    LengthSpinBox = None


def _length_field(parent, value: float):
    """A field whose value is metres and whose text follows the document."""
    if LengthSpinBox is not None:
        field = LengthSpinBox(parent, minimum=MIN_SIDE, maximum=MAX_SIDE)
    else:
        field = QDoubleSpinBox(parent)
        field.setRange(MIN_SIDE, MAX_SIDE)
        field.setDecimals(3)
        field.setSingleStep(0.10)
        field.setSuffix(" m")
    field.setValue(value)
    return field


def _default_sides() -> tuple:
    """A 3–4–5 triangle to start from: three metres each in a metric
    document, three feet each in an imperial one."""
    unit = units.model_unit()
    if unit in ("in", "ft", "ft-in", "in-frac", "ft-in-frac"):
        foot = units.FT_M
        return 3.0 * foot, 4.0 * foot, 5.0 * foot
    return 3.0, 4.0, 5.0


# ---------------------------------------------------------------------------
# The dialog
# ---------------------------------------------------------------------------

class TriangleDialog(QDialog):
    """Three side fields, a live summary and the Construct button."""

    def __init__(self, viewport, parent=None) -> None:
        super().__init__(parent or viewport.window())
        self._viewport = viewport
        self.setWindowTitle("Triangle from three sides")
        self.setMinimumWidth(420)
        self._build_ui()
        self._update_preview()

    # ---- Layout ------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        unit = units.unit_label(units.model_unit())
        hint = QLabel(
            "Enter the three side lengths. They are shown and typed in the "
            f"document's units: <b>{unit}</b>.")
        hint.setWordWrap(True)
        root.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(6)
        first, second, third = _default_sides()
        self._a = _length_field(self, first)
        self._b = _length_field(self, second)
        self._c = _length_field(self, third)
        form.addRow("Side a", self._a)
        form.addRow("Side b", self._b)
        form.addRow("Side c", self._c)
        root.addLayout(form)

        self._summary = QLabel()
        self._summary.setWordWrap(True)
        self._summary.setMinimumHeight(58)
        root.addWidget(self._summary)

        note = QLabel(
            "A flat face in the ground plane, centred on the model origin. "
            "It is created as the group «Triangle», in the current layer.")
        note.setWordWrap(True)
        note.setEnabled(False)
        root.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._ok = buttons.button(QDialogButtonBox.Ok)
        self._ok.setText("Construct triangle")
        buttons.button(QDialogButtonBox.Cancel).setText("Close")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        for field in (self._a, self._b, self._c):
            field.valueChanged.connect(self._update_preview)

    # ---- Reading the fields ------------------------------------------------
    def _sides(self):
        """The three lengths in metres, or ``None`` after pointing at the
        field that does not hold a valid length."""
        for field in (self._a, self._b, self._c):
            error = getattr(field, "error_text", None)
            if error is not None:
                message = error()
                if message:
                    self._summary.setText(message)
                    field.setFocus()
                    return None
            field.interpretText()
        return self._a.value(), self._b.value(), self._c.value()

    def _update_preview(self, *_args) -> None:
        sides = [self._a.value(), self._b.value(), self._c.value()]
        try:
            geometry = triangle_geometry(*sides)
        except ValueError as exc:
            self._summary.setText(str(exc))
            self._ok.setEnabled(False)
            return

        angles = geometry["angles"]
        angle_text = " · ".join(
            units.fmt_angle(angles[key]) for key in ("A", "B", "C"))
        text = (f"Area: {units.fmt_area(geometry['area'])}    "
                f"Perimeter: {units.fmt_len(geometry['perimeter'])}\n"
                f"Angles A–B–C: {angle_text}")
        if geometry["right"]:
            text += "    (right triangle)"
        self._summary.setText(text)
        self._ok.setEnabled(True)

    # ---- Constructing ------------------------------------------------------
    def accept(self) -> None:
        sides = self._sides()
        if sides is None:
            return
        try:
            geometry = triangle_geometry(*sides)
        except ValueError as exc:
            self._summary.setText(str(exc))
            return

        viewport = self._viewport
        a, b, c = sides

        def build(scene):
            create_triangle(scene, a, b, c)

        history = viewport.history
        history.execute(SnapshotImport(build))
        if history.last_error:
            self._summary.setText(
                "The triangle could not be created: "
                + history.last_error.split(": ", 1)[-1])
            return

        notify = getattr(viewport, "notify_scene_changed", None)
        if callable(notify):
            notify()
        viewport.update()
        flash = getattr(viewport, "flash_status", None)
        if callable(flash):
            flash("Triangle {} created.".format(
                units.fmt_triple(a, b, c)), 4000)
        super().accept()


# ---------------------------------------------------------------------------
# Tool registration (the plugin entry point)
# ---------------------------------------------------------------------------

class TriangleFromThreeSidesTool(Tool):
    """Extensions-menu tool that opens the three-side dialog."""

    name = "Triangle from three sides"
    shortcut = None
    description = ("Construct a triangle from its three side lengths, in the "
                   "document's units.")
    uses_snap = False

    def on_activate(self, viewport) -> None:
        TriangleDialog(viewport, parent=viewport.window()).exec()

    def on_deactivate(self, viewport) -> None:
        pass
