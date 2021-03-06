from argparse import ArgumentParser
from os import path, makedirs
import proso.geography.answers as answer
import proso.geography.decorator as decorator
import proso.geography.difficulty
import proso.geography.user as user
import gc
import numpy as np
import pandas
import sys
from datetime import datetime
import matplotlib.pyplot as plt


def parser_init(required=None):
    parser = ArgumentParser()
    parser.add_argument(
        '-a',
        '--answers',
        metavar='FILE',
        required=_is_required(required, '--answers'),
        help='path to the CSV with answers')
    parser.add_argument(
        '--options',
        metavar='FILE',
        required=_is_required(required, '--options'),
        help='path to the CSV with answer options')
    parser.add_argument(
        '--ab-values',
        metavar='FILE',
        dest='ab_values',
        required=_is_required(required, '--ab-values'),
        help='path to the CSV with ab values')
    parser.add_argument(
        '--answer-ab-values',
        metavar='FILE',
        dest='answer_ab_values',
        required=_is_required(required, '--answer-ab-values'),
        help='path to the CSV with answer ab values')
    parser.add_argument(
        '--places',
        metavar='FILE',
        required=_is_required(required, '--places'),
        help='path to the CSV with places')
    parser.add_argument(
        '-d',
        '--destination',
        metavar='DIR',
        required=True,
        help='path to the directory where the created data will be saved')
    parser.add_argument(
        '-o',
        '--output',
        metavar='EXT',
        dest='output',
        default='png',
        help='extension for the output fles')
    parser.add_argument(
        '--drop-classrooms',
        type=int,
        dest='drop_classrooms',
        help='drop users having some of the first answer from classroom')
    parser.add_argument(
        '--only-classrooms',
        type=int,
        dest='only_classrooms',
        help='only users having some of the first answer from classroom')
    parser.add_argument(
        '--drop-tests',
        action='store_true',
        dest='drop_tests',
        help='drop users having at least one test answer')
    parser.add_argument(
        '--answers-per-user',
        type=int,
        dest='answers_per_user',
        help='drop user having less than the given number of answers')
    parser.add_argument(
        '--data-dir',
        type=str,
        metavar='DIRECTORY',
        dest='data_dir',
        default='./data',
        help='directory with data files, used when the data files are specified')
    parser.add_argument(
        '--storage',
        type=str,
        default='hdf',
        choices=['csv', 'hdf', 'pkl'])
    parser.add_argument(
        '--map-code',
        dest='map_code',
        nargs='+',
        type=str)
    parser.add_argument(
        '--map-type',
        dest='map_type',
        nargs='+',
        type=str)
    parser.add_argument(
        '--place-asked-type',
        dest='place_asked_type',
        nargs='+',
        type=str)
    parser.add_argument(
        '--drop-users',
        dest='drop_users',
        action='store_true',
        help='when filtering the data drop users having invalid answers')
    parser.add_argument(
        '--min-date',
        dest='min_date',
        type=date_limit,
        help='date lower bound for which the data is taken')
    parser.add_argument(
        '--max-date',
        dest='max_date',
        type=date_limit,
        help='date lower bound for which the data is taken')
    parser.add_argument(
        '--drop-outliers',
        dest='drop_outliers',
        type=int)
    parser.add_argument(
        '--verbose',
        dest='verbose',
        action='store_true')
    parser.add_argument(
        '--filter-abvalue',
        nargs='+',
        type=str,
        dest='filter_abvalue')
    return parser


def date_limit(value):
    if len(value) == 10:
        return datetime.strptime(value, '%Y-%m-%d')
    else:
        return datetime.strptime(value, '%Y-%m-%d_%H:%M:%S')


def write_cache(args, dataframe, filename, force_storage=None):
    if not path.exists(args.destination):
        makedirs(args.destination)
    if args.storage == 'csv' or force_storage == 'csv':
        if not path.exists('%s/%s.csv' % (args.destination, filename)):
            print 'writing CSV cache "%s" (%s lines)' % (filename, len(dataframe))
            dataframe.to_csv('%s/%s.csv' % (args.destination, filename), index=False)
    elif args.storage == 'pkl' or force_storage == 'pkl':
        if not path.exists('%s/%s.pkl' % (args.destination, filename)):
            print 'writing PICKLE cache "%s" (%s lines)' % (filename, len(dataframe))
            dataframe.to_pickle('%s/%s.pkl' % (args.destination, filename))
    else:
        print 'writing HDF cache "%s" (%s lines)' % (filename, len(dataframe))
        dataframe.to_hdf('%s/storage.hdf' % args.destination, filename.replace('.', '_'))


def read_cache(args, filename, csv_parser=None):
    try:
        print 'trying to read HDF cache "%s"' % filename
        result = pandas.read_hdf('%s/storage.hdf' % args.destination, filename.replace('.', '_'))
    except:
        print 'failed to read HDF cache "%s"' % filename
        try:
            print 'trying to read PICKLE cache "%s"' % filename
            result = pandas.read_pickle('%s/%s.pkl' % (args.destination, filename))
        except:
            print 'failed to read PICKLE cache "%s"' % filename
            try:
                print 'trying to read CSV cache "%s"' % filename
                if csv_parser:
                    result = csv_parser('%s/%s.csv' % (args.destination, filename))
                else:
                    result = pandas.read_csv('%s/%s.csv' % (args.destination, filename), index_col=False)
                write_cache(args, result, filename, force_storage='pkl')
            except:
                print 'failed to read CSV cache "%s"' % filename
                return None
    print '%s lines loaded' % len(result)
    return result


def data_hash(args):
    return ('apu_%s__dcs_%s__ocs_%s__dts_%s__mc_%s__pat_%s__mt_%s__du_%s__mind_%s__maxd_%s__do_%s__fab_%s' % (
        args.answers_per_user,
        args.drop_classrooms,
        args.only_classrooms,
        args.drop_tests,
        'x'.join(args.map_code if args.map_code else []),
        'x'.join(args.place_asked_type if args.place_asked_type else []),
        'x'.join(args.map_type if args.map_type else []),
        args.drop_users,
        args.min_date,
        args.max_date,
        args.drop_outliers,
        'x'.join(args.filter_abvalue if args.filter_abvalue else []))).replace(' ', '_')


def parser_group(parser, groups):
    parser.add_argument(
        '--groups',
        choices=groups,
        nargs='+',
        help='generate only a limited set of plots')
    parser.add_argument(
        '--skip-groups',
        choices=groups,
        dest='skip_groups',
        nargs='+',
        help='generate only a limited set of plots')
    return parser


def decorator_optimization(answers):
    if len(answers) == 0:
        print "There are no answers to analyze"
        sys.exit()
    decorated = decorator.rolling_success(
        decorator.last_in_session(
            decorator.session_number(answers)))
    return decorated


def load_feedback(args, data):
    cache_filename = 'feedback.rating_%s' % hash(tuple(data['id']))
    csv_parser = lambda f: pandas.read_csv(f, index_col=False, parse_dates=['inserted'])
    feedback = read_cache(args, cache_filename, csv_parser=csv_parser)
    if feedback is not None:
        return feedback
    filename = args.data_dir + '/feedback.rating.csv'
    if not path.exists(filename):
        return None
    feedback = csv_parser(filename)
    feedback = decorator.success_before(feedback[feedback['user'].isin(data['user'].unique())], data)
    write_cache(args, feedback, cache_filename)
    return feedback


def load_answers(args, all_needed=True):
    filename = 'geography.answer_%s' % data_hash(args)
    data_all = None
    if all_needed:
        data_all = load_answers_all(args)
    data = read_cache(args, filename, csv_parser=answer.from_csv)
    if data is not None:
        return data, data_all
    if args.min_date or args.max_date:
        time_filename = 'geography.answer__mind_%s__maxd_%s__du_%s' % (args.min_date, args.max_date, args.drop_users)
        data = read_cache(args, time_filename, csv_parser=answer.from_csv)
    if data is None:
        if all_needed:
            data = data_all
        else:
            data = load_answers_all(args)
    if args.min_date:
        data = answer.apply_filter(data, lambda d: d['inserted'] >= args.min_date, drop_users=args.drop_users)
    if args.max_date:
        data = answer.apply_filter(data, lambda d: d['inserted'] <= args.max_date, drop_users=args.drop_users)
    if args.min_date or args.max_date:
        write_cache(args, data, time_filename)
    if args.map_code:
        data = answer.apply_filter(data, lambda x: x['place_map_code'] in args.map_code, drop_users=args.drop_users)
    if args.map_type:
        data = answer.apply_filter(data, lambda x: x['place_map_type'] in args.map_type, drop_users=args.drop_users)
    if args.place_asked_type:
        data = answer.apply_filter(data, lambda x: x['place_asked_type'] in args.place_asked_type, drop_users=args.drop_users)
    if args.map_code or args.place_asked_type or args.map_type:
        del data['rolling_success']
        del data['last_in_session']
        del data['session_number']
        data = decorator_optimization(data)
    if args.filter_abvalue:
        data = answer.apply_filter(data, lambda d: all(map(lambda g: g in d['ab_values'], args.filter_abvalue)))
    if args.drop_tests:
        data = answer.apply_filter(data, lambda x: np.isnan(x['test_id']))
    if args.drop_classrooms and args.only_classrooms:
        raise Exception("Can't have data both with and without classrooms")
    if args.drop_classrooms:
        data, _ = answer.drop_classrooms(data, classroom_size=args.drop_classrooms)
    if args.only_classrooms:
        _, data = answer.drop_classrooms(data, classroom_size=args.only_classrooms)
    if args.answers_per_user:
        data = answer.drop_users_by_answers(data, answer_limit_min=args.answers_per_user)
    if args.drop_outliers:
        answers_per_user = user.answers_per_user(data)
        [limit_min, limit_max] = np.percentile(answers_per_user.values(), [args.drop_outliers, 100 - args.drop_outliers])
        valid_users = map(lambda (u, _): u, filter(lambda (u, n): n >= limit_min and n <= limit_max, answers_per_user.items()))
        data = data[data['user'].isin(valid_users)]
    write_cache(args, data, filename)
    return data, data_all


def load_answers_all(args):
    data = read_cache(args, 'geography.answer', csv_parser=answer.from_csv)
    if data is not None:
        return data
    answers_file = args.answers if args.answers else args.data_dir + '/geography.answer.csv'
    options_file = args.options if args.options else args.data_dir + '/geography.answer_options.csv'
    ab_values_file = args.ab_values if args.ab_values else args.data_dir + '/geography.ab_value.csv'
    answer_ab_values_file = args.answer_ab_values if args.answer_ab_values else args.data_dir + '/geography.answer_ab_values.csv'
    place_file = args.places if args.places else args.data_dir + '/geography.place.csv'
    if not path.exists(options_file):
        options_file = None
    if not path.exists(ab_values_file):
        ab_values_file = None
    if not path.exists(answer_ab_values_file):
        answer_ab_values_file = None
    data = answer.from_csv(
        answer_csv=answers_file,
        answer_options_csv=options_file,
        answer_ab_values_csv=answer_ab_values_file,
        ab_value_csv=ab_values_file,
        place_csv=place_file,
        should_sort=False)
    data = decorator_optimization(data)
    write_cache(args, data, 'geography.answer')
    return data


def load_difficulty_and_prior_skill(args, data_all):
    difficulty = read_cache(args, 'difficulty')
    prior_skill = read_cache(args, 'prior_skill')
    if difficulty is not None or data_all is None:
        return (
            proso.geography.difficulty.dataframe_to_difficulty(difficulty) if difficulty is not None else None,
            proso.geography.user.dataframe_to_prior_skill(prior_skill) if prior_skill is not None else None
        )
    difficulty, prior_skill = proso.geography.difficulty.prepare_difficulty_and_prior_skill(data_all)
    write_cache(args, proso.geography.difficulty.difficulty_to_dataframe(difficulty), 'difficulty')
    write_cache(args, proso.geography.user.prior_skill_to_dataframe(prior_skill), 'prior_skill')
    gc.collect()
    return difficulty, prior_skill


def get_destination(args, prefix=''):
    dest_file = args.destination + '/' + prefix + data_hash(args)
    if not path.exists(dest_file):
        makedirs(dest_file)
    return dest_file


def savefig(args, figure, name, prefix='', resize=1):
    filename = get_destination(args, prefix) + '/' + name + '.' + args.output
    resized = map(lambda x: resize * x, figure.get_size_inches())
    figure.set_size_inches(resized[0], resized[1])
    figure.tight_layout()
    figure.savefig(filename, bbox_inches='tight')
    print "Saving", filename
    plt.close(figure)


def is_group(args, group):
    return (not args.groups or group in args.groups) and (not args.skip_groups or group not in args.skip_groups)


def is_any_group(args, groups):
    return any([is_group(args, group) for group in groups])


def _is_required(required, name):
    return required is not None and name in required
