import wx

from windows import MainWindow
from multiprocess import Management
from controller import ExperimentController as Ctrl
import asyncio

from events import EVT_CLS

from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from concurrent.futures import ThreadPoolExecutor






async def main(loop):
    test = True

    management = Management()

    gui_q = Management.Queue()
    gui_q.put(True)
    force_q, pos_q, exp_controller_q, plot_ctrl_q = management.Queue(),management.Queue(),management.Queue(),management.Queue()
    exp_info_q = management.Queue()
    controller = Ctrl(exp_controller_q,plot_ctrl_q,pos_q,force_q,gui_q,exp_info_q,test=test)

    app = WxAsyncApp()

    frame = MainWindow(None,controller,management)
    frame.Show()
    await app.MainLoop()







if __name__=='__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
