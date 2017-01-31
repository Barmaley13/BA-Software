"""
Header Variable Class
"""

### INCLUDES ###
import re
import math
import parser
import logging

from base import HeaderBase
from common import OPEN_CIRCUIT, SHORT_CIRCUIT


### CONSTANTS ###
## Formula Parser ##
FORMULA_DELIMITERS = re.compile('[()+\-*/%&|^~<>,.]')

## Logger ##
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)


### FUNCTIONS ###
## Get liters considering tank type ##
def _get_liters(constants, level):
    """
    Calculates liters. Usually we would use formulas for such a calculation. But this a special case since
    it requires tank type parsing.

    :param constants: Dictionary of constants for the liters calculations
    :param level: Level of the tank
    :return: liters
    """
    liters = None
    radius = None

    tank_type = constants['tank_type']
    diameter = constants['diameter']
    length = constants['length']
    area = constants['area']

    if diameter:
        radius = diameter / 2

    if tank_type == 'Constant' and area:
        liters = area * level * 1000
    elif tank_type == 'Vertical' and radius:
        area = math.pi * pow(radius, 2)
        liters = area * level * 1000
    elif tank_type == 'Horizontal' and diameter and length:
        liters = length * (math.acos((radius - level) / radius) * pow(radius, 2) -
                           math.sqrt(level * (diameter - level)) * (radius - level)) * 1000

    return liters


### CLASSES ###
class HeaderVariable(HeaderBase):
    """ Header Variable Class """

    def __init__(self, formula, **kwargs):
        """
        Initializes header variable, done as part of Header initialization by using provided variable dictionary.

        :param formula: formula to calculate this variable. You can use any internal constant names in this
            formula that have been declared earlier.
        :return: Header Variable instance
        """
        defaults = {
            # Local Must Haves
            'formula': formula,
            # Internal
            '_formula': None,
            '_external': False,
            # Short Circuit
            'min_alarm': None,
            'min_alarm_message': SHORT_CIRCUIT,
            # Open Circuit
            'max_alarm': None,
            'max_alarm_message': OPEN_CIRCUIT

        }
        defaults.update(kwargs)
        self.compiled_formulas = {}
        super(HeaderVariable, self).__init__(**defaults)

    ## Formula Related ##
    def apply_formula(self, provider):
        """
        Applies formula and returns result of formula application.

        :param provider: data provider that we are working with
        :return: result of formula application if successful or None if could not calculated formula for some reason.

        .. note:: Even though IDE tells that data provider argument is not used,
                  it is used during execution of ``eval`` function!!!
                  Also, not sure if this will work as a function rather than as a method.
        """
        output = None

        # Data that is necessary for computing the formula
        data_in = provider['data_in']
        constants = provider['constants'][self['data_field']]
        data_out = provider['data_out'][self['data_field']]

        # Check if formula has been compiled
        raw_formula = self['formula']
        if raw_formula not in self.compiled_formulas or self.compiled_formulas[raw_formula] is None:
            self._compile_formula(provider)

        try:
            compiled_formula = self.compiled_formulas[raw_formula]
            result = eval(compiled_formula)
            # LOGGER.debug("result = " + str(result))
            if result is not None:
                output = float(result)
            else:
                LOGGER.warning('Formula Parser Warning: Formula result is None!')
        except:
            LOGGER.warning('Formula Parser Warning: Compiled formula can not be calculated!')
            # LOGGER.debug("raw_formula = " + str(raw_formula))
            # LOGGER.debug("compiled_formula = " + str(self['_formula']))
            # LOGGER.debug("data_in = " + str(data_in))
            # LOGGER.debug("constants = " + str(constants))
            # LOGGER.debug("data_out = " + str(data_out))

        data_out[self['internal_name']] = output

        return output

    def _compile_formula(self, provider):
        """
        Compiles formulas which helps speed up calculation process.

        :param provider: data provider that we are working with
        :return: NA
        """
        data_in = provider['data_in']
        constants = provider['constants'][self['data_field']]
        data_out = provider['data_out'][self['data_field']]

        LOGGER.debug("*** Processing " + self['data_field'] + "***")
        LOGGER.debug("data_in = " + str(data_in))
        LOGGER.debug("constants = " + str(constants))

        # Parse formula
        raw_formula = self['formula']
        _formula = raw_formula.replace(" ", "")
        _formula = _formula.replace('^', '**')
        variables = FORMULA_DELIMITERS.split(_formula)
        LOGGER.debug("variables = " + str(variables))
        delimiters = FORMULA_DELIMITERS.findall(_formula)
        LOGGER.debug("delimiters = " + str(delimiters))

        # Compile formula
        compiled_formula = None
        for index, variable in enumerate(variables):
            if variable:
                if variable == 'self':
                    variable = self['data_field']

                if variable in data_in:
                    if data_in[variable] is None:
                        LOGGER.warning("Formula Parser Warning: No value specified for " + variable + "!")
                        break
                    else:
                        variables[index] = "data_in['" + variable + "']"
                elif variable in constants:
                    if constants[variable] is None:
                        LOGGER.warning("Formula Parser Warning: No value specified for " + variable + "!")
                        break
                    else:
                        variables[index] = "constants['" + variable + "']"
                elif variable in data_out:
                    if data_out[variable] is None:
                        LOGGER.warning("Formula Parser Warning: No value specified for " + variable + "!")
                        break
                    else:
                        variables[index] = "data_out['" + variable + "']"
                elif hasattr(math, variable):
                    variables[index] = 'math.' + variable
                elif variable in ('_get_liters', 'round', 'constants', 'int', 'float', 'sum', 'len'):
                    pass
                elif not variable.isdigit():
                    LOGGER.warning("Formula Parser Warning: Can not parse " + variable + "!")
                    break
        else:
            _formula = [None] * (len(variables) + len(delimiters))
            _formula[::2] = variables
            _formula[1::2] = delimiters
            self['_formula'] = ''.join(_formula)
            LOGGER.debug("formula = " + str(_formula))
            LOGGER.debug("constants = " + str(constants))
            compiled_formula = parser.expr(self['_formula']).compile()

        self.compiled_formulas[raw_formula] = compiled_formula
