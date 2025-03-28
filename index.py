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
    public_adtnumber = 0
    public_teennumber = 0
    public_seat = []
    public_occupied = []

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('mainpage.ui',self)
        # print(widget.currentIndex())
        self.setStyleSheet("background-color: white;") # 배경화면 색상

        self.btn_search.clicked.connect(self.gotoSearch)
        self.btn_book.clicked.connect(self.gotoBookPage)
        self.adminButton = self.findChild(QPushButton, "btn_adminlogin")
        self.adminButton.clicked.connect(self.show_admin_login)

        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #105FFA; /* 버튼 배경색 */
                color: white;             /* 텍스트 색 */
                border-radius: 4px;      /* 모서리를 둥글게 */
            }
        """)

        self.btn_book.setStyleSheet("""
            QPushButton {
                background-color: #105FFA; /* 버튼 배경색 */
                color: white;             /* 텍스트 색 */
                border-radius: 4px;      /* 모서리를 둥글게 */
            }
        """)

        self.btn_adminlogin.setStyleSheet("""
            QPushButton {
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
            # print(widget.currentIndex())
        else:
            print("관리자 로그인 취소됨")


    def gotoSearch(self):
        #예매조회 페이지 2번
        widget.setCurrentIndex(widget.currentIndex()+2)
        # print(widget.currentIndex())
    
    def gotoBookPage(self):
        #예매 페이지 3번
        widget.setCurrentIndex(widget.currentIndex()+3)
        # print(widget.currentIndex())

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
        # print(widget.currentIndex())

class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gohome)
        self.btn_search.clicked.connect(self.startsearch)
        self.input_key.returnPressed.connect(self.startsearch)
        

    def gohome(self):
        self.input_key.clear()
        labels = self.findChildren(QLabel)
        for label in labels:
            if label.objectName().startswith("inplbl_"):
                label.setText("")         #홈으로가면 Label, LineEdit 초기화
        widget.setCurrentIndex(widget.currentIndex()-2)
        print(widget.currentIndex())

    def startsearch(self):
        std_ticket_id = self.input_key.text()
        if std_ticket_id == '':
            QMessageBox.warning(self, '오류', '예매번호를 입력해주세요')
        elif not std_ticket_id.isdigit():   #예매번호 숫자 외에 입력시
            QMessageBox.warning(self, '오류', '예매번호는 숫자만 입력해주세요')
        else:
            self.loadData(std_ticket_id) 

    def loadData(self, std_ticket_id):  
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()

        conn.begin() 

        query = '''
           SELECT t.TICKET_ID, t.user_id, g.name, m.title, s.START_TIME
             FROM TICKETINFO t, schedule s, gallery g, movieinfo m
            WHERE t.USER_ID = g.USER_ID
              AND t.SCHEDULE_ID = s.SCHEDULE_ID 
              AND s.MOVIE_ID = m.MOVIE_ID
              AND t.TICKET_ID = :v_std_ticket_id
            ORDER BY t.TICKET_ID
                '''

        cursor.execute(query, {'v_std_ticket_id': str(std_ticket_id)})

        lst_ticket = []
        for _, item in enumerate(cursor):
            lst_ticket.append(item)
        print(lst_ticket)
        self.makeTable(lst_ticket)

        cursor.close()
        conn.close()

    def makeTable(self,lst_ticket):
            if not lst_ticket:  #예매번호 없을때 
                QMessageBox.warning(self, '오류', '예매번호가 없어요')
                self.inplbl_1.setText('')
                self.inplbl_2.setText('')
                self.inplbl_3.setText('')
                self.inplbl_4.setText('')
                return
            for i in range(len(lst_ticket[0])):
               getattr(self,f'inplbl_{i+1}').setText(str(lst_ticket[0][i]))

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
        self.input_moviename.clear()
        self.input_movietime.clear()
        self.input_theater.clear()
        for i in range(1, 4):
            for j in range(1, 5):
                btn = getattr(self, f"btn_{i}time{j}")
                btn.setText('')
                btn.setEnabled(False)
        # print(GlobalStore.public_selectname)

    def goNext(self):
        self.resetLabelSignal.emit()
        widget.setCurrentIndex(widget.currentIndex() + 1)
        print(GlobalStore.public_selecttheater)

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
    resetLabelSignal = pyqtSignal()
    def __init__(self):
        super(BookPage2,self).__init__()
        loadUi('bookpage2.ui',self)

        self.lbl_adtnum.setText('0')
        self.lbl_teennum.setText('0')

        self.input_adt.setText('0')
        self.input_teen.setText('0')

        self.input_adt.textChanged.connect(self.checkInput)
        self.input_teen.textChanged.connect(self.checkInput)

        self.btn_next.setEnabled(False)
        self.btn_goback.clicked.connect(self.goBack)
        self.btn_next.clicked.connect(self.goNext)

        for i in range(1,9):
            btn_adt = getattr(self, f"btn_adt{i}")
            btn_teen = getattr(self, f"btn_teen{i}")

            btn_adt.setCheckable(True)
            btn_teen.setCheckable(True)

            btn_adt.clicked.connect(self.getAdultNumber)
            btn_teen.clicked.connect(self.getTeenNumber)
            btn_adt.clicked.connect(self.btn_Activate)
            btn_teen.clicked.connect(self.btn_Activate)

    def resetLabel(self):
        self.lbl_selectmovie.setText(GlobalStore.public_selectname)
        self.lbl_selecttime.setText(GlobalStore.public_selecttime)
        self.lbl_selecttheater.setText(GlobalStore.public_selecttheater)
        self.lbl_adtnum.setText(str(GlobalStore.public_adtnumber))
        self.lbl_teennum.setText(str(GlobalStore.public_teennumber))

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(GlobalStore.public_selecttheater,GlobalStore.public_selectname,GlobalStore.public_selecttime)
        # print(widget.currentIndex())

    def goNext(self):
        # 예약된 좌석 불러오기
        self.loadOccupiedSeats()
        self.resetLabelSignal.emit()
        widget.setCurrentIndex(widget.currentIndex()+1)

    def getAdultNumber(self):
        num_adt = 0
        btn = self.sender()
        if btn:
            num_adt = btn.text()
        self.input_adt.setText(num_adt)
        self.lbl_adtnum.setText(num_adt)
        return num_adt

    def getTeenNumber(self):
        num_teen = 0
        btn = self.sender()
        if btn:
            num_teen = btn.text()
        self.input_teen.setText(num_teen)
        self.lbl_teennum.setText(num_teen)
        return num_teen
    
    def btn_Activate(self):
        clicked_btn = self.sender()
        btn_name = clicked_btn.objectName()

        if btn_name.startswith("btn_adt"):
            if clicked_btn.isChecked():
                for i in range(1, 9):
                    btn = getattr(self, f"btn_adt{i}")
                    if btn != clicked_btn:
                        btn.setChecked(False)
                        btn.setStyleSheet("")
                clicked_btn.setStyleSheet("background-color: gray;")
                self.input_adt.setText(clicked_btn.text())
                GlobalStore.public_adtnumber = clicked_btn.text()
                self.adt_text = clicked_btn.text()
            else:
                clicked_btn.setStyleSheet("")
                self.input_adt.setText("0")
                GlobalStore.public_adtnumber = "0"
                self.adt_text = "0"

        elif btn_name.startswith("btn_teen"):
            if clicked_btn.isChecked():
                for i in range(1, 9):
                    btn = getattr(self, f"btn_teen{i}")
                    if btn != clicked_btn:
                        btn.setChecked(False)
                        btn.setStyleSheet("")
                clicked_btn.setStyleSheet("background-color: gray;")
                self.input_teen.setText(clicked_btn.text())
                GlobalStore.public_teennumber = clicked_btn.text()
                self.teen_text = clicked_btn.text()
            else:
                clicked_btn.setStyleSheet("")
                self.input_teen.setText("0")
                self.teen_text = "0"
        self.checkInput()

    def checkInput(self):
        adt_text = self.input_adt.text()
        teen_text = self.input_teen.text()

        if adt_text or teen_text:
            self.btn_next.setEnabled(True)
        else:
            self.btn_next.setEnabled(False)

        GlobalStore.public_adtnumber = adt_text
        GlobalStore.public_teennumber = teen_text

     # 예약된 좌석 불러오기 
    def loadOccupiedSeats(self):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        query = '''
            SELECT s.seat_number
            FROM ticketseat ts
            JOIN seatinfo s ON ts.seatinfo_id = s.seatinfo_id
            JOIN ticketinfo ti ON ts.ticket_id = ti.ticket_id
            JOIN schedule sc ON ti.schedule_id = sc.schedule_id
            JOIN movieinfo m ON sc.movie_id = m.movie_id
            WHERE m.title = :title
            AND TO_CHAR(sc.start_time, 'HH24:MI') || '~' || TO_CHAR(sc.end_time, 'HH24:MI') = :time
            AND sc.cnmtheater_id = :theater
        '''
        title = GlobalStore.public_selectname
        time = GlobalStore.public_selecttime
        theater = int(GlobalStore.public_selecttheater[0])  # '1관' → 1

        print(title, time, theater)

        cursor.execute(query, {'title': title, 'time': time, 'theater': theater})
        result = cursor.fetchall()
        conn.close()

        # 결과를 전역변수에 저장
        for row in result:
            GlobalStore.public_occupied.append(row[0])
        
class BookPage3(QDialog):
    def __init__(self):
        super(BookPage3,self).__init__()
        loadUi('bookpage3.ui',self)

        self.btn_goback.clicked.connect(self.goBack)
        self.btn_next.setDisabled(True)
        self.btn_next.clicked.connect(self.goNext)

        # print(GlobalStore.public_occupied)
        buttons = self.findChildren(QPushButton)
        # print(buttons[0].text())

        for i in range(len(buttons) - 2):
            seatbtn = getattr(self, f'seat_{i + 1}')
            seatbtn.clicked.connect(lambda _, sb=seatbtn: self.selectSeat(sb.text()))

    def selectSeat(self,text):
        temp = []
        GlobalStore.public_seat = []
        total_peoplenum = int(GlobalStore.public_adtnumber) + int(GlobalStore.public_teennumber)
        temp.append(text)
        # print(int(text[1:]))
        # print(int(text[1:]) + 1)
        for i in range(total_peoplenum - 1):
            if int(text[1:]) + i + 1 < 10:
                temp.append(f'{text[:2]}{int(text[1:]) + i + 1}')
        if total_peoplenum == len(temp):
            for i in temp:
                GlobalStore.public_seat.append(i)
            if set(GlobalStore.public_seat) & set(GlobalStore.public_occupied):
                QMessageBox.warning(self,'경고','이미 예약된 자리가 있어서 선택불가합니다.')
            else:
                buttons = self.findChildren(QPushButton)
                for i in range(len(buttons) - 2):
                    seatbtn1 = getattr(self, f'seat_{i + 1}')
                    seatbtn1.setStyleSheet(
                        """QPushButton{""
                        }""")
                    
                for j in GlobalStore.public_seat:
                    # print(j)
                    for i in range(len(buttons) - 2):
                        seatbtn2 = getattr(self, f'seat_{i + 1}')
                        if seatbtn2.text() == j:
                            # print(seatbtn)
                            seatbtn2.setStyleSheet(
                                """QPushButton{
                                background-color: black;
                                color: white;
                                border-radius: 4px;
                                }"""
                            )

                lbl_seat_text = ", ".join(GlobalStore.public_seat)
                self.lbl_seat.setText(lbl_seat_text)

                if len(GlobalStore.public_seat) == 0:
                    self.btn_next.setDisabled(True)
                else:
                    self.btn_next.setDisabled(False)
        else:
            QMessageBox.warning(self,'경고','인원에 맞지 않는 좌석입니다.')
        
    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        GlobalStore.public_seat = []
        GlobalStore.public_occupied = []
        print(GlobalStore.public_occupied)
        buttons = self.findChildren(QPushButton)
        for i in range(len(buttons) - 2):
            seatbtn1 = getattr(self, f'seat_{i + 1}')
            seatbtn1.setStyleSheet(
            """QPushButton{""
            }""")
        self.lbl_seat.setText('')
        buttons = self.findChildren(QPushButton)
        for i in range(len(buttons) - 2):
            seatbtn3 = getattr(self, f'seat_{i + 1}')
            seatbtn3.setDisabled(False)
        # print(widget.currentIndex())

    def goNext(self):
        widget.setCurrentIndex(widget.currentIndex()+1)

    def resetLabel(self):
        self.lbl_selectmovie.setText(GlobalStore.public_selectname)
        self.lbl_selecttime.setText(GlobalStore.public_selecttime)
        self.lbl_selecttheater.setText(GlobalStore.public_selecttheater)
        self.lbl_adtnum.setText(GlobalStore.public_adtnumber)
        self.lbl_teennum.setText(GlobalStore.public_teennumber)
        buttons = self.findChildren(QPushButton)
        for j in GlobalStore.public_occupied:
            for i in buttons:
                if j == i.text():
                    i.setDisabled(True)

    def getSeatNum(self,theaternum):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        query = '''
            SELECT seat_number
            FROM seatinfo
            WHERE CNMTHEATER_ID = :theaternum
        '''
        cursor.execute(query, {'theaternum': theaternum})
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        print(result)

class BookPage4(QDialog):
    def __init__(self):
        super(BookPage4,self).__init__()
        loadUi('bookpage4.ui',self)

        self.btn_user.clicked.connect(self.userInformation)
        self.btn_guest.clicked.connect(self.guestInformation)

    def userInformation(self):
        user_name = self.input_userid.text()
        if user_name == '':
            QMessageBox.warning(self,"입력 누락","모든 정보를 입력해주세요")
        else:        
            QMessageBox.information(self, "입력 완료", "회원정보 입력 완료되었습니다.")   

    def guestInformation(self):
        guest_name = self.input_name.text()
        guest_phone = self.input_phone.text()
        guest_birth = self.input_birth.text()
        guest_gender = self.input_gender.text()
        QMessageBox.information(self, "환영함", "비회원으로 결제 진행합니다.")

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        print(widget.currentIndex())
# class BookPage4(QDialog):
#     def __init__(self):
#         super(BookPage4,self).__init__()
#         loadUi('bookpage4.ui',self)

#         self.btn_goback.clicked.connect(self.goBack)

#     def goBack(self):
#         widget.setCurrentIndex(widget.currentIndex()-1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    mainwindow = MainWindow()
    adminPage = AdminPage()
    searchpage = SearchPage()
    bookpage1 = BookPage1()
    bookpage2 = BookPage2()
    bookpage3 = BookPage3()
    bookpage4 = BookPage4()
    bookpage1.resetLabelSignal.connect(bookpage2.resetLabel)
    bookpage2.resetLabelSignal.connect(bookpage3.resetLabel)
    widget.addWidget(mainwindow)
    widget.addWidget(adminPage)
    widget.addWidget(searchpage)
    widget.addWidget(bookpage1)
    widget.addWidget(bookpage2)
    widget.addWidget(bookpage3)
    widget.addWidget(bookpage4)
    widget.show()
    app.exec_()

    # 결제창에서 회원유무
    # 엔터누르면 확인되게 하는거
    # 초기화 해라 제발