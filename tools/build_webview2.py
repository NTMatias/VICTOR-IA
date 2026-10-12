"""Build Windows hosts from sources and a pinned, verified official WebView2 SDK."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

VERSION = '1.0.4258.31'
SHA256 = '56f7f4b8bf9aee4b8efefbbdd4f67d5f74ebd1b100ed0806da71bf76af481aa9'
URL = f'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/{VERSION}/microsoft.web.webview2.{VERSION}.nupkg'

def build():
    if os.name != 'nt':
        raise RuntimeError('Los hosts WebView2 requieren Windows x64.')
    target = Path(__file__).resolve().parents[1] / 'victor/gui/webview2'
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file():
        raise RuntimeError('Falta el compilador de .NET Framework 4.x de Windows.')
    print(f'Descargando SDK WebView2 {VERSION} desde NuGet oficial...', flush=True)
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError('La descarga no coincide con el SHA256 fijado; no se compilará.')
    with zipfile.ZipFile(io.BytesIO(data)) as sdk:
        for name, member in {
            'Microsoft.Web.WebView2.Core.dll': 'lib/net462/Microsoft.Web.WebView2.Core.dll',
            'Microsoft.Web.WebView2.WinForms.dll': 'lib/net462/Microsoft.Web.WebView2.WinForms.dll',
            'WebView2Loader.dll': 'runtimes/win-x64/native/WebView2Loader.dll',
        }.items():
            (target / name).write_bytes(sdk.read(member))
    for source, binary in [('SpotifyHost.cs', 'SpotifyHost.exe'), ('WhatsAppHost.cs', 'WhatsAppWebHost.exe')]:
        args = [str(compiler), '/nologo', '/target:winexe', '/platform:x64', '/out:' + str(target / binary),
                '/r:System.Windows.Forms.dll', '/r:System.Drawing.dll', '/r:System.Web.Extensions.dll',
                '/r:' + str(target / 'Microsoft.Web.WebView2.Core.dll'),
                '/r:' + str(target / 'Microsoft.Web.WebView2.WinForms.dll'), str(target / source)]
        subprocess.run(args, check=True, timeout=60, shell=False)
        print('Compilado ' + binary, flush=True)

if __name__ == '__main__':
    build()
