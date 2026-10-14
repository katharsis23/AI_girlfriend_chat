pragma Singleton
import QtQuick
import App 1.0

// M3 role tokens bound to the active theme (spec §5.3). Python owns the values.
QtObject {
    readonly property var c: ThemeController.colors

    readonly property color background: c.background
    readonly property color surface: c.surface
    readonly property color surfaceVariant: c.surfaceVariant
    readonly property color primary: c.primary
    readonly property color onPrimary: c.onPrimary
    readonly property color secondary: c.secondary
    readonly property color tertiary: c.tertiary
    readonly property color onSurface: c.onSurface
    readonly property color onSurfaceVariant: c.onSurfaceVariant
    // Never resolve to a missing key: fall back to onSurface (and finally to a
    // sensible default) so text is always readable on the active theme.
    readonly property color text: (c.text !== undefined && c.text !== "")
                                  ? c.text
                                  : ((c.onSurface !== undefined && c.onSurface !== "")
                                     ? c.onSurface : "#FFFFFF")
    readonly property color outline: c.outline
    readonly property color error: c.error
    readonly property color onError: c.onError
    readonly property color userBubble: c.userBubble
    readonly property color onUserBubble: c.onUserBubble
    readonly property color assistantBubble: c.assistantBubble
    readonly property color onAssistantBubble: c.onAssistantBubble

    // non-color tokens
    readonly property int radius: 20
    readonly property int spacingS: 8
    readonly property int spacingM: 12
    readonly property int spacingL: 16
    readonly property int fontSizeS: 12
    readonly property int fontSizeM: 15
    readonly property int fontSizeL: 20
    readonly property int fontSizeXL: 28
    readonly property int durationShort: 150
    readonly property int durationMedium: 250
}
