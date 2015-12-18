from ui import MainWindow
from adex_processor import ADEXProcessor

class Main:
    def __init__(self):
        # init config
        self.mWindow = MainWindow()
        self.mADEX = ADEXProcessor()
    def run(self):
        self.mWindow.show()

if __name__ == '__main__':
    mMain = Main()
    mMain.run()
