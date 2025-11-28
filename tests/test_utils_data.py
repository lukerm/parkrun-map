import string

from parkrun_map.utils.data import get_course_data


def test_get_course_data_no_filters():
    df_courses = get_course_data()
    assert len(df_courses) >= 2557
    assert 'airliebeach' in df_courses['event_name'].values
    assert 'winthroptrailhead' in df_courses['event_name'].values


def test_get_course_data_event_name_letters():
    df_courses_a = get_course_data(event_name_letters='a')
    assert 93 <= len(df_courses_a) < 100  # 93 at time of writing
    assert 'airliebeach' in df_courses_a['event_name'].values
    assert 'winthroptrailhead' not in df_courses_a['event_name'].values

    df_courses_A = get_course_data(event_name_letters='A')
    assert len(df_courses_A) == len(df_courses_a)

    df_courses_b = get_course_data(event_name_letters='b')
    assert 246 <= len(df_courses_b) < 250  # 246 at time of writing
    assert 'airliebeach' not in df_courses_b['event_name'].values
    assert 'bairnsdale' in df_courses_b['event_name'].values
    assert 'winthroptrailhead' not in df_courses_b['event_name'].values

    df_courses_a_or_b = get_course_data(event_name_letters='ab')
    assert len(df_courses_a_or_b) == len(df_courses_a) + len(df_courses_b)
    assert 'airliebeach' in df_courses_a_or_b['event_name'].values
    assert 'bairnsdale' in df_courses_a_or_b['event_name'].values
    assert 'winthroptrailhead' not in df_courses_a_or_b['event_name'].values

    df_courses_all_letters = get_course_data(event_name_letters=string.ascii_letters)
    assert len(df_courses_all_letters) == len(get_course_data())


def test_get_course_data_hemisphere():
    df_courses_northern = get_course_data(only_north_hemisphere=True)
    assert df_courses_northern['latitude'].min() >= 0

    df_courses_southern = get_course_data(only_north_hemisphere=False)
    assert df_courses_southern['latitude'].max() < 0

    df_courses_northern_or_southern = get_course_data(only_north_hemisphere=None)
    assert len(df_courses_northern_or_southern) == len(df_courses_northern) + len(df_courses_southern)