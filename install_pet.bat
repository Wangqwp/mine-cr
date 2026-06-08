@echo off
if not exist " %USERPROFILE%\.codex\pets\my-dog\ mkdir \%USERPROFILE%\.codex\pets\my-dog\
copy /Y \C:\Users\86138\Desktop\mine-cr\pet_run\spritesheet_new.webp\ \%USERPROFILE%\.codex\pets\my-dog\spritesheet.webp\
echo Done! Please restart Codex app.
pause
