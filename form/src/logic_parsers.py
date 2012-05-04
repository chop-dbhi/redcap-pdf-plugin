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

    def add_constraint(self, var, vals):
        ''' Adds a new constraint to the LogicParser instance. 

        Karguments:
        var -- The variable name for the element. 
        vals -- A list of all the numeric acceptable values for the element.
        '''
        if self.const.has_key(var):
            self.const[var].extend(vals)
        else:
            self.const[var] = vals

    def evaluate(self, var_name, logic):
        ''' Return True if the element is not constrained by any elements in
        the constrained list, False otherwise. 

        Keyword arguments:
        var_name -- The variable name for the element.
        logic -- The string containing the branching logic for the element.
        '''
      
        space = re.compile('\s+')
        variable=re.compile('((?:\[[0-9a-z_A-Z]*\])?\[([0-9a-z_A-Z]+)\(?([0-9]*)\)?\]\s?([=><]+)\s?[\'\"]?(-?[\s0-9]*)[\'\"]?)(\s*and|\s*or)?\s*(.*)')
        function=re.compile('\s*(([a-zA-Z_0-9]+\([^\)]*\))\s*([=><]*)\s*\'?\"?\s*([0-9]*)\s*\'?\"?\s*)(.*)')
        logic = re.sub(space, ' ', logic)

        orig_str = logic
        
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

            new_val = " %(value)s " %{'value': new_val}
             
            orig_str = re.sub(re.escape(repl_str), new_val, orig_str)
            var = variable.search(remaining)
        
        # Evaluate the funcitons in the expression
        func = function.search(logic)
        while func != None:
            repl_str = func.group(1)
            var = func.group(2)
            op = func.group(3)
            val = func.group(4)
            remaining = func.group(5)

            new_val = " %(value)s " %{'value':self._get_val(var, op, val)}
            orig_str = re.sub(re.escape(repl_str), new_val, orig_str)
            func = function.search(remaining)
        try:
            result = eval(orig_str)
            if not result:
                self.blacklist.append(var_name)
            return result
        except:
            e = sys.exc_info()[1]
            print e
            raise BranchingLogicError("The branching logic \'%(logic_str)s\' \
cannot be properly evaluated by the LogicParser.\n"
                %{'logic_str': logic}, logic)
        return None
