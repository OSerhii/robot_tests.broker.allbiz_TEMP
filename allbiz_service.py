#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from iso8601 import parse_date
from pytz import timezone
import urllib
import json
import os


def convert_time(date):
    date = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
    return timezone('Europe/Kiev').localize(date).strftime('%Y-%m-%dT%H:%M:%S.%f%z')


def subtract_min_from_date(date, minutes):
    date_obj = datetime.strptime(date.split("+")[0], '%Y-%m-%dT%H:%M:%S.%f')
    return "{}+{}".format(date_obj - timedelta(minutes=minutes), date.split("+")[1])


def convert_datetime_to_allbiz_format(isodate):
    iso_dt = parse_date(isodate)
    day_string = iso_dt.strftime("%d/%m/%Y %H:%M")
    return day_string


def convert_string_from_dict_allbiz(string):
    return {
        u"грн.": u"UAH",
        u"True": u"1",
        u"False": u"0",
        u"Відкриті торги": u"aboveThresholdUA",
        u"Відкриті торги з публікацією англ. мовою": u"aboveThresholdEU",
        u'Класифікацiя предмета закупівлi за ДК021:2015': u'ДК021',
        u'Код ДК (ДК003)': u'ДК003',
        u'Код ДК (ДК018)': u'ДК018',
        u'з урахуванням ПДВ': True,
        #u'з ПДВ': True,
        u'без урахуванням ПДВ': False,
        u'Очiкування пропозицiй': u'active.tendering',
        u'Перiод уточнень': u'active.enquiries',
        u'Аукцiон': u'active.auction',
        u'Прекваліфікація': u'active.pre-qualification',
        u'Оскарження прекваліфікації': u'active.pre-qualification.stand-still',
        u'вимога': u'claim',
        u'дано відповідь': u'answered',
        u'вирішено': u'resolved',
        u'Так': True,
        u'Ні': False,
        u'на розглядi': u'pending',
        u'На розгляді': u'pending',
        u'не вирішено(обробляється)': u'pending',
        u'відмінено': u'cancelled',
        u'відмінена': u'cancelled',
        u'Переможець': u'active',
    }.get(string, string)


def adapt_procuringEntity(role_name, tender_data):
    if role_name == 'tender_owner':
        tender_data['data']['procuringEntity']['name'] = u"ТОВ Величний Свинарник"
        if tender_data['data'].has_key('procurementMethodType'):
            if "above" in tender_data['data']['procurementMethodType']:
                tender_data['data']['tenderPeriod']['startDate'] = subtract_min_from_date(
                    tender_data['data']['tenderPeriod']['startDate'], 1)
    return tender_data


def adapt_delivery_data(tender_data):
    for index in range(len(tender_data['data']['items'])):
        value = tender_data['data']['items'][index]['deliveryAddress']['region']
        if value == u"місто Київ":
            tender_data['data']['items'][index]['deliveryAddress']['region'] = u"Київ"
    return tender_data


def adapt_view_tender_data(value, field_name):
    if 'value.amount' in field_name:
        value = float(value.replace(" ", ""))
    # elif 'currency' in field_name:
    #     value = value.split(' ')[1]
    # elif 'valueAddedTaxIncluded' in field_name:
    #     value = ' '.join(value.split(' ')[2:])
    elif 'minimalStep.amount' in field_name:
        value = float("".join(value.split(" ")[:-4]))
    elif 'unit.name' in field_name:
        value = value.split(' ')[1]
    elif 'quantity' in field_name:
        value = float(value.split(' ')[0])
    elif 'questions' in field_name and '.date' in field_name:
        value = convert_time(value.split(' - ')[0])
    elif 'Date' in field_name:
        value = convert_time(value)
    return convert_string_from_dict_allbiz(value)


def adapt_view_lot_data(value, field_name):
    if 'value.amount' in field_name:
        value = float("".join(value.split(' ')[:-4]))
    elif 'minimalStep.currency' in field_name:
        value = value.split(' ')[-1]
    elif 'currency' in field_name:
        value = value.split(' ')[-4]
    elif 'valueAddedTaxIncluded' in field_name:
        value = ' '.join(value.split(' ')[-3:]).strip()
    elif 'minimalStep.amount' in field_name:
        value = float("".join(value.split(' ')[:-1]))
    return convert_string_from_dict_allbiz(value)


def adapt_view_item_data(value, field_name):
    if 'unit.name' in field_name:
        value = ' '.join(value.split(' ')[1:])
    elif 'quantity' in field_name:
        value = float(value.split(' ')[0])
    elif 'Date' in field_name:
        value = convert_time(value)
    return convert_string_from_dict_allbiz(value)


def get_related_elem_description(tender_data, feature, item_id):
    if item_id == "":
        for elem in tender_data['data']['{}s'.format(feature['featureOf'])]:
            if feature['relatedItem'] == elem['id']:
                return elem['description']
    else:
        return item_id


def custom_download_file(url, file_name, output_dir):
    urllib.urlretrieve(url, ('{}/{}'.format(output_dir, file_name)))


def add_second_sign_after_point(amount):
    amount = str(repr(amount))
    if '.' in amount and len(amount.split('.')[1]) == 1:
        amount += '0'
    return amount


def get_bid_phone(internal_id, bid_index):
    r = urllib.urlopen('https://lb.api-sandbox.openprocurement.org/api/2.3/tenders/{}'.format(internal_id)).read()
    tender = json.loads(r)
    bid_id = tender['data']['qualifications'][int(bid_index)]["bidID"]
    for bid in tender['data']['bids']:
        if bid['id'] == bid_id:
            return bid['tenderers'][0]['contactPoint']['telephone']


def get_upload_file_path():
    return os.path.join(os.getcwd(), 'src/robot_tests.broker.allbiz/testFileForUpload.txt')