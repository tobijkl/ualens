Output screenshots/debug-nav.gif
Set Width 1600
Set Height 900
Set FontSize 14
Set Shell "zsh"
Set Padding 0

Hide
Type "cd /Users/tobias/Projects/ualens"
Enter
Sleep 300ms
Type "uv run ualens-mock-server > /dev/null 2>&1 &"
Enter
Sleep 2s
Show

Type "uv run ualens --url opc.tcp://127.0.0.1:4840/freeopcua/server/"
Enter
Sleep 8s

# Navigate to Objects, expand
Down
Enter
Sleep 2s
Screenshot screenshots/debug-1-objects-expanded.png

# 4 x Down -> SimulationDevice
Down
Screenshot screenshots/debug-2-down1.png
Down
Screenshot screenshots/debug-3-down2.png
Down
Screenshot screenshots/debug-4-down3.png
Down
Screenshot screenshots/debug-5-down4.png

# Expand SimulationDevice
Enter
Sleep 3s
Screenshot screenshots/debug-6-simdev-expanded.png

# Navigate into children
Down
Sleep 1s
Screenshot screenshots/debug-7-after-down.png

Type "q"
Sleep 500ms

Hide
Type "kill %1"
Enter
Sleep 300ms
