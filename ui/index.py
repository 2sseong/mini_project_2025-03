import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, pyqtSignal
import urllib.request
from urllib.parse import urlparse, parse_qs, unquote
from PyQt5.QtCore import Qt, pyqtSignal, QSize

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

import cx_Oracle as oci

sid = 'XE'
host = '210.119.14.60'
port = 1521
username = 'movie'
password = '1234'

class GlobalStore:
    public_selectname = ''
    public_selecttime = ''
    public_selecttheater = ''
    public_adtnumber = ''
    public_teennumber = ''
    public_seat = ''

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('mainpage.ui',self)
        print(widget.currentIndex())
        self.setStyleSheet("background-color: #EFF0F5;") # 배경화면 색상

        self.btn_search.clicked.connect(self.gotoSearch)
        self.btn_book.clicked.connect(self.gotoBookPage)
        self.adminButton = self.findChild(QPushButton, "btn_adminlogin")
        self.adminButton.clicked.connect(self.show_admin_login)

        self.btn_search.setStyleSheet("""
            btn_search {
                background-color: #105FFA; /* 버튼 배경색 */
                color: white;             /* 텍스트 색 */
                border-radius: 4px;      /* 모서리를 둥글게 */
            }
        """)

        self.btn_book.setStyleSheet("""
            btn_book {
                background-color: #105FFA; /* 버튼 배경색 */
                color: white;             /* 텍스트 색 */
                border-radius: 4px;      /* 모서리를 둥글게 */
            }
        """)

        self.btn_adminlogin.setStyleSheet("""
            btn_adminlogin {
                background-color: #105FFA; /* 버튼 배경색 */
                color: white;             /* 텍스트 색 */
                border-radius: 4px;      /* 모서리를 둥글게 */
            }
        """)

        self.lbl_title.setStyleSheet("color: black;")

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
        print("성공적으로 로그인되었습니다.", user_id, user_pw)



class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("admin_login.ui", self)

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
        self.btn_gotohome.clicked.connect(self.gohome)

    def gohome(self):
        widget.setCurrentIndex(widget.currentIndex()-2)
        print(widget.currentIndex())

class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gohome)
        self.btn_search.clicked.connect(self.startsearch)

    def gohome(self):
        widget.setCurrentIndex(widget.currentIndex()-2)
        print(widget.currentIndex())

    def startsearch(self):
        std_ticket_id = self.input_key.text()
        if std_ticket_id == '':
            QMessageBox.warning(self, '오류', '예매번호를 입력해주세요')
        else:
            self.loadData(std_ticket_id) 

    def loadData(self, std_ticket_id):  
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()

        conn.begin() 

        query = '''
           SELECT user_id, name, phone_number, role_id
             FROM gallery
            WHERE user_id = :v_std_ticket_id
                '''

        cursor.execute(query, {'v_std_ticket_id': int(std_ticket_id)})

        lst_ticket = []
        for _, item in enumerate(cursor):
            lst_ticket.append(item)
        print(lst_ticket)
        self.makeTable(lst_ticket)

        cursor.close()
        conn.close()

    def makeTable(self,lst_ticket):
            self.inplbl_1.setText(str(lst_ticket[0][0]))
            self.inplbl_2.setText(str(lst_ticket[0][1]))
            self.inplbl_3.setText(str(lst_ticket[0][2]))
            self.inplbl_4.setText(str(lst_ticket[0][3]))

# class BookPage1(QDialog):
#     resetLabelSignal = pyqtSignal()
#     def __init__(self):
#         super(BookPage1,self).__init__()
#         loadUi('bookpage1.ui',self)
#         # global public_selectname
#         movielist = []
#         movietime = {1:[],
#                      2:[],
#                      3:[]}
        
#         for i in range(len(self.loadName())):
#             movielist.append(self.loadName()[i][0])

#         movietime[1].append(self.loadTime()[0][0])
#         movietime[2].append(self.loadTime()[1][0])
#         print(self.loadName()[0])
#         for i in range(len(movielist)):
#             name_movie = getattr(self, f"name_movie{i + 1}")
#             btn_movie = getattr(self,f"btn_movie{i + 1}")
#             name_movie.setText(movielist[i])
#             btn_movie.clicked.connect(lambda _, text = name_movie.text() : self.selectMovieName(text))
#             # public_selectname = self.input_moviename.text()
#             # btn_movie.clicked.connect(self.printName)
            
#         for i in range(len(movietime)):
#             for j in range(len(movietime[i + 1])):
#                 btn_time = getattr(self,f"btn_{i + 1}time{j + 1}")
#                 btn_time.setText(movietime[i + 1][j])
#                 btn_time.clicked.connect(lambda _, text = btn_time.text() : self.selectTime(text))
#                 btn_time.clicked.connect(self.selectTheater)
                
        
#         self.btn_movie1.setIcon(QIcon('eximg.jpg'))
#         self.btn_movie1.setIconSize(self.btn_movie1.size())

#         self.input_moviename.textChanged.connect(self.checkInput)
#         self.input_movietime.textChanged.connect(self.checkInput)
#         self.input_theater.textChanged.connect(self.checkInput)

#         self.btn_next.setEnabled(False)
#         self.btn_gohome.clicked.connect(self.goHome)
#         self.btn_next.clicked.connect(self.goNext)

#         # 시간대 출력
#         print(movietime)

#     # def printName(self):
#     #     global public_selectname
#     #     print(public_selectname) 

#     def selectMovieName(self, movie_name):
#         self.input_moviename.setText(movie_name)

#     def selectTime(self, time):
#         self.input_movietime.setText(time)

#     def selectTheater(self,theater):
#         sender = self.sender()
#         if sender:
#             self.input_theater.setText(sender.objectName()[4] + '관')
        
#     def printObjectName(self):
#         sender = self.sender()
#         if sender:
#             print(sender.objectName())

#     def goHome(self):
#         widget.setCurrentIndex(widget.currentIndex()-3)
        
#     def goNext(self):
#         self.resetLabelSignal.emit()
#         widget.setCurrentIndex(widget.currentIndex()+1)

#     def checkInput(self):
#         input_moviename = self.input_moviename.text()
#         input_movietime = self.input_movietime.text()
#         input_theater = self.input_theater.text()

#         if input_moviename and input_movietime and input_theater:
#             self.btn_next.setEnabled(True)
#         else:
#             self.btn_next.setEnabled(False)
#         GlobalStore.public_selectname = input_moviename
#         GlobalStore.public_selecttime = input_movietime
#         GlobalStore.public_selecttheater = input_theater
#         # print(GlobalStore.public_selectname)
#         # print(GlobalStore.public_selecttime)
#         # print(GlobalStore.public_selecttheater)

#     def loadTime(self):  
#         conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
#         cursor = conn.cursor()

#         conn.begin() 

#         query = '''
#             SELECT to_char(s.START_TIME , 'HH24:MM') || '~' || to_char(s.END_TIME , 'HH24:MM') AS "TIME"
#               FROM SCHEDULE s
#                 '''

#         cursor.execute(query)

#         lst_time = []
#         for _, item in enumerate(cursor):
#             lst_time.append(item)
#         print(lst_time)
#         cursor.close()
#         conn.close()
#         return lst_time
    
#     def loadName(self):  
#         conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
#         cursor = conn.cursor()

#         conn.begin() 

#         query = '''
#           SELECT title
#             FROM (SELECT *
#   		            FROM movieinfo
#                    ORDER BY opening_date)
#             WHERE rownum <=3
#                 '''

#         cursor.execute(query)

#         lst_name = []
#         for _, item in enumerate(cursor):
#             lst_name.append(item)
#         print(lst_name)
#         cursor.close()
#         conn.close()
#         return lst_name

class BookPage1(QDialog):
    resetLabelSignal = pyqtSignal()

    def __init__(self):
        super(BookPage1, self).__init__()
        loadUi('bookpage1.ui', self)

        self.movie_id = None  # 선택된 영화의 movie_id 저장

        # 모든 시간 버튼 비활성화
        for i in range(1, 4):  # 관 1~3
            for j in range(1, 5):  # 시간 버튼 1~4
                btn = getattr(self, f"btn_{i}time{j}")
                btn.setEnabled(False)

        # 영화 리스트 로드 및 버튼 연결
        self.movielist = self.loadName()
        for i, (title, movie_id, poster_url) in enumerate(self.movielist):
            name_movie = getattr(self, f"name_movie{i + 1}")
            btn_movie = getattr(self, f"btn_movie{i + 1}")

            name_movie.setText(title)
            btn_movie.clicked.connect(lambda _, t=title: self.selectMovieName(t))

            # 실제 이미지 주소 추출
            real_url = extract_real_image_url(poster_url)
            try:
                image_data = urllib.request.urlopen(real_url).read()
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                icon = QIcon(pixmap)
                btn_movie.setIcon(icon)
                btn_movie.setIconSize(QSize(120, 180))
                btn_movie.setMinimumSize(QSize(120, 180))
            except Exception as e:
                print(f"이미지 로딩 실패: {poster_url}")
                print(e)



        # 시간 버튼 공통 이벤트 연결
        for i in range(1, 4):
            for j in range(1, 5):
                btn_time = getattr(self, f"btn_{i}time{j}")
                btn_time.clicked.connect(lambda _, b=btn_time: self.selectTime(b.text()))
                btn_time.clicked.connect(self.selectTheater)

 
        # 입력값 감지
        self.input_moviename.textChanged.connect(self.checkInput)
        self.input_movietime.textChanged.connect(self.checkInput)
        self.input_theater.textChanged.connect(self.checkInput)

        self.btn_next.setEnabled(False)
        self.btn_gohome.clicked.connect(self.goHome)
        self.btn_next.clicked.connect(self.goNext)

    def selectMovieName(self, movie_name):
        self.input_moviename.setText(movie_name)
        self.movie_id = self.getMovieIdByTitle(movie_name)

        # 관별 시간대 로딩 및 버튼 세팅
        for hall_num in range(1, 4):
            times = self.loadTime(hall_num, self.movie_id)
            for j in range(1, 5):
                btn_name = f"btn_{hall_num}time{j}"
                btn = getattr(self, btn_name, None)
                if btn:
                    if j <= len(times):
                        btn.setText(times[j - 1][0])
                        btn.setEnabled(True)
                    else:
                        btn.setText('')
                        btn.setEnabled(False)

    def selectTime(self, time):
        self.input_movietime.setText(time)

    def selectTheater(self):
        sender = self.sender()
        if sender:
            self.input_theater.setText(sender.objectName()[4] + '관')

    def goHome(self):
        widget.setCurrentIndex(widget.currentIndex() - 3)

    def goNext(self):
        self.resetLabelSignal.emit()
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def checkInput(self):
        input_moviename = self.input_moviename.text()
        input_movietime = self.input_movietime.text()
        input_theater = self.input_theater.text()

        self.btn_next.setEnabled(bool(input_moviename and input_movietime and input_theater))

        GlobalStore.public_selectname = input_moviename
        GlobalStore.public_selecttime = input_movietime
        GlobalStore.public_selecttheater = input_theater

    def loadTime(self, hall, movie_id):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        query = '''
            SELECT to_char(s.start_time, 'HH24:MI') || '~' || to_char(s.end_time, 'HH24:MI') AS time_slot
              FROM schedule s
             WHERE s.cnmtheater_id = :hall
               AND s.movie_id = :movie_id
            ORDER BY START_TIME
        '''
        cursor.execute(query, {'hall': hall, 'movie_id': movie_id})
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    def loadName(self):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        query = '''
            SELECT title, movie_id, poster
              FROM (SELECT *
                      FROM movieinfo
                     ORDER BY opening_date)
             WHERE rownum <= 3
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    def getMovieIdByTitle(self, title):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        query = 'SELECT movie_id FROM movieinfo WHERE title = :title'
        cursor.execute(query, {'title': title})
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    


# 일부로 class BookPage1 바깥에 있음
def extract_real_image_url(poster_url):
    parsed = urlparse(poster_url)
    query = parse_qs(parsed.query)
    if 'src' in query:
        return unquote(query['src'][0])
    return poster_url


class BookPage2(QDialog):
    def __init__(self):
        super(BookPage2,self).__init__()
        loadUi('bookpage2.ui',self)

        self.btn_next.setEnabled(False)

        # if seat != '':
        #     self.btn_next.setEnabled(True)
        # print(GlobalStore.public_selectname)
        # print(GlobalStore.public_selecttime)
        # print(GlobalStore.public_selecttheater)

        self.input_adt.setText('0')
        self.input_teen.setText('0')

        self.input_adt.textChanged.connect(self.checkInput)
        self.input_teen.textChanged.connect(self.checkInput)

        self.btn_goback.clicked.connect(self.goBack)
        self.btn_next.clicked.connect(self.goNext)

        for i in range(1,9):
            btn_adt = getattr(self, f"btn_adt{i}")
            btn_teen = getattr(self, f"btn_teen{i}")
            btn_adt.clicked.connect(self.getAdultNumber)
            btn_teen.clicked.connect(self.getTeenNumber)

    def resetLabel(self):
        self.lbl_test1.setText(GlobalStore.public_selectname)
        self.lbl_test2.setText(GlobalStore.public_selecttime)
        self.lbl_test3.setText(GlobalStore.public_selecttheater)

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())

    def goNext(self):
        widget.setCurrentIndex(widget.currentIndex()+1)

    def getAdultNumber(self):
        num_adt = 0
        btn = self.sender()
        if btn:
            num_adt = btn.text()
        self.input_adt.setText(str(num_adt))
        return num_adt

    def getTeenNumber(self):
        num_teen = 0
        btn = self.sender()
        if btn:
            num_teen = btn.text()
        self.input_teen.setText(num_teen)
        return num_teen
    
    def checkInput(self):
        adt_text = self.input_adt.text()
        teen_text = self.input_adt.text()

        if adt_text or teen_text:
            self.btn_next.setEnabled(True)
        else:
            self.btn_next.setEnabled(False)
        
class BookPage3(QDialog):
    def __init__(self):
        super(BookPage3,self).__init__()
        loadUi('bookpage3.ui',self)

        seat = '1'

        self.btn_next.setEnabled(False)

        if seat != '':
            self.btn_next.setEnabled(True)

        self.btn_goback.clicked.connect(self.goBack)
        self.btn_next.clicked.connect(self.goNext)

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())

    def goNext(self):
        widget.setCurrentIndex(widget.currentIndex()+1)
    
# obj = BookPage1()
# obj.checkInput()
# print(public_selectname)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    mainwindow = MainWindow()
    adminPage = AdminPage()
    searchpage = SearchPage()
    bookpage1 = BookPage1()
    bookpage2 = BookPage2()
    bookpage3 = BookPage3()
    bookpage1.resetLabelSignal.connect(bookpage2.resetLabel)
    widget.addWidget(mainwindow)
    widget.addWidget(adminPage)
    widget.addWidget(searchpage)
    widget.addWidget(bookpage1)
    widget.addWidget(bookpage2)
    widget.addWidget(bookpage3)
    widget.show()
    app.exec_()

    # 결제창에서 회원유무
    # 엔터누르면 확인되게 하는거
    # 초기화 해라 제발