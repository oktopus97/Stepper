from wx import App
from windows import MainWindow
from multiprocess import Management
from controller import ExperimentController as Ctrl



def main():


    management = Management()
    force_q, pos_q, controller_q = management.Queue(),management.Queue(),management.Queue()
    controller = Ctrl(controller_q,pos_q,force_q,test=True)

    app = App()
    frame = MainWindow(None,controller,management)
    frame.Show()

    app.MainLoop()


if __name__=='__main__':

    main()
