Output test/m0.gif

Set Shell "zsh"
Set FontSize 16
Set FontFamily "JetBrains Mono"
Set Width 960
Set Height 500
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Margin 0
Set BorderRadius 8
Set TypingSpeed 100ms
Set WindowBar Colorful

Enter
Type 'echo "Getting your IP address"'
Sleep 1500ms
Enter
Ctrl+Y
Enter
Type 'export MY_IP=$(curl ifconfig.me)'
Sleep 3500ms
Enter 2
Type 'echo "your IP address is: $MY_IP"'
Sleep 1500ms
Enter
Sleep 5s