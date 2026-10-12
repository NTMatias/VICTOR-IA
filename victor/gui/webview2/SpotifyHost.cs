// Native child window: no separate browser window. Official WebView2 SDK.
using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Windows.Forms;
using System.Web.Script.Serialization;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

sealed class SpotifyHost : Form {
    readonly IntPtr parent;
    readonly string url, profile, pipeName;
    NamedPipeServerStream pipe;
    readonly WebView2 view = new WebView2();
    readonly System.Windows.Forms.Timer lifetime = new System.Windows.Forms.Timer();
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    [StructLayout(LayoutKind.Sequential)] struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] static extern bool IsWindow(IntPtr handle);
    [DllImport("user32.dll")] static extern IntPtr GetParent(IntPtr handle);
    [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr context);
    protected override CreateParams CreateParams {
        get {
            var cp = base.CreateParams;
            cp.Parent = parent;
            cp.Style = unchecked((int)0x56000000); // CHILD | VISIBLE | CLIPCHILDREN | CLIPSIBLINGS
            cp.ExStyle = 0; cp.X = cp.Y = 0;
            return cp;
        }
    }
    void Publish(object data) { Console.WriteLine(json.Serialize(data)); Console.Out.Flush(); }
    SpotifyHost(IntPtr owner, string address, string storage, string channel) {
        parent = owner; url = address; profile = storage; pipeName=channel;
        FormBorderStyle = FormBorderStyle.None; ShowInTaskbar = false;
        TopLevel=false;
        AutoScaleMode = AutoScaleMode.None; BackColor = Color.FromArgb(18,18,18);
        view.Dock = DockStyle.Fill; Controls.Add(view);
        lifetime.Interval = 100;
        lifetime.Tick += delegate {
            if (!IsWindow(parent)) { Close(); return; }
            Rect rect;
            if (GetClientRect(parent, out rect)) {
                var size = new Size(Math.Max(1, rect.Right), Math.Max(1, rect.Bottom));
                if (Size != size) Size = size;
            }
        };
        Load += Initialize;
        FormClosed += delegate { lifetime.Stop();if(pipe!=null)pipe.Dispose();view.Dispose(); };
    }
    async void Initialize(object sender, EventArgs e) {
        lifetime.Start();
        Publish(new { kind="host", hwnd=Handle.ToInt64(), parent=GetParent(Handle).ToInt64() });
        var input = new Thread(delegate() {
            try {
                var security=new PipeSecurity();security.SetAccessRuleProtection(true,false);
                security.AddAccessRule(new PipeAccessRule(WindowsIdentity.GetCurrent().User,PipeAccessRights.ReadWrite,AccessControlType.Allow));
                pipe=new NamedPipeServerStream(pipeName,PipeDirection.In,1,PipeTransmissionMode.Byte,PipeOptions.Asynchronous,4096,4096,security);
                Publish(new {kind="pipe_ready"});pipe.WaitForConnection();
                var reader=new StreamReader(pipe,System.Text.Encoding.UTF8);
                string line;
                while ((line=reader.ReadLine()) != null) {
                    var command = json.Deserialize<System.Collections.Generic.Dictionary<string,object>>(line);
                    BeginInvoke(new Action(async delegate {
                        if ((string)command["command"] == "close") Close();
                        else if ((string)command["command"] == "probe" && view.CoreWebView2 != null) {
                            string result=await view.ExecuteScriptAsync((string)command["script"]);
                            Publish(new { kind="probe", result=result });
                        } else if ((string)command["command"] == "capture" && view.CoreWebView2 != null) {
                            using(var image=new FileStream((string)command["path"],FileMode.Create))
                                await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png,image);
                            Publish(new { kind="captured" });
                        }
                    }));
                }
                if (!IsDisposed) BeginInvoke(new Action(Close));
            } catch { if (!IsDisposed && IsHandleCreated) BeginInvoke(new Action(Close)); }
        }); input.IsBackground=true;input.Start();
        try {
            var environment=await CoreWebView2Environment.CreateAsync(null, profile);
            await view.EnsureCoreWebView2Async(environment);
            view.CoreWebView2.Settings.AreDevToolsEnabled = false;
            view.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            view.CoreWebView2.Settings.IsStatusBarEnabled = false;
            view.CoreWebView2.Settings.IsZoomControlEnabled = false;
            view.CoreWebView2.PermissionRequested += delegate(object _, CoreWebView2PermissionRequestedEventArgs args) {
                args.State=args.PermissionKind.ToString()=="ProtectedMediaIdentifier" ? CoreWebView2PermissionState.Allow : CoreWebView2PermissionState.Deny;
            };
            view.CoreWebView2.NewWindowRequested += delegate(object _, CoreWebView2NewWindowRequestedEventArgs args) {
                args.Handled=true;
                if (args.IsUserInitiated && args.Uri.StartsWith("https://open.spotify.com/",StringComparison.Ordinal))
                    Publish(new {kind="link", url=args.Uri});
            };
            view.CoreWebView2.NavigationStarting += delegate(object _, CoreWebView2NavigationStartingEventArgs args) {
                if (!args.Uri.StartsWith(url,StringComparison.Ordinal)) args.Cancel=true;
            };
            view.CoreWebView2.NavigationCompleted += delegate(object _, CoreWebView2NavigationCompletedEventArgs args) {
                Publish(new {kind=args.IsSuccess?"loaded":"error", hwnd=Handle.ToInt64(), parent=GetParent(Handle).ToInt64(), message=args.IsSuccess?"": "No se pudo cargar Spotify. Pulsa Reconectar."});
            };
            view.CoreWebView2.ProcessFailed += delegate { Publish(new {kind="error", message="El reproductor se desconectó. Pulsa Reconectar."}); };
            view.Source=new Uri(url);
        } catch (Exception error) {
            Publish(new {kind="error", message=error is WebView2RuntimeNotFoundException ? "Instala Microsoft Edge WebView2 Runtime y pulsa Reconectar." : "No se pudo iniciar el reproductor integrado. Pulsa Reconectar."});
        }
    }
    [STAThread] static void Main(string[] args) {
        if (args.Length != 4) return;
        Uri address;
        if (!Uri.TryCreate(args[1],UriKind.Absolute,out address) || address.Host!="127.0.0.1" || address.Scheme!="http") return;
        Console.SetOut(new StreamWriter(Console.OpenStandardOutput()) { AutoFlush=true });
        try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch (EntryPointNotFoundException) { }
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new SpotifyHost(new IntPtr(long.Parse(args[0])),args[1],args[2],args[3]));
    }
}
