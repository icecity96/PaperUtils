import click
import ast
import math
import scipy.stats as stats


class PythonLiteralOption(click.Option):
    """Code copy from https://stackoverflow.com/questions/47631914/how-to-pass-several-list-of-arguments-to-click-option"""
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)

def t_test_p_value(x1, x2, s1, s2, n1, n2):
    s1, s2 = s1/math.sqrt(n1), s2/math.sqrt(n2)
    if s1 < 1e-10 and s2 < 1e-10:
        return x1 > x2
    if n2 == 1: # one sample
        t = (x1 - x2)/(s1/math.sqrt(n1))
        free_dom = n1
    elif s2 != 0 and (0.5 < s1/s2 < 2):
        s_p = math.sqrt(
            ((n1 - 1) * (s1 ** 2) + (n2 - 1) * (s2 ** 2) ) / (n1 + n2 - 2)
        )
        t = (x1 - x2) / (s_p * math.sqrt(1 / n1 + 1 / n2))
        free_dom = n1 + n2 - 2
    else:
        s_p = math.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
        t = (x1 - x2) / s_p
        free_dom = ((s1 ** 2) / n1 + (s2 ** 2) / n2) ** 2 / ((s1 ** 2 / n1)**2/(n1-1) + (s2 ** 2 / n2)**2/(n2-1))
    p = stats.t.sf(t, free_dom)
    return p < 0.05
    