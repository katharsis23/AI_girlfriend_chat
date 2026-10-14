import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

// Reusable color picker popup (M3-ish). Emits `colorPicked(hex)` with a
// normalized "#RRGGBB" string. Contains a saturation/value square, a hue bar
// and a hex field so it works without any extra native dialogs.
Popup {
    id: picker
    property color value: "#000000"
    signal colorPicked(string hex)

    modal: true
    focus: true
    padding: 16
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    // QML `color` channels are floats in [0,1]; convert to 0..255 ints first,
    // otherwise toString(16) emits fractions (e.g. "0.8") instead of hex bytes.
    function _byte(v) {
        var n = Math.round(Math.max(0, Math.min(1, v)) * 255)
        return n.toString(16).padStart(2, "0")
    }

    function _normalize(c) {
        return "#" + _byte(c.r) + _byte(c.g) + _byte(c.b)
    }

    // h/s/v working state
    property real hue: 0
    property real sat: 1
    property real val: 1

    function _loadFromColor(c) {
        // hsvHue is -1 for grayscale colors; clamp to 0 so the hue bar stays valid.
        hue = Math.max(0, c.hsvHue)
        sat = c.hsvSaturation
        val = c.hsvValue
    }

    Component.onCompleted: _loadFromColor(value)
    onValueChanged: if (!svArea.pressed && !hueBar.pressed) _loadFromColor(value)

    function _currentColor() {
        return Qt.hsva(hue, sat, val, 1)
    }

    function _emit() {
        colorPicked(_normalize(_currentColor()))
    }

    background: Rectangle {
        radius: Theme.radius
        color: Theme.surface
        border.width: 1
        border.color: Theme.outline
    }

    contentItem: ColumnLayout {
        spacing: 12
        implicitWidth: 280

        // Saturation / Value square
        Rectangle {
            id: svRect
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            radius: 10
            clip: true

            Canvas {
                id: svCanvas
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    // value (black -> transparent)
                    var g = ctx.createLinearGradient(0, 0, 0, height)
                    g.addColorStop(0, "rgba(0,0,0,0)")
                    g.addColorStop(1, "rgba(0,0,0,1)")
                    ctx.fillStyle = g
                    ctx.fillRect(0, 0, width, height)
                    // saturation (white -> hue)
                    var g2 = ctx.createLinearGradient(0, 0, width, 0)
                    g2.addColorStop(0, "rgba(255,255,255,1)")
                    g2.addColorStop(1, Qt.hsva(picker.hue, 1, 1, 1).toString())
                    ctx.fillStyle = g2
                    ctx.fillRect(0, 0, width, height)
                }
                Connections {
                    target: picker
                    function onHueChanged() { svCanvas.requestPaint() }
                }
            }
            // hue base underneath
            Rectangle {
                z: -1
                anchors.fill: parent
                color: Qt.hsva(picker.hue, 1, 1, 1)
            }

            MouseArea {
                id: svArea
                anchors.fill: parent
                function pick(mx, my) {
                    picker.sat = Math.max(0, Math.min(1, mx / width))
                    picker.val = 1 - Math.max(0, Math.min(1, my / height))
                    picker._emit()
                }
                onPressed: pick(mouseX, mouseY)
                onPositionChanged: if (pressed) pick(mouseX, mouseY)

                Rectangle {
                    width: 14; height: 14; radius: 7
                    x: picker.sat * svArea.width - width / 2
                    y: (1 - picker.val) * svArea.height - height / 2
                    color: "transparent"
                    border.width: 2
                    border.color: "white"
                    Rectangle {
                        anchors.fill: parent; anchors.margins: 2
                        radius: 5; color: "transparent"
                        border.width: 1; border.color: "black"
                    }
                }
            }
        }

        // Hue bar
        Rectangle {
            id: hueBar
            Layout.fillWidth: true
            Layout.preferredHeight: 18
            radius: 9
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.000; color: "#ff0000" }
                GradientStop { position: 0.167; color: "#ffff00" }
                GradientStop { position: 0.333; color: "#00ff00" }
                GradientStop { position: 0.500; color: "#00ffff" }
                GradientStop { position: 0.667; color: "#0000ff" }
                GradientStop { position: 0.833; color: "#ff00ff" }
                GradientStop { position: 1.000; color: "#ff0000" }
            }
            MouseArea {
                anchors.fill: parent
                function pick(mx) {
                    picker.hue = Math.max(0, Math.min(0.9999, mx / width))
                    svCanvas.requestPaint()
                    picker._emit()
                }
                onPressed: pick(mouseX)
                onPositionChanged: if (pressed) pick(mouseX)
            }
            Rectangle {
                width: 8; height: parent.height + 6
                radius: 3
                anchors.verticalCenter: parent.verticalCenter
                x: picker.hue * hueBar.width - width / 2
                color: "transparent"
                border.width: 2
                border.color: "white"
            }
        }

        // Preview + hex input
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 36
                radius: 8
                color: picker._currentColor()
                border.width: 1
                border.color: Theme.outline
            }
            TextField {
                id: hexField
                Layout.fillWidth: true
                text: picker._normalize(picker._currentColor())
                placeholderText: "#RRGGBB"
                color: Theme.onSurface
                font.family: "monospace"
                onTextEdited: commitHex()
                onAccepted: commitHex()
                function commitHex() {
                    var t = text.trim()
                    if (/^#?[0-9a-fA-F]{6}$/.test(t)) {
                        var c = "#" + (t[0] === "#" ? t.substring(1) : t)
                        picker._loadFromColor(c)
                        svCanvas.requestPaint()
                        picker.colorPicked(c)
                    }
                }
            }
        }
    }
}
