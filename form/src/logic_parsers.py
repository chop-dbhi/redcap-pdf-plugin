import string
import re
import sys

class BranchingLogicError(Exception):
    ''' Error raised when an error in parsing logic occurs.
    '''
    def __init__(self, msg, logic):
        self.msg = msg
        self.logic = logic
        print msg


class LogicParser(object):
    def __init__(self):
        self.const = {}
        self.blacklist = []
        self.no_print_regex = []

    def _get_val(self, var, op, val, checked='1'):
        if self.const.has_key(var):
            if op =='=':
                op = '=='
            if any(eval(str(v) + op + val) for v in self.const[var]):
                if checked == '1':
                    return True
                return False
            else:
                if checked == '1':
                    return False
                else:
                    return True
        if var in self.blacklist:
            if checked == '1':
                return False
            return True
        return True

    def has_constraint(self, var_name):
        ''' Returns True if the form is constrained on the variable.
    
        Arguments:
        var_name -- The name of the variable to check for.
        '''
        return self.const.has_key(var_name)

    def get_const_vals(self, var_name):
        ''' Returns the values a variable name is constrained on. Returns and
        empty array if it has no constraints.
        '''

        if self.const.has_key(var_name):
            return self.const[var_name]
        return []
    
    def add_no_print_regex(self, vals):
        ''' Compiles and adds regular expressions to the no print list.
            If a field name matches the regular expression, 
            it is not printed.
        '''
        for val in vals:
            compiled = re.compile(val)
            self.no_print_regex.append(compiled)

    def add_constraint(self, var, vals):
        ''' Adds a new constraint to the LogicParser instance. 

        Keyword arguments:
        var -- The variable name for the element. 
        vals -- A list of all the numeric acceptable values for the element.
        '''
        if self.const.has_key(var):
            self.const[var].extend(vals)
        else:
            self.const[var] = vals

    def can_print(self, var_name):
        for regex in self.no_print_regex:
            if regex.match(var_name):
                return False
            else:
                return True
        if not self.no_print_regex:
            return True

    def evaluate(self, var_name, logic):
        ''' Return True if the element is not constrained by any elements in
        the constrained list, False otherwise. 

        Keyword arguments:
        var_name -- The variable name for the element.
        logic -- The string containing the branching logic for the element.
        '''
      
        space = re.compile('\s+')
        variable=re.compile(
                ('((?:\[[0-9a-z_]*\])?\[([0-9a-z_]+)\(?([0-9]*)\)?\]\s?'
                 '([!=><]+)\s?[\'\"]?\\s*\[?\s*(-?[0-9a-z_\-]*)\s*\]?\s'
                 '*[\'\"]?)(\s*and|\s*or)?\s*(.*)'),
                flags=re.IGNORECASE)
        function=re.compile(
                ('\s*(([a-z_0-9]+\([^\)]*\))\s*([!=><]*)\s*\'?\"?\s*([0-9]*)\s'
                 '*\'?\"?\s*)(.*)'),
                flags=re.IGNORECASE)

        logic = re.sub(space, ' ', logic)

        orig_str = logic
      
        if self.can_print(var_name):
            # Evaluate the variables in the expression
            var = variable.search(logic)
            while var != None:
                repl_str = var.group(1)
                name = var.group(2)
                op = var.group(4)
                val = var.group(5)
                checkbox = var.group(3)
                remaining = var.group(7)
                
                if checkbox != '':
                    new_val = self._get_val(name, op, checkbox, val)
                else:
                    new_val = self._get_val(name, op, val)

                new_val =" {value} ".format(value=new_val)
                orig_str = re.sub(re.escape(repl_str), new_val, orig_str)
                var = variable.search(remaining)
            
            # Evaluate the functions in the expression
            func = function.search(logic)
            while func != None:
                repl_str = func.group(1)
                var = func.group(2)
                op = func.group(3)
                val = func.group(4)
                remaining = func.group(5)

                new_val = " {value} ".format(value=self._get_val(var, op, val))
                orig_str = re.sub(re.escape(repl_str), new_val, orig_str)
                func = function.search(remaining)
            try:
                andor = re.search('(\sand|\sor)', 
                                  orig_str,
                                  flags=re.IGNORECASE)
                if andor:
                    orig_str = re.sub(andor.group(1), 
                                      string.lower(andor.group(1)), 
                                      orig_str)
                result = eval(orig_str)
                if not result:
                    self.blacklist.append(var_name)
                return result
            except:
                e = sys.exc_info()[1]
                print e
                raise BranchingLogicError(
                        ("The branching logic '{logic_str}' cannot be properly"
                         "evaluated by the LogicParser.\n".format(logic_str=logic)),
                        logic)
            else:
                self.blacklist.append(var_name)
        else:
            self.blacklist.append(var_name)
        return None
