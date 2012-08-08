from base_form import Form
from datetime import date

class RedcapForm(Form):
    def __init__(self, *args, **kwargs):
        self.multiline = args[1]
        name= args[0]
        Form.__init__(self,name, **kwargs)
        self._header_box = []
        self.headerflag=False

    def setup(self):
        self.add_to_header_box("Clinician Name", RedcapForm.text_element,
            ('Times-Roman', 11))
        self.add_to_header_box("Study ID", RedcapForm.number_element,
            ('Times-Roman', 11))
        self.add_to_header_box("Date", RedcapForm.date_element,
            ('Times-Roman', 11))
        self.set_border(1.0, 0.5, 0.5, 0.5)
        self.set_header("Confidential", 'left',('Times-Italic', 12), True)
        cur_date = date.today();
        self.set_footer("Form generated on " + str(cur_date.month) + "/" +
                str(cur_date.day) + "/" +
                str(cur_date.year), 'left',('Times-Roman', 10), True)
        self.set_font('Times-Roman', 11)

    def add_to_header_box(self, element, callback,font, choices=None):
        self._header_box.append((element, callback,font, choices))

    def print_header_box(self):
        lft = self._left
        rt = self._right
        self._left = 275
        self._right = 540
        old_x, old_y = self.text_obj.getCursor()
        old_fnt = self.font
        old_fnt_size = self.font_size
        self.text_obj.setTextOrigin(self._left, 20 + self.spacing)
        self._x, self._y = self.text_obj.getCursor()
        self.headerflag=True
        for f in self._header_box:
            self.set_font(f[2][0], f[2][1])
            if f[3]:
                f[1](self,f[0],f[3])
            else:
                f[1](self,f[0])
        self.headerflag=False
        x, y = self.text_obj.getCursor()
        Form._draw_box(self,self._left-5, 20, self._right+5 , y+ self.spacing/2.0)
        self._left = lft
        self._right = rt
        self.text_obj.setTextOrigin(old_x, old_y)
        self._x, self._y = self.text_obj.getCursor()
        self.set_font(old_fnt, old_fnt_size)
    
    def multiline_check(self):
        if not self.headerflag:
            if not self.multiline:
                if self._x != self._left:
                    self.new_line()

    def no_print(self, question):
        pass

    def new_page(self, break_text=False):
        if not self.is_new_page():
            if len(self._header_box):
                self.print_header_box()
            Form.new_page(self,break_text)

    def render(self):
        if len(self._header_box):
            self.print_header_box()
        return Form.render(self)

    def integer_element(self, question):
        Form.text_element(self, question, .5)
        self.multiline_check() 

    def number_element(self, question):
        Form.text_element(self, question, 1)
        self.multiline_check() 
    
    def text_element(self, question):
        Form.text_element(self, question, 2)
        self.multiline_check() 
    
    def date_element(self, question):
        Form.date_element(self, question)
        self.multiline_check() 
    
    def date_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')
        self.multiline_check() 

    def date_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
        self.multiline_check() 
    
    def time(self, question):
        Form.time_element(self, question, 'hhmm')
        self.multiline_check() 

    def time_mm_ss(self, question):
        Form.time_element(self, question, 'mmss')
        self.multiline_check() 

    def datetime_mdy(self, question):
        Form.date_element(self, question, 'mmddyyyy')
        Form.time_element(self, '', 'hhmm')
        self.multiline_check() 

    def datetime_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
        Form.time_element(self, '', 'hhmm')
        self.multiline_check() 

    def datetime_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')
        Form.time_element(self, '', 'hhmm')
        self.multiline_check() 

    def datetime_sec_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
        Form.time_element(self, '', 'hhmmss') 
        self.multiline_check() 

    def datetime_sec_mdy(self, question):
        Form.date_element(self, question, 'mmddyyyy')
        Form.time_element(self, '', 'hhmmss') 
        self.multiline_check() 

    def datetime_sec_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')
        Form.time_element(self, '', 'hhmmss') 
        self.multiline_check() 

    def descriptive_element(self, text):
        Form.text_element(self, text, 0)
        self.multiline_check() 

    def truefalse_element(self, text):
        Form.radio_element(self, text, ['True','False']) 
        self.multiline_check() 
    
    def yesno_element(self, text):
        Form.radio_element(self, text, ['Yes','No']) 
        self.multiline_check() 

    def radio_element(self, text, choices):
        Form.radio_element(self, text, choices)
        self.multiline_check() 

    def check_box_element(self, text, choices):
        Form.check_box_element(self, text, choices)
        self.multiline_check() 

    def dropdown_element(self, text, choices):
        Form.radio_element(self, text, choices)
        self.multiline_check() 

    def note_element(self, text):
        Form.note_element(self, text, 3)
        self.multiline_check() 

    def sql_element(self, text):
        Form.text_element(self, text, 2)
        self.multiline_check() 
    
    def print_grey(self, line, text):
        self.canvas.setFillGray(0.90)
        self.canvas.drawString(self._x + self.char_len/2.0  , self._y - self.char_len / 3.0, text)
        self.canvas.setFillGray(0.0)

    def print_grey_txt_field(self,text, grey_txt):
        len_ques = self.canvas.stringWidth(text, self.font, self.font_size)
        line = self.canvas.stringWidth(grey_txt, self.font, self.font_size) + self.char_len * 2.0
        self.canvas.setLineWidth(1)
        if self._x != self._left:
            if self._x + len_ques + line + self.char_len > self._right:
                self.new_line()

        self.print_text(text)
        self.print_grey(line, grey_txt)
        self.print_text_line(line)

    def calculated_element(self, text):
        self.print_grey_txt_field(text, 'CALCULATED')
