#!/usr/bin/python
# -*- coding: utf-8  -*-
# Migrate coordinate templates used in categories
# 23 Dec 2020	Mike Peel	Started

import pywikibot
import numpy as np
import astropy as ap

def get_precision(val):
	print(val)
	if '.' in val:
		val = val.split('.')[1]
		length = len(val)
	else:
		length = 0
	# print(len(val))
	return 10**-len(val)

def calc_coord(params):
	if len(params) >= 8:
		lat = float(params[0]) + (float(params[1])/60.0)+(float(params[2])/(60.0*60.0))
		if 'S' in params[3]:
			lat = -lat
		lon = float(params[4]) + (float(params[5])/60.0)+(float(params[6])/(60.0*60.0))
		if 'W' in params[7]:
			lon = -lon
		precision = get_precision(params[2])/(60.0*60.0)
	elif len(params) >= 2:
		lat = float(params[0])
		lon = float(params[1])
		precision = get_precision(params[0])
	# print(lon)
	# print(lat)
	# print(precision)
	return lat, lon, precision

def check_match(lat1, lon1, prec1, lat2, lon2, prec2):
	# prec = np.min[prec1, prec2])
	# print(prec1)
	# print(prec2)
	# print(prec)

	# From https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
	c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
	distance = 6373.0 * c
	print(distance)
	# print(6373.0*prec)
	if distance < 10:
		return True
	else:
		return False


commons = pywikibot.Site('commons', 'commons')
repo = commons.data_repository()
# cat = pywikibot.Page(commons, 'Category:Mirador de las Nieves')
# cat = pywikibot.Page(commons, 'Category:Lovell Telescope')
globe_item = pywikibot.ItemPage(repo, 'Q2')

coord_templates = ['Object location']
debug = True
remove_from_commons = False

template = pywikibot.Page(commons, 'Template:'+coord_templates[0])
targetcats = template.embeddedin(namespaces='14')
for cat in targetcats:
	print('https://commons.wikimedia.org/wiki/'+cat.title().replace(" ","_"))
	try:
		wd_item = pywikibot.ItemPage.fromPage(cat)
		item_dict = wd_item.get()
	except:
		print("No Wikidata sitelink found")
		continue

	try:
		existing_id = item_dict['claims']['P301']
		print('P301 exists, following that.')
		for clm2 in existing_id:
			wd_item = clm2.getTarget()
			item_dict = wd_item.get()
			qid = wd_item.title()
	except:
		null = 0

	print('https://www.wikidata.org/wiki/'+wd_item.title())

	coordinate = False
	try:
		P625 = item_dict['claims']['P625']
	except:
		P625 = ''
	print(P625)
	if P625 != '':
		for clm in P625:
			try:
				coordinate = clm.getTarget()
				print(coordinate)
				print(coordinate.lat)
			except:
				P625 = 'Bad'
	if P625 == 'Bad':
		print('Problem with coordinates')
		continue

	count = 0
	for template in cat.templatesWithParams():
		for tpl in coord_templates:
			if tpl in template[0].title():
				count += 1
	if count != 1:
		print('Wrong number of coordinate templates (' + str(count) + '), skipping')
		continue

	done = False
	for template in cat.templatesWithParams():
		for tpl in coord_templates:
			# print(tpl)
			if not done:
				if tpl in template[0].title():
					# print(template)
					print(template[0].title())
					print(template[1])
					if 'wikidata' not in str(template[1]) and 'Wikidata' not in str(template[1]):
						lat, lon, precision = calc_coord(template[1])
						if not coordinate:
							coordinateclaim  = pywikibot.Claim(repo, u'P625')
							coordinate = pywikibot.Coordinate(lat=lat, lon=lon, precision=precision, site=commons,globe_item=globe_item)
							coordinateclaim.setTarget(coordinate)
							test = 'y'
							if debug:
								test = input('Save coordinate?')
							if test == 'y':
								wd_item.addClaim(coordinateclaim, summary=u'Importing coordinate from Commons')
								done = True
						test1 = check_match(lat, lon, precision, coordinate.lat, coordinate.lon, coordinate.precision)
					else:
						test1 = True
					if test1 and remove_from_commons:
						try:
							template_string = '{{'+tpl+cat.text.split('{{'+tpl)[1].split('}}')[0]+"}}"
							print(template_string)
							target_text = cat.text.replace(template_string,'')
						except:
							template_string = '{{'+tpl.lower()+cat.text.split('{{'+tpl.lower())[1].split('}}')[0]+"}}"
							print(template_string)
							target_text = cat.text.replace(template_string,'')
						target_text = target_text.replace('\n\n\n','\n')
						if 'Wikidata Infobox' not in target_text:
							target_text = "{{Wikidata Infobox}}\n" + target_text
						target_text = target_text.replace('\n\n\n','\n')
						print("New text:")
						print(target_text)
						test = 'y'
						if debug:
							test = input('Remove from Commons')
						if test == 'y':
							cat.text = target_text
							cat.save('Coordinates now through the infobox')
