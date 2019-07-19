import wx

def cao(parent):
    sizer = wx.BoxSizer(wx.HORIZONTAL)

    close = wx.Button(parent, label='Close')
    apply = wx.Button(parent, label='Apply')
    ok = wx.Button(parent, label='OK')

    parent.Bind(wx.EVT_BUTTON, parent.OnClose,close)
    parent.Bind(wx.EVT_BUTTON, parent.OnApply,apply)
    parent.Bind(wx.EVT_BUTTON, parent.OnOK,ok)

    for button in close, apply, ok:
        sizer.Add(button,0,wx.EXPAND,0)
    return sizer, close, apply, ok

def inputsizer(spec_tuple):
    title, default, panel = spec_tuple
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    if type(default) is tuple:
        input  = wx.RadioBox(panel,label=title,choices=default)
    else:
        label = wx.StaticText(panel,label=title)
        input = wx.TextCtrl(panel,-1)
        if default is not None:
            input.SetValue(default)
        sizer.Add(label, 0, wx.LEFT,0)

    sizer.Add(input, 0, wx.RIGHT,0)
    return sizer, input
