Output screenshots/03-connected.gif
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
Screenshot screenshots/03-connected.png

Type "q"
Sleep 500ms

Hide
Type "kill %1"
Enter
Sleep 300ms
