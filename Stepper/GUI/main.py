import wx

from windows import MainWindow
from multiprocess import Management
from controller import ExperimentController as Ctrl

from events import EVT_CLS

from concurrent.futures import ThreadPoolExecutor





def main():
    test = False

    management = Management()
    exp_q = management.Queue()
    inf_q = management.Queue()

    controller = Ctrl(exp_q, inf_q,test=test)

    app = wx.App()

    frame = MainWindow(None,controller,management)
    frame.Show()
    app.MainLoop()


if __name__=='__main__':

    main()
