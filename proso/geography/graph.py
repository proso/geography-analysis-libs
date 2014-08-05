import session
import decorator
import user
import overtime
import success
import numpy
import scipy.stats


def plot_user_ratio(figure, answers, group_column, group_name_mapping=None, answer_numbers=None, session_numbers=None):
    ax = figure.add_subplot(111)
    group_names = []
    to_plots = []
    labels = None
    for group_name, group_data in answers.groupby(group_column):
        to_plot = []
        current_labels = []
        if answer_numbers is not None:
            for num in answer_numbers:
                to_plot.append(user.user_ratio(
                    group_data,
                    answer_number=num))
                current_labels.append(str(num) + ' answers')
        else:
            for num in session_numbers:
                to_plot.append(user.user_ratio(
                    group_data,
                    session_number=num))
                current_labels.append(str(num) + ' sessions')
        labels = current_labels
        to_plots.append(to_plot)
        group_names.append(group_name_mapping[group_name] if group_name_mapping else group_name)

    to_plots = map(list, zip(*to_plots))
    ax.set_xlabel(group_column)
    ax.set_ylabel('Ratio of Users')
    for to_plot, label in zip(to_plots, labels):
        group_names, to_plot = zip(*sorted(zip(group_names, to_plot)))
        ax.plot(group_names, to_plot, label=label)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))


def boxplot_success_per_user(figure, answers, group_column, group_name_mapping=None):
    ax = figure.add_subplot(111)
    labels = []
    to_plot = []
    for group_name, group_data in answers.groupby(group_column):
        s = success.success_per_user(group_data).values()
        to_plot.append(s)
        labels.append(
            str(group_name_mapping[group_name] if group_name_mapping else group_name) + '\n(' + str(len(s)) + ')')
    _boxplot(ax, to_plot, labels)


def boxplot_answers_per_user(figure, answers, group_column, group_name_mapping=None):
    ax = figure.add_subplot(111)
    labels = []
    to_plot = []
    for group_name, group_data in answers.groupby(group_column):
        number = user.answers_per_user(group_data)
        to_plot.append(number.values())
        labels.append(
            str(group_name_mapping[group_name] if group_name_mapping else group_name) + '\n(' + str(len(number)) + ')')
    ax.set_yscale('log')
    ax.set_xlabel(group_column)
    ax.set_ylabel('number of answers')
    _boxplot(ax, to_plot, labels)
    figure.tight_layout()


def hist_answers_per_user(figure, answers, group_column, group_name_mapping=None):
    ax = figure.add_subplot(111)
    to_plots = []
    group_names = []
    for group_name, group_data in answers.groupby(group_column):
        to_plots.append(numpy.log10(user.answers_per_user(group_data).values()))
        group_names.append(group_name)
    if group_name_mapping:
        group_names = [group_name_mapping[group_name] for group_name in group_names]
    else:
        group_names = map(str, group_names)
    group_names, to_plots = zip(*sorted(zip(group_names, to_plots)))
    ax.hist(
        to_plots,
        label=[group_name + ' (' + str(len(to_plot)) + ')' for group_name, to_plot in zip(group_names, to_plots)],
        normed=True,
        )
    ax.legend()
    ax.set_xlabel("Number of Answers (log)")
    ax.set_ylabel("Number of Users (normed)")
    figure.tight_layout()


def hist_rolling_success(figure, answers, prior_skill):
    limits = numpy.percentile(prior_skill.values(), [25, 75])
    answers_low = answers[
        answers['user'].apply(lambda user: prior_skill[user] < limits[0])]
    answers_medium = answers[
        answers['user'].apply(
            lambda user: prior_skill[user] >= limits[0] and prior_skill[user] < limits[1])]
    answers_high = answers[
        answers['user'].apply(lambda user: prior_skill[user] >= limits[1])]
    ax = figure.add_subplot(111)
    ax.hist(
        [
            zip(*success.rolling_success_per_user(answers_low).values())[0],
            zip(*success.rolling_success_per_user(answers_medium).values())[0],
            zip(*success.rolling_success_per_user(answers_high).values())[0]
        ],
        label=['Users with Low Skill', 'Users with Medium Skill', 'Users with High Skill'],
        bins=10,
        normed=True)
    ax.legend(loc='upper left')
    figure.tight_layout()


def boxplot_success_diff(figure, answers, group_column, session_number_first, session_number_second):
    ax = figure.add_subplot(111)
    labels = []
    to_plot = []
    for group_name, group_data in answers.groupby(group_column):
        diffs = session.session_success_diffs(
            group_data,
            session_number_first,
            session_number_second)
        to_plot.append(diffs)
        labels.append(group_name + '\n(' + str(len(diffs)) + ')')
    _boxplot(ax, to_plot, labels)
    ax.set_xlabel(group_column)
    ax.set_ylabel('relative success difference')


def boxplot_prior_skill_diff(figure, answers, difficulty, group_column, session_number_first, session_number_second):
    ax = figure.add_subplot(111)
    labels = []
    to_plot = []
    for group_name, group_data in answers.groupby(group_column):
        diffs = session.session_prior_skill_diffs(
            group_data,
            difficulty,
            session_number_first,
            session_number_second)
        to_plot.append(diffs)
        labels.append(group_name + '\n(' + str(len(diffs)) + ')')
    _boxplot(ax, to_plot, labels)
    ax.set_yscale('log')
    ax.set_xlabel(group_column)
    ax.set_ylabel('relative difference between prior skills')


def plot_answers_per_week(figure, answers):
    ax1 = figure.add_subplot(111)
    to_plot = sorted(overtime.answers_per_week(answers).items())
    xs = range(len(to_plot))
    ax1.plot(xs, zip(*to_plot)[1], 'b-o')
    ax1.set_xlabel('week from project start')
    ax1.set_ylabel('average number of answers per user', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    to_plot = sorted(overtime.users_per_week(answers).items())
    xs = range(len(to_plot))
    ax2 = ax1.twinx()
    ax2.set_ylabel('number of users', color='r')
    ax2.plot(xs, zip(*to_plot)[1], 'r-v', linewidth=1)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')


def plot_stay_on_rolling_success(figure, answers, prior_skill):
    limits = numpy.percentile(prior_skill.values(), [25, 75])
    answers_low = answers[
        answers['user'].apply(lambda user: prior_skill[user] < limits[0])]
    answers_medium = answers[
        answers['user'].apply(
            lambda user: prior_skill[user] >= limits[0] and prior_skill[user] < limits[1])]
    answers_high = answers[
        answers['user'].apply(lambda user: prior_skill[user] >= limits[1])]
    stay_all = sorted(success.stay_on_rolling_success(answers).items())
    stay_low = sorted(success.stay_on_rolling_success(answers_low).items())
    stay_medium = sorted(success.stay_on_rolling_success(answers_medium).items())
    stay_high = sorted(success.stay_on_rolling_success(answers_high).items())
    to_plot = {
        'All Users': stay_all,
        'Users with Low Skill': stay_low,
        'Users with Medium Skill': stay_medium,
        'Users with High Skill': stay_high
    }
    i = 1
    for title, data in to_plot.items():
        ax = figure.add_subplot(2, 2, i)
        _plot_errorbar(ax, data)
        ax.set_title(title)
        ax.set_xlabel('rolling success rate (last 10 answers)')
        ax.set_ylabel('probability of staying')
        i += 1
    figure.tight_layout()


def plot_session_length(figure, answers):
    if 'session_number' in answers:
        data = answers
    else:
        data = decorator.session_number(answers)
    length = session.session_length(data)
    ax1 = figure.add_subplot(111)
    ax1.plot(zip(*length.items())[0], zip(*length.items())[1], 'b-')
    ax1.set_xlabel('session number')
    ax1.set_ylabel('session length', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    session_limit = max([session_number if portion >= 0.01 else 0
        for session_number, portion in session.session_user_portion(answers).items()])
    users_for_limit = data[data['session_number'] == session_limit]['user'].values
    data_for_limit = data[data['user'].isin(users_for_limit)]
    data_for_limit = data_for_limit[data_for_limit['session_number'] <= session_limit]
    for_limit_length = session.session_length(data_for_limit)
    ax1.plot(
        zip(*for_limit_length.items())[0],
        zip(*for_limit_length.items())[1], 'b--')

    hist = session.session_users(data)
    ax2 = ax1.twinx()
    ax2.set_yscale('log')
    ax2.set_ylabel('number of users', color='r')
    ax2.plot(zip(*hist.items())[0], zip(*hist.items())[1], 'r-.', linewidth=2)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')


def plot_session_prior_skill(figure, answers, difficulty):
    if 'session_number' in answers:
        data = answers
    else:
        data = decorator.session_number(answers)
    prior_skill = session.session_prior_skill(data, difficulty)
    hist = session.session_users(data)
    ax1 = figure.add_subplot(111)
    ax1.plot(zip(*prior_skill.items())[0], zip(*prior_skill.items())[1], 'b-')
    ax1.set_xlabel('session number')
    ax1.set_ylabel('average prior skill', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.set_yscale('log')
    ax2.set_ylabel('number of users', color='r')
    ax2.plot(zip(*hist.items())[0], zip(*hist.items())[1], 'r-.', linewidth=2)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')


def plot_session_success(figure, answers):
    if 'session_number' in answers:
        data = answers
    else:
        data = decorator.session_number(answers)
    success = session.session_success(data)
    hist = session.session_users(data)
    ax1 = figure.add_subplot(111)
    ax1.plot(zip(*success.items())[0], zip(*success.items())[1], 'b-')
    ax1.set_xlabel('session number')
    ax1.set_ylabel('success rate', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.set_yscale('log')
    ax2.set_ylabel('number of users', color='r')
    ax2.plot(zip(*hist.items())[0], zip(*hist.items())[1], 'r-.', linewidth=2)
    for tl in ax2.get_yticklabels():
        tl.set_color('r')


def plot_success_per_week(figure, answers):
    ax = figure.add_subplot(111)
    globally = sorted(overtime.success_per_week(answers).items())
    by_user = sorted(overtime.success_by_user_per_week(answers).items())
    xs = range(len(by_user))
    ax.plot(xs, zip(*globally)[1], 'b-o', label='mean success rate')
    ax.plot(xs, zip(*by_user)[1], 'r-v', label='mean success rate by user')
    ax.set_xlabel('week from project start')
    ax.set_ylabel('success rate')
    ax.legend()


def _boxplot(ax, to_plot, labels):
    if len(to_plot) == 2:
        tstat, pvalue = scipy.stats.ttest_ind(numpy.log(to_plot[0]), numpy.log(to_plot[1]))
        pvalue = str(int(100 * pvalue if pvalue else 0) / 100.0)
        ax.text(
            0.8, 0.8,
            'p-value: ' + str(pvalue),
            horizontalalignment='center', verticalalignment='baseline')
    means = []
    medians = []
    stds = []
    for i in to_plot:
        means.append(numpy.mean(i))
        stds.append(numpy.std(i))
        medians.append(numpy.median(i))
    labels, to_plot, means, medians, stds = zip(*sorted(
        zip(labels, to_plot, means, medians, stds)))
    ax.boxplot(to_plot)
    ax.errorbar(range(1, len(to_plot) + 1), means, yerr=stds, fmt='o')
    for i, m in zip(range(len(means)), means):
        ax.annotate(str(numpy.round(m, 2)), (i + 1, m))
    for i, m in zip(range(len(medians)), medians):
        ax.annotate(str(numpy.round(m, 2)), (i + 1, m))
    ax.set_xticklabels(labels)
    for label in ax.get_xticklabels():
        label.set_rotation(10)


def _plot_errorbar(plt, data, **argw):
    """
        Args:
            plt (matplotlib.axes.Axes):
                handler for matplotlib
            data (dict):
                xs -> (mean, standar deviation)
    """
    plt.errorbar(
        zip(*data)[0],
        zip(*(zip(*data)[1]))[0],
        yerr=zip(*(zip(*data)[1]))[1],
        **argw)
