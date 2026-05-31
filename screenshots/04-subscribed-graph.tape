Output screenshots/04-subscribed-graph.gif
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

Down
Enter
Sleep 2s
Down
Down
Down
Down
Sleep 300ms
Enter
Sleep 2s
Down
Sleep 1s

# Subscribe and immediately graph
Type "s"
Sleep 1s
Type "g"
Sleep 15s
Screenshot screenshots/04-subscribed-graph.png

Type "q"
Sleep 500ms

Hide
Type "kill %1"
Enter
Sleep 300ms
