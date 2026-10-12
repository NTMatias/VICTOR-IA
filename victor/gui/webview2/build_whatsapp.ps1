$ErrorActionPreference = 'Stop'
$whatsappCompiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$whatsappArguments = @(
    '/nologo', '/target:winexe', '/platform:x64',
    ('/out:' + (Join-Path $PSScriptRoot 'WhatsAppWebHost.exe')),
    '/r:System.Windows.Forms.dll', '/r:System.Drawing.dll', '/r:System.Web.Extensions.dll',
    ('/r:' + (Join-Path $PSScriptRoot 'Microsoft.Web.WebView2.Core.dll')),
    ('/r:' + (Join-Path $PSScriptRoot 'Microsoft.Web.WebView2.WinForms.dll')),
    (Join-Path $PSScriptRoot 'WhatsAppHost.cs')
)
& $whatsappCompiler @whatsappArguments
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar WhatsAppHost.' }
