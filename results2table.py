import pandas as pd
import scipy.stats as stats
import numpy as np
import click
from utils import PythonLiteralOption, t_test_p_value
import pyperclip

@click.command()
@click.option('--file', default="./data.csv", help='File to read')
@click.option('--sep', default=",", help='Separator')
@click.option('--model', cls=PythonLiteralOption, default=[], help='Your model(s) name')
@click.option('--model_col', default="model", help='Column name for model name')
@click.option('--dataset_col', default=None, help='Columns to group by')
@click.option('--metric', cls=PythonLiteralOption, default=[], help='Your metric(s) name')
@click.option('--precision', default=4, help='Precision of metric')
@click.option('--output', default=None, help='File to write')
def generate_latex_table(file, sep, model, model_col, dataset_col, metric, precision, output):
    prec = '{:.'+str(precision)+"f}"
    if dataset_col is None:
        usecols = [model_col]  + metric
    else:
        usecols = [model_col] + [dataset_col] + metric
    df = pd.read_csv(file, sep=sep, usecols=usecols)
    if dataset_col is None:
        groups = df.groupby([model_col]).agg([np.mean, 'std'])
    else:
        groups = df.groupby([dataset_col] + [model_col]).agg([np.mean, 'std'])
    groups = groups.reset_index()
    groups = groups.fillna(0)
    models = groups[model_col].unique().tolist()
    models = [model_name for model_name in models if model_name not in model] + model
    
    latex_str = '%%\\usepackage{multirow}\n%%\\usepackage{ulem}\n\\begin{table}[htbp]\n\\centering\n\\caption{The overview of performances comparision. The best result is marked in \\textbf{bold} and the second best result is marked with \\uline{underline}. * indicates that \\MODELNAME significantly outperforms the best baseline based on one-tail $t\\text{-}test$ ($p\\text{-}value < 0.05$)}\n'
    
    latex_str += '''\\begin{tabular}'''
    
    if dataset_col is not None:
        datasets = groups[dataset_col].unique().tolist()
        latex_str += '{l' + 'c' * len(metric) * len(datasets) + '}\n'
        latex_str += '\\hline\n' ## Top line of the table.
        for dataset in datasets:
            latex_str += '& \\multicolumn{' + str(len(metric)) + '}{c}{' + dataset + '} '
        latex_str += '\\\\' + '\cline{2-' + str(len(metric) * len(datasets)) + '}' +'\n'
        for dataset in datasets:
            latex_str += '& ' + ' & '.join(metric)
        latex_str += '\\\\\n'
        latex_str += '\\hline\n'
        
        model_line_flag = True
        for model_name in models:
            if model_name in model and model_line_flag:
                latex_str += '\\hline\n'
                model_line_flag = False
            latex_str +=  model_name
            for dataset in datasets:
                group_dataset = groups[groups[dataset_col] == dataset].copy()
                if not any(group_dataset[model_col] == model_name):
                    for metric_name in metric:
                        latex_str += '& -'
                    continue
                for metric_name in metric:
                    group_dataset[metric_name+'ranks'] = list(stats.rankdata(-1 * group_dataset[metric_name]['mean']))
                    rank = group_dataset[group_dataset[model_col]==model_name][metric_name+'ranks'].values[0]
                    if int(rank) == 1:
                        latex_str += ' & \\textbf{' + prec.format(group_dataset[group_dataset[model_col]==model_name][metric_name]['mean'].values[0]) + '}'
                    elif int(rank) == 2:
                        latex_str += ' & \\uline{' + prec.format(group_dataset[group_dataset[model_col]==model_name][metric_name]['mean'].values[0]) + '}'
                    else:
                        latex_str += ' & ' + prec.format(group_dataset[group_dataset[model_col]==model_name][metric_name]['mean'].values[0])
                           
                    if model_name in model and int(rank) <= len(model): # wether significant better than baselines
                        baseline_idx = group_dataset[~group_dataset[model_col].isin(model)][metric_name]['mean'].idxmax()
                        baseline = group_dataset.loc[baseline_idx, model_col].values[0]
                        N1, N2 = df[(df[dataset_col] == dataset) & (df[model_col] == model_name)][metric_name].count(), df[(df[dataset_col] == dataset) & (df[model_col] == baseline)][metric_name].count()
                        x1, x2 = group_dataset[group_dataset[model_col]==model_name][metric_name]['mean'].values[0], group_dataset[group_dataset[model_col]==baseline][metric_name]['mean'].values[0]
                        s1, s2 = group_dataset[group_dataset[model_col]==model_name][metric_name]['std'].values[0], group_dataset[group_dataset[model_col]==baseline][metric_name]['std'].values[0]
                        significant = t_test_p_value(x1, x2, s1, s2, N1, N2)
                        if significant:
                            latex_str += '$^*$'
                    latex_str += '$\pm$' + prec.format(group_dataset[group_dataset[model_col]==model_name][metric_name]['std'].values[0])                   
            latex_str += '\\\\\n'
                                    
    else:
        latex_str += r'{l' + 'c' * len(metric) + '}\n'
        latex_str += '\\hline\n' ## Top line of the table.
        latex_str += ' & ' + ' & '.join(metric)
        latex_str += '\\\\\n'
        latex_str += '\hline\n'
        model_line_flag = True
        for model_name in models:
            if model_name in model and model_line_flag:
                latex_str += '\\hline\n'
                model_line_flag = False
            latex_str +=  model_name
            for metric_name in metric:
                groups[metric_name+'ranks'] = list(stats.rankdata(-1 * groups[metric_name]['mean']))
                rank = groups[groups[model_col]==model_name][metric_name+'ranks'].values[0]
                if int(rank) == 1:
                    latex_str += ' & \\textbf{' + prec.format(groups[groups[model_col]==model_name][metric_name]['mean'].values[0]) + '}'
                elif int(rank) == 2:
                    latex_str += ' & \\uline{' + prec.format(groups[groups[model_col]==model_name][metric_name]['mean'].values[0]) + '}'
                else:
                    latex_str += ' & ' + prec.format(groups[groups[model_col]==model_name][metric_name]['mean'].values[0])
                           
                if model_name in model and int(rank) <= len(model): # wether significant better than baselines
                    baseline_idx = groups[~groups[model_col].isin(model)][metric_name]['mean'].idxmax()
                    baseline = groups.loc[baseline_idx, model_col].values[0]
                    N1, N2 = df[df[model_col] == model_name][metric_name].count(), df[df[model_col] == baseline][metric_name].count()
                    x1, x2 = groups[groups[model_col]==model_name][metric_name]['mean'].values[0], groups[groups[model_col]==baseline][metric_name]['mean'].values[0]
                    s1, s2 = groups[groups[model_col]==model_name][metric_name]['std'].values[0], groups[groups[model_col]==baseline][metric_name]['std'].values[0]
                    significant = t_test_p_value(x1, x2, s1, s2, N1, N2)
                    if significant:
                        latex_str += '$^*$'
                latex_str += '$\pm$' + prec.format(groups[groups[model_col]==model_name][metric_name]['std'].values[0])                   
            latex_str += '\\\\\n'
            
        
    latex_str += '\\hline\n' ## Bottom line of the table.
    latex_str += '''\\end{tabular}\n\\end{table}'''
    pyperclip.copy(latex_str)   # copy to clipboard
    if output is not None:
        with open(output, 'w') as f:
            f.write(latex_str)
    return latex_str

if __name__ == '__main__':
   generate_latex_table() 