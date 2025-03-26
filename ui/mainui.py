import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets, QtGui
from PyQt5.uic import loadUi

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('mainpage.ui',self)
        print(widget.currentIndex())

        self.btn_search.clicked.connect(self.gotoSearch)
        self.btn_book.clicked.connect(self.gotoBookPage)

    def gotoSearch(self):
        widget.setCurrentIndex(widget.currentIndex()+1)
        print(widget.currentIndex())
    
    def gotoBookPage(self):
        widget.setCurrentIndex(widget.currentIndex()+2)
        print(widget.currentIndex())

    

class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gotohome)

    def gotohome(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())

class BookPage1(QDialog):
    def __init__(self):
        super(BookPage1,self).__init__()
        loadUi('bookpage1.ui',self)
        self.btn_gotohome.clicked.connect(self.gotohome)

    def gotohome(self):
        widget.setCurrentIndex(widget.currentIndex()-2)
        print(widget.currentIndex())

    def loadImg(self):
        qPixmapVar = QPixmap()
        qPixmapVar.load('eximg.jpg')
        self.moviephoto1.setPixmap(qPixmapVar)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    mainwindow = MainWindow()
    searchpage = SearchPage()
    bookpage1 = BookPage1()
    widget.addWidget(mainwindow)
    widget.addWidget(searchpage)
    widget.addWidget(bookpage1)
    widget.show()
    app.exec_()
