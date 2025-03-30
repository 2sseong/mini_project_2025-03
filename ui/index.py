import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, pyqtSignal
import urllib.request
from urllib.parse import urlparse, parse_qs, unquote
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QObject, QEvent  # ✅ 여기 추가!
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
from datetime import datetime


# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

import cx_Oracle as oci

sid = 'XE'
host = '210.119.14.60'
port = 1521
username = 'movie'
password = '1234'

# ESC 방지용
class EscBlocker(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            return True  # ESC 무시
        return super().eventFilter(obj, event)

class GlobalStore:
    public_selectname = ''
    public_selecttime = ''
    public_selecttheater = ''
    public_adtnumber = 0
    public_teennumber = 0
    public_seat = []
    public_occupied = []
    public_personinfo = []
    public_theaterprice = 0
    public_payfinal = 0
    public_poster_url = ''
    public_user_id = ''
    public_ticket_code = ''
    public_final_price = 0  # ✅ 총 결제 금액 저장용 전역변수




# 결제 insert문 전역함수
def insert_payment_ticket():
    # 영수증 코드 생성 함수 (예: PAY202503290001)
    def generate_payment_code():
        today = datetime.now().strftime("%Y%m%d")
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()
        cursor.execute("SELECT NVL(MAX(pay_id), 0) + 1 FROM pay")
        next_id = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return f'PAY{today}{str(next_id).zfill(4)}', next_id

    # 예매번호 생성 함수: 전화번호 뒤 4자리 + 종료시간(HHMM) + 관 ID
    def generate_ticket_code(phone_number, end_time, theater_id, seatinfo_id):
        phone_suffix = phone_number[-4:]
        time_str = end_time.strftime('%H%M')
        return f'{phone_suffix}{time_str}{theater_id}{seatinfo_id}'

    # 회원 여부 판단 (전역 user_id 기준)
    user_id = GlobalStore.public_user_id
    is_member = bool(user_id)  # 0이거나 빈 문자열이면 False
    if is_member:
        user_id = int(user_id)

    # DB 연결
    conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
    cursor = conn.cursor()

    try:
        user_info = GlobalStore.public_personinfo

        # 공통 정보
        phone = user_info[1] if not is_member else user_info[1]  # 회원일 경우도 phone 필요
        theater_id = int(GlobalStore.public_selecttheater[0])
        title = GlobalStore.public_selectname
        time_slot = GlobalStore.public_selecttime
        adt = int(GlobalStore.public_adtnumber)
        teen = int(GlobalStore.public_teennumber)
        seat_list = GlobalStore.public_seat
        price = GlobalStore.public_theaterprice
        final_amount = price * adt + (price - 2000) * teen

        # 상영 시간 분리
        start_time_str, end_time_str = time_slot.split('~')

        # 스케줄 ID 및 종료시간 조회
        cursor.execute("""
            SELECT schedule_id, end_time
            FROM schedule s
            JOIN movieinfo m ON s.movie_id = m.movie_id
            WHERE m.title = :title
              AND TO_CHAR(s.start_time, 'HH24:MI') = :start_time
              AND TO_CHAR(s.end_time, 'HH24:MI') = :end_time
              AND s.cnmtheater_id = :theater_id
        """, {
            'title': title,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'theater_id': theater_id
        })
        schedule_id, end_time = cursor.fetchone()

        # 비회원이면 user_id 생성 + gallery insert
        if not is_member:
            cursor.execute("SELECT NVL(MAX(user_id), 101) + 1 FROM gallery")
            user_id = cursor.fetchone()[0]

            name = user_info[0]
            phone = user_info[1]
            birth_str = user_info[2]
            gender = user_info[3]

            if birth_str:
                birth_date = datetime.strptime(birth_str, '%Y-%m-%d').date()
            else:
                birth_date = None

            cursor.execute("""
                INSERT INTO gallery(user_id, name, phone_number, birth_date, gender, role_id)
                VALUES (:user_id, :name, :phone_number, :birth_date, :g_val, 3)
            """, {
                'user_id': user_id,
                'name': name,
                'phone_number': phone,
                'birth_date': birth_date,
                'g_val': gender
            })

        # 결제 코드, pay_id 생성
        payment_code, pay_id = generate_payment_code()

        # ticket_id, 예매번호 생성
        cursor.execute("SELECT NVL(MAX(ticket_id), 301) + 1 FROM ticketinfo")
        ticket_id = cursor.fetchone()[0]
        ticket_code = generate_ticket_code(phone, end_time, theater_id, seat_list[0])


        # 좌석 ID 리스트 조회
        seatinfo_ids = []
        for seat in seat_list:
            cursor.execute("""
                SELECT seatinfo_id
                FROM seatinfo
                WHERE seat_number = :seat_number AND cnmtheater_id = :cnmtheater_id
            """, {'seat_number': seat, 'cnmtheater_id': theater_id})
            seatinfo_id = cursor.fetchone()[0]
            seatinfo_ids.append(seatinfo_id)
        # ✅ 첫 번째 seatinfo_id 사용해서 예매번호 생성
        first_seat_id = seatinfo_ids[0]
        ticket_code = generate_ticket_code(phone, end_time, theater_id, first_seat_id)
        GlobalStore.public_ticket_code = ticket_code  # ✅ 전역변수에 저장!


        # pay insert
        cursor.execute("""
            INSERT INTO pay(pay_id, payment_code, user_id, payment_date, amount)
            VALUES (:pay_id, :code, :user_id, SYSDATE, :amount)
        """, {'pay_id': pay_id, 'code': payment_code, 'user_id': user_id, 'amount': final_amount})

        # ticketinfo insert
        cursor.execute("""
            INSERT INTO ticketinfo(ticket_id, ticket_code, schedule_id, user_id, adult, youth)
            VALUES (:ticket_id, :ticket_code, :schedule_id, :user_id, :adult_cnt, :youth_cnt)
        """, {
            'ticket_id': ticket_id,
            'ticket_code': ticket_code,
            'schedule_id': schedule_id,
            'user_id': user_id,
            'adult_cnt': adt,
            'youth_cnt': teen
        })

        # ticketseat insert
        for seatinfo_id in seatinfo_ids:
            cursor.execute("""
                INSERT INTO ticketseat(ticket_id, seatinfo_id)
                VALUES (:tid, :sid)
            """, {'tid': ticket_id, 'sid': seatinfo_id})

        # ticketpay insert
        cursor.execute("""
            INSERT INTO ticketpay(pay_id, ticket_id)
            VALUES (:pay_id, :ticket_id)
        """, {'pay_id': pay_id, 'ticket_id': ticket_id})

        # 커밋 및 알림
        conn.commit()
        QMessageBox.information(None, "성공", f"예매 완료\n예매번호: {ticket_code}\n영수증 코드: {payment_code}")

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        conn.rollback()
        QMessageBox.critical(None, "DB 오류", f"{str(e)}\n\n{tb}")

    finally:
        cursor.close()
        conn.close()

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('mainpage.ui',self)
        # print(widget.currentIndex())

        self.btn_search.clicked.connect(self.gotoSearch)
        self.btn_book.clicked.connect(self.gotoBookPage)
        self.adminButton = self.findChild(QPushButton, "btn_adminlogin")
        self.adminButton.clicked.connect(self.show_admin_login)

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
        super(AdminPage, self).__init__()
        loadUi("adminpage.ui", self)

        # FigureCanvas 생성해서 QDesigner에서 만든 QWidget에 붙이기
        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax = self.canvas.figure.add_subplot(111)

        layout = QVBoxLayout(self.graph_widget)  # ← Qt Designer에서 만든 QWidget
        layout.addWidget(self.canvas)

        self.btn_sales.clicked.connect(self.Sales)
        self.btn_go_to_main.clicked.connect(self.gotomain)

    def Sales(self):
        self.loadData()
        # 예시 데이터
        titles = ['영화1', '영화2', '영화3']
        counts = [10, 20, 15]

        self.ax.clear()
        self.ax.bar(titles, counts, color='skyblue')
        self.ax.set_title('영화별 예매 수')
        self.ax.set_xlabel('영화 제목')
        self.ax.set_ylabel('예매 수')
        self.ax.tick_params(axis='x', rotation=45)
        self.canvas.draw()

    def loadData(self):
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()

        conn.begin() 

        query = '''
           SELECT to_char(SUM(amount), '999,999,999,999') 
             FROM pay
                '''

        cursor.execute(query)

        total = cursor.fetchone()[0]
        self.lbl_total.setText(f'{total}원')

    def gotomain(self):
        widget.setCurrentIndex(widget.currentIndex()-1)


class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gohome)
        self.btn_search.clicked.connect(self.startsearch)
        self.input_key.returnPressed.connect(self.startsearch)
        

    def gohome(self):
        self.input_key.clear()
        self.tbl_search.setModel(None)
        widget.setCurrentIndex(widget.currentIndex()-2)
        

    def startsearch(self):
        std_ticket_code = self.input_key.text()
        if std_ticket_code == '':
            QMessageBox.warning(self, '오류', '예매번호를 입력해주세요')
        elif not std_ticket_code.isdigit():   #예매번호 숫자 외에 입력시
            QMessageBox.warning(self, '오류', '예매번호는 숫자만 입력해주세요')
        else:
            self.loadData(std_ticket_code) 

    def loadData(self, std_ticket_code):  
        conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
        cursor = conn.cursor()

        conn.begin() 

        query = '''
                SELECT t.user_id
                    , g.name
                    , m.title
                    , to_char(s.START_TIME,'YYYY-MM-DD')
                    , to_char(s.START_TIME,'HH24:MI') || '~' || to_char(s.END_TIME,'HH24:MI')
                    , LISTAGG(i.seat_number, ', ') WITHIN GROUP (ORDER BY i.seat_number)
                    , count(*)
                 FROM TICKETINFO t, schedule s, gallery g, movieinfo m, ticketseat h, SEATINFO i
                WHERE t.USER_ID = g.USER_ID
                  AND s.MOVIE_ID = m.MOVIE_ID
                  AND t.SCHEDULE_ID = s.SCHEDULE_ID 
                  AND t.TICKET_ID = h.TICKET_ID
                  AND i.SEATINFO_ID = h.SEATINFO_ID
                  AND t.ticket_code = :v_std_ticket_code
                GROUP BY t.user_id,
                        g.name,
                        m.title,
                        TO_CHAR(s.START_TIME,'YYYY-MM-DD'),
                        TO_CHAR(s.START_TIME, 'HH24:MI') || '~' || TO_CHAR(s.END_TIME, 'HH24:MI')
                '''

        cursor.execute(query, {'v_std_ticket_code': str(std_ticket_code)})

        lst_ticket = cursor.fetchall()
        # print(lst_ticket)        
        self.makeTable(lst_ticket)

        cursor.close()
        conn.close()

    def makeTable(self,lst_ticket):
        if not lst_ticket:  #예매번호 없을때 
            QMessageBox.warning(self, '오류', '예매번호가 없어요')
            self.tbl_search.setModel(None)
            return
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['회원ID', '예약자명', '영화제목','상영날짜', '상영시간', '좌석','인원 수'])
        for row in lst_ticket:
            items = [QStandardItem(str(col)) for col in row]
            model.appendRow(items)

        self.tbl_search.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_search.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_search.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_search.setSortingEnabled(True)
        self.tbl_search.setModel(model)



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

        # 포스터 URL 전역 저장
        for title, movie_id, poster_url in self.movielist:
            if title == movie_name:
                real_url = extract_real_image_url(poster_url)
                GlobalStore.public_poster_url = real_url
                break

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
        # print(GlobalStore.public_selecttheater)

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
        # print(GlobalStore.public_selecttheater,GlobalStore.public_selectname,GlobalStore.public_selecttime)
        # print(widget.currentIndex())

    def goNext(self):
        # 예약된 좌석 불러오기
        self.loadOccupiedSeats()
        self.loadTheaterPrice()
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

        self.lbl_adtnum.setText(adt_text)
        self.lbl_teennum.setText(teen_text)

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

        # print(title, time, theater)

        cursor.execute(query, {'title': title, 'time': time, 'theater': theater})
        result = cursor.fetchall()
        conn.close()

        # 결과를 전역변수에 저장
        for row in result:
            GlobalStore.public_occupied.append(row[0])

    def loadTheaterPrice(self):
        try:
            theater = GlobalStore.public_selecttheater[:1]
            conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
            cursor = conn.cursor()

            query = '''
                    SELECT price
                    FROM cnmtheater
                    WHERE cnmtheater_id = :v_theater
            '''

            cursor.execute(query, {'v_theater': theater})
            result = cursor.fetchone()
            # print(result[0])
            GlobalStore.public_theaterprice = result[0]
            # print(GlobalStore.public_theaterprice)
            cursor.close()
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "DB 오류", str(e))
        
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

                if self.lbl_seat.text() == '':
                    self.btn_next.setDisabled(True)
                else:
                    self.btn_next.setDisabled(False)
        else:
            QMessageBox.warning(self,'경고','인원에 맞지 않는 좌석입니다.')
        
    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        GlobalStore.public_seat = []
        GlobalStore.public_occupied = []
        # print(GlobalStore.public_occupied)
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
        self.btn_next.setDisabled(True)
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
        # print(result)
    
 
class BookPage4(QDialog):
    resetLabelSignal = pyqtSignal()
    def __init__(self):
        super(BookPage4,self).__init__()
        loadUi('bookpage4.ui',self)

        self.btn_goback.clicked.connect(self.goBack)
        self.btn_user.clicked.connect(self.userInformation)
        self.btn_guest.clicked.connect(self.guestInformation)

    def userInformation(self):
        dlg = userPayment() #payment클래스 쓰기위한 변수
        user_id = self.input_userid.text()
        GlobalStore.public_personinfo.append(user_id)
        GlobalStore.public_user_id = user_id # 추가한 코드
        if user_id == '':
            QMessageBox.warning(self, "입력 누락", "모든 정보를 입력해주세요")
            return

        try:
            conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
            cursor = conn.cursor()

            query = '''
                SELECT name, phone_number, to_char(birth_date,'yyyy-mm-dd'), gender
                FROM gallery
                WHERE user_id = :v_user_id
            '''

            cursor.execute(query, {'v_user_id': user_id})
            result = cursor.fetchone()
            # print(result)
            cursor.close()
            conn.close()

            if result:
                name, phone, birth, gender = result
                GlobalStore.public_personinfo.clear() # 클리어 작업 넣기personinfo
                QMessageBox.information(
                    self, "회원 확인",
                    f"회원정보 확인 완료:\n이름: {name}\n전화: {phone}\n생일: {birth}\n성별: {gender}"
                )
                for i in result:
                    GlobalStore.public_personinfo.append(i)
                # print(GlobalStore.public_personinfo[0])
                dlg.exec() == QDialog.Accepted
                widget.setCurrentIndex(widget.currentIndex()+5) 
            else:
                QMessageBox.warning(self, "오류", "해당 회원이 존재하지 않습니다.")

        except Exception as e:
            QMessageBox.critical(self, "DB 오류", str(e))

    def guestInformation(self): 
        dlg = guestPayment()
        guest_name = self.input_name.text() or None
        guest_phone = self.input_phone.text()
        guest_birth = self.input_birth.text() or None
        guest_gender = self.input_gender.text() or None
        if guest_phone == '':
            QMessageBox.warning(self, "경고", "전화번호 기입은 필수입니다.")
            return
        if not guest_phone.isdigit() or len(guest_phone) != 11:
            QMessageBox.warning(self, "경고", "전화번호는 11자리 숫자여야 합니다.")
            return
        
        GlobalStore.public_personinfo.clear() # 클리어 작업 넣기personinfo
        GlobalStore.public_personinfo.append(guest_name)
        GlobalStore.public_personinfo.append(guest_phone)
        GlobalStore.public_personinfo.append(guest_birth)
        GlobalStore.public_personinfo.append(guest_gender)
        QMessageBox.information(self, "비회원 결제", "비회원정보 입력이 완료되어 결제창으로 이동합니다.")
        dlg.exec() == QDialog.Accepted
        widget.setCurrentIndex(widget.currentIndex()+5) 
            
        # print(GlobalStore.public_personinfo)

    def goBack(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
        # print(widget.currentIndex())

class userPayment(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("userpayment.ui", self)
        self.btn_pay.setEnabled(False)
        self.btn_pay.clicked.connect(self.goReceipt2)
        
        # for widget in self.findChildren(QLabel):
        #     print(widget.objectName())

        # 총 금액 계산
        adt_price = GlobalStore.public_theaterprice * int(GlobalStore.public_adtnumber)
        teen_price = (GlobalStore.public_theaterprice - 2000) * int(GlobalStore.public_teennumber)
        total = adt_price + teen_price - 1000  # -1000은 할인 금액
        GlobalStore.public_final_price = total  # ✅ 전역변수에 저장

        self.lbl_selectmovie.setText(GlobalStore.public_selectname)
        self.lbl_selecttime.setText(GlobalStore.public_selecttime)
        self.lbl_selecttheater.setText(GlobalStore.public_selecttheater)
        self.lbl_adtnum.setText(f'{GlobalStore.public_adtnumber}명')
        self.lbl_teennum.setText(f'{GlobalStore.public_teennumber}명')
        self.lbl_selected_seat.setText(', '.join(GlobalStore.public_seat))
        self.lbl_payexplain1.setText(f'성인 가격 : {adt_price}원')
        self.lbl_payexplain2.setText(f'청소년 가격 : {teen_price}원')
        self.lbl_total.setText(f'{total}원')

        self.btn_poster.setStyleSheet("""                     
                        QPushButton {
                               background-color: none;  /* 배경색 변경 방지 */
                                color: black;  /* 텍스트 색상 유지 (필요 시 조정) */
                                border: none;  /* 테두리 없애기 */
                        }
                                      
                        QPushButton:hover {
                               background-color: none;  /* 배경색 변경 방지 */
                                color: black;  /* 텍스트 색상 유지 (필요 시 조정) */
                                border: none;  /* 테두리 없애기 */
                        }
        """)

        self.btn_payenter.clicked.connect(self.getPayEnter)

        real_url = extract_real_image_url(GlobalStore.public_poster_url)
        try:
            image_data = urllib.request.urlopen(real_url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            icon = QIcon(pixmap)
            self.btn_poster.setIcon(icon)
            self.btn_poster.setIconSize(QSize(120, 180))
            self.btn_poster.setMinimumSize(QSize(120, 180))
        except Exception as e:
            print(f"이미지 로딩 실패: {GlobalStore.public_poster_url}")
            print(e)

    def getPayEnter(self):
        if self.input_pay.text() == '':
            QMessageBox.warning(self, "경고", "가격을 입력해주세요")
            self.input_pay.clear()
            self.btn_pay.setEnabled(False)  # ❗ 실패 시 다시 비활성화
        elif int(self.input_pay.text()) < int(self.lbl_total.text()[:-1]):
            QMessageBox.warning(self, "경고", "입력하신 가격이 최종 가격보다 작습니다.")
            self.input_pay.clear()
            self.btn_pay.setEnabled(False)
        else:
            self.lbl_change.setText(str(int(self.input_pay.text()) - int(self.lbl_total.text()[:-1])) + '원')
            self.btn_pay.setEnabled(True)  # ✅ 정상 금액 입력 후 결제 가능

    def goReceipt2(self):
        # 돈을 안 넣었을 경우
        if self.input_pay.text() == '' or int(self.input_pay.text()) < GlobalStore.public_final_price:
            QMessageBox.warning(self, "경고", "결제 금액을 정확히 입력해주세요.")
            return
        
        insert_payment_ticket()  # 실제 결제 처리
        bookpage5.resetpaylabel() # 전역변수 가져오기
        widget.setCurrentIndex(widget.currentIndex()+1)
        self.accept()
    

class guestPayment(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("guestpayment.ui", self)
        self.btn_pay.setEnabled(True)
        self.btn_pay.clicked.connect(self.goReceipt2) 
        
        # 총 금액 계산
        adt_price = GlobalStore.public_theaterprice * int(GlobalStore.public_adtnumber)
        teen_price = (GlobalStore.public_theaterprice - 2000) * int(GlobalStore.public_teennumber)
        total = adt_price + teen_price - 1000  # -1000은 할인 금액
        GlobalStore.public_final_price = total  # ✅ 전역변수에 저장

        self.lbl_selectmovie.setText(GlobalStore.public_selectname)
        self.lbl_selecttime.setText(GlobalStore.public_selecttime)
        self.lbl_selecttheater.setText(GlobalStore.public_selecttheater)
        self.lbl_adtnum.setText(f'{GlobalStore.public_adtnumber}명')
        self.lbl_teennum.setText(f'{GlobalStore.public_teennumber}명')
        self.lbl_selected_seat.setText(', '.join(GlobalStore.public_seat))
        self.lbl_payexplain1.setText(f'성인 가격 : {adt_price}원')
        self.lbl_payexplain2.setText(f'청소년 가격 : {teen_price}원')
        self.lbl_total.setText(f'{total}원')

        self.btn_payenter.clicked.connect(self.getPayEnter)

        self.btn_poster.setStyleSheet("""                     
                        QPushButton {
                               background-color: none;  /* 배경색 변경 방지 */
                                color: black;  /* 텍스트 색상 유지 (필요 시 조정) */
                                border: none;  /* 테두리 없애기 */
                        }
                                      
                        QPushButton:hover {
                               background-color: none;  /* 배경색 변경 방지 */
                                color: black;  /* 텍스트 색상 유지 (필요 시 조정) */
                                border: none;  /* 테두리 없애기 */
                        }
        """)

        self.btn_payenter.clicked.connect(self.getPayEnter)

        real_url = extract_real_image_url(GlobalStore.public_poster_url)
        try:
            image_data = urllib.request.urlopen(real_url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            icon = QIcon(pixmap)
            self.btn_poster.setIcon(icon)
            self.btn_poster.setIconSize(QSize(120, 180))
            self.btn_poster.setMinimumSize(QSize(120, 180))
        except Exception as e:
            print(f"이미지 로딩 실패: {GlobalStore.public_poster_url}")
            print(e)

    def getPayEnter(self):
        if self.input_pay.text() == '':
            QMessageBox.warning(self, "경고", "가격을 입력해주세요")
            self.input_pay.clear()
            self.btn_pay.setEnabled(False)  # ❗ 실패 시 다시 비활성화
        elif int(self.input_pay.text()) < int(self.lbl_total.text()[:-1]):
            QMessageBox.warning(self, "경고", "입력하신 가격이 최종 가격보다 작습니다.")
            self.input_pay.clear()
            self.btn_pay.setEnabled(False)
        else:
            self.lbl_change.setText(str(int(self.input_pay.text()) - int(self.lbl_total.text()[:-1])) + '원')
            self.btn_pay.setEnabled(True)  # ✅ 정상 금액 입력 후 결제 가능


    def goReceipt2(self):
            # 돈을 안 넣었을 경우
        if self.input_pay.text() == '' or int(self.input_pay.text()) < GlobalStore.public_final_price:
            QMessageBox.warning(self, "경고", "결제 금액을 정확히 입력해주세요.")
            return

        insert_payment_ticket()  # 실제 결제 처리
        bookpage5.resetpaylabel()
        widget.setCurrentIndex(widget.currentIndex()+1)
        self.accept()

class BookPage5(QDialog):
    def __init__(self):
        super(BookPage5,self).__init__()
        loadUi('bookpage5.ui',self)
        self.btn_home.clicked.connect(self.go0page)
    print(GlobalStore.public_ticket_code)

    def resetpaylabel(self):
        # 예매번호 출력
        self.lbl_rescode.setText(GlobalStore.public_ticket_code)

        # 기본 정보 출력
        self.lbl_selectmovie.setText(GlobalStore.public_selectname)
        self.lbl_selecttime.setText(GlobalStore.public_selecttime)
        self.lbl_selecttheater.setText(GlobalStore.public_selecttheater)
        self.lbl_adtnum.setText(f'{GlobalStore.public_adtnumber}명')
        self.lbl_teennum.setText(f'{GlobalStore.public_teennumber}명')
        self.lbl_selected_seat.setText(', '.join(GlobalStore.public_seat))
        # 총 결제 금액
        total = GlobalStore.public_final_price
        self.lbl_total.setText(f'총 금액 : {total}원')

        # 포스터 이미지 설정
        real_url = extract_real_image_url(GlobalStore.public_poster_url)
        try:
            image_data = urllib.request.urlopen(real_url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            icon = QIcon(pixmap)
            self.btn_poster.setIcon(icon)
            self.btn_poster.setIconSize(QSize(120, 180))
            self.btn_poster.setMinimumSize(QSize(120, 180))
        except Exception as e:
            print(f"포스터 이미지 로딩 실패: {GlobalStore.public_poster_url}")
            print(e)

    def go0page(self):
        GlobalStore.public_selectname = ''
        GlobalStore.public_selecttime = ''
        GlobalStore.public_selecttheater = ''
        GlobalStore.public_adtnumber = 0
        GlobalStore.public_teennumber = 0
        GlobalStore.public_seat = []
        GlobalStore.public_occupied = []
        GlobalStore.public_personinfo = []
        GlobalStore.public_theaterprice = 0
        GlobalStore.public_payfinal = 0
        GlobalStore.public_poster_url = ''
        widget.setCurrentIndex(widget.currentIndex()-7)
        #초기화

        #영화 정보들 다 초기화
        bookpage1.input_moviename.setText('')
        bookpage1.input_movietime.setText('')
        bookpage1.input_theater.setText('')

        #시간 선택 초기화
        for i in range(1, 3 + 1):
            for j in range(1, 4 + 1):
                btn = getattr(bookpage1, f"btn_{i}time{j}")
                btn.setText('')
                btn.setEnabled(False)

        for i in range(1, 9):
            getattr(bookpage2, f"btn_adt{i}").setChecked(False)
            getattr(bookpage2, f"btn_adt{i}").setStyleSheet("")
            getattr(bookpage2, f"btn_teen{i}").setChecked(False)
            getattr(bookpage2, f"btn_teen{i}").setStyleSheet("")

        

        bookpage2.lbl_selectmovie.setText('')
        bookpage2.lbl_selecttime.setText('')
        bookpage2.lbl_selecttheater.setText('')
        bookpage2.lbl_adtnum.setText('0')
        bookpage2.lbl_teennum.setText('0')
        bookpage2.input_adt.setText('0')
        bookpage2.input_teen.setText('0')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 🔒 여기 추가: 앱 전체에 Esc 무력화 필터 설치
    esc_blocker = EscBlocker()
    app.installEventFilter(esc_blocker)
    widget = QtWidgets.QStackedWidget()
    mainwindow = MainWindow()
    adminPage = AdminPage()
    searchpage = SearchPage()
    bookpage1 = BookPage1()
    bookpage2 = BookPage2()
    bookpage3 = BookPage3()
    bookpage4 = BookPage4()
    bookpage5 = BookPage5()
    userpayment = userPayment()
    guestpayment = guestPayment()
    bookpage1.resetLabelSignal.connect(bookpage2.resetLabel)
    bookpage2.resetLabelSignal.connect(bookpage3.resetLabel)
    widget.addWidget(mainwindow)
    widget.addWidget(adminPage)
    widget.addWidget(searchpage)
    widget.addWidget(bookpage1)
    widget.addWidget(bookpage2)
    widget.addWidget(bookpage3)
    widget.addWidget(bookpage4)
    widget.addWidget(bookpage5)
    widget.addWidget(userpayment)
    widget.addWidget(guestpayment)
    widget.show()
    app.exec_()
    
    # 결제 가격 두번뜸