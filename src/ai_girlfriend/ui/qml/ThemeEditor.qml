import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import App 1.0
import "components"

// Note: ColorPicker is resolved from the components/ directory imported above.

// Create or edit a custom theme (spec §5.4). Editing a built-in theme is not
// allowed; pass `themeId` of an existing *custom* theme to edit it, or leave it
// empty to start from the current theme's colors.
Page {
    id: view
    property string themeId: ""

    readonly property bool isEditing: themeId.length > 0

    // Working copy of the colors, seeded once when the page is created.
    property var draftColors: ({})
    property string draftName: ""
    property bool draftDark: ThemeController.isDark

    Component.onCompleted: {
        if (isEditing) {
            draftColors = Backends.settings.themeColors(themeId)
            draftName = Backends.settings.themeInfo(themeId).name
            draftDark = Backends.settings.themeInfo(themeId).dark
        } else {
            // Start from the currently active theme as a sensible default.
            draftColors = Backends.settings.themeColors(Backends.settings.currentTheme)
            draftName = qsTr("My theme")
            draftDark = ThemeController.isDark
        }
    }

    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: view.isEditing ? qsTr("Edit theme") : qsTr("New theme")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    // Live preview strip.
    Rectangle {
        id: preview
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 72
        color: view.draftColors.background !== undefined ? view.draftColors.background : Theme.background
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10
            Repeater {
                model: ["primary", "secondary", "tertiary", "surface", "userBubble", "assistantBubble"]
                Rectangle {
                    Layout.preferredWidth: 40; Layout.preferredHeight: 40; radius: 20
                    color: view.draftColors[modelData] !== undefined ? view.draftColors[modelData] : "transparent"
                    border.width: 1
                    border.color: Theme.outline
                }
            }
            Label {
                Layout.fillWidth: true
                text: view.draftName
                color: view.draftColors.onSurface !== undefined ? view.draftColors.onSurface : Theme.onSurface
                font.pixelSize: Theme.fontSizeM + 1
                elide: Text.ElideRight
            }
        }
    }

    ScrollView {
        anchors.top: preview.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: bottomBar.top
        clip: true

        ColumnLayout {
            width: Math.min(view.width - 32, 640)
            x: (view.width - width) / 2
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    placeholderText: qsTr("Theme name")
                    text: view.draftName
                    color: Theme.onSurface
                    onTextEdited: view.draftName = text
                }
                Switch {
                    text: qsTr("Dark")
                    checked: view.draftDark
                    // Relying on the Material default left this text black in
                    // the dark theme; bind it to the role explicitly.
                    contentItem: Text {
                        text: parent.text
                        color: Theme.onSurface
                        font: parent.font
                        verticalAlignment: Text.AlignVCenter
                        opacity: parent.enabled ? 1.0 : 0.5
                    }
                    onToggled: view.draftDark = checked
                }
            }

            Repeater {
                model: Backends.settings.colorTokens
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Label {
                        Layout.fillWidth: true
                        text: modelData
                        color: Theme.onSurfaceVariant
                        font.pixelSize: Theme.fontSizeS + 1
                    }
                    // Swatch button: opens the color picker.
                    Rectangle {
                        id: swatch
                        Layout.preferredWidth: 40; Layout.preferredHeight: 32
                        radius: 8
                        color: view.draftColors[modelData] !== undefined ? view.draftColors[modelData] : "transparent"
                        border.width: 1
                        border.color: Theme.outline
                        Accessible.role: Accessible.Button
                        Accessible.name: qsTr("Pick color for %1").arg(modelData)
                        MouseArea {
                            anchors.fill: parent
                            onClicked: colorPicker.pick(modelData, swatch.color)
                        }
                    }
                    TextField {
                        Layout.preferredWidth: 140
                        text: view.draftColors[modelData] !== undefined ? view.draftColors[modelData] : ""
                        color: Theme.onSurface
                        font.family: "monospace"
                        onTextEdited: {
                            var c = Object.assign({}, view.draftColors)
                            c[modelData] = text
                            view.draftColors = c
                        }
                    }
                    Connections {
                        // When the picker confirms a color, write it into the draft.
                        target: colorPicker
                        enabled: colorPicker.currentToken === modelData
                        function onColorPicked(hex) {
                            var c = Object.assign({}, view.draftColors)
                            c[modelData] = hex
                            view.draftColors = c
                        }
                    }
                }
            }
        }
    }

    // Color picker popup, reused for every token swatch.
    ColorPicker {
        id: colorPicker
        property string currentToken: ""
        anchors.centerIn: parent
        function pick(token, color) {
            currentToken = token
            value = color
            _loadFromColor(color)
            open()
        }
    }

    // Bottom action bar: save + delete (edit mode only).
    Rectangle {
        id: bottomBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 72
        color: Theme.surface

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Button {
                visible: view.isEditing
                text: qsTr("Delete")
                // Explicit text color: the Material default rendered black in
                // the dark theme because it isn't bound to our Theme tokens.
                contentItem: Text {
                    text: parent.text
                    color: Theme.onSurface
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    opacity: parent.enabled ? 1.0 : 0.5
                }
                onClicked: {
                    if (Backends.settings.deleteTheme(view.themeId)) {
                        view.StackView.view.pop()
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Save")
                highlighted: true
                contentItem: Text {
                    text: parent.text
                    color: Theme.onPrimary
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    opacity: parent.enabled ? 1.0 : 0.5
                }
                onClicked: {
                    var id = view.themeId.length > 0
                             ? view.themeId
                             : view.draftName.trim().toLowerCase().replace(/\s+/g, "-")
                    var saved = Backends.settings.saveTheme(id, view.draftName,
                                                            view.draftDark, view.draftColors)
                    if (saved.length > 0) {
                        view.StackView.view.pop()
                    } else {
                        // Reuse the global snackbar via the error signal.
                        Backends.chat.errorRaised(qsTr("Invalid theme: check the colors and the name."))
                    }
                }
            }
        }
    }
}
