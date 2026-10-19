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
        title: Backends.chat.characterName.length ? Backends.chat.characterName : qsTr("Your companion")
        subtitle: Backends.chat.busy ? qsTr("Writing a message…") : qsTr("Here with you")
        IconButton { glyph: "＋"; accessibleName: qsTr("New conversation"); enabled: !Backends.chat.busy; onClicked: { messages.clear(); Backends.chat.resetChat() } }
        IconButton { glyph: "◷"; accessibleName: qsTr("Chat history"); enabled: !Backends.chat.busy; onClicked: view.StackView.view.push(Qt.resolvedUrl("ChatHistoryView.qml")) }
        IconButton { glyph: "⚙"; accessibleName: qsTr("Settings"); onClicked: view.openSettings() }
    }

    ListModel { id: messages }
    function adoptTranscript(transcript) {
        messages.clear()
        for (var i = 0; i < transcript.length; ++i) messages.append({ "role": transcript[i].role, "text": transcript[i].text })
        Qt.callLater(list.scrollToEnd)
    }
    function send() {
        var t = field.text.trim()
        if (t.length === 0 || Backends.chat.busy) return
        Backends.chat.sendMessage(t)
        field.clear()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true; Layout.fillHeight: true
            Rectangle {
                anchors.fill: parent
                anchors.margins: 10
                radius: 20
                color: Qt.alpha(Theme.surface, 0.56)
                border.width: 1
                border.color: Qt.alpha(Theme.outline, 0.18)
            }
            ListView {
                id: list
                anchors.fill: parent; anchors.margins: 12
                clip: true; model: messages; spacing: 8
                topMargin: 8; bottomMargin: 12
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                delegate: MessageBubble { role: model.role; text: model.text }
                footer: Item {
                    width: list.width; height: Backends.chat.busy ? 48 : 0; clip: true
                    Behavior on height { NumberAnimation { duration: Theme.durationShort } }
                    TypingIndicator { x: 8; y: 5; visible: Backends.chat.busy }
                }
                NumberAnimation { id: scrollAnim; target: list; property: "contentY"; duration: 240; easing.type: Easing.OutCubic }
                function scrollToEnd() {
                    if (contentHeight + topMargin + bottomMargin <= height) return
                    scrollAnim.stop(); scrollAnim.to = originY + contentHeight - height + bottomMargin; scrollAnim.start()
                }
            }
            EmptyState {
                anchors.fill: parent
                visible: messages.count === 0
                greeting: Backends.chat.greeting
                expression: view.currentExpression
                source: Backends.chat.expressionUrl(view.currentExpression)
                emoji: Backends.chat.portraitEmoji
                showPortrait: true
            }
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 92
            color: Theme.background
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14; anchors.topMargin: 12; anchors.bottomMargin: 14; spacing: 10
                TextField {
                    id: field
                    Layout.fillWidth: true; Layout.fillHeight: true
                    enabled: !Backends.chat.busy
                    placeholderText: qsTr("Write something sweet…")
                    placeholderTextColor: Theme.onSurfaceVariant
                    color: Theme.onSurface; font.pixelSize: Theme.fontSizeM
                    leftPadding: 18; rightPadding: 18
                    verticalAlignment: TextInput.AlignVCenter; selectByMouse: true
                    Accessible.name: qsTr("Message")
                    Accessible.description: qsTr("Type a message and press Enter to send")
                    onAccepted: view.send()
                    background: Rectangle {
                        radius: 22; color: Theme.surface
                        border.width: field.activeFocus ? 1.5 : 1
                        border.color: field.activeFocus ? Theme.primary : Qt.alpha(Theme.outline, 0.28)
                        Behavior on border.color { ColorAnimation { duration: 120 } }
                    }
                }
                IconButton {
                    id: sendBtn; filled: true; glyph: "↑"; accessibleName: qsTr("Send")
                    enabled: !Backends.chat.busy && field.text.trim().length > 0
                    Layout.preferredWidth: 48; Layout.preferredHeight: 48
                    onClicked: view.send()
                }
            }
        }
    }
    Connections {
        target: Backends.chat
        function onMessageAppended(role, text) { messages.append({ "role": role, "text": text }); Qt.callLater(list.scrollToEnd) }
        function onExpressionChanged(id) { view.currentExpression = id }
        function onBusyChanged(value) { if (!value) field.forceActiveFocus(); Qt.callLater(list.scrollToEnd) }
        function onChatLoaded(id, transcript) { view.adoptTranscript(transcript); var stack = view.StackView.view; if (stack && stack.depth > 1) stack.pop(null) }
    }
    Connections { target: Backends.settings; function onCharacterChanged(id) { messages.clear(); view.currentExpression = Backends.chat.initialExpression } }
    Component.onCompleted: field.forceActiveFocus()
}
