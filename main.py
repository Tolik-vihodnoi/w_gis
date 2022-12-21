import requests
import pytest


class GisApi:
    def __init__(self, url: str):
        self.url = url

    def req_get(self, params=dict()):
        return requests.get(self.url, params=params)

    def req_get_json(self, params=dict()):
        return requests.get(self.url, params=params).json()


gis = GisApi("https://regions-test.2gis.com/1.0/regions")


def max_val_page():
    total = gis.req_get_json().get("total")
    if total <= 0:
        raise ValueError
    p = (total - 15)
    if p <= 0:
        return 1
    i = divmod(p, 14)[0]
    f = divmod(p, 14)[1]
    if f != 0:
        return 1 + i + 1
    else:
        return 1 + i


def get_all_name_set():
    cities_set = set()
    for n in range(1, (max_val_page() + 1)):
        cc_items = gis.req_get_json(params={'page': n,
                                            'page_size': 15}).get("items")
        for city in cc_items:
            cc_name = city.get('name')
            cities_set.add(cc_name.lower())
    return cities_set


def test_total():
    total = gis.req_get_json().get("total")
    assert total == len(get_all_name_set())


@pytest.mark.parametrize('params', [
    {'q': ''},
    {'q': 'ош'},
    {'q': 'ОЩ'},
    {'q': 12},
    {'q': 'no'},
    {'q': 0},
]
                         )
def test_q_min_symbols(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("error").get('message') == \
           "Параметр 'q' должен быть не менее 3 символов"


@pytest.mark.parametrize(('params', 'expected'), [
    ({'q': 'НОВосибИрСк'}, "Новосибирск"),
    ({'q': 'НОВОСИБИРСК'}, "Новосибирск"),
    ({'q': 'новосибирск'}, "Новосибирск"),
]
                         )
def test_q_registr(params, expected):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("items")[0].get('name') == \
           expected


@pytest.mark.parametrize(('params', 'expected'), [
    ({'q': 'рСк', 'country_code': 'ru'}, 5),
    ({'q': 'рСк', 'country_code': 5, 'page': '0'}, 5),
    ({'q': 'рСк', 'country_code': 'ru', 'page': '0', 'page_size': 'asfd'},
     5),
]
                         )
def test_q_is_ignored(params, expected):
    assert gis.req_get(params=params).ok
    assert len(gis.req_get_json(params=params).get("items")) == expected


@pytest.mark.parametrize(('params', 'expected'), [
    ({'q': 'novosibirsk'}, 0),
    ({'q': 'yjdjcb,bhcr'}, 0),
    ({'q': 'новосибирКС'}, 0),
    ({'q': 0.1}, 0),
    ({'q': "+,."}, 0),
    ({'q': "1,3"}, 0),
    ({'q': False}, 0),
    ({'q': True}, 0),
]
                         )
def test_q_incorrect_values(params, expected):
    assert gis.req_get(params=params).ok
    assert len(gis.req_get_json(params=params).get("items")) == expected


@pytest.mark.parametrize('params', [
    {'q': 999999999999999999999999999999999999999999999999999999999},
    {'q': "новосибирсксочимосквасанктпетербургтагилошкаменьнаобиорел"},
]
                         )
def test_q_max(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("error")


@pytest.mark.parametrize('params', [
    {'q': 'влад'},
    {'q': 'рск'},
    {'q': "кт-пе"},
    {'q': "Нов"},
]
                         )
def test_q_search(params):
    assert gis.req_get(params=params).ok
    city_set_must = set()
    for city in get_all_name_set():
        if params.get('q').lower() in city:
            city_set_must.add(city.lower())
    city_set_resp = set()
    for n in range(1, (max_val_page() + 1)):
        items = gis.req_get_json(params=params).get("items")
        for city in items:
            name = city.get('name')
            city_set_resp.add(name.lower())
    assert city_set_resp == city_set_must


@pytest.mark.parametrize(('params', 'expected'), [
    ({'country_code': 'ru', 'page_size': 15}, 'ru'),
    ({'country_code': 'kg', 'page_size': 15}, 'kg'),
    ({'country_code': 'kz', 'page_size': 15}, 'kz'),
    ({'country_code': 'cz', 'page_size': 15}, 'cz'),
]
                         )
def test_cc_correct_values(params, expected):
    assert gis.req_get(params=params).ok
    cc_items = gis.req_get_json(params=params).get("items")
    for country in cc_items:
        cc_country = country.get('country')
        assert cc_country.get('code') == expected


@pytest.mark.parametrize('params', [
    {'country_code': 'asfase'},
    {'country_code': 'ua'},
    {'country_code': -12},
    {'country_code': 1.2},
    {'country_code': ''},
    {'country_code': 0},
    {'country_code': False},
    {'country_code': True},
]
                         )
def test_cc_incorrect_values(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("error").get('message') == \
           "Параметр 'country_code' может быть одним из следующих значений: " \
           "ru, kg, kz, cz"


def test_cc_default():
    for n in range(1, (max_val_page() + 1)):
        assert gis.req_get(params={'page': n, 'page_size': 15}).ok
    code_list = []
    for n in range(1, (max_val_page() + 1)):
        cc_items = gis.req_get_json(params={'page': n,
                                            'page_size': 15}).get("items")
        for country in cc_items:
            cc_country = country.get('country')
            code = cc_country.get('code')
            code_list.append(code)
    assert set(code_list) == {'ru', 'kz', 'kg', 'cz', 'ua'}


@pytest.mark.parametrize(('params'), [
    {'page': 1},
    {'page': 99},
    {'page': +2},
]
                         )
def test_p_correct_values(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("total")


@pytest.mark.parametrize(('params'), [
    {'page': ''},
    {'page': 0},
    {'page': -2},
    {'page': "+,."},
    {'page': 1.2},
    {'page': False},
    {'page': True}
]
                         )
def test_p_incorrect_values(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("error")


def test_p_default():
    p_size_list = [5, 10, 15]
    for n in p_size_list:
        assert gis.req_get(params={'page_size': n}).ok
    for n in p_size_list:
        assert gis.req_get_json(params={'page_size': 5}).get("items")[0].get(
            'id') == 196


@pytest.mark.parametrize(('params', 'expected'), [
    ({'page_size': 5}, 5),
    ({'page_size': 10}, 10),
    ({'page_size': 15}, 15),
    ({'page_size': +5}, 5),
]
                         )
def test_ps_correct_value(params, expected):
    assert gis.req_get(params=params).ok
    assert len(gis.req_get_json(params=params).get("items")) == expected


@pytest.mark.parametrize(('params'), [
    {'page_size': ''},
    {'page_size': 0},
    {'page_size': -2},
    {'page_size': 2},
    {'page_size': 99999999999},
    {'page_size': "+,."},
    {'page_size': 1.2},
    {'page_size': False},
    {'page_size': True}
]
                         )
def test_ps_incorrect_values(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("error")


@pytest.mark.parametrize('params', [
    {'page': 1, 'country_code': 'ru'},
    {},
    {'page': 2},
]
                         )
def test_ps_default(params):
    assert gis.req_get(params=params).ok
    assert len(gis.req_get_json(params=params).get("items")) == 15


@pytest.mark.parametrize('params', [
    {'page_size': None},
    {'p': None},
    {'q': None},
    {'country_code': None},
]
                         )
def test_none(params):
    assert gis.req_get(params=params).ok
    assert gis.req_get_json(params=params).get("total") == 22
