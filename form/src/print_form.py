#!/usr/bin/env python
import sys
import re
import httplib
import string
import string
import zipfile
from glob import glob
import os
import inspect
from ConfigParser import ConfigParser
try:
    import xml.etree.cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        try:
            import cElementTree as etree
        except ImportError:
            import elementtree.ElementTree as etree

from redcap_form import RedcapForm
from logic_parsers import LogicParser

class ArgumentError(Exception):
    ''' Error raised when the wrong number/type of arguments are used.
    '''
    def __init__(self, msg):
        self.msg = msg
        print msg

class ConstraintError(Exception):
    ''' Error raised when the constraint section is not in the constraint file
    supplied.
    '''
    def __init__(self, msg, const):
        self.msg = msg
        self.const = const
        print msg

def clean_html(text):
    '''Return a string with the html elements removed.
    
    Arguments:
    text -- The text to remove html tags from.
    '''
    br = re.compile('< ?br ?/?>')
    text = br.sub(" <BR> ",text)
    asci_newline = re.compile('\n')
    text = asci_newline.sub(" <BR> ", text)
    bold = re.compile('</? ?[bB] ?>')
    text = bold.sub(' [[B]] ', text)
    tags=re.compile('<\s?/?[\sa-zA-Z=\'\"#0-9]*>')
    text = tags.sub(' ', text)
    return text

class PdfForm(object):
    def __init__(self, xml_file, config_file=None):
        self.tree = etree.parse(xml_file)
        self.cur_form = None
        self.multiline=True
        self.all_same_page=False

        self.doc = None
        self.indent_stack = {}
        self.logic_parser = LogicParser()
        self.to_print = []

        if config_file != None:
            self.config = ConfigParser()
            self.config.read(config_file)
        self._indent = True
        self.print_const_name=None

    def revert_indent_val(self):
        self._indent = not self._indent

    def add_constraint_list(self, const_section):
        '''If  proceessed without running add_constraint_list
        then will print all forms and elements in the project.

        Arguments:
        const_section -- The section in the config_file to use along with
            the base seciton
        '''
        multiline=True
        if not self.config:
            raise ValueError("self.config is %(self.config)s: Please set the config file before adding constraint." %({'config': self.config, 
                                                }))
        sections = ['base', const_section]
        for sec in sections:
            if self.config.has_section(sec):
                for name, vals in self.config.items(sec):
                    if name == '__print_name':
                        if vals == 'True':
                            self.print_const_name=const_section
                    elif name == '__multiline':
                        self.multiline = eval(vals)
                    elif name == '__all_same_page':
                        self.all_same_page = eval(vals)
                    elif name != '__forms':
                        self.logic_parser.add_constraint(name, eval(vals))
            else:
                if sec != 'base':
                    raise ConstraintError('%(sec)s is not in the constraint file.', sec);


    def _get_choices(self, choices):
        ''' Return a list of valid choices for the current question.

        Arguments:
        choices -- the string from REDCap data dictionary containing the
        choices.
        '''
        vals = choices.split("\\n")
        if len(vals) > 1:
            return map(lambda c: c.lstrip(' 0123456789').lstrip(',').strip(' '), vals)
        else:
            vals = choices.split("|", 2)
            if len(vals) > 1:
                return vals
            elif len(vals) == 1:
                one = re.match("\s?[0-9.-]*\s?,\s?(.*)",vals[0]);
                if one:
                    return [one.group(1)] 
        return None

    def _get_level(self, names):
        ''' Return the set of all the field names that the current field is
        branched under

        Arguments:
        names -- The branching logic string from the redcap export
        '''
        vals = re.split(' and | or ', names)
        indented_test = []
        if vals[0] != '':
            for v in vals:
                logic = v
                long_form = re.search('\[([a-z_0-9]*)\](\[[a-z_0-9\(\)]*\][0-9 \'=]*)', v)
                if long_form:
                    v = long_form.group(2)
                word = re.search('\[([a-z_0-9\(\)]*)\]([0-9 \'=]*)', v)
                if word != None:
                    val = word.group(2)
                    logic = word.group(1)
                    rm_num = re.search('([a-z_0-9]*)\(([0-9]*)\)', logic)
                    if rm_num != None:
                        #Pull out the number for checkboxes
                        logic = rm_num.group(1)
                        check_num = rm_num.group(2)
                indented_test.append(logic)
        return set(indented_test)

    def _indent_ques(self, logic, cur_field):
        ''' Indent the left margin as necessary for the field's level.

        Arguments:
        logic -- The set of fields that the current field is nested under
        cur_field -- The current field name.
        '''
        if self.indent_stack == {}:
            if len(logic) > 0:
                self.indent_stack[cur_field] = 1
                self.doc.start_indent()
                self.all_forms.start_indent()
        else:
            top = sorted(self.indent_stack.values()).pop()
            if len(logic) == 0:
                for k in self.indent_stack.keys():
                    self.doc.stop_indent()
                    self.all_forms.stop_indent()
                self.indent_stack={}
                return {}
            high = 0
            for l in logic:
                if self.indent_stack.has_key(l):
                    if self.indent_stack[l] > high:
                        high = self.indent_stack[l]
            if high == 0:
                num = 0
                for k in self.indent_stack.keys():
                    if num > 0:
                        self.doc.stop_indent()
                        self.all_forms.stop_indent()
                    del self.indent_stack[k]
                    num+=1
                self.indent_stack[cur_field] = 1
            elif high == top:
                self.doc.start_indent()
                self.all_forms.start_indent()
                self.indent_stack[cur_field] = top + 1
            else:
                num = 0
                for k, v in self.indent_stack.items():
                    if v > high:
                        del self.indent_stack[k]
                        if num > 0:
                            self.doc.stop_indent()
                            self.all_forms.stop_indent()
                        num+=1
                self.indent_stack[cur_field] = high + 1
   
    def __reset_indent(self):
        if self.indent_stack != {}:
            top = sorted(self.indent_stack.values()).pop()
            for val in range(top):
                self.all_forms.stop_indent()

    def process(self,const):
        ''' Parse and create the RedcapForm associated with the REDcap XML data
        dictionary.
        '''
        self.all_forms = RedcapForm('ALL.pdf', self.multiline)
        self.all_forms.setup()

        for item in self.tree.iter('item'):
            form_name = item.findtext('form_name')
            if self.to_print == [] or form_name in self.to_print:
                name = form_name.replace('_', " ")
                prop_name = string.capwords(name)
                if self.cur_form == None:
                    if const != None:
                        self.doc = RedcapForm(const + '_' + item.findtext('form_name')+".pdf",
                                self.multiline)
                    else:
                        self.doc = RedcapForm(item.findtext('form_name')+".pdf",
                                self.multiline)
                    if self.print_const_name != None:
                        self.doc.print_const_name(self.print_const_name)
                    self.doc.setup()
                    self.doc.form_name(prop_name)
                    self.all_forms.form_name(prop_name)
                    self.cur_form = item.findtext('form_name')

                elif not self.cur_form == item.findtext('form_name'):
                    self.doc.render()
                    self.__reset_indent()
                    if const != None:
                        self.doc = RedcapForm(const + '_' + item.findtext('form_name')+".pdf",
                                self.multiline)
                    else:
                        self.doc = RedcapForm(item.findtext('form_name')+".pdf",
                                self.multiline)
                    self.indent_stack = {}
                    if self.print_const_name != None:
                        self.doc.print_const_name(self.print_const_name)
                    self.doc.setup()
                    self.doc.form_name(prop_name)
                    if not self.all_same_page: 
                        self.all_forms.new_page()
                    self.all_forms.form_name(prop_name)
                    
                    self.cur_form = item.findtext('form_name')

                redcap_types = {
                    'number': RedcapForm.number_element,
                    'integer': RedcapForm.integer_element,
                    'text': RedcapForm.text_element,
                    'checkbox': RedcapForm.check_box_element,
                    'yesno': RedcapForm.yesno_element,
                    'dropdown': RedcapForm.radio_element,
                    'date_mdy': RedcapForm.date_element,
                    'date' : RedcapForm.date_ymd,
                    'date_dmy' : RedcapForm.date_dmy,
                    'date_ymd' : RedcapForm.date_ymd,
                    'truefalse': RedcapForm.truefalse_element,
                    'notes': RedcapForm.note_element,
                    'descriptive': RedcapForm.descriptive_element,
                    'sql': RedcapForm.sql_element,
                    'radio': RedcapForm.radio_element,
                    'calc': RedcapForm.calculated_element,
                    'file' : RedcapForm.no_print,
                    'time' : RedcapForm.time,
                    'time_mm_ss' : RedcapForm.time_mm_ss,
                    'datetime_mdy' : RedcapForm.datetime_mdy,
                    'datetime_dmy' : RedcapForm.datetime_dmy,
                    'datetime_ymd' : RedcapForm.datetime_ymd,
                    'datetime_seconds_dmy' : RedcapForm.datetime_sec_dmy,
                    'datetime_seconds_mdy' : RedcapForm.datetime_sec_mdy,
                    'datetime_seconds_ymd' : RedcapForm.datetime_sec_ymd,
                    'slider' : RedcapForm.slider_element,
                }

                field_text = clean_html(item.findtext('field_label'))
                field_type = item.findtext('field_type')
                field_name = item.findtext('field_name')
                branching_logic = item.findtext('branching_logic')

                if field_type == 'text':
                    spec = item.findtext('text_validation_type_or_show_slider_number')
                    if spec != '':
                        field_type = spec
                choices = self._get_choices(item.findtext('select_choices_or_calculations'))
                if branching_logic =='' or self.logic_parser.evaluate(field_name, branching_logic):
                    if self._indent != '':
                        logic_vals = self._get_level(branching_logic)
                        indent_stack = self._indent_ques(logic_vals, field_name)
                    if item.findtext('section_header'):
                        self.doc.section_name(clean_html(item.findtext('section_header')))
                        self.all_forms.section_name(clean_html(item.findtext('section_header')))
                    if choices != None:
                        if redcap_types.has_key(field_type):
                            redcap_types[field_type](self.doc, field_text, choices)
                            redcap_types[field_type](self.all_forms, field_text, choices)
                        else:
                            redcap_types['text'](self.doc, field_text)
                            redcap_types['text'](self.all_forms, field_text)
                    else:
                        if redcap_types.has_key(field_type):
                            redcap_types[field_type](self.doc, field_text)
                            redcap_types[field_type](self.all_forms, field_text)
                        else:
                            redcap_types['text'](self.doc, field_text)
                            redcap_types['text'](self.all_forms, field_text)
        self.all_forms.render()
        self.doc.render()

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        params = {}
    if len(argv) == 5:
        argv.pop()
        config_file = argv.pop()
        const_name = argv.pop()
        zip_name = argv.pop()
        xml_data = argv.pop()
    elif len(argv) == 4:
        config_file = argv.pop()
        const_name = argv.pop()
        zip_name = argv.pop()
        xml_data = argv.pop()
    elif len(argv) == 3:
        argv.pop()
        zip_name = argv.pop()
        xml_data = argv.pop()
        const_name = None
        config_file = None
    elif len(argv) == 2:
        zip_name = argv.pop()
        xml_data = argv.pop()
        const_name = None
        config_file = None
    else:
        raise ArgumentError('Received %(received)s argument(s) instead of the \
        expected %(expected)s argument(s).' %({'received': str(len(argv)),
        'expected': '1-5',}))
    
    if config_file!= None and const_name != None:
        form = PdfForm(xml_data,
            os.path.join(
                 os.path.join(
                     os.path.dirname(os.path.dirname(inspect.getfile(inspect.currentframe()))),
                      'config_files'), config_file))
        form.add_constraint_list(const_name)
    else:
        form = PdfForm(xml_data)
    form.process(const_name)

    zip_handle = zipfile.ZipFile(zip_name, "w")

    for name in glob("*.pdf"):
        zip_handle.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
    zip_handle.close()

if __name__ == '__main__':
    main()
