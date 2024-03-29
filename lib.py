# ONLY CHANGE STUFF IN THIS SECTION, NOT IN THE OTHER SECTIONS. SET GLOBAL CONTENTS AND SETTINGS HERE
__debug_lib__ = __debug__  # Weather to show warnings and debug info. Default: __debug__. Change this to False, if you want to hide the librarys internal debug information, even when you debug your application
__debug_extended__ = False  # Weather to show internal debug info (mainly for debugging the library itself).

DEC_DGTS = 64  # How many decimal digits (without rounding errors) shall be used.
#################################################################################################
# Init
ESC_STYLES = {"Error": '\033[41m\033[30m', "Error_txt": '\033[0m\033[31m', "Warning": '\033[43m\033[30m',
              "Warning_txt": '\033[0m\033[33m', "Default": '\033[0m', "Hacker_cliche": "\033[38;2;0;255;0m ", "Green_BG": '\033[42m\033[30m'}

# Note: Appart from this, you have to install 'Jinja2' (e.g. using pip)
import asyncio
import colorsys as cls
import math as mt
import decimal as dc
import copy as cpy
import random as rndm
import pyppeteer as pt
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import matplotlib.patches as ptc
import numpy as np
import pandas as pd
import pandas.io.formats.style as sty
import latex2sympy2 as l2s2
import sympy as smp
import scipy as sp
import sys

libs = [asyncio, cls, mt, pt, plt, np, pd, dc, cpy, l2s2, tck, smp, sp, sys, rndm]

if DEC_DGTS <= dc.MAX_PREC:
    dc.getcontext().prec = DEC_DGTS
else:
    print(ESC_STYLES["Warning"] + "Config Warning: Passed value of" + str(
        DEC_DGTS) + "for DEC_DGTS exceeds allowed precission of " + str(
        dc.MAX_PREC) + " (might vary depending on the system). Using " + str(dc.MAX_PREC) + "instead." + ESC_STYLES[
              "Warning"])

if __debug_lib__:
    print(
        "Running in debug mode. Use 'python <PATH TO YOUR FILE> -oo to run in optimized mode and hide debug information")
    for lib in libs:
        try:
            print("Using", lib.__name__, lib.__version__)
        except AttributeError:
            pass
    print("\n\n####################################################################\n\n")

# Latex Setup:
plt.rcParams['text.usetex'] = True
plt.rcParams['text.latex.preamble'] = r'\usepackage{xfrac, amsmath}'
plt.rcParams['font.size'] = 14
plt.rcParams['axes.labelsize'] = 25
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['errorbar.capsize'] = 5
plt.rcParams['lines.markersize'] = 10


########################################################################################################
# internal Functions

def _warn(name, description):
    print("\n" + ESC_STYLES["Warning"] + "WARNING: " + name + ESC_STYLES["Default"] + " " + ESC_STYLES[
        "Warning_txt"] + description + ESC_STYLES["Default"] + "\n")


def _error(name, description):
    print(
        "\n\n\n(" + ESC_STYLES["Error"] + "Error: " + name + ESC_STYLES["Default"] + " " + ESC_STYLES[
            "Error_txt"] + description +
        ESC_STYLES["Default"] + ")\n\n\n")
    raise Exception(name + ": " + description)


########################################################################################################
# Fun
async def motivate():
    browser = await pt.launch(headless=True)
    page = await browser.newPage()
    await page.goto("https://deepai.org/machine-learning-model/text-generator")
    await page.waitForSelector(selector=".qc-cmp2-summary-buttons")
    await page.evaluate("document.querySelector('.qc-cmp2-summary-buttons').querySelectorAll('button')[1].click()")

    prompt = "motivational text explaining that the physics laboratory courses are implemented badly, boring and exhausting. The text shall value and appreciate my previous progress on the corresponding lab report and assure me that I will manage to finish it soon."

    fn = "()=>{document.querySelector('textarea.model-input-text-input').value = '" + prompt + "';document.querySelector('button#modelSubmitButton').click();console.log('done');}"
    await page.evaluate(fn)
    await page.waitForSelector('.try-it-result-area > div > pre')
    fn = "document.querySelector('.try-it-result-area').querySelector('pre').innerText"
    res = await page.evaluate(fn)
    print(res)

    await browser.close()


def motivate_me():  # Use GPT-2 to generate and show a motivational text to convince you to proceed
    asyncio.run(motivate())


######################################################################
# Misc
def index_of(arr, start=0):
    return list(range(start, len(arr)))


def invert_list(list):
    res = [0 for l in list]
    for i in index_of(list):
        res[len(res) - i - 1] = list[i]

    return res

def optimal_indices(arr, target):
    res = []
    epsilon = abs(target-arr[0])
    for i in index_of(arr):
        if abs(target-arr[i]) <= epsilon:
            epsilon = abs(target-arr[i])
    for i in index_of(arr):
        if abs(target-arr[i]) <= epsilon:
            res.append(i)

    return res

#####################################################################
# Datasets and Data-Handling

class Solvers:
    class Euler:

        def evaluate(self, resolution, stop=None, variable_values=None):
            res = [[self.initial_condition[i]] for i in index_of(self.initial_condition)]

            client_wants_ds = type(variable_values) is list
            if variable_values is not None:
                stop = variable_values[-1]
                if not client_wants_ds:
                    variable_values = [variable_values]
            else:
                variable_values = []

            variable_values.sort()
            client_values = [[]] + [[] for var in self.result_variables]
            client_values_i = 0
            i = 1
            while True:
                args = {self.variable.n: res[0][i - 1]}
                for k in index_of(self.result_variables):
                    args[self.result_variables[k].n] = res[1 + k][i - 1]
                if len(variable_values) > client_values_i and variable_values[client_values_i] <= res[0][
                    i - 1] + resolution:
                    client_values[0].append(variable_values[client_values_i])
                    for j in index_of(self.result_variables):
                        client_values[1 + j].append(
                            res[1 + j][i - 1] + (variable_values[client_values_i] - res[0][i - 1]) *
                            self.differential_equations[j].sympy.xreplace(args))

                    client_values_i += 1
                res[0].append(res[0][i - 1] + resolution)
                for j in index_of(self.result_variables):
                    res[1 + j].append(
                        res[1 + j][i - 1] + resolution * self.differential_equations[j].sympy.xreplace(args))

                if res[0][i] >= stop:
                    break
                i += 1

            if client_wants_ds:
                return Dataset(c_names=[self.variable.str] + [var.str for var in self.result_variables],
                               lists=client_values)

            if len(client_values) == 1:
                return variable_values[0]

            return Dataset(c_names=[self.variable.str] + [var.str for var in self.result_variables], lists=res)

        def __init__(self, result_variables, variable, differential_equations, initial_condition):
            # tuple initial_condition, MatEx diferential_equation
            self.differential_equations = differential_equations
            self.initial_condition = initial_condition
            self.variable = variable
            self.result_variables = result_variables

    class Root:
        def __init__(self, expression, epsilon):
            self.expression = MatEx(expression.variables.values(), sympy=expression.sympy) if type(expression) is Formula else expression
            delkeys = []
            for key in self.expression.variables.keys():
                if "\\sigma_{" in key:
                    delkeys.append(key)

            for key in delkeys:
                self.expression.variables.__delitem__(key)

            self.epsilon = Val(epsilon)
            self._old_recursion_limit = sys.getrecursionlimit()



        def evaluate(self, initial_guesses):
            if len(initial_guesses) >= self._old_recursion_limit:
                sys.setrecursionlimit(self._old_recursion_limit + len(initial_guesses))
            fun = smp.lambdify([var.n for var in self.expression.variables.values()], self.expression.sympy)
            initial_guess = initial_guesses[0]
            initial_guesses.remove(initial_guess)
            res = sp.optimize.root(fun, initial_guess)

            if len(initial_guesses) > 0:
                ret_ds = self.evaluate(initial_guesses)
            else:
                ret_dict = {}
                for key in self.expression.variables.keys():
                    ret_dict[key] = []
                ret_ds = Dataset(dictionary=ret_dict)

            if not res.success:
                return ret_ds

            for r in index_of(ret_ds.col(0)):
                for c in index_of(ret_ds.row(r)):
                    if not ((ret_ds.at(r, c) - self.epsilon).v <= res.x[c] <= (ret_ds.at(r, c) + self.epsilon).v):
                        break
                    if c == len((ret_ds.row(r))) - 1:
                        # res already in ret_dict
                        return ret_ds

            ret_ds.add_row([Val(component) for component in res.x])
            return ret_ds

        def __del__(self):
            sys.setrecursionlimit(self._old_recursion_limit)


class Val:  # Todo: document!

    @property
    def v(self):
        return self._v
    @v.setter
    def v(self, new_v):
        self._v = dc.Decimal(new_v)
        self._known_decimal_figures = 0 if "." not in str(new_v) else len(str(new_v).split('.')[1])
        self._known_decimal_figures += 0 if "e" not in str(new_v) else (-int(str(new_v).split('e')[1]) - 1 - len(str(new_v).split('e')[1]))

    @property
    def e(self):
        return self._e

    @e.setter
    def e(self, new_e):
        self._e = dc.Decimal(new_e)
        self._e_known_decimal_figures = 0 if "." not in str(new_e) else len(str(new_e).split('.')[1])
        self._e_known_decimal_figures += 0 if "e" not in str(new_e) else (
                    -int(str(new_e).split('e')[1]) - 1 - len(str(new_e).split('e')[1]))

    @staticmethod
    def to_val(val, modify=lambda val: val):
        if type(val) is Val:
            return modify(val)
        try:
            return Val(modify(val))
        except dc.InvalidOperation:
            return str(val)
        except:
            return Val(float(modify(val)))

    @staticmethod
    def weighted_mean(val_list=None):
        x_over_sig_sq = dc.Decimal(0)
        rez_sig_sq = dc.Decimal(0)

        for val in val_list:
            x_over_sig_sq += dc.Decimal(val.v / (val.e ** 2))
            rez_sig_sq += dc.Decimal(1 / (val.e ** 2))

        return Val(str(x_over_sig_sq / rez_sig_sq), str(mt.sqrt(dc.Decimal(1 / rez_sig_sq))))

    def __init__(self, val, err="NaN"):
        self.v = dc.Decimal(val)
        self.e = dc.Decimal(err)
        self._known_decimal_figures = 0 if "." not in str(val) else len(str(val).split('.')[1])
        self._known_decimal_figures += 0 if "e" not in str(val) else (-int(str(val).split('e')[1]) - 1 - len(str(val).split('e')[1]))
        self._e_known_decimal_figures = 0 if "." not in str(err) else len(str(err).split('.')[1])
        self._e_known_decimal_figures += 0 if "e" not in str(err) else (-int(str(err).split('e')[1]) - 1 - len(str(err).split('e')[1]))
    def __str__(self):
        return self.sig_round(warn_for_bad_error=False)[0]
        # return str(self.v) if mt.isnan(self.e) or type(self.e) == str else self.sig_round()[0]

    def __float__(self):
        return float(self.v)

    def __truediv__(self, other):
        x = Var("x")
        y = Var("y")
        return Formula([x, y], "x/y").at([[x, self], [y, other]], as_val=True)

    def __add__(self, other):
        x = Var("x")
        y = Var("y")
        return Formula([x, y], "x+y").at([[x, self], [y, other]], as_val=True)

    def __sub__(self, other):
        x = Var("x")
        y = Var("y")
        return Formula([x, y], "x-y").at([[x, self], [y, other]], as_val=True)

    def __mul__(self, other):
        x = Var("x")
        y = Var("y")
        return Formula([x, y], "x*y").at([[x, self], [y, other]], as_val=True)

    def __pow__(self, other):
        x = Var("x")
        y = Var("y")
        return Formula([x, y], "x*y").at([[x, self], [y, other]], as_val=True)

    def get(self):
        return cpy.deepcopy(self.v)

    def set(self, val):
        self.v = val
        self._known_decimal_figures = 0 if "." not in str(val) else len(str(val).split('.')[1])
        self._known_decimal_figures += 0 if "e" not in str(val) else (
                    -int(str(val).split('e')[1]) - 1 - len(str(val).split('e')[1]))

    def get_err(self):
        return cpy.deepcopy(self.e)

    def set_err(self, new_err):
        self.e = new_err
        self._e_known_decimal_figures = 0 if "." not in str(new_err) else len(str(new_err).split('.')[1])
        self._e_known_decimal_figures += 0 if "e" not in str(new_err) else (
                    -int(str(new_err).split('e')[1]) - 1 - len(str(new_err).split('e')[1]))

    def sig_round(self, sig_digits=1, additional_digit=True, warn_for_bad_error=True):
        val = self.get()
        err = self.get_err()
        if mt.isnan(err) or err <= 0:
            if warn_for_bad_error:
                _warn("ValueWarning",
                      "Can't sig_round() Val with error 'NaN' or '0', but got (" + str(val) + ", " + str(err) + ")")
            if val == 0:
                return ["0"]
            if val.is_nan():
                return ["NaN"]

            dec_pot = dc.Decimal(mt.floor(mt.log10(abs(val))) - sig_digits - 1)
            val *= dc.Decimal(10 ** -dec_pot)
            val = round(val)
            return [str(val * dc.Decimal(10 ** dec_pot)) if abs(dec_pot) < 3 else str(val) + " \cdot 10^{" + str(
                dec_pot) + "}"]

        if mt.isnan(err) or type(val) is str or type(err) is str:
            _error("Invalid Value",
                   "Can only sig_round Vals with well-defined values and error, but got " + str(val) + ", " + str(err))
            return

        if val.is_nan():
            return ["NaN"]
        sig_pos = mt.floor(mt.log10(
            err))  # position of the first significant figure relative to the decimal point (Number of digits between first significant digit and point, can be negative (behind point), 0 is in front of point)

        if __debug_extended__:
            print("Position of first significant digit: ", sig_pos)

        dec_pot = -(
            -sig_pos + sig_digits - 1 if -sig_pos + sig_digits - 1 <= self._e_known_decimal_figures else self._e_known_decimal_figures)  # digits the point gets shifted by
        err *= dc.Decimal(10 ** -dec_pot)
        if additional_digit and err < 3:
            err *= dc.Decimal(10)
            dec_pot -= 1

        err = mt.ceil(err)
        str_err = str(err) + ("" if dec_pot == 0 else " \cdot 10^{" + str(dec_pot) + "}")

        val *= dc.Decimal(10 ** -dec_pot)
        val = round(val)
        str_val = str(val) + ("" if dec_pot == 0 else " \cdot 10^{" + str(dec_pot) + "}")

        if self.v == 0:
            percent = "NaN"
        else:
            percent = abs(dc.Decimal(100) * self.e / self.v)
            perc_pot = mt.floor(mt.log10(percent)) - 1
            if abs(perc_pot + 1) <= 3:
                if perc_pot >= 0:
                    percent = mt.ceil(percent)
                else:
                    percent *= dc.Decimal(10) ** dc.Decimal(-perc_pot)
                    percent = mt.ceil(percent)
                    percent *= dc.Decimal(10) ** dc.Decimal(perc_pot)
                percent = str(percent)
            else:
                percent *= dc.Decimal(10) ** dc.Decimal(-perc_pot)
                percent = mt.ceil(percent)
                percent = str(percent) + " \cdot 10^{" + str(perc_pot) + "}"

        return [str_val + " \\pm " + str_err + " \: (\\pm " + percent + "\\%)", str_val, str_err, percent]

    def sigma_interval(self, true_value):
        if type(true_value) is Val:
            true_value = true_value.v
        if type(true_value) is not dc.Decimal:
            true_value = dc.Decimal(true_value)

        return abs(true_value - self.v)/self.e


class Var:
    n = ""
    str = ""

    def __init__(self, name):
        self.str = name
        self.n = smp.Symbol(name)

    def __str__(self):
        return self.str

    def __float__(self):
        return self.n


class MatEx:
    @property
    def sympy(self):
        return self._sympy

    @sympy.setter
    def sympy(self, new_sympy):
        self._raw_sympy = new_sympy
        self._sympy = self._raw_sympy.doit()
        self._latex = l2s2.latex(self._sympy)

    @property
    def latex(self):
        return "$" + self._latex + "$"

    @latex.setter
    def latex(self, new_latex):
        self.sympy = l2s2.latex2sympy(new_latex)

    def __init__(self, variables, latex="", sympy=None):
        self.variables = {}
        for var in variables:
            if type(var) is str:
                self.variables[var] = Var(var)
            else:
                self.variables[var.str] = var
        self.sympy = sympy if sympy is not None else (None if latex == "" else l2s2.latex2sympy(latex))

    def __str__(self):
        return self.latex

    def at(self, var_val_pairs):
        tmp_sympy = self._sympy.doit()
        for var_val_pair in var_val_pairs:
            if isinstance(var_val_pair[0], Var):
                var_val_pair[0] = var_val_pair[0].n

            tmp_sympy = tmp_sympy.subs(var_val_pair[0], var_val_pair[1])
        return tmp_sympy


class Formula(MatEx):

    @staticmethod
    def from_mat_ex(mat_ex):
        return Formula(variables=list(mat_ex.variables.keys()), sympy=mat_ex.sympy)

    def update_errors(self):
        _err = 0
        for var in list(self.variables.keys()):
            if "\\sigma_{" not in var and "\\sigma_{" + var + "}" not in list(self.variables.keys()):
                self.variables["\\sigma_{" + var + "}"] = Var('\\sigma_{' + var + '}')
        for key in self.variables.keys():
            if "\\sigma_{" not in key:
                _err += (smp.Derivative(self.sympy, self.variables[key].n) * self.variables[
                    "\\sigma_{" + str(key)+"}"].n) ** 2
        self.error = MatEx(variables=list(list(self.variables.values())), sympy=smp.sympify(smp.sqrt(_err)))

        if __debug_extended__:
            print("Updated errors of " + self.latex + " to " + self.error.latex)

    @property
    def error(self):
        err = cpy.deepcopy(self._error)
        for key in self.preset_variables.keys():
            err.sympy = err.sympy.subs(self.variables[key].n, self.preset_variables[key])
        return err

    @error.setter
    def error(self, new_error):
        self._error = new_error

    @property
    def sympy(self):
        # in order to take into account preset variables
        preset_sympy = self._sympy
        for key in self.preset_variables.keys():
            preset_sympy = preset_sympy.subs(self.variables[key].n, self.preset_variables[key])
        return preset_sympy

    @sympy.setter
    def sympy(self, new_sympy):
        MatEx.sympy.fset(self, new_sympy)
        self.update_errors()

    @property
    def latex(self):
        # in order to take into account preset variables
        frml = self.clone()
        for key in self.preset_variables.keys():
            frml.sympy = frml.sympy.subs(self.variables[key].n, self.preset_variables[key])
        for atom in frml.sympy.atoms(smp.Float):
            frml.sympy = frml.sympy.subs(atom, smp.N(atom, 1))

        frml.sympy = smp.sympify(frml.sympy)
        try:
            frml.sympy = smp.simplify(frml.sympy)
        except:
            pass
        return "$" + frml._latex + "$"

    @latex.setter
    def latex(self, new_latex):
        MatEx.latex.fset(self, new_latex)
        self.update_errors()

    def __init__(self, variables=None, latex="", sympy=None):

        self.preset_variables = {}
        self.error = None
        if variables is None:
            variables = []
        MatEx.__init__(self, variables, latex, sympy)

    def __str__(self):
        ret_err = self.error.sympy
        ret_err = ret_err.doit()
        ret_err = smp.sympify(ret_err)
        ret_err = smp.simplify(ret_err)
        for atom in ret_err.atoms(smp.Float):
            ret_err = ret_err.subs(atom, smp.N(atom, 1))

        return self.latex[1:-1] + " \\pm " + smp.latex(ret_err)

    def at(self, var_val_pairs, as_val=True):
        for variable in self.preset_variables.keys():
            var_val_pairs.append([self.variables[variable], self.preset_variables[variable]])
        for i in index_of(var_val_pairs):
            if isinstance(var_val_pairs[i][1], Val) and "\\sigma_{" not in var_val_pairs[i][0].str:
                var_val_pairs.append([self.variables["\\sigma_{" + var_val_pairs[i][0].str + "}"], var_val_pairs[i][1].e])
                var_val_pairs[i][1] = var_val_pairs[i][1].v

        if as_val:
            return Val(str(MatEx.at(self, var_val_pairs).evalf()), str(self.error.at(var_val_pairs).evalf()))
        if self.error is None:
            return MatEx.at(self, var_val_pairs), None
        return MatEx.at(self, var_val_pairs), self.error.at(var_val_pairs)

    def set_variables(self, var_val_pairs):
        for var_val_pair in var_val_pairs:
            val = cpy.deepcopy(var_val_pair[1])
            val.e = dc.Decimal("NaN")
            self.preset_variables[var_val_pair[0].str] = val.v
            self.preset_variables["\\sigma_{" + var_val_pair[0].str + "}"] = var_val_pair[1].e

    def substitute_variables(self, var_formula_pairs):
        for pair in var_formula_pairs:
            self.sympy = self.sympy.subs(pair[0].n, pair[1].sympy)
            self.error.sympy = self.error.sympy.subs(self.error.variables["\\sigma_{" + pair[0].str + "}"].n, pair[1].error.sympy)
            for dict_entry in pair[1].variables.items():
                self.variables[dict_entry[0]] = dict_entry[1]
            for dict_entry in pair[1].error.variables.items():
                self.error.variables[dict_entry[0]] = dict_entry[1]

    def to_val(self, var_val_pairs):
        at = self.at(var_val_pairs, as_val=False)
        try:
            return Val(str(at[0].evalf()), str(at[1].evalf()))
        except dc.InvalidOperation:
            _error(name="ConversionError",
                   description="Can't convert sympy (" + str(at[0].evalf()) + "\\pm" + str(at[
                                                                                               1].evalf()) + ") to Val. Make shure that the specified key-value-pairs are providing values for all used variables, so that the sympy-expressioon can be evaluated to a numeric expression and doesn't contain any unset variables.")

    def clone(self):
        return cpy.deepcopy(self)

    def create_values(self, var_values, var=None, val_label=None):
        if val_label is None:
            val_label = self.latex
        if var is None:
            var = list(self.variables.values())[0].str
        if type(var) is Var:
            var = var.str

        err_label = "\sigma_{" + val_label + "}"
        data = {var: var_values, val_label: []}
        preset_sympy = self.sympy.subs(self.variables["\\sigma_{" + var + "}"].n, 0)
        # for key in self.preset_variables.keys():
        #     preset_sympy = preset_sympy.subs(self.variables[key].n, self.preset_variables[key])
        preset_err_sympy = self.error.sympy.subs(self.variables["\\sigma_{" + var + "}"].n, 0)
        for key in self.preset_variables.keys():
            preset_err_sympy.subs(self.variables[key].n, self.preset_variables[key])
        fast_val = smp.utilities.lambdify(self.variables[var].n, preset_sympy)
        fast_err = smp.utilities.lambdify(self.variables[var].n, preset_err_sympy)
        for var_val in var_values:
            val = Val(fast_val(var_val), str(fast_err(var_val)))
            if val.e == 0:
                val.e = dc.Decimal("NaN")
            data[val_label].append(val)

        return Dataset(dictionary=data)  # , r_names=[var, val_label]


class Dataset:  # Object representing a full Dataset

    def __init__(self, x_label=None, y_label=None, dictionary=None, lists=None, csv_path=None, r_names=None,
                 c_names=None, val_err_index_pairs=None, title=None):
        self.frame = pd.DataFrame()
        self.title = title
        self.plot_color = None
        if val_err_index_pairs is None:
            val_err_index_pairs = []
        if dictionary is not None:
            self.from_dictionary(dictionary, r_names)
        elif lists is not None:
            self.from_lists(lists, r_names, c_names)
        elif csv_path is not None:
            self.from_csv(csv_path)

        self.bind_errors(val_err_index_pairs)

        self.x_label = x_label
        self.y_label = y_label

    def row(self, index):
        try:
            res = self.frame.loc[index]
        except:
            res = self.frame.iloc[index]
        return res

    def rename_rows(self, indices, new_names):
        name_dict = {}
        for i in index_of(indices):
            name_dict[self.get_row_names()[indices[i]]] = new_names[i]
        self.frame.rename(mapper=name_dict, inplace=True, axis="rows")

    def rename_cols(self, indices, new_names):
        name_dict = {}
        for i in index_of(indices):
            #name_dict[self.get_col_names()[indices[i]]] = new_names[i]
            name_dict[indices[i] if type(indices[i]) is str else self.get_col_names()[indices[i]]] = new_names[i]

        self.frame.rename(mapper=name_dict, inplace=True, axis="columns")

    def add_column(self, content, name, index=None):
        if index is None:
            index = len(self.get_col_names())
        self.frame.insert(loc=index, column=name, value=content)

    def add_row(self, content):
        self.frame = pd.concat([self.frame, Dataset(lists=[[c] for c in content], c_names=self.get_col_names()).frame],
                               axis="index", ignore_index=True)


    def col(self, index):
        try:
            res = self.frame[index]
        except:
            res = self.frame[self.get_col_names()[index]]
        return list(res)

    def at(self, r_index, c_index):
        r_name = r_index if type(r_index) is not int else self.get_names([r_index, c_index])[0]
        c_name = c_index if type(c_index) is not int else self.get_names([r_index, c_index])[1]
        return self.frame.at[r_name, c_name]

    def set(self, r_index, c_index, value):
        r_name = r_index if type(r_index) is not int else self.get_names([r_index, c_index])[0]
        c_name = c_index if type(c_index) is not int else self.get_names([r_index, c_index])[1]
        self.frame.at[r_name, c_name] = value

    def disp_row(self, index):
        print(self.row([index]))

    def disp_col(self, index):
        print(self.col([index]))

    def get_names(self, location):
        for i in index_of(location):
            if type(location[i]) is not int:
                location[i] = list(self.frame.columns).index(location[i])

        return [self.frame.index[location[0]],
                self.frame.columns[location[1]]]

    def get_row_names(self):
        return self.frame.index.to_list()

    def get_col_names(self):
        return self.frame.columns.to_list()

    def apply(self, method, r_indices=None, c_indices=None):
        if r_indices is None:
            r_indices = index_of(self.get_row_names())
        if c_indices is None:
            c_indices = self.get_col_names()

        if type(r_indices) is not list:
            r_indices = [r_indices]
        if type(c_indices) is not list:
            c_indices = [c_indices]

        for r_index in r_indices:
            for c_index in c_indices:
                self.set(r_index, c_index, method(self.at(r_index, c_index), r_index, c_index))

    def print(self, extended=False):
        if extended:
            max_rows = pd.get_option('display.max_rows')
            max_cols = pd.get_option('display.max_columns')
            max_col_width = pd.get_option('display.max_colwidth')
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.max_colwidth', None)
        print(self.frame)
        if extended:
            pd.set_option('display.max_rows', max_rows)
            pd.set_option('display.max_columns', max_cols)
            pd.set_option('display.max_colwidth', max_col_width)

    def delete(self, c_indices=None, r_indices=None):
        if c_indices is None:
            c_indices = []

        if r_indices is None:
            r_indices = []

        c_names = []
        r_names = []

        if type(c_indices) is not list:
            c_names.append(c_indices if type(c_indices) is not int else self.get_col_names()[c_indices])
        else:
            for c_index in c_indices:
                c_names.append(c_index if type(c_index) is not int else self.get_col_names()[c_index])

        if type(r_indices) is not list:
            r_names.append(r_indices if type(r_indices) is not int else self.get_row_names()[r_indices])
        else:
            for r_index in r_indices:
                r_names.append(r_index if type(r_index) is not int else self.get_row_names()[r_index])

        for r_name in r_names:
            self.frame.drop(index=r_name, inplace=True)

        for c_name in c_names:
            self.frame.drop(columns=c_name, inplace=True)

    def bind_error(self, value_col_index, error_col_index):
        val_col = self.col(value_col_index)
        err_col = self.col(error_col_index)

        for i in index_of(err_col):
            val_col[i].e = err_col[i].v
        self.delete(c_indices=error_col_index)

    def bind_errors(self, val_err_index_pairs):
        for pair in val_err_index_pairs:
            self.bind_error(pair[0], pair[1])

    def from_dictionary(self, dictionary, r_names=None,
                        items=None):  # Initialize the Dataset with a Python dictionary. Parameters: dictionary: The dictionary of lists to read the data from. items (otional): Which items (lists) of the dictionary to use. Default is 'None', which will use all items.
        data = {}
        if items == None:
            items = list(dictionary.keys())
        if __debug_extended__:
            print("Using items", items, "for creation")

        if not isinstance(dictionary, dict):
            _error("Type Error",
                   "Parameter 'dictionary' must be of Type <class 'dict'>, but has type " + str(type(dictionary)))
            return -1

        for item in items:
            data[item] = []
            for val in dictionary[item]:
                if not type(val) is Val:
                    data[item].append(Val.to_val(val))
                else:
                    data[item].append(val)

        if r_names is not None:
            self.frame = pd.DataFrame(data, r_names)
        else:
            self.frame = pd.DataFrame(data)

    def from_lists(self, lists, r_names=None, c_names=None, strict=False):
        if c_names is None:
            c_names = []

        if r_names is None:
            r_names = range(len(lists[0]))

        if len(lists) != len(c_names):
            if strict:
                _error("Parameter Length Missmatch", "Parameters 'lists' and 'c_names' must have the same length but "
                                                     "have shapes (" + str(len(lists)) + ") and ("
                       + str(len(c_names)) + ").")
                return -1
            if __debug_lib__:
                _warn("Parameter Length Missmatch", "Parameters 'lists' and 'c_names' must have the same length but "
                                                    "have shapes (" + str(len(lists)) + ") and (" + str(len(c_names)) +
                      "). Missing c_names will be initialized with standard indices, missing lists with all 'None'.")
            while len(c_names) < len(lists):
                c_names.append(len(c_names))
            while len(lists) < len(c_names):
                lists.append([None for i in lists[0]])
        try:
            data = {}
            for i in index_of(c_names):
                data[c_names[i]] = lists[i]
            self.frame = pd.DataFrame(data)
        except ValueError:
            max_len = len(lists[0])
            for i in index_of(lists, start=1):
                if len(lists[i]) != len(lists[i - 1]):
                    if strict:
                        _error("ValueError",
                               "All items in 'lists' must have same dimension, but items at Indices " + str(
                                   i - 1) + " and " + str(i) + " have shapes (" + str(
                                   len(lists[i - 1])) + ") and (" + str(len(lists[i])) + ").")
                        return -1
                    _warn("ValueWarning", "All items in 'lists' must have same dimension, but items at Indices " + str(
                        i - 1) + " and " + str(i) + " have shapes (" + str(len(lists[i - 1])) + ") and (" + str(
                        len(lists[i])) + "). Short items will be filled with 'NaN' of type dc.Decimal")
                    max_len = np.max([len(lists[i]), len(lists[i - 1]), max_len])
                    if __debug_extended__:
                        print("Maximal detected list-length:", max_len)
            for i in index_of(lists):
                while len(lists[i]) < max_len:
                    lists[i].append(dc.Decimal('NaN'))
        data = {}
        for i in index_of(c_names):
            data[c_names[i]] = []
            for j in index_of(lists[i]):
                try:
                    data[c_names[i]].append(Val.to_val(lists[i][j]))
                except TypeError:
                    data[c_names[i]].append(lists[i][j])

        self.frame = pd.DataFrame(data, r_names)

    def from_csv(self, path, delimiter=None, c_names_from_row=0, c_names=None, indices_from_row=None, usecols=None,
                 userows=None, NaN_alias="NaN", compression=None, strict=False, modify_cols={}, modify_rows={}):
        # TODO: TEST

        temp = pd.read_csv(filepath_or_buffer=path, sep=delimiter, header=c_names_from_row, names=c_names,
                           index_col=indices_from_row, na_values=NaN_alias, na_filter=True,
                           verbose=__debug_extended__, compression=compression, quotechar="\"", comment="#",
                           on_bad_lines='error' if strict else 'warn', dtype=object)

        shp = temp.shape
        for r in range(shp[0]):
            for c in range(shp[1]):
                temp.iloc[r].iloc[c] = Val.to_val(temp.iloc[r].iloc[c])

        for k in modify_cols.keys():
            for i in index_of(temp.get[k]):
                temp.get[k][i] = modify_rows[k](temp.get[k][i])

        for k in modify_rows.keys():
            for i in index_of(temp.loc[k]):
                temp.loc[k][i] = modify_rows[k](temp.loc[k][i])

        if userows is None:
            userows = range(shp[0])
        if usecols is None:
            usecols = range(shp[1])

        temp = temp.iloc[:, [col for col in usecols]]
        self.frame = temp.loc[userows]
        self.apply(lambda obj, r_index, c_index: Val.to_val(obj))

    def filter(self, c_index, filter_method):
        if type(c_index) is str:
            c_index = self.get_col_names().index(c_index)
        #if c_index <= len(self.col(c_index)):
            #return
        col = list(self.col(c_index))
        for i in index_of(col):
            if filter_method(col[i]):
                self.delete(r_indices=i)
                self.filter(c_index, filter_method)
                break

    def to_csv(self, path, delimiter=";", columns=None, show_index=False):
        if columns is None:
            columns = self.get_col_names()
        self.frame.to_csv(path, sep=delimiter, index_label=self.x_label, columns=columns, index=show_index)

    def to_latex(self, show_index=False):

        ds = cpy.deepcopy(self)
        ds.apply(lambda cell, row, col: "$" + str(cell) + "$")
        styler = sty.Styler(ds.frame)
        if not show_index:
            styler.hide(axis="index")

        col_frmt = "|l|"
        for col in self.get_col_names():
            col_frmt += "l|"

        ltx = styler.to_latex(position_float="centering", label="tab:my_table", caption="\\todo{caption}",
                              column_format=col_frmt)
        ltx = ltx.replace("\\begin{tabular}{" + col_frmt + "}", "\\begin{tabular}{" + col_frmt + "}" + "\n\hline")
        ltx = ltx.replace("\\\\", "\\\\ \hline", 1)
        ltx = ltx.replace("\end{tabular}", "\hline\n\end{tabular}")
        return ltx

    def clone(self):
        res = cpy.deepcopy(self)
        res.apply(lambda val, x, y: cpy.deepcopy(val))
        return res


class Legend_Entry:

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_label):
        self._label = new_label
        self.update()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_color):
        self._color = new_color
        self.update()

    def update(self):
        self.patch = ptc.Patch(color=self._color, label=self.label)

    def __init__(self, name, color):
        self._label = name
        self.color = color


class Legend:
    def __init__(self, location=None, entries=None):
        if entries is None:
            entries = {}

        self.entries = entries
        self.patches = [Legend_Entry(name=entry["name"], color=entry["color"]) for entry in self.entries]
        if location is not None:
            self.location = location
        else:
            self.location = "upper right"

class Visualizers:
    class Dotted_line:
        def __init__(self, dataset, color="black", index_pair=None, linestyle="dashed"):
            if index_pair is None:
                index_pair = [0, 1]
            self.dataset = dataset
            self.color = color
            self.index_pair = index_pair
            self.linestyle = linestyle

    class Text:
        def __init__(self, content, position, fontsize=None, color="black", alignment="center", background_color=None):
            self.alignment = alignment
            self.content = content
            self.position = position
            self.fontsize = fontsize if fontsize is not None else plt.rcParams['font.size']
            self.color = color
            self.background_color = background_color if background_color is not None else [0, 0, 0, 0]


class Plot:

    @staticmethod
    def generate_color(index):
        golden_ratio = (1 + mt.sqrt(5)) / 2
        if index == 0:
            return [cls.hsv_to_rgb(1 / 3, 1, 1)[i] for i in range(3)]

        last_color = cls.rgb_to_hsv(Plot.generate_color(index - 1)[0], Plot.generate_color(index - 1)[1], Plot.generate_color(index - 1)[2])
        h = last_color[0] + 1 / 3
        v = last_color[2]
        s = last_color[1]
        if index % 3 == 0 and index != 0:
            h += (1 / 3) / 2 ** (mt.floor(index / 3))
            h = h - mt.floor(h)
            if index % 6 == 0:
                v -= (1 / 2) / 2 ** (mt.floor(index / 6))
            else:
                s -= (1 / 2) / 2 ** (mt.floor(1 + index / 6))

        return [cls.hsv_to_rgb(h, s, v)[i] for i in range(3)]

    @property
    def point_colors(self):
        return self._point_colors

    @point_colors.setter
    def point_colors(self, new_colors):
        self._point_colors = new_colors

    @property
    def curve_colors(self):
        return self._curve_colors

    @curve_colors.setter
    def curve_colors(self, new_colors):
        self._curve_colors = new_colors

    def update_plt(self):
        plt.figure(self.fig)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)

        if type(self.sigma_interval) not in [tuple, list]:
            self.sigma_interval = (self.sigma_interval, self.sigma_interval)

        for i in index_of(self.curve_datasets):
            dataset = self.curve_datasets[i]
            if dataset is None:
                continue
            plt.plot([val.v for val in list(dataset.col(self.curve_column_index_pairs[i][0]))], [val.v for val in list(dataset.col(self.curve_column_index_pairs[i][1]))],
                     color=Plot.generate_color(i) if self.curve_colors[i] is None and dataset.plot_color is None else (self.curve_colors[i] if self.curve_colors[i] is not None else dataset.plot_color))

        for vis in self.visualizers:
            if type(vis) is Visualizers.Dotted_line:
                plt.plot([val.v for val in vis.dataset.col(vis.index_pair[0])], [val.v for val in vis.dataset.col(vis.index_pair[1])], color = vis.color, linestyle=vis.linestyle)
            if type(vis) is Visualizers.Text:
                self.axes.text(vis.position[0], vis.position[1], vis.content, fontsize=vis.fontsize, horizontalalignment=vis.alignment, backgroundcolor=vis.background_color)

        for i in index_of(self.point_datasets):
            dataset = self.point_datasets[i]
            if dataset is None:
                continue
            err_ds = dataset.clone()
            err_ds.filter(1, lambda val: mt.isnan(val.e) or val.e is None)
            if len(err_ds.frame.columns) > 0:
                plt.errorbar(x=[val.v for val in list(err_ds.col(self.point_column_index_pairs[i][0]))], y=[val.v for val in list(err_ds.col(self.point_column_index_pairs[i][1]))],
                             yerr=[self.sigma_interval[1] * val.e for val in list(err_ds.col(self.point_column_index_pairs[i][1]))],
                             xerr=[self.sigma_interval[0] * val.e for val in list(err_ds.col(self.point_column_index_pairs[i][0]))],
                             fmt='None', ecolor=Plot.generate_color(i) if self.point_colors[i] is None and dataset.plot_color is None else (self.point_colors[i] if self.point_colors[i] is not None else dataset.plot_color))

            if len(dataset.frame.columns) > 0:
                plt.scatter([val.v for val in list(dataset.col(self.point_column_index_pairs[i][0]))], [val.v for val in list(dataset.col(self.point_column_index_pairs[i][1]))],
                            marker="x", color=Plot.generate_color(i) if self.point_colors[i] is None and dataset.plot_color is None else (self.point_colors[i] if self.point_colors[i] is not None else dataset.plot_color))

        plt.title(self.title, fontsize=40)

        if self.x_label is not None:
            plt.xlabel(self.x_label)
        if self.y_label is not None:
            plt.ylabel(self.y_label)

        if len(self.legend.patches) > 0:
            self.axes.legend(loc=self.legend.location, handles=[entry.patch for entry in self.legend.patches], fontsize=18)

        if self.bounds["x"][0] is not None:
            plt.xlim(left=self.bounds["x"][0])
        if self.bounds["x"][1] is not None:
            plt.xlim(right=self.bounds["x"][1])
        if self.bounds["y"][0] is not None:
            plt.ylim(bottom=self.bounds["y"][0])
        if self.bounds["y"][1] is not None:
            plt.ylim(top=self.bounds["y"][1])

    def show(self):
        self.update_plt()
        plt.show()

    def save(self, path, dpi=None):
        self.update_plt()
        if dpi is None:
            plt.savefig(fname=path)
        else:
            plt.savefig(fname=path, dpi=dpi)

    def add_points(self, new_point_dataset, new_column_index_pair=None, color=None):
        self.point_datasets.append(new_point_dataset)
        self.point_column_index_pairs.append((0, 1) if new_column_index_pair is None else (new_column_index_pair[0] if new_column_index_pair[0] is not None else 0, new_column_index_pair[1] if new_column_index_pair[1] is not None else 1))
        self.point_colors.append(color)
        self.update_plt()

    def add_curve(self, curve_dataset, new_column_index_pair=None, color=None):
        self.curve_datasets.append(curve_dataset)
        self.curve_column_index_pairs.append((0, 1) if new_column_index_pair is None else (new_column_index_pair[0] if new_column_index_pair[0] is not None else 0, new_column_index_pair[1] if new_column_index_pair[1] is not None else 1))
        self.point_colors.append(color)
        self.update_plt()

    def add_visualizers(self, new_visualizers):
        if type(new_visualizers) is not list:
            self.visualizers.append(new_visualizers)
        else:
            self.visualizers += new_visualizers
    def update_legend(self):
        entries = [{"name": self.point_datasets[i].title,
                                       "color": Plot.generate_color(i) if self.point_datasets[i].plot_color is None else self.point_datasets[i].plot_color} for i in index_of(self.point_datasets)]
        entries += [{"name": self.curve_datasets[i].title,
                                       "color": Plot.generate_color(i) if self.curve_datasets[i].plot_color is None else self.curve_datasets[i].plot_color} for i in index_of(self.curve_datasets)]
        self.legend = Legend(entries=entries)

    def __init__(self, point_datasets=None, curve_datasets=None, point_column_index_pairs=None, curve_column_index_pairs=None, title="Title", x_label=None, y_label=None):
        if curve_datasets is None:
            curve_datasets = []
        if point_datasets is None:
            point_datasets = []

        if type(point_datasets) is Dataset:
            point_datasets = [point_datasets]
        if type(curve_datasets) is Dataset:
            curve_datasets = [curve_datasets]

        self.fig, self.axes = plt.subplots(figsize=(12, 7.5))
        self.title = title
        self.axes.grid(which="major", linestyle="-", linewidth=1)
        self.axes.grid(which="minor", linestyle=":", linewidth=0.75)
        self.axes.xaxis.set_minor_locator(tck.AutoMinorLocator(4))
        self.axes.yaxis.set_minor_locator(tck.AutoMinorLocator(4))
        self.point_datasets = point_datasets
        self.curve_datasets = curve_datasets
        self.sigma_interval = 1
        self.legend = Legend()
        self.bounds = {"x": [None, None],
                  "y": [None, None]}
        self.visualizers = []

        self.point_column_index_pairs = [[(0 if point_column_index_pairs is None or point_column_index_pairs[pcipi] is None or point_column_index_pairs[pcipi][0] is None else point_column_index_pairs[pcipi][0]), 1 if point_column_index_pairs is None or point_column_index_pairs[pcipi] is None or point_column_index_pairs[pcipi][1] is None else point_column_index_pairs[pcipi][1]] for pcipi in index_of(point_datasets)]
        self.curve_column_index_pairs = [[(0 if curve_column_index_pairs is None or curve_column_index_pairs[ccipi] is None or curve_column_index_pairs[ccipi][0] is None else curve_column_index_pairs[ccipi][0]), 1 if curve_column_index_pairs is None or curve_column_index_pairs[ccipi] is None or curve_column_index_pairs[ccipi][1] is None else curve_column_index_pairs[ccipi][1]] for ccipi in index_of(curve_datasets)]

        self.point_colors = [None for pds in self.point_datasets]
        self.curve_colors = [None for cds in self.curve_datasets]
        for i in index_of(self.point_column_index_pairs):
            for j in index_of(self.point_column_index_pairs[i]):
                if type(self.point_column_index_pairs[i][j]) is str:
                    self.point_column_index_pairs[i][j] = self.point_datasets[i].get_col_names().index(self.point_column_index_pairs[i][j])

        self.update_legend()

        # TODO:CHECK ALL LABELS
        self.x_label = x_label if x_label is not None else (self.point_datasets[0].get_col_names()[self.point_column_index_pairs[0][0]] if len(self.point_datasets) > 0 else self.curve_datasets[0].get_col_names()[self.curve_column_index_pairs[0][0]])
        self.y_label = y_label if y_label is not None else (self.point_datasets[0].get_col_names()[self.point_column_index_pairs[0][1]] if len(self.point_datasets) > 0 else self.curve_datasets[0].get_col_names()[self.curve_column_index_pairs[0][1]])
        for point_dataset in point_datasets:
            point_dataset.x_label = self.x_label
            point_dataset.y_label = self.y_label
        for curve_dataset in curve_datasets:
            curve_dataset.x_label = self.x_label
            curve_dataset.y_label = self.y_label


class Covariance_Matrix:

    def inverse(self, sigma_list):
        return np.linalg.inv(self.at(sigma_list))

    def at(self, sigma_list, as_list=False):
        arr = [[self._correlation_matrix[row_i][cell_i] * sigma_list[cell_i] * sigma_list[row_i] for cell_i in
                index_of(self._correlation_matrix[row_i])] for row_i in index_of(self._correlation_matrix)]
        if as_list:
            return arr
        return np.matrix(arr)

    def covariance_coefficient(self, variable_names, sigma):
        return self._correlation_matrix[self.variables[variable_names[0]]][self.variables[variable_names[1]]] * sigma[
            0] * sigma[1]

    def resulting_sigma(self, formula, sigma_list):
        res = 0
        for i in index_of(self.variables):
            for j in index_of(self.variables):
                res += self.covariance_coefficient((self.variables[i], self.variables[j]),
                                                   (sigma_list[i], sigma_list[j])) * smp.diff(formula.sympy,
                                                                                              self.variables[
                                                                                                  i]) * smp.diff(
                    formula.sympy, self.variables[j])

        return mt.sqrt(res)

    def __init__(self, variable_names, covariance_coefficients=None):
        self.variables = variable_names
        self._correlation_matrix = []
        if covariance_coefficients is None:
            covariance_coefficients = {}
        for var in variable_names:
            self._correlation_matrix.append([])
            for var2 in variable_names:
                try:
                    self._correlation_matrix[-1].append(covariance_coefficients[str(var) + " " + str(var2)])
                except KeyError:
                    self._correlation_matrix[-1].append(1 if str(var) is str(var2) else 0)

        self.numpy = np.matrix(self._correlation_matrix)


class Fit:
    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, new_dataset):
        self._dataset = new_dataset
        self.update()

    @staticmethod
    def fit_linear(x, y):
        one_over_sig_sqr = dc.Decimal(0)
        x_over_sig_sqr = dc.Decimal(0)
        x_sqr_over_sig_sqr = dc.Decimal(0)
        x_y_over_sig_sqr = dc.Decimal(0)
        y_over_sig_sqr = dc.Decimal(0)

        for i in index_of(x):
            one_over_sig_sqr += dc.Decimal(dc.Decimal(1) / y[i].e ** dc.Decimal(2))
            x_sqr_over_sig_sqr += dc.Decimal(x[i].v ** 2 / y[i].e ** dc.Decimal(2))
            x_over_sig_sqr += dc.Decimal(x[i].v / y[i].e ** dc.Decimal(2))
            x_y_over_sig_sqr += dc.Decimal(x[i].v * y[i].v / y[i].e ** dc.Decimal(2))
            y_over_sig_sqr += dc.Decimal(y[i].v / y[i].e ** dc.Decimal(2))

        delta = dc.Decimal(one_over_sig_sqr * x_sqr_over_sig_sqr - x_over_sig_sqr ** dc.Decimal(2))
        m = Val(0)
        b = Val(0)
        m.set(dc.Decimal(
            (dc.Decimal(1) / delta * (one_over_sig_sqr * x_y_over_sig_sqr - x_over_sig_sqr * y_over_sig_sqr))))
        m.set_err(dc.Decimal(mt.sqrt(dc.Decimal((1) / delta * one_over_sig_sqr))))
        b.set(dc.Decimal(
            dc.Decimal(1) / delta * (x_sqr_over_sig_sqr * y_over_sig_sqr - x_over_sig_sqr * x_y_over_sig_sqr)))
        b.set_err(dc.Decimal(mt.sqrt(dc.Decimal(1) / delta * x_sqr_over_sig_sqr)))

        chi_sqr = Val("0")
        for i in index_of(x):
            chi_sqr.v += dc.Decimal((dc.Decimal(1) / y[i].e * (y[i].v - m.v * x[i].v - b.v)) ** dc.Decimal(2))

        return m, b, chi_sqr

    @staticmethod
    def _fit_chi_squared_untested_algebraic(x, y, formula, estimated_parameters, precision, x_variable, fit_variables,
                                            covariance_matrix):
        D = np.matrix([[Formula(formula.variables, sympy=smp.diff(formula.at([x_variable, x[i]]), fit_variables[j])).at(
            [[fit_variables[k], estimated_parameters[k]] for k in index_of(fit_variables)], as_val=True).v for i in
                        index_of(x)] for j in index_of(fit_variables)])
        var_val_pairs = [[fit_variables[i], estimated_parameters[i]] for i in index_of(estimated_parameters)]
        f = np.matrix(
            [formula.at([cpy.deepcopy(var_val_pairs).append([x_variable, x[k]])], as_val=True).v for k in index_of(x)])

        residual = np.subtract(np.matrix([y]), f)
        delta_a = np.matmul(D.transpose(), np.linalg.inv(covariance_matrix))
        delta_a = np.matmul(delta_a, D)
        delta_a = np.matmul(np.linalg.inv(delta_a), D.transpose())
        delta_a = np.matmul(delta_a, np.linalg.inv(covariance_matrix))
        delta_a = np.matmul(delta_a, residual)

        length_delta_a = 0
        for component in delta_a[0]:
            length_delta_a += component ** 2

        length_delta_a = np.sqrt(length_delta_a)
        new_a = list(np.add(estimated_parameters, delta_a[0]))
        if length_delta_a < precision:
            M = np.matrix([y])
            M = np.subtract(M, np.matmul(D, delta_a))
            M = np.subtract(M, f)
            chi_squared = np.matmul(M.transpose(), np.linalg.inv(covariance_matrix))
            chi_squared = np.matmul(chi_squared, M)

            if abs(chi_squared - len(x) + len(fit_variables)) < precision * chi_squared:
                covariance_matrix_a = D.transpose()
                covariance_matrix_a = np.matmul(covariance_matrix_a, np.linalg.inv(covariance_matrix))
                covariance_matrix_a = np.matmul(covariance_matrix_a, D)
                covariance_matrix_a = np.linalg.inv(covariance_matrix_a)
                return new_a, covariance_matrix_a
        else:
            Fit.fit_chi_squared(x, y, formula, new_a, precision, x_variable, fit_variables, covariance_matrix)

    def fit_chi_squared(self, x, y, formula, estimated_parameters, x_variable, fit_variables, covariance_matrix, bounds, output_formula_only=False):
        if covariance_matrix is not None:
            covariance_matrix = covariance_matrix.at([y_val.e for y_val in y])
        vars = [x_variable.n]

        for variable in fit_variables:
            vars.append(variable.n)
        if estimated_parameters is None:
            estimated_parameters = [1 for p in fit_variables]
        if bounds is None:
            bounds = ([-mt.inf for p in fit_variables], [mt.inf for p in fit_variables])

        diffs = [smp.utilities.lambdify(vars, smp.diff(formula.sympy, var)) for var in vars[1:]]
        def jacobi(*args):
            res_list = []
            for x in args[0]:
                args_cpy = list(args)
                args_cpy[0] = x
                args_cpy = tuple(args_cpy)
                res = []
                for i in index_of(args[1:]):
                    res.append(diffs[i](*args_cpy))
                res_list.append(res)
            return res_list

        resulting_params, cov_mat, info_dict, mesg, ier = sp.optimize.curve_fit(
            smp.utilities.lambdify(vars, formula.sympy), [x_val.v for x_val in x], [y_val.v for y_val in y],
            estimated_parameters, sigma=covariance_matrix, absolute_sigma=True, full_output=True, bounds=bounds, jac=jacobi, maxfev=1600)

        formula = cpy.deepcopy(formula)
        formula.set_variables([[fit_variables[i], Val(resulting_params[i], np.sqrt(np.diag(cov_mat))[i])] for i in index_of(resulting_params)])

        if output_formula_only:
            return formula

        chi_squared = 0
        for i in index_of(y):
            chi_squared += (y[i].v - formula.at([[x_variable, x[i]]]).v)**2/y[i].e**2
        for i in index_of(resulting_params):
            resulting_params[i] = Val(resulting_params[i], np.sqrt(np.diag(cov_mat))[i])
            return resulting_params, chi_squared, cov_mat

    def k_fold(self, k, preset_folds=None):
        if __debug_extended__:
            print("\n\nPERFORMING K-FOLD TO FORMULA:")
            print(self.formula.latex)
        #preset folds is a dict {'x_lists': [_LIST_OF_LISTS_OF_X_VALS_], 'y_lists': [_LIST_OF_LISTS_OF_Y_VALS_]} where each list in 'x', 'y' represents the x or y values of a single fold
        if preset_folds is not None:
            x_lists = preset_folds["x_lists"]
            y_lists = preset_folds["y_lists"]
        else:
            split_ds = self.dataset.clone()
            x_lists = []
            y_lists = []
            n = len(split_ds.col(self.x_index))
            for j in range(k-1):
                x = []
                y = []
                for i in range(mt.floor(n/k)):
                    chosen_index = rndm.randint(0, len(split_ds.col(self.x_index))-1)
                    x.append(split_ds.col(self.x_index)[chosen_index])
                    y.append(split_ds.col(self.y_index)[chosen_index])
                    split_ds.delete(r_indices=[chosen_index])

                x_lists.append(x)
                y_lists.append(y)
            #put rest of split_ds into last fold:
            x_lists.append(split_ds.col(self.x_index))
            y_lists.append(split_ds.col(self.y_index))

        mses = []#mean squared errors
        for i in range(k):
            x = []
            y = []
            for j in [n for n in range(k) if n != i]:
                x += x_lists[j]
                y += y_lists[j]
            if __debug_extended__:
                print("STARTING", i, "-th FIT")
            formula = self.fit_chi_squared(x, y, self.fit_formula, self.estimated_parameters, self.x_variable, self.fit_variables, None, self.bounds,True)
            mse = 0
            for j in index_of(y_lists[i]):
                mse += (y_lists[i][j].v - formula.at([[self.x_variable, x_lists[i][j]]]).v) ** 2

            if __debug_extended__:
                print("GOT MSE", mse)
            mses.append(mse / len(y_lists[i]))

        CV = 0
        for i in range(k):
            CV += mses[i]

        CV /= k

        return {"CV": CV, "MSEs": mses, "folds": {'x_lists': x_lists, 'y_lists': y_lists}}
    @staticmethod
    def chi_squared(ds, formula, x_variable, x_index=0, y_index=1):
        y = ds.col(y_index)
        x = ds.col(x_index)
        ret = 0
        for i in index_of(ds.col(x_index)):
            ret += (y[i].v - formula.at([[x_variable, x[i]]]).v) ** 2 / y[i].e ** 2
        return ret

    @staticmethod
    def reduced_chi_squared(ds, formula, x_variable, number_of_fit_parameters, x_index=0, y_index=1):
        return Fit.chi_squared(ds, formula, x_variable, x_index, y_index)/(len(ds.col(x_index)) - number_of_fit_parameters)

    def update(self):
        if self.is_linear:
            self.result["m"], self.result["b"], self.result["chi_squared"] = Fit.fit_linear(
                self.dataset.col(self.x_index), self.dataset.col(self.y_index))
            self.result["reduced_chi_squared"]  = self.result["chi_squared"]/(len(self.dataset.col(self.x_index)) - 2)
        else:
            params, chi_squared, cov_mat = self.fit_chi_squared(self.dataset.col(self.x_index),
                                                                self.dataset.col(self.y_index), self.fit_formula,
                                                                self.estimated_parameters, self.x_variable,
                                                                self.fit_variables, self.covariance_matrix, self.bounds)
            for i in index_of(params):
                self.result[self.fit_variables[i].str] = Val(params[i], np.sqrt(np.diag(cov_mat))[i])

            self.result["chi_squared"] = chi_squared
            self.result["reduced_chi_squared"] = chi_squared / (
                    len(self.dataset.col(self.x_index)) - len(self.fit_variables))
            self.result["covariance_matrix"] = cov_mat

    def formula(self):
        if self.is_linear:
            if self.x_variable is None:
                x_name = "x" if type(self._dataset.get_col_names()[self.x_index]) is int else self._dataset.get_col_names()[
                    self.x_index]
            x_var = self.x_variable if self.x_variable is not None else Var(x_name)
            return Formula([x_var], sympy=self.result["m"].v * x_var.n +
                                          self.result["b"].v)
        else:
            var_val_pairs = [[self.fit_variables[i], self.result[self.fit_variables[i].str]]
                             for i in index_of(self.fit_variables)]
            res = self.fit_formula.clone()
            res.set_variables(var_val_pairs)
            return res

    def __init__(self, dataset, x_index=0, y_index=1, is_linear=True, fit_formula=None, x_variable=None,
                 fit_variables=None, covariance_matrix=None, estimated_parameters=None, bounds=None):

        self.result = {}
        self.fit_formula = fit_formula
        self._dataset = dataset
        self.x_index = x_index if type(x_index) is int else dataset.get_col_names().index(x_index)
        self.y_index = y_index if type(y_index) is int else dataset.get_col_names().index(y_index)
        self.is_linear = is_linear
        self.x_variable = x_variable
        self.fit_variables = fit_variables
        self.covariance_matrix = covariance_matrix
        self.estimated_parameters = estimated_parameters
        self.bounds = bounds
        self.update()


###################################################################################################
# Best motivateMe() texts:
# I understand that your physics laboratory courses may be draining and downright boring, but don't let these setbacks deter you from your goals. Your previous progress on the lab report was phenomenal, and that is a true testament to your intelligence and hardworking nature. Though the courses may not be implemented as efficiently as they should be, do not let this dull your passions. Remain focused and committed to your goals, and you will successfully complete the lab report in no time. Keep striving for greatness!
