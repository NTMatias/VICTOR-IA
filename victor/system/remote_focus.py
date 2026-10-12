"""Sonda de foco aislada en subproceso: nunca lee texto ni valores de campos.

UI Automation identifica Edit (incluidos navegadores compatibles). Win32 sirve
de respaldo. El servidor termina la sonda si UIA se bloquea en una aplicación.
"""
import ctypes
import json
import time
from ctypes import wintypes as w
from victor.system.remote_input import foreground_title


def native_editable():
    class INFO(ctypes.Structure):
        _fields_=[('cbSize',w.DWORD),('flags',w.DWORD),('active',w.HWND),('focus',w.HWND),
                  ('capture',w.HWND),('menu',w.HWND),('move',w.HWND),('caret',w.HWND),('rect',w.RECT)]
    user=ctypes.WinDLL('user32',use_last_error=True)
    info=INFO();info.cbSize=ctypes.sizeof(info)
    user.GetGUIThreadInfo.argtypes=[w.DWORD,ctypes.POINTER(INFO)]
    if not user.GetGUIThreadInfo(0,ctypes.byref(info)) or not info.focus:return False,''
    name=ctypes.create_unicode_buffer(256)
    user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    user.GetClassNameW(info.focus,name,len(name))
    user.GetWindowLongW.argtypes=[w.HWND,ctypes.c_int];user.GetWindowLongW.restype=w.LONG
    style=user.GetWindowLongW(info.focus,-16)
    return 'edit' in name.value.lower() and not style & (0x800|0x20),str(info.focus)  # readonly/password


def main():
    automation=None;com=None
    try:
        import comtypes as com
        from comtypes.client import GetModule, CreateObject
        com.CoInitialize()
        client=GetModule('UIAutomationCore.dll')
        automation=CreateObject(client.CUIAutomation,interface=client.IUIAutomation)
    except Exception:automation=None
    try:
        while True:
            try:
                owner,title=foreground_title()
                editable,field=native_editable()
                if automation is not None:
                    try:
                        element=automation.GetFocusedElement()
                        if element:
                            field=str(tuple(element.GetRuntimeId()))[:150]
                            editable=bool(element.CurrentControlType==50004 and element.CurrentIsEnabled and not element.CurrentIsPassword)
                            if editable:
                                try:
                                    value=element.GetCurrentPattern(10002).QueryInterface(client.IUIAutomationValuePattern)
                                    editable=not value.CurrentIsReadOnly
                                except Exception:pass
                    except Exception:pass
                if foreground_title()[1]!=title:editable=False
                print(json.dumps({'type':'focus','window':title[:300],'editable':editable,'field':field,'owner':str(owner)}),flush=True)
            except Exception:
                print(json.dumps({'type':'focus','window':'','editable':False}),flush=True)
            time.sleep(.3)
    finally:
        if com:com.CoUninitialize()


if __name__=='__main__':main()
