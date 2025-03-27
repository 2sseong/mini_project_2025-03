import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets, QtGui
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt




class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('mainpage.ui',self)
        print(widget.currentIndex())

        self.btn_search.clicked.connect(self.gotoSearch)
        self.btn_book.clicked.connect(self.gotoBookPage)
        # self.btn_book.setEnabled(False)
        self.adminButton = self.findChild(QPushButton, "loginButton")
        self.adminButton.clicked.connect(self.show_admin_login)

    def show_admin_login(self):
        dlg = LoginDialog()
        if dlg.exec_() == QDialog.Accepted:

            # 로그인 성공
            print("관리자 로그인 성공! 관리자 페이지로 이동 가능.")
            # 관리자 페이지 1번, 함수 만들어 안쓰고 바로 호출함
            widget.setCurrentIndex(widget.currentIndex()+1) 
            print(widget.currentIndex())
            
        else:
            print("관리자 로그인 취소됨")
    
    def gotoSearch(self):
        #예매조회 페이지 2번
        widget.setCurrentIndex(widget.currentIndex()+2)
        print(widget.currentIndex())


    def gotoBookPage(self):
        #예매 페이지 3번
        widget.setCurrentIndex(widget.currentIndex()+3)
        print(widget.currentIndex())

    def loginFunction(self):
        user_id = self.user_id.text()
        user_pw = self.user_pw.text()
        print("성공적으로 로그인되었습니다."), user_id, user_pw

#로그인 입력창
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("admin_login.ui", self)

        self.btn_ok.clicked.connect(self.check_login)
        #self.btnCancel.clicked.connect(self.reject)

    def check_login(self):
        user_id = self.user_id.text()
        user_pw = self.user_pw.text()

        #관리자 계정 로그인
        if user_id == "admin" and user_pw == "1234":
            QMessageBox.information(self, "로그인 성공", "로그인에 성공했습니다!")
            self.accept()
        else:
            QMessageBox.warning(self, "로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")


class AdminPage(QDialog):
    def __init__(self):
        super(AdminPage,self).__init__()
        loadUi('adminpage.ui', self)    

        self.btn_go_to_main.clicked.connect(self.gotomain)
    
    
    def gotomain(self):
        # 관리자 페이지 1번이므로,  홈으로 돌아오게 하려면 -1
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())



class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gotohome)

    def gotohome(self):
        # 예매조회 페이지 2번이므로,  홈으로 돌아오게 하려면 -2
        widget.setCurrentIndex(widget.currentIndex()-2)
        print(widget.currentIndex())


class BookPage1(QDialog):
    def __init__(self):
        super(BookPage1,self).__init__()
        loadUi('bookpage1.ui',self)
        self.btn_gohome.clicked.connect(self.goHome)
        self.btn_next.clicked.connect(self.goNext)

        self.btn_movie1.setIcon(QIcon('eximg.jpg'))
        self.btn_movie1.setIconSize(self.btn_movie1.size())

    def goHome(self):
        widget.setCurrentIndex(widget.currentIndex()-3)
        
    def goNext(self):
        widget.setCurrentIndex(widget.currentIndex()+1)

class BookPage2(QDialog):
    def __init__(self):
        super(BookPage2,self).__init__()
        loadUi('bookpage2.ui',self)
        self.btn_goback.clicked.connect(self.goBack)
        self.btn_next.clicked.connect(self.goNext)

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())

    def goNext(self):
        widget.setCurrentIndex(widget.currentIndex()+1)

class BookPage3(QDialog):
    def __init__(self):
        super(BookPage3,self).__init__()
        loadUi('bookpage3.ui',self)
        self.btn_goback.clicked.connect(self.goBack)

        for i in range(1,9):
            btn_adt = getattr(self, f"btn_adt{i}")
            btn_teen = getattr(self, f"btn_teen{i}")
            btn_adt.clicked.connect(self.getAdultNumber)
            btn_teen.clicked.connect(self.getTeenNumber)

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())

    def getAdultNumber(self):
        num_adt = 0
        btn = self.sender()
        if btn:
            num_adt = btn.text()
        self.input_adt.setText(num_adt)

    def getTeenNumber(self):
        num_teen = 0
        btn = self.sender()
        if btn:
            num_teen = btn.text()
        self.input_teen.setText(num_teen)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    mainwindow = MainWindow()
    adminPage = AdminPage()
    searchpage = SearchPage()
    bookpage1 = BookPage1()
    bookpage2 = BookPage2()
    bookpage3 = BookPage3()
    widget.addWidget(mainwindow)
    widget.addWidget(adminPage)
    widget.addWidget(searchpage)
    widget.addWidget(bookpage1)
    widget.addWidget(bookpage2)
    widget.addWidget(bookpage3)
   
    widget.show()
    app.exec_()

    # 결제창에서 회원유무
    # 해당창에서 선택되지 않으면 다음페이지 못넘어가게 하기!!!!!!!!!!!!