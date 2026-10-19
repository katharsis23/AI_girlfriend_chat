import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: bar
    property string title: ""
    property string subtitle: ""
    property bool showBack: false
    signal backClicked()
    default property alias actions: actionRow.data
    implicitHeight: 76
    color: Theme.background

    RowLayout {
        z: 2
        anchors.fill: parent
        anchors.leftMargin: 14; anchors.rightMargin: 12
        spacing: 8
        IconButton { visible: bar.showBack; glyph: "‹"; accessibleName: qsTr("Back"); onClicked: bar.backClicked(); implicitWidth: 38; implicitHeight: 38 }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: bar.showBack ? 0 : 4
            spacing: 3
            Label { Layout.fillWidth: true; text: bar.title; elide: Text.ElideRight; color: Theme.onSurface; font.pixelSize: 19; font.weight: Font.DemiBold }
            RowLayout {
                spacing: 6
                Rectangle { width: 7; height: 7; radius: 4; color: Theme.secondary }
                Label { Layout.fillWidth: true; visible: bar.subtitle.length > 0; text: bar.subtitle; elide: Text.ElideRight; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS }
            }
        }
        Row { id: actionRow; spacing: 2 }
        IconButton { visible: !bar.showBack; glyph: "—"; accessibleName: qsTr("Minimize window"); implicitWidth: 32; implicitHeight: 32; onClicked: bar.Window.window.showMinimized() }
        IconButton { visible: !bar.showBack; glyph: "×"; accessibleName: qsTr("Close window"); implicitWidth: 32; implicitHeight: 32; onClicked: bar.Window.window.close() }
    }
    MouseArea {
        anchors.fill: parent
        z: 1
        acceptedButtons: Qt.LeftButton
        onPressed: function(mouse) { if (mouse.button === Qt.LeftButton) bar.Window.window.startSystemMove() }
    }
    Rectangle { anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter; width: parent.width - 28; height: 1; color: Qt.alpha(Theme.outline, 0.22) }
}
