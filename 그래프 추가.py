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
        self.loadCount()

        self.ax.clear()
        self.ax.bar(self.title, self.count, color='skyblue')
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
     
    def loadCount(self):
        self.title = []
        self.count =[]
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
            self.count.append(i[1])
            self.title.append(i[0])
        print(self.title)
        print(self.count)

    def gotomain(self):
        widget.setCurrentIndex(widget.currentIndex()-1)