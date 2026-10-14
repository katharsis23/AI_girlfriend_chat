import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: view
    signal openSettings()

    property string currentExpression: Backends.chat.initialExpression
    readonly property bool wide: width >= 760

    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: Backends.chat.characterName
        subtitle: Backends.chat.busy ? qsTr("typing…") : ""
        IconButton {
            glyph: "✚"
            accessibleName: qsTr("New conversation")
            enabled: !Backends.chat.busy
            onClicked: { messages.clear(); Backends.chat.resetChat() }
        }
        IconButton {
            glyph: "🗎"
            accessibleName: qsTr("Chat history")
            enabled: !Backends.chat.busy
            onClicked: view.StackView.view.push(Qt.resolvedUrl("ChatHistoryView.qml"))
        }
        IconButton {
            glyph: "⚙"
            accessibleName: qsTr("Settings")
            onClicked: view.openSettings()
        }
    }

    ListModel { id: messages }

    // Replace the transcript with a previously stored conversation and continue
    // it (the ChatBackend already retargeted its active chat id).
    function adoptTranscript(transcript) {
        messages.clear()
        for (var i = 0; i < transcript.length; ++i) {
            messages.append({ "role": transcript[i].role, "text": transcript[i].text })
        }
        Qt.callLater(list.scrollToEnd)
    }

    function send() {
        var t = field.text.trim()
        if (t.length === 0 || Backends.chat.busy) return
        Backends.chat.sendMessage(t)
        field.clear()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // portrait panel (wide layouts)
        Rectangle {
            visible: view.wide
            Layout.fillHeight: true
            Layout.preferredWidth: Math.min(view.width * 0.34, 360)
            color: Theme.surface
            Behavior on color { ColorAnimation { duration: Theme.durationMedium } }

            ColumnLayout {
                anchors.centerIn: parent
                width: parent.width - 48
                spacing: 20
                Portrait {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: Math.min(parent.width, 260)
                    Layout.preferredHeight: Math.min(parent.width, 260)
                    expression: view.currentExpression
                    source: Backends.chat.expressionUrl(view.currentExpression)
                    emoji: Backends.chat.portraitEmoji
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: Backends.chat.characterName
                    color: Theme.text
                    font.pixelSize: Theme.fontSizeXL
                    font.weight: Font.Medium
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ListView {
                    id: list
                    anchors.fill: parent
                    clip: true
                    model: messages
                    topMargin: 16
                    bottomMargin: 8
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}

                    delegate: MessageBubble {
                        role: model.role
                        text: model.text
                    }

                    footer: Item {
                        width: list.width
                        height: Backends.chat.busy ? 52 : 0
                        clip: true
                        Behavior on height { NumberAnimation { duration: Theme.durationShort } }
                        TypingIndicator {
                            x: 16
                            y: 6
                            visible: Backends.chat.busy
                        }
                    }

                    NumberAnimation {
                        id: scrollAnim
                        target: list
                        property: "contentY"
                        duration: 250
                        easing.type: Easing.OutCubic
                    }
                    function scrollToEnd() {
                        if (contentHeight + topMargin + bottomMargin <= height) return
                        scrollAnim.stop()
                        scrollAnim.to = originY + contentHeight - height + bottomMargin
                        scrollAnim.start()
                    }
                }

                EmptyState {
                    anchors.fill: parent
                    visible: messages.count === 0
                    greeting: Backends.chat.greeting
                    expression: view.currentExpression
                    source: Backends.chat.expressionUrl(view.currentExpression)
                    emoji: Backends.chat.portraitEmoji
                    showPortrait: !view.wide
                }
            }

            // input bar (spec §7.2)
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 76
                color: Theme.background

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 12
                    anchors.bottomMargin: 12
                    spacing: 12

                    TextField {
                        id: field
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        enabled: !Backends.chat.busy
                        placeholderText: qsTr("Write a message…")
                        placeholderTextColor: Theme.onSurfaceVariant
                        color: Theme.onSurface
                        font.pixelSize: Theme.fontSizeM
                        leftPadding: 20
                        rightPadding: 20
                        verticalAlignment: TextInput.AlignVCenter
                        selectByMouse: true
                        Accessible.name: qsTr("Message")
                        Accessible.description: qsTr("Type a message and press Enter to send")
                        onAccepted: view.send()
                        background: Rectangle {
                            radius: height / 2
                            color: Theme.surfaceVariant
                            border.width: field.activeFocus ? 2 : 0
                            border.color: Theme.primary
                            opacity: field.enabled ? 1.0 : 0.6
                        }
                    }
                    IconButton {
                        id: sendBtn
                        filled: true
                        glyph: "↑"
                        accessibleName: qsTr("Send")
                        enabled: !Backends.chat.busy && field.text.trim().length > 0
                        Layout.preferredWidth: 52
                        Layout.preferredHeight: 52
                        onClicked: view.send()
                    }
                }
            }
        }
    }

    Connections {
        target: Backends.chat
        function onMessageAppended(role, text) {
            messages.append({ "role": role, "text": text })
            Qt.callLater(list.scrollToEnd)
        }
        function onExpressionChanged(id) { view.currentExpression = id }
        function onBusyChanged(value) {
            if (!value) field.forceActiveFocus()
            Qt.callLater(list.scrollToEnd)
        }
        function onChatLoaded(id, transcript) {
            view.adoptTranscript(transcript)
            // If we're on the history page, pop back to the chat.
            var stack = view.StackView.view
            if (stack && stack.depth > 1) stack.pop(null)
        }
    }
    Connections {
        target: Backends.settings
        function onCharacterChanged(id) {      // new character => fresh transcript (spec §6.2)
            messages.clear()
            view.currentExpression = Backends.chat.initialExpression
        }
    }
    Component.onCompleted: field.forceActiveFocus()
}
