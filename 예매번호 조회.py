class SearchPage(QDialog):
    def __init__(self):
        super(SearchPage,self).__init__()
        loadUi('searchpage.ui',self)

        self.btn_gotohome.clicked.connect(self.gotohome)
        self.btn_search.clicked.connect(self.startsearch)

    def gotohome(self):
        widget.setCurrentIndex(widget.currentIndex()-1)
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