// Visible official WhatsApp Web with the VICTOR palette and recent previews.
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

sealed class WhatsAppHost : Form {
    readonly IntPtr parent;
    readonly string profile, pipeName;
    readonly WebView2 view = new WebView2();
    readonly System.Windows.Forms.Timer lifetime = new System.Windows.Forms.Timer();
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    NamedPipeServerStream pipe;
    bool closing;
    readonly HashSet<string> recentRequests=new HashSet<string>();
    [StructLayout(LayoutKind.Sequential)] struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] static extern bool IsWindow(IntPtr handle);
    [DllImport("user32.dll")] static extern IntPtr GetParent(IntPtr handle);
    [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr context);
    static bool Official(string value) {
        Uri uri;
        return Uri.TryCreate(value,UriKind.Absolute,out uri) && uri.Scheme=="https" &&
               uri.Host=="web.whatsapp.com" && uri.IsDefaultPort && String.IsNullOrEmpty(uri.UserInfo);
    }
    protected override CreateParams CreateParams {
        get { var cp=base.CreateParams;cp.Parent=parent;cp.Style=unchecked((int)0x56000000);cp.ExStyle=0;cp.X=cp.Y=0;return cp; }
    }
    readonly object outputLock = new object();
    void Publish(object data) { lock(outputLock) { Console.WriteLine(json.Serialize(data));Console.Out.Flush(); } }
    WhatsAppHost(IntPtr owner,string storage,string channel) {
        parent=owner;profile=storage;pipeName=channel;
        json.MaxJsonLength=4*1024*1024;
        FormBorderStyle=FormBorderStyle.None;ShowInTaskbar=false;TopLevel=false;
        AutoScaleMode=AutoScaleMode.None;BackColor=Color.FromArgb(21,23,28);
        view.Dock=DockStyle.Fill;Controls.Add(view);
        lifetime.Interval=100;lifetime.Tick += delegate {
            if (!IsWindow(parent)) { Close();return; }
            Rect rect;if(GetClientRect(parent,out rect)) {
                var size=new Size(Math.Max(1,rect.Right),Math.Max(1,rect.Bottom));if(Size!=size)Size=size;
            }
        };
        Load+=Initialize;
        FormClosed+=delegate { closing=true;lifetime.Stop();if(pipe!=null)pipe.Dispose();view.Dispose(); };
    }
    void Input() {
        try {
            var security=new PipeSecurity();security.SetAccessRuleProtection(true,false);
            security.AddAccessRule(new PipeAccessRule(WindowsIdentity.GetCurrent().User,PipeAccessRights.ReadWrite,AccessControlType.Allow));
            pipe=new NamedPipeServerStream(pipeName,PipeDirection.In,1,PipeTransmissionMode.Byte,PipeOptions.Asynchronous,4096,4096,security);
            Publish(new {kind="pipe_ready"});pipe.WaitForConnection();
            using(var reader=new StreamReader(pipe,System.Text.Encoding.UTF8)) {
                string line;
                while((line=reader.ReadLine())!=null && !closing) {
                    var command=json.Deserialize<Dictionary<string,object>>(line);
                    BeginInvoke(new Action(async delegate {
                        try {
                            string action=(string)command["command"];
                            if(action=="close")Close();
                            else if(view.CoreWebView2!=null && action=="reload")view.Reload();
                            else if(view.CoreWebView2!=null && action=="theme") {
                                view.CoreWebView2.Profile.PreferredColorScheme=(string)command["theme"]=="light" ?
                                    CoreWebView2PreferredColorScheme.Light : CoreWebView2PreferredColorScheme.Dark;
                                await view.ExecuteScriptAsync("window.__victorWhatsAppTheme && window.__victorWhatsAppTheme("+json.Serialize(command["theme"])+")");
                            }
                            else if(view.CoreWebView2!=null && action=="whatsapp") {
                                var request=command["payload"] as Dictionary<string,object>;
                                if(request!=null && request.ContainsKey("request") && request.ContainsKey("action") && (string)request["action"]=="open")recentRequests.Add((string)request["request"]);
                                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(command["payload"]));
                            }
#if WHATSAPP_TEST
                            else if(view.CoreWebView2!=null && action=="test_palette") {
                                var result=await view.ExecuteScriptAsync("JSON.stringify({vars:Array.from(getComputedStyle(document.body)).filter(k=>k.startsWith('--')&&(/WDS-(background|content|border|systems|persistent)|navbar/.test(k)||/#fcf5eb/i.test(getComputedStyle(document.body).getPropertyValue(k)))).slice(0,160).map(k=>[k,getComputedStyle(document.body).getPropertyValue(k)])})");
                                Publish(new {kind="test_palette",result=result});
                            }
                            else if(view.CoreWebView2!=null && action=="test_inspect") {
                                var result=await view.ExecuteScriptAsync("JSON.stringify({main:document.querySelector('#main header')?.innerText,messages:Array.from(document.querySelectorAll('#messages .selectable-text')).map(e=>e.innerText),trusted:window.victorFixture?.lastClickTrusted})");
                                Publish(new {kind="test_inspected",result=result});
                            }
                            else if(view.CoreWebView2!=null && action=="test_event") {
                                await view.ExecuteScriptAsync("window.victorFixture.receive("+json.Serialize(command["text"])+")");
                                Publish(new {kind="test_done"});
                            }
#endif
                            // Read-only diagnostics never include chat text.
                            else if(view.CoreWebView2!=null && action=="diagnostic") {
                                var result=await view.ExecuteScriptAsync("JSON.stringify({url:location.origin,title:document.title,ready:document.readyState,qr:!!document.querySelector('canvas'),theme:document.documentElement.dataset.victorTheme,side:document.querySelector('#side')?getComputedStyle(document.querySelector('#side')).backgroundColor:null,body:getComputedStyle(document.body).backgroundColor})");
                                Publish(new {kind="diagnostic",result=result});
                            }
                            else if(view.CoreWebView2!=null && action=="capture") {
                                using(var image=new FileStream((string)command["path"],FileMode.Create))
                                    await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png,image);
                                Publish(new {kind="captured"});
                            }
                        } catch { Publish(new {kind="error",message="No se pudo actualizar WhatsApp. Pulsa Reconectar."}); }
                    }));
                }
            }
            if(!closing && !IsDisposed)BeginInvoke(new Action(Close));
        } catch { if(!closing && !IsDisposed && IsHandleCreated)BeginInvoke(new Action(Close)); }
    }
    async void Initialize(object sender,EventArgs e) {
        lifetime.Start();Publish(new {kind="host",hwnd=Handle.ToInt64(),parent=GetParent(Handle).ToInt64()});
        var input=new Thread(Input);input.IsBackground=true;input.Start();
        try {
            var environment=await CoreWebView2Environment.CreateAsync(null,profile);
            await view.EnsureCoreWebView2Async(environment);
            if(closing)return;
            view.CoreWebView2.Settings.AreDevToolsEnabled=false;
            view.CoreWebView2.Settings.IsStatusBarEnabled=false;
            var bridge=File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"whatsapp_recent.js"))+"\n"+File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"whatsapp_theme.js"));
            await view.CoreWebView2.AddScriptToExecuteOnDocumentCreatedAsync(bridge);
            view.CoreWebView2.WebMessageReceived+=async delegate(object _,CoreWebView2WebMessageReceivedEventArgs args) {
                if(!Official(args.Source))return;
                try {
                    var payload=json.Deserialize<Dictionary<string,object>>(args.WebMessageAsJson);
                    if(!payload.ContainsKey("kind") || (string)payload["kind"]!="whatsapp")return;
                    if(payload.ContainsKey("type") && (string)payload["type"]=="target") {
                        string request=(string)payload["request"];if(!recentRequests.Remove(request))return;
                        double x=Convert.ToDouble(payload["x"]),y=Convert.ToDouble(payload["y"]);
                        if(Double.IsNaN(x) || Double.IsNaN(y) || x<0 || y<0 || x>16384 || y>16384)return;
                        await view.CoreWebView2.CallDevToolsProtocolMethodAsync("Input.dispatchMouseEvent",json.Serialize(new {type="mousePressed",x=x,y=y,button="left",clickCount=1}));
                        await view.CoreWebView2.CallDevToolsProtocolMethodAsync("Input.dispatchMouseEvent",json.Serialize(new {type="mouseReleased",x=x,y=y,button="left",clickCount=1}));
                        Publish(new {kind="whatsapp",type="result",request=request,ok=true});
                    } else Publish(payload);
                } catch { } // Page data is not executable native code.
            };
#if WHATSAPP_TEST
            var fixture=Environment.GetEnvironmentVariable("VICTOR_WHATSAPP_FIXTURE");
            if(!String.IsNullOrEmpty(fixture)) {
                view.CoreWebView2.AddWebResourceRequestedFilter("https://web.whatsapp.com/*",CoreWebView2WebResourceContext.Document);
                view.CoreWebView2.WebResourceRequested+=delegate(object _,CoreWebView2WebResourceRequestedEventArgs args) {
                    var bytes=System.Text.Encoding.UTF8.GetBytes(File.ReadAllText(fixture));
                    args.Response=environment.CreateWebResourceResponse(new MemoryStream(bytes),200,"OK","Content-Type: text/html; charset=utf-8");
                };
            }
#endif
            view.CoreWebView2.PermissionRequested+=delegate(object _,CoreWebView2PermissionRequestedEventArgs args) {
                // WhatsApp keeps its own permission prompts for explicitly requested features.
                args.State=Official(args.Uri) && args.IsUserInitiated ? CoreWebView2PermissionState.Default : CoreWebView2PermissionState.Deny;
            };
            view.CoreWebView2.NewWindowRequested+=delegate(object _,CoreWebView2NewWindowRequestedEventArgs args) {
                args.Handled=true;if(!args.IsUserInitiated)return;
                if(Official(args.Uri))view.Source=new Uri(args.Uri);
                else { Uri uri;if(Uri.TryCreate(args.Uri,UriKind.Absolute,out uri) && (uri.Scheme=="http" || uri.Scheme=="https"))Publish(new {kind="link",url=args.Uri}); }
            };
            view.CoreWebView2.NavigationStarting+=delegate(object _,CoreWebView2NavigationStartingEventArgs args) {
                if(!Official(args.Uri)) {
                    args.Cancel=true;
                    Uri uri;if(args.IsUserInitiated && Uri.TryCreate(args.Uri,UriKind.Absolute,out uri) && (uri.Scheme=="https" || uri.Scheme=="http"))Publish(new {kind="link",url=args.Uri});
                }
            };
            view.CoreWebView2.NavigationCompleted+=delegate(object _,CoreWebView2NavigationCompletedEventArgs args) {
                Publish(new {kind=args.IsSuccess?"loaded":"error",hwnd=Handle.ToInt64(),parent=GetParent(Handle).ToInt64(),message=args.IsSuccess?"":"No se pudo cargar WhatsApp. Revisa tu conexión y pulsa Reconectar."});
            };
            view.CoreWebView2.ProcessFailed+=delegate { Publish(new {kind="error",message="WhatsApp se desconectó. Pulsa Reconectar."}); };
            view.Source=new Uri("https://web.whatsapp.com/");
        } catch(Exception error) {
            Publish(new {kind="error",message=error is WebView2RuntimeNotFoundException ? "Instala Microsoft Edge WebView2 Runtime y pulsa Reconectar." : "No se pudo iniciar WhatsApp integrado. Pulsa Reconectar."});
        }
    }
    [STAThread] static void Main(string[] args) {
        long owner;
        if(args.Length!=4 || args[1]!="https://web.whatsapp.com/" || !long.TryParse(args[0],out owner) || !IsWindow(new IntPtr(owner)))return;
        Console.SetOut(new StreamWriter(Console.OpenStandardOutput(),new System.Text.UTF8Encoding(false)) {AutoFlush=true});
        try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch(EntryPointNotFoundException) { }
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new WhatsAppHost(new IntPtr(owner),args[2],args[3]));
    }
}
