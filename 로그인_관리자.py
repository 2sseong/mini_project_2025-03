# 총 매출 조회
def loadData():
    adminPage.lbl_total.setText("")
    conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
    cursor = conn.cursor()
    conn.begin() 
    query = '''
       SELECT to_char(SUM(amount), '999,999,999,999') 
         FROM pay
            '''
    cursor.execute(query)
    total = cursor.fetchone()[0]
    adminPage.lbl_total.setText(f'{total}원')
 
# 인원 조회
def loadCount():
    title = []
    count =[]
    conn = oci.connect(f'{username}/{password}@{host}:{port}/{sid}')
    cursor = conn.cursor()
    conn.begin() 
    query = '''
            SELECT m.title
                , count(*)
            FROM MOVIEINFO m 
                , SCHEDULE s 
                , TICKETINFO t 
                , TICKETSEAT i
            WHERE m.MOVIE_ID = s.MOVIE_ID
            AND s.schedule_id = t.schedule_id
            AND t.TICKET_ID  = i.TICKET_ID
            GROUP BY m.title
            ORDER BY m.title
            '''
    cursor.execute(query)
    for i in cursor.fetchall():
        count.append(i[1])
        title.append(i[0])
    cursor.close()
    conn.close()
    return count, title
def  graphSales():
    adminPage.canvas = FigureCanvas(Figure(figsize=(5, 3)))
    adminPage.ax = adminPage.canvas.figure.add_subplot(111)
    layout = QVBoxLayout(adminPage.graph_widget)
    layout.addWidget(adminPage.canvas)
    adminPage.ax.clear()
    counts, titles = loadCount()
    print(counts,titles)
    adminPage.ax.bar(titles, counts, color='skyblue')
    adminPage.ax.set_title('영화별 예매 수')
    adminPage.ax.set_xlabel('영화 제목')
    adminPage.ax.set_ylabel('예매 수')
    adminPage.ax.tick_params(axis='x', rotation=45)
    adminPage.canvas.draw()
  
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("admin_login.ui", self)

        self.btn_ok.clicked.connect(self.check_login)
        
    def check_login(self):
        user_id = self.user_id.text()
        user_pw = self.user_pw.text()

        #관리자 계정 로그인
        if user_id == "admin" and user_pw == "1234":
            QMessageBox.information(self, "로그인 성공", "로그인에 성공했습니다!")
            loadData()
            loadCount()
            graphSales()
            self.accept()
            
        else:
            QMessageBox.warning(self, "로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")

class AdminPage(QDialog):
    def __init__(self):
        super(AdminPage, self).__init__()
        loadUi("adminpage.ui", self)

        self.btn_go_to_main.clicked.connect(self.gotomain)

    def gotomain(self):
        widget.setCurrentIndex(widget.currentIndex()-1)