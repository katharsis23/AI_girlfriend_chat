import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

AbstractButton {
    id: row
    property string title: ""
    property string subtitle: ""
    property string glyph: ""
    implicitHeight: 82
    padding: 13
    hoverEnabled: true
    Accessible.role: Accessible.Button
    Accessible.name: title
    Accessible.description: subtitle
    background: Rectangle {
        radius: 18
        color: row.down || row.hovered ? Theme.surfaceVariant : Theme.surface
        border.width: 1
        border.color: row.hovered ? Qt.alpha(Theme.primary, 0.45) : Qt.alpha(Theme.outline, 0.18)
        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }
    contentItem: RowLayout {
        spacing: 13
        Rectangle {
            Layout.preferredWidth: 46; Layout.preferredHeight: 46; radius: 16
            color: Qt.alpha(Theme.primary, 0.13)
            Text { anchors.centerIn: parent; text: row.glyph; color: Theme.primary; font.pixelSize: 23 }
        }
        ColumnLayout {
            Layout.fillWidth: true; spacing: 4
            Label { Layout.fillWidth: true; text: row.title; color: Theme.onSurface; font.pixelSize: Theme.fontSizeM; font.weight: Font.DemiBold }
            Label { Layout.fillWidth: true; text: row.subtitle; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS; elide: Text.ElideRight }
        }
        Text { text: "›"; color: Theme.onSurfaceVariant; font.pixelSize: 26 }
    }
}
