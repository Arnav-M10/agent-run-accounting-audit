"""Generate the manuscript's descriptive denominator figure from audit outputs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
cmu = json.loads((ROOT / 'audit_results.json').read_text())
wild = json.loads((ROOT / 'independent_results.json').read_text())['selected_model_summary']
browse = cmu['domain_model']['search/browsecomp']['DeepSeek-V3.2']
fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.8))
fig.patch.set_facecolor('white')
panels = [
    ('CMU · DeepSeek-V3.2 · BrowseComp',
     ['All initiated attempts\n69 / 496', 'Retained trajectories\n69 / 160'],
     [100 * browse['known_attempt_mean_reward_removed_zero'], 100 * browse['complete_mean_reward']],
     'Binary success (%)'),
    ('WildClawBench · Claude Fable 5',
     ['All released tasks\nn = 60', 'Assistant-ending traces\nn = 55'],
     [100 * wild['all_mean_score'], 100 * wild['assistant_ending_mean_score']],
     'Mean native task score (%)'),
]
for ax, (title, labels, values, ylabel) in zip(axes, panels):
    ax.bar(range(2), values, width=.56, color=['#245b87', '#c26835'])
    ax.set_xticks(range(2)); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 80); ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, pad=16)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=.17); ax.set_axisbelow(True)
    for idx, value in enumerate(values):
        ax.text(idx, value + 1.8, '{:.1f}%'.format(value), ha='center', fontsize=12)
fig.subplots_adjust(bottom=.27, top=.87, wspace=.35)
fig.text(.5, .055,
         'Different inclusion policies describe different run populations.\n'
         'CMU excluded attempts are assigned zero; the WildClawBench filter is hypothetical.\n'
         'These descriptive contrasts do not estimate a causal effect of filtering.',
         ha='center', fontsize=9, color='#444444')
out = ROOT / 'figures'; out.mkdir(exist_ok=True)
fig.savefig(out / 'denominator_comparison.png', dpi=220, bbox_inches='tight')
fig.savefig(out / 'denominator_comparison.svg', bbox_inches='tight')
plt.close(fig)
print('Saved figures/denominator_comparison.png and .svg')
