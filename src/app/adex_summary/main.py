from ui import MainWindow

class Main:
    def __init__(self):
        # init config
        self.mWindow = MainWindow()
    def run(self):
        self.mWindow.show()

if __name__ == '__main__':
    mMain = Main()
    mMain.run()
