import string
import re
from math import floor, ceil

from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class FormCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self,*args, **kwargs)
        self._codes=[]
    
    def showPage(self):
        self._codes.append(self._code)
        self._startPage()
    
    def save(self):
        page_num = 1
        total = len(self._codes)
        for c in self._codes:
            self._code = c 
            pg_size = self._pagesize
            self.setFont("Times-Roman", 10)
            txt = '%(num)s/%(total)s' % {
                    'num': page_num,
                    'total':total,
                    }
            char_len = self.stringWidth("O", 'Times-Roman', 10)
            x_start = (pg_size[0] - self.stringWidth(txt, 'Times-Roman',10) -
            char_len * 5)
            text_obj = self.beginText()
            text_obj.setTextOrigin(x_start, 30.0)
            text_obj.textOut(txt)
            self.drawText(text_obj)
            canvas.Canvas.showPage(self)
            page_num+=1
        self._doc.SaveToFile(self._filename, self)

class Form(object):
    def __init__(self, filename, font="Times-Roman", font_size=12):
        self.canvas = FormCanvas(filename, bottomup=0, pagesize=letter)
        self.text_obj = self.canvas.beginText()
        self._x, self._y = self.text_obj.getCursor()
        self.margin = .25 * inch 
        self.fm_name = None

        self.set_font(font, font_size)
        self.spacing = self.font_size * 1.60
 
        self._page_width, self._page_height = letter
        self.set_border(0.5, 0.5, 0.5, 0.5)
        self._start_left = self._left
        
        self._last_multi = False
        self.form_name_prefix = None

        self.header_footer = []

    def _draw_box(self, x1, y1, x2, y2, line_width=.25):
        self.canvas.setLineWidth(line_width)
        self.canvas.line(x1, y1, x2, y1)
        self.canvas.line(x1, y1, x1, y2)
        self.canvas.line(x1, y2, x2, y2)
        self.canvas.line(x2, y1, x2, y2)

    def print_const_name(self, name=None):
        if name != None:
            self.form_name_prefix = name
            
    
    def set_font(self, font, font_size=12):
        '''Change the font type and size.
        
        Arguments:
        font -- The string specifyig the font to use when rendering text. Must
            be recognized by ReportLab in order to render correctly.
        
        Keyword Arguments:
        font_size -- Number specifying the size of the font to use when
            rendering text. Default is 12.
        '''
        self.font = font
        self.font_size = font_size
        self.text_obj.setFont(self.font,self.font_size)
        self.char_len = self.canvas.stringWidth("O", self.font, self.font_size)
        self.indent = self.char_len 
        self._y = self._y - self.font_size + font_size
        self.font_size = font_size
        self.text_obj.setTextOrigin(self._x, self._y)
        self._x, self._y = self.text_obj.getCursor()
    
    def set_border(self, top, bottom, left, right):
        '''Set the margins of the Form. 

        Arguments:
        top -- Number specifying in inches the size of the top margin.
        bottom -- Number specifying in inches the size of the bottom margin.
        left -- Number specifying in inches the size of the left margin.
        right -- Number specifying in inches the size of the right margin.
        '''
        self._left = left * inch
        self._top = top * inch
        self._bottom = self._page_height - (bottom * inch)
        self._right = self._page_width - (right * inch)
        self._x = self._left
        self._y = self._top + self.font_size
        self.text_obj.setTextOrigin(self._x, self._y)
   
    def show_border(self):
        '''Print the margin border on the current page.
        '''
        self._draw_box(self._start_left, self._top, self._right, self._bottom)

    def render(self):
        '''Render the PDF. Call when finished constructing the form.
        '''
        self.canvas.drawText(self.text_obj)
        self.canvas.showPage()
        self.canvas.save()
        return self.canvas   
 
    def add_total_page_num(self):
        '''Add the (current page number)/(total page number) to header.
        '''
        self.page_num=True

    def _add_continued_footer(self):
        self.set_footer("(Continued on next page.)", "right", ("Times-Italic",
        12))

    def new_page(self, break_text=False):
        '''Go to the next page and set header/footer.

        Arguments:
        break_text -- Boolean value. If set to True, 'continued on the next
        page.' is added to the footer.
        '''
        if break_text:
            self._add_continued_footer()
        self.canvas.drawText(self.text_obj)
        self.canvas.showPage()
        self.text_obj = self.canvas.beginText()
        self.set_font(self.font, self.font_size)
        self.text_obj.setTextOrigin(self._left, self._top + self.font_size)
        self._x, self._y = self.text_obj.getCursor()
        
        for x in self.header_footer:
            self._set_header_footer(x.get('text', None), x.get('location',None),
                x.get('headfoot', None), x.get("font"))

    def new_line(self, **kwargs):
        '''Move the cursor to beginning of the next line.
        '''
        break_text = kwargs.get('break_text', False)
        spacing = kwargs.get('spacing', self.spacing)
        if self._y + spacing >= self._bottom:
            self.new_page(break_text)
        else:
            self.text_obj.setTextOrigin(self._left, self._y + spacing)
            self._x, self._y = self.text_obj.getCursor()
 
    def _set_header_footer(self,text_prt,location,headfoot,font):
        if location == 'left':
            x_start = self.margin
        elif location == 'center':
            len_text = self.canvas.stringWidth(text_prt, self.font,
                self.font_size)
            x_start = (self.page_width - len_text) / 2.0
        elif location == 'right':
            len_text = self.canvas.stringWidth(text_prt, self.font,
                self.font_size)
            x_start = self._page_width - len_text - self.char_len - self.margin
        else:
            raise ValueError("Document: %(hf_location)s is not a valid choice \
                for header or footer. Please specify 'left', 'right' or \
                'center'." %{hf_location : location})
        
        if headfoot == 'header':
            y_start = self.font_size + self.margin
        elif headfoot == 'footer':
            y_start = self._page_height - self.margin
        else:
            raise ValueError("%(placement)s is not a valid option. Please \
                select 'header' or 'footer'." %{placement : headfoot})
        fnt = self.font
        fnt_sz = self.font_size
        self.set_font(font[0], font[1])

        self.text_obj.setTextOrigin(x_start, y_start)
        self.text_obj.textOut(text_prt)
        self.text_obj.setTextOrigin(self._x, self._y)
        self.set_font(fnt, fnt_sz)
    
    def remove_header_footer(self, text):
        '''Remove the header/footer with the associated text. If text is not a
        current header/footer do nothing.

        Arguments:
        text -- The string to be removed from the header or footer.
        '''
        for x in self.header_footer:
            if x.has_key(text):
                self.header.remove(x)
    
    def set_header(self, text, location, font, all_pg=False):
        '''Specify a header for the Document
        
        Arguments:
        text -- The string that will be set as the header.
        location -- Specifies where the header should be placed. Can either be
            'left', 'center' or 'right' 
        all_pg -- Boolean value specifing whether the header should be on all
            pages.
        '''
        self._set_header_footer(text, location, 'header', font) 
        if all_pg:
            self.header_footer.append({'text':text, 
                                       'location': location,
                                       'headfoot': 'header',
                                       'font': font,
                                     })

    def set_footer(self, text, location, font, all_pg=False):
        '''Specifies the footer for the Document
        
        Arguments:
        text -- The string that will be set as the footer.
        location -- Specifies where the footer should be placed. Can either be
            'left', 'center' or 'right' 
        all_pg -- Boolean value specifing whether the footer should be on all
            pages.

        '''
        self._set_header_footer(text, location, 'footer', font) 
        if all_pg:
            self.header_footer.append({'text':text, 
                                       'location': location,
                                       'headfoot': 'footer',
                                       'font':  font,
                                     })

    def print_text(self, text, **kwargs):
        '''Print the text to the current cursor(x,y) position, making sure 
        it fits within the page borders and will word wrap where necessary.

        Arguments:
        text -- The string to print to the form.
        '''
        newline = re.compile("<BR>")

        text = text.strip() 
        len_txt = self.canvas.stringWidth(text, self.font, self.font_size)
        if len_txt > self._right - self._left:
            if not self._x == self._left:
                self.new_line(**kwargs)
            words = text.split()
            len_words = map(lambda wrd: self.canvas.stringWidth(wrd, self.font,
                self.font_size), words)
            line = 0
            line_str = ""
            while len(words) > 0:
                word = words.pop(0) + ""
                if newline.match(word):
                    self.text_obj.textOut(line_str)
                    self.new_line()
                    line_str = ""
                else:
                    new_wrd_len = self.canvas.stringWidth(word,self.font,
                            self.font_size)
                    wrd_len = self.canvas.stringWidth(line_str, self.font,
                        self.font_size) 
                    if self._x + wrd_len + new_wrd_len > self._right:
                        self.text_obj.textOut(line_str)
                        self.new_line(**kwargs)
                        line_str = ""
                    line_str+=word + " "
            if not line_str == "": 
                self.text_obj.textOut(line_str)
                line_str = line_str.strip()
                self.text_obj.setTextOrigin(self._x +
                    self.canvas.stringWidth(line_str, self.font, self.font_size), self._y)
                self._x, self._y = self.text_obj.getCursor()
        else:
            if self._last_multi == True:
                if self._x != self._left:
                    self.new_line()
                self._last_multi = False
            lines = newline.split(text)
            while len(lines) > 1:
                line = lines.pop(0)
                self.text_obj.textOut(line)
                self.text_obj.setTextOrigin(self._x +
                    self.canvas.stringWidth(line, self.font, self.font_size), self._y)
                self._x, self._y = self.text_obj.getCursor()
                self.new_line()
            line = lines.pop()
            self.text_obj.textOut(line)
            self.text_obj.setTextOrigin(self._x +
                self.canvas.stringWidth(line, self.font, self.font_size), self._y)
            self._x, self._y = self.text_obj.getCursor()

    def form_name(self, name, font_name="Times-BoldItalic", font_size=20):
        '''Add form name to the form.

        Arguments:
        name -- The string that will be added as the form name.
        
        Keyword Arguments:
        font_name -- The name of the font to render the form name. Make sure
            it is accepted by ReportLab in order to work properly.
        font_size -- Number specifying the size of the font to use to render
            the name.
        '''
        if self.form_name_prefix != None:
            name = self.form_name_prefix + " - " + name
        self.fm_name = name
        old_ft = self.font
        old_ft_sz = self.font_size
        self.set_font(font_name, font_size)
        self.print_text(name)
        self.new_line()
        self.text_obj.setTextOrigin(self._start_left, self._y - self.spacing/2.0)
        self._x, self._y = self.text_obj.getCursor()
        
        self.canvas.setLineWidth(2.5)
        self.canvas.line(self._x, self._y, self._right, self._y)
        self.text_obj.setTextOrigin(self._start_left, self._y + (inch * .05))
        self._x, self._y = self.text_obj.getCursor()
        
        self.canvas.setLineWidth(1)
        self.canvas.line(self._x, self._y, self._right, self._y)
        self.text_obj.setTextOrigin(self._start_left, self._y + self.spacing)
        self._x, self._y = self.text_obj.getCursor()
        self.set_font(old_ft, old_ft_sz)

    def section_name(self, name, font_name="Times-Bold", font_size=14):  
        '''Add section name to the form.

        Arguments:
        name -- The string that will be added as the section name.
        
        Keyword Arguments:
        font_name -- The name of the font to use to render the section name. Make sure
            it is accepted by ReportLab in order to work properly.
        font_size -- Number specifying the size of the font to use to render the name.
        '''

        old_ft = self.font
        old_ft_sz = self.font_size
        self.set_font(font_name, font_size)
        if self._x != self._left:
            if self._y + self.spacing * 2 >= self._bottom:
                self.new_page()
            else:
                self.text_obj.setTextOrigin(self._start_left, self._y + self.spacing)
                self._x, self._y = self.text_obj.getCursor()
        else:
            self.text_obj.setTextOrigin(self._start_left, self._y)
            self._x, self._y = self.text_obj.getCursor()
        if self._y + self.spacing * 2 >= self._bottom:
            self.new_page()
        self.print_text(name)
        self.new_line() 
        self.text_obj.setTextOrigin(self._start_left, self._y - self.spacing/1.5)
        self._x, self._y = self.text_obj.getCursor()
        
        self.canvas.setLineWidth(1.5)
        self.canvas.line(self._x, self._y, self._right, self._y)
        self.set_font(old_ft, old_ft_sz)
        self.text_obj.setTextOrigin(self._left, self._y + self.spacing)
        self._x, self._y = self.text_obj.getCursor()

    def start_indent(self):
        '''Indent the start of the line. Will return if already in the center
        of the page.
        '''
        if self._left + self.indent >= (self._right - self._left)/2.0:
            return
        if self._x != self._left:
            self.new_line()
        self._left = self._left + self.indent
        self.text_obj.setTextOrigin(self._left, self._y)
        self._x, self._y = self.text_obj.getCursor()
        
    def stop_indent(self):
        '''Unindent the start of the line. Will not go past the margin borders.
        '''
        if self._left == self.margin:
            return
        if self._x != self._left:
            self.new_line()
        self._last_multi = False
        self._left = self._left - self.indent  
        self.text_obj.setTextOrigin(self._left, self._y)
        self._x, self._y = self.text_obj.getCursor()
  
    def _date_space(self, not_start=True):
        space = self.char_len * .75
        self.text_obj.setTextOrigin(self._x + space, self._y)
        self._x, self._y = self.text_obj.getCursor()

    def _time_space(self, not_start=True):
        space = self.char_len * .75
        if not_start:
            self.text_obj.setTextOrigin(self._x + space/2.0, self._y - space/2.0)
            self._x, self._y = self.text_obj.getCursor()
            self.text_obj.textOut(':')
            self.text_obj.setTextOrigin(self._x + space, self._y + space/2.0)
            self._x, self._y = self.text_obj.getCursor()
        else:
            self.text_obj.setTextOrigin(self._x + space, self._y)
            self._x, self._y = self.text_obj.getCursor()

    def _draw_txt_box(self, txt_format, space_callback):
        self.canvas.setLineWidth(.5)
        up_y  = self._y - self.font_size
        space = self.char_len * .75
        line_len = self.char_len * 2
        last_l = None
        for l in txt_format:
            if last_l == None:
                space_callback(self, False)
                last_l = l
            elif last_l != l:
                space_callback(self)
                last_l = l
            self.canvas.line(self._x, self._y, self._x, up_y)
            self.canvas.line(self._x,self._y,self._x + line_len ,self._y)
            self.canvas.line(self._x + line_len, self._y, self._x + line_len,
                up_y)
            self.canvas.setFillGray(0.90)
            start = (line_len) / 4.0
            self.canvas.drawString(self._x + start  , self._y - self.char_len
                /3.0, string.upper(l))
            self.canvas.setFillGray(0.0)
            self.text_obj.setTextOrigin(self._x + line_len, self._y)
            self._x, self._y = self.text_obj.getCursor()
        self.text_obj.setTextOrigin(self._x + self.char_len, self._y)
        self._x, self._y = self.text_obj.getCursor()
    
    def _box_element(self, text, txt_format, format_callback):
        len_txt = self.canvas.stringWidth(text, self.font, self.font_size)
        len_date = len(txt_format) * self.char_len * 2
        
        if self._x != self._left:
            if len_txt + len_date + 2 * self.char_len + self._x > self._right:
                self.new_line()    
        self.print_text(text)
        self._draw_txt_box(txt_format, format_callback)

    def date_element(self, text, date_format='mmddyy'):
        '''Add date element to the form.

        Arguemnts:
        text -- The string to be rendered with the date boxes.
        
        Keyword Arguments:
        date_format -- The string specifying the format for the date boxes. A
            space will be placed between different letters.
        '''
        self._box_element(text, date_format, Form._date_space)
         
    def time_element(self, text, time_format='hhmm'):
        '''Add time element to the form.

        Arguemnts:
        text -- The string to be rendered with the time boxes.
        time_format -- The string specifying the format for the time boxes. A
            colon will be placed between different letters.
        '''
        self._box_element(text, time_format, Form._time_space)
       
    def text_element(self, text, line_len = 1):
        '''Add a text element to the form.

        Arguments:
        text -- The text to render with the text line.
        line_len -- Number specifying the length of the blank line in inches. 
        '''
        len_ques = self.canvas.stringWidth(text, self.font, self.font_size)
        line = line_len * inch
        self.canvas.setLineWidth(1)
        if self._x != self._left:
            if self._x + len_ques + line + self.char_len > self._right:
                self.new_line()
        
        self.print_text(text)
        self.canvas.setLineWidth(.5)
        self._x, self._y = self.text_obj.getCursor()
        if self._x + line > self._right:
            if line > self._right - self._left:
                while line > 0:
                    if line + self._x > self._right:
                        self.canvas.line(self._x, self._y, self._right, self._y)
                        self.new_line()
                        line = line - (self._right-self._x)
                    else:
                        self.canvas.line(self._x , self._y, self._x + line,
                            self._y)
                        self.new_line()
                        line = 0
            else:
                self.new_line()
                self.canvas.line(self._x, self._y, self._x + line, self._y)
                self.new_line()
        else:
            self.canvas.line(self._x, self._y, self._x + line, self._y)
            self.text_obj.setTextOrigin(self._x + line + self.char_len,
                self._y)
            self._x, self._y = self.text_obj.getCursor()
        
    def _draw_radio_button(self, size=12):
        radius = size / 3
        self.canvas.setLineWidth(.5)
        self.canvas.circle(self._x, self._y-radius, radius)
        self.text_obj.setTextOrigin(self._x + radius * 1.5, self._y)
        self._x, self._y = self.text_obj.getCursor()
    
    def _draw_checkbox(self, size=7):
        self.canvas.setLineWidth(0.5)
        self.canvas.rect(self._x, self._y - (self.font_size / 1.75), size, size, stroke=1)
        self._x = self._x + size * 1.25
        self.text_obj.setTextOrigin(self._x, self._y)
        self._x, self._y = self.text_obj.getCursor()
 
    def _multi_choice(self, text, choices, shape_callback, size=12):
        text = text.strip()
        num_opts = len(choices)
        len_options = map(lambda choice: self.canvas.stringWidth(choice, self.font, self.font_size), choices)
        sorted_len = sorted(len_options, reverse=True)
        total_len = sum(len_options) + self.char_len * (num_opts + 1)
        ques_len = self.canvas.stringWidth(text, self.font, self.font_size) 

        #Print Multiple Choice Question on same line if possible
        if (total_len + self.char_len * (num_opts + 1) + ques_len <=
            self._right - self._left):
            if (self._x + total_len + self.char_len * (num_opts + 1) + ques_len
                > self._right):
                if self._x != self._left:
                    self.new_line()
            self.print_text(text, break_text=True)
            self.text_obj.setTextOrigin(self._x + self.char_len * 2, self._y)
            self._x, self._y = self.text_obj.getCursor()
            i = 0
            for c in choices:
                    shape_callback(self,size)
                    self.text_obj.textOut(c)
                    self.text_obj.setTextOrigin(self._x + len_options[i] +
                        self.char_len * 1.5, self._y)
                    i += 1
                    self._x, self._y = self.text_obj.getCursor()
        else:
            if self._x != self._left:
                self.new_line(break_text=True)
            self.print_text(text, break_text=True)
            self.new_line(break_text=True)
            
            #If all choices will fit on the same line then equally space
            if (sorted_len[0] * num_opts) + (num_opts * size) + (num_opts * self.char_len) < self._right - self._left:
                size_space = (self._right - (self._left + size)) / (num_opts * 1.0)
            else:
                #Find largest choice and base columns off that
                size_space = sorted_len[0] + self.char_len + size
        
            num_per_row = floor((self._right - self._left) /(size_space) )
            if num_per_row == 0:
                num_per_row = 1
        
            rows = ceil(num_opts / num_per_row)   

            index = 0
            self.text_obj.setTextOrigin(self._x + self.char_len, self._y)
            self._x, self._y = self.text_obj.getCursor()
            for n in range(int(rows)):
                for m in range(int(num_per_row)):
                    shape_callback(self,size)
                    self.text_obj.textOut(choices[index])
                    self.text_obj.setTextOrigin(self._x + size_space - size, self._y)
                    self._x, self._y = self.text_obj.getCursor()
                    index += 1
                    if index > num_opts - 1:
                        break
                if n != int(rows) - 1:
                    if self._y + self.spacing >= self._bottom:
                        self.new_page(True)
                        self.text_obj.setTextOrigin(self._x + self.char_len, self._y)
                        self._x, self._y = self.text_obj.getCursor()
                    else:
                        self.text_obj.setTextOrigin(self._left + self.char_len, self._y
                            + self.spacing)
                        self._x, self._y = self.text_obj.getCursor()
            if self._left + self.char_len < self._x:
                self._last_multi = True
            else:
                self.text_obj.setTextOrigin(self._left - self.char_len, self._y)
                self._x, self._y = self.text_obj.getCursor()

    def check_box_element(self, text, choices):
        '''Add a checkbox element to the form.

        Arguments:
        text -- The string that will render as the question text.
        choices -- An array containing the choices as strings to be rendered as
            individual checkbox choices. 
        '''
        self._multi_choice(text, choices, Form._draw_checkbox, size=7)
    
    def radio_element(self, text, choices):
        '''Add a radio button element to the form.

        Arguments:
        text -- The string that will render as the question text.
        choices -- An array containing the choices as strings to rendered as
            individual radio button choices. 
        '''
        self._multi_choice(text, choices, Form._draw_radio_button, size=12)
    
    def _draw_slider(self, choices):
        assert(len(choices)==3)
        line_len = (self._right - self._start_left) /2.0

        if self._x + line_len > self._right: 
            self.new_line()
            self.new_line()
            self.text_obj.setTextOrigin(self._x + line_len/2.0, self._y)
            self._x, self._y = self.text_obj.getCursor()
        
        up_y = self._y - (self.font_size / 3.0)
        down_y = self._y + (self.font_size / 3.0)
        line_start = self._x
        
        middle_x = (line_len / 2.0) + self._x
        self.canvas.setLineWidth(.5)
        self.canvas.line(self._x, self._y, self._x + line_len, self._y)
        
        self.canvas.line(self._x, up_y, self._x, down_y)
        self.canvas.line(self._x + line_len, up_y, self._x + line_len, down_y)
        self.canvas.line(middle_x, up_y, middle_x, down_y)
        
        #TODO: make sure that the string text fits into a fixed with space. If
        #not word wrap.
        x = self._x - self.canvas.stringWidth(choices[0], self.font,
                self.font_size) / 2.0
        self.text_obj.setTextOrigin(x, self._y - self.font_size /2.0)
        self._x, self._y = self.text_obj.getCursor()
        self.print_text(choices[0])

        x = line_start + line_len - self.canvas.stringWidth(choices[2], self.font,
                self.font_size) / 2.0
        self.text_obj.setTextOrigin(x, self._y)
        self._x, self._y = self.text_obj.getCursor()
        self.print_text(choices[2])
       
        x = middle_x - self.canvas.stringWidth(choices[1], self.font,
                self.font_size) / 2.0
        self.text_obj.setTextOrigin(x, self._y)
        self._x, self._y = self.text_obj.getCursor()
        self.print_text(choices[1])
        
        self.text_obj.setTextOrigin(x, self._y + self.font_size/2.0)
        self._x, self._y = self.text_obj.getCursor()

    def slider_element(self, text, choices):
        '''Add a slider element to the form.
        
        Arguments:
        text -- The string that will render as the question text.
        choices -- String array containing 3 choices that will render along the
            top of the slider.
        '''
        if self._x != self._left:
            self.new_line()
        
        self.print_text(text)
        self.text_obj.setTextOrigin(self._x + self.char_len * 6, self._y)
        self._x, self._y = self.text_obj.getCursor()
        
        self._draw_slider(choices)
        old_ft_sz = self.font_size 
        self.font_size = 8
        self.set_font(self.font,old_ft_sz)
        self.new_line()

    def note_element(self, text, line_nums=8):
        '''Add a note element to the form.
        
        Arguments:
        text -- The string that will render as the question text.
        
        Keyword Arguments:
        line_nums -- Integer specifying the number of lines in the note box.
        '''
        if self._x != self._left:
            self.new_line()
        if self._y + (self.spacing * line_nums + 1) >= self._bottom:
            self.new_page()
        self.print_text(text)
        if self._x!=self._left:
            self.new_line(spacing=inch*.05)
        self._draw_box(self._x + self.char_len, self._y, self._right, self._y +
            (line_nums * self.spacing)) 
        self.text_obj.setTextOrigin(self._left, self._y + (self.spacing *
            (line_nums)))
        self._x, self._y = self.text_obj.getCursor()
        self.new_line()

    def SaveToFile(self, filename, pdfdata):
        '''Save the rendered pdf to a file.

        Arguments:
        filename -- The name of the file to save the pdf as.
        pdfdata -- The pdfdata to write to the file.
        '''
        if hasattr(getattr(filename, "write", None), '__call__'):
            myfile = 0
            f = filename
            filename = utf8str(getattr(filename, 'name', ''))
        else:
            myfile = 1
            filename = utf8str(filename)
            f = open(filename, 'wb')
        f.write(pdfdata)
