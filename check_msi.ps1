$msi = 'C:\Users\86138\AppData\Local\Temp\wsl.msi'
if (Test-Path $msi) {
    $shell = New-Object -ComObject WindowsInstaller.Installer
    $db = $shell.OpenDatabase($msi, 0)
    $view = $db.OpenView("SELECT Value FROM Property WHERE Property = 'ProductName'")
    $view.Execute()
    $record = $view.Fetch()
    Write-Host "ProductName: $($record.StringData(1))"
    $view.Close()

    $view = $db.OpenView("SELECT * FROM Directory")
    $view.Execute()
    $record = $view.Fetch()
    while ($record -ne $null) {
        $dir = $record.StringData(1)
        Write-Host "Dir: $dir = $($record.StringData(2))"
        $record = $view.Fetch()
    }
    $view.Close()

    $view = $db.OpenView("SELECT * FROM Component")
    $view.Execute()
    $record = $view.Fetch()
    while ($record -ne $null) {
        Write-Host "Component: $($record.StringData(1)) = $($record.StringData(2))"
        $record = $view.Fetch()
    }
    $view.Close()
    $db.Commit()
}
