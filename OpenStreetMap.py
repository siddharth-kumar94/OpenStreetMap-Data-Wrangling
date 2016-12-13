#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import csv

FILENAME = 'sample.osm'

def audit_street(street):
    street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    street_prefix_re = re.compile(r'(^\S+.?)(\s)', re.IGNORECASE)

    street_mapping = {
        'Rd': 'Road',
        'Rd.': 'Road',
        'St': 'Street',
        'St.': 'Street',
        'Ave': 'Avenue',
        'Ave.': 'Avenue',
        'Ct': 'Court',
        'Ct.': 'Court',
        'Blvd': 'Boulevard',
        'Blvd.': 'Boulevard',
        'Bl': 'Boulevard',
        'Dr': 'Drive',
        'Dr.': 'Drive',
        'Cir': 'Circle',
        'Cir.': 'Circle',
        'Ln': 'Lane',
        'Ln.': 'Lane'
    }

    direction_mapping = {
        'N': 'North',
        'N.': 'North',
        'S': 'South',
        'S.': 'South',
        'E': 'East',
        'E.': 'East',
        'W': 'West',
        'W.': 'West',
        'SW': 'Southwest',
        'SW.': 'Southwest',
        'SE': 'Southeast',
        'SE.': 'Southeast',
        'NE': 'Northeast',
        'NE.': 'Northeast',
        'NW': 'Northwest',
        'NW.': 'Northwest',
    }

    street_type = ''
    street_prefix = ''
    street_suffix = ''

    m = street_type_re.search(street)
    street_name = street
    if m:
        street_type = m.group()

        # if street type is actually a direction
        if (street_type in direction_mapping.keys()) or (street_type in direction_mapping.values()):
            street_suffix = street_type
            street_name = street.replace(street_type, '').strip()
            if street_suffix in direction_mapping.keys():
                street = street.replace(street_suffix, direction_mapping[street_suffix])

        l = street_type_re.search(street_name)
        street_type = l.group()

        street_name = street_name.replace(street_type, '').strip()

        if street_type in street_mapping.keys():
            street = street.replace(street_type, street_mapping[street_type])

    n = street_prefix_re.search(street_name)
    if n:
        street_prefix = n.group(1)
        if street_prefix in direction_mapping.keys():
            street = street.replace(street_prefix, direction_mapping[street_prefix], 1)

    return street

def audit_state_name(state):
    state_mapping = {'OH': 'Ohio',
                     'OH - Ohio': 'Ohio'}

    if state in state_mapping.keys():
        state = state_mapping[state]

    return state

def audit_max_speed(speed):
    speed_parts = speed.split()
    if len(speed_parts) < 2:
        speed += ' mph'

    return speed

def audit_city_name(city):
    city_parts = city.split(',')
    if len(city_parts)>1:
        city = city_parts[0]

    city = city.title() #capitalizes first letter of city name

    return city

def audit_phone_number(phone):
    remove_chars = [',', '(', ')', '-', '+', '.', ' ']
    for char in remove_chars:
        phone = phone.replace(char, '')
    return phone

def audit_county_name(county):
    if ':' in county:
        county = county.split(':')[1]

    if county ==  'OH':
        return None

    return county

def audit_postcode(postcode):
    if len(postcode) < 5:
        return None

    if '-' in postcode:
        postcode = postcode.split('-')[0]

    if ' ' in postcode:
        postcode = postcode.split()[1]

    return postcode

def audit_cuisine(cuisine):
    cuisine = cuisine.replace(' ', '_')
    cuisine = cuisine.replace(',', '')
    return cuisine.lower()

def is_valid_way_element(tags):
    unwanted_way_keys = ['building', 'leisure', 'shop', 'amenity', 'tourism', 'landuse', 'housename']

    for way_tag in tags:
        if (way_tag['key'] in unwanted_way_keys) or (way_tag['type']=='addr'):
            return False

    return True

def get_tag_type(tag_key):
    lower_colon_re = re.compile(r'^([a-z]|_)+:')
    m = lower_colon_re.search(tag_key)

    if m:
        tag_type = m.group()[: -1]
        tag_key = tag_key[len(tag_type) + 1:]
        return [tag_key, tag_type]

    return None

def get_tag_naming_authority(tag_key):
    auth_names = ['gnis', 'tiger']
    lower_colon_re = re.compile(r'^([a-z]|_)+:')
    m = lower_colon_re.search(tag_key)

    if m:
        tag_auth = m.group()[: -1]
        if tag_auth in auth_names:
            tag_key = tag_key[len(tag_auth) + 1:]
            return [tag_key, tag_auth]

    return None

def process_key(key_name):
    key_num_re = re.compile(r'^([a-z_]*)((_)([1-9]))?$', re.IGNORECASE)

    #removes trailing number if necessary
    m = key_num_re.search(key_name)
    if m:
        key_name = m.group(1)

    key_mapping = {'County': 'county_name',
                   'County_num': 'county_id',
                   'ST_alpha': 'state',
                   'ST_num': 'state_id',
                   'alt_name': 'name_1',
                   'abbr_name': 'short_name',
                   'url': 'website',
                   'photo': 'image'
                   }

    if key_name in key_mapping.keys():
        key_name = key_mapping[key_name]

    return key_name.lower()

def process_value(key, value):
    split_symbols = [';', ',_', ',', ':', '_/_']
    split_vals = list()

    if key in ['ref', 'county', 'destination', 'phone', 'exit_to', 'cuisine', 'amenity'] or key.startswith('zip'):
        for symbol in split_symbols:
            if symbol in value:
                for item in value.split(symbol):
                    split_vals.append(item.strip())
                break

        if len(split_vals) == 0:
            split_vals.append(value)

    else:
         split_vals.append(value)

    return split_vals


node_attribs = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
way_attribs = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']

node_elements = []
way_elements = []

with open (FILENAME) as f:

    for event, elem in ET.iterparse(f, events=('start',)):

        if elem.tag == 'node' or elem.tag == 'way':

            elem_attribs = {}
            tags = []
            way_nodes = []

            #goes through attributes of first level elements
            for attrib_key, attrib_val in elem.attrib.iteritems():

                if elem.tag == 'node':
                    if attrib_key in node_attribs:
                        elem_attribs[attrib_key] = attrib_val.encode('utf-8')

                elif elem.tag == 'way':
                    if attrib_key in way_attribs:
                        elem_attribs[attrib_key] = attrib_val.encode('utf-8')

            # handling children
            nd_pos = 0

            for child in elem:
                child_dict = dict()
                child_dict['id'] = elem.get('id')

                #parses 'tag' tags in way and node
                if child.tag == 'tag':
                    key = child.get('k')
                    value = child.get('v')
                    type = 'regular'
                    naming_auth = 'NA'

                    # gets naming authority if any
                    # removes naming authority from key name if necessary
                    key_auth_list = get_tag_naming_authority(key)
                    if key_auth_list is not None:
                        key = key_auth_list[0]
                        naming_auth = key_auth_list[1]

                    # gets tag type if any
                    # removes type from key name if necessary
                    key_type_list = get_tag_type(key)
                    if key_type_list is not None:
                        key = key_type_list[0]
                        type = key_type_list[1]

                    # changes key name if repetitive name is used
                    key = process_key(key)

                    #splits values with multiple values embedded within
                    value_list = process_value(key, value)

                    for separated_val in value_list:
                        child_dict = dict()
                        child_dict['id'] = elem.get('id')
                        value = separated_val

                        # audit state name
                        if key == 'state':
                            value = audit_state_name(value)

                        # audit city name
                        if key == 'city':
                            value = audit_city_name(value)

                        # audit postcode
                        if key in ['postcode', 'zip_left', 'zip_right']:
                            value = audit_postcode(value)

                        #parses way_tags
                        if elem.tag == 'way':
                            # audit street name
                            if key in ['name', 'name_1']:
                                value = audit_street(value)

                            #audit max speed
                            if key == 'maxspeed':
                                value = audit_max_speed(value)

                            #audit county name
                            if key == 'county':
                                value = audit_county_name(value)

                        #parses node tags
                        elif elem.tag == 'node':
                            #audit street name
                            if key == 'street':
                                value = audit_street(value)

                            #audit phone number
                            if key == 'phone':
                                value = audit_phone_number(value)

                            #audit cuisine
                            if key == 'cuisine':
                                value = audit_cuisine(value)

                        # fills dict and appends to list of tags
                        child_dict['key'] = key
                        child_dict['value'] = value
                        if value is not None:
                            child_dict['value'] = value.encode('utf-8')
                        child_dict['type'] = type
                        child_dict['naming_auth'] = naming_auth

                        if child_dict['value'] is not None:
                            tags.append(child_dict)

                #parses 'nd' tags in way
                elif child.tag == 'nd':
                    if elem.tag == 'way':
                        child_dict['node_id'] = child.get('ref')
                        child_dict['position'] = nd_pos
                        nd_pos += 1
                        way_nodes.append(child_dict)

            #creates final dict
            elem_dict = {}

            if elem.tag == 'node':
                elem_dict['node'] = elem_attribs
                elem_dict['node_tags'] = tags
                node_elements.append(elem_dict)

            elif elem.tag == 'way':
                elem_dict['way'] = elem_attribs
                elem_dict['way_tags'] = tags
                elem_dict['way_nodes'] = way_nodes

                #checks if element is valid before appending
                if is_valid_way_element(tags):
                    way_elements.append(elem_dict)

def write_top_level(elem_list, tag_name, header, outfile):
    with open (outfile, 'w') as f:
        writer = csv.DictWriter(f, header)
        for element in elem_list:
            writer.writerow(element[tag_name])

def write_child_tags(elem_list, list_name, header, outfile):
    with open (outfile, 'w') as f:
        writer = csv.DictWriter(f, header)
        for element in elem_list:
            for tag in element[list_name]:
                writer.writerow(tag)

node_header = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
tag_header = ['id', 'key', 'value', 'type', 'naming_auth']
way_header = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
way_node_header = ['id', 'node_id', 'position']

write_top_level(node_elements, 'node', node_header, 'nodes.csv')
write_top_level(way_elements, 'way', way_header, 'ways.csv')
write_child_tags(node_elements, 'node_tags', tag_header, 'nodes_tags.csv')
write_child_tags(way_elements, 'way_tags', tag_header, 'ways_tags.csv')
write_child_tags(way_elements, 'way_nodes', way_node_header, 'ways_nodes.csv')




