from base_form import Form
from datetime import date

class RedcapForm(Form):
    def __init__(self, *args, **kwargs):
        Form.__init__(self,*args, **kwargs)
        self._header_box = []

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

        for f in self._header_box:
            self.set_font(f[2][0], f[2][1])
            if f[3]:
                f[1](self,f[0],f[3])
            else:
                f[1](self,f[0])
        x, y = self.text_obj.getCursor()
        Form._draw_box(self,self._left-5, 20, self._right+5 , y+ self.spacing/2.0)
        self._left = lft
        self._right = rt
        self.text_obj.setTextOrigin(old_x, old_y)
        self._x, self._y = self.text_obj.getCursor()
        self.set_font(old_fnt, old_fnt_size)
    
    def no_print(self, question):
        pass

    def new_page(self, break_text=False):
        if len(self._header_box):
            self.print_header_box()
        Form.new_page(self,break_text)

    def render(self):
        if len(self._header_box):
            self.print_header_box()
        return Form.render(self)

    def integer_element(self, question):
        Form.text_element(self, question, .5)

    def number_element(self, question):
        Form.text_element(self, question, 1)
    
    def text_element(self, question):
        Form.text_element(self, question, 2)
    
    def date_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')

    def date_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
    
    def time(self, question):
        Form.time_element(self, question, 'hhmm')

    def time_mm_ss(self, question):
        Form.time_element(self, question, 'mmss')

    def datetime_mdy(self, question):
        Form.date_element(self, question, 'mmddyyyy')
        Form.time_element(self, '', 'hhmm')

    def datetime_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
        Form.time_element(self, '', 'hhmm')

    def datetime_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')
        Form.time_element(self, '', 'hhmm')

    def datetime_sec_dmy(self, question):
        Form.date_element(self, question, 'ddmmyyyy')
        Form.time_element(self, '', 'hhmmss') 

    def datetime_sec_mdy(self, question):
        Form.date_element(self, question, 'mmddyyyy')
        Form.time_element(self, '', 'hhmmss') 

    def datetime_sec_ymd(self, question):
        Form.date_element(self, question, 'yyyymmdd')
        Form.time_element(self, '', 'hhmmss') 

    def descriptive_element(self, text):
        Form.text_element(self, text, 0)

    def truefalse_element(self, text):
        Form.radio_element(self, text, ['True','False']) 
    
    def yesno_element(self, text):
        Form.radio_element(self, text, ['Yes','No']) 

    def dropdown_element(self, text, choices):
        Form.radio_element(self, text, choices)

    def note_element(self, text):
        Form.note_element(self, text, 3)

    def sql_element(self, text):
        Form.text_element(self,question, 2)

