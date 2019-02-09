#!/usr/bin/python
# -*- coding: utf-8  -*-
# Remove locally defined commons category links when bad or pointing to a redirect
# Mike Peel     01-Jan-2019      v1 - start
# Mike Peel     14-Jan-2019      v1.1 - tweaks for enwp bot approval
# Mike Peel     20-Jan-2019      v1.2 - last check for files in a category
# Mike Peel     21-Jan-2019      v1.3 - tweaks to removal code and template list

from __future__ import unicode_literals

import pywikibot
import numpy as np
import time
import string
from pywikibot import pagegenerators
import urllib
from pibot_functions import *

maxnum = 100000
nummodified = 0

wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()  # this is a DataSite object
commons = pywikibot.Site('commons', 'commons')
enwp = pywikibot.Site('en', 'wikipedia')
debug = 0
trip = 1
templates = ['commonscat', 'Commonscat', 'commonscategory', 'Commonscategory', 'commons category', 'Commons category', 'commons cat', 'Commons cat', 'Commons category-inline', 'commons category-inline', 'Commons cat-inline', 'commons cat-inline', 'commonscat-inline', 'Commonscat-inline', 'Commons category inline', 'commons category inline', 'commons-cat-inline', 'Commons-cat-inline', 'Commons cat inline', 'commons cat inline', 'commonscat inline', 'Commonscat inline', 'Commons Category', 'commons Category','commonscatinline', 'Commonscatinline']

catredirect_templates = ["category redirect", "Category redirect", "seecat", "Seecat", "see cat", "See cat", "categoryredirect", "Categoryredirect", "catredirect", "Catredirect", "cat redirect", "Cat redirect", "catredir", "Catredir", "redirect category", "Redirect category", "cat-red", "Cat-red", "redirect cat", "Redirect cat", "category Redirect", "Category Redirect", "cat-redirect", "Cat-redirect"]

targetcats = ['Commons category link is the pagename‎', 'Commons category link is defined as the pagename‎', 'Commons category link is locally defined‎']

for categories in range(0,2):
	for targetcat in targetcats:
		cat = pywikibot.Category(enwp, targetcat)
		if categories:
			pages = pagegenerators.SubCategoriesPageGenerator(cat, recurse=False);
		else:
			pages = pagegenerators.CategorizedPageGenerator(cat, recurse=False);
		for page in pages:

			# Optional skip-ahead to resume broken runs
			if trip == 0:
				if "Exposition Internationale des Arts" in page.title():
					trip = 1
				else:
					print page.title()
					continue

			# Cut-off at a maximum number of edits	
			print ""
			print nummodified
			if nummodified >= maxnum:
				print 'Reached the maximum of ' + str(maxnum) + ' entries modified, quitting!'
				exit()

			# Get the Wikidata item
			try:
				wd_item = pywikibot.ItemPage.fromPage(page)
				item_dict = wd_item.get()
				qid = wd_item.title()
			except:
				# If that didn't work, go no further
				print page.title() + ' - no page found'
				continue

			print "\n" + qid
			print page.title()

			# Get the candidate commonscat link
			target_text = page.get()
			id_val = 0
			abort = 0
			commonscat_string = ""
			for i in range(0,len(templates)):
				try:
					value = (target_text.split("{{"+templates[i]+"|"))[1].split("}}")[0]
					if value and id_val == 0:
						id_val = value
						commonscat_string = "{{"+templates[i]+"|"+id_val+"}}"
						commonscat_string2 = "|"+id_val
						commonscat_string2a = "{{"+templates[i]
				except:
					null = 1
					try:
						value = (target_text.split("{{"+templates[i]+" |1="))[1].split("}}")[0]
						if value and id_val == 0:
							id_val = value
							commonscat_string = "{{"+templates[i]+"|1="+id_val+"}}"
							commonscat_string2 = "|1="+id_val
							commonscat_string2a = "{{"+templates[i]
					except:
						null = 2
			if id_val == 0:
				# We didn't find the commons category link, skip this one.
				continue

			# Do some tidying of the link
			if "|" in id_val:
				try:
					if 'position' in id_val.split("|")[0] or 'bullet' in id_val.split("|")[0]:
						if 'position' in id_val.split("|")[1] or 'bullet' in id_val.split("|")[1]:
							id_val = id_val.split("|")[2]
						else:
							id_val = id_val.split("|")[1]
					else:
						id_val = id_val.split("|")[0]
				except:
					continue
			try:
				id_val = id_val.strip()
			except:
				null = 1

			# Check for bad characters
			if "{" in id_val or "<" in id_val or ">" in id_val or "]" in id_val or "[" in id_val:
				continue

			print id_val
			commonscat = u"Category:" + id_val

			# If we have a P910 value, switch to using that Wikidata item
			try:
				existing_id = item_dict['claims']['P910']
				print 'P910 exists, following that.'
				for clm2 in existing_id:
					wd_item = clm2.getTarget()
					item_dict = wd_item.get()
					print wd_item.title()
			except:
				null = 0

			# Double-check that there is a sitelink on Wikidata
			try:
				sitelink = item_dict['sitelinks']['commonswiki']
				sitelink_check = 1
			except:
				sitelink_check = 0
			print "sitelink: " + str(sitelink_check)

			# If we don't have a sitelink on Wikidata, let's at least check that the enwp one exists
			if id_val != 0 and sitelink_check == 0:
				try:
					commonscat_page = pywikibot.Page(commons, commonscat)
					text = commonscat_page.get()
				except:
					last_check = check_if_category_has_contents(id_val,site=commons)
					if last_check == False:
						print 'Found a bad sitelink - removing it'
						target_text = target_text.replace("* " + commonscat_string+"\n", '')
						target_text = target_text.replace("*" + commonscat_string+"\n", '')
						target_text = target_text.replace(commonscat_string+"\n", '')
						target_text = target_text.replace(commonscat_string, '')
						page.text = target_text
						test = 'y'
						savemessage = "Removing Commons category ("+id_val+") as it does not exist"
						if debug == 1:
							print target_text
							print id_val
							print savemessage
							test = raw_input("Continue? ")
						if test == 'y':
							nummodified += 1
							page.save(savemessage)
							continue

			# Only attempt to do the next part if we have a commons category link both locally and on wikidata
			if id_val != 0 and sitelink_check == 1:
				print sitelink

				# First, fix broken commons category links
				try:
					commonscat_page = pywikibot.Page(commons, commonscat)
					category_text = commonscat_page.get()
				except:
					last_check = check_if_category_has_contents(id_val,site=commons)
					if last_check == False:
						print 'Found a bad sitelink, but there is one on wikidata we can use'
						target_text = target_text.replace(commonscat_string2a + commonscat_string2, commonscat_string2a+"|"+sitelink.replace('Category:',''))
						page.text = target_text
						test = 'y'
						savemessage = "Changing locally defined but nonexistent Commons category (Category:"+id_val+") to the one from Wikidata ("+sitelink+")"
						if debug == 1:
							print target_text
							print id_val
							print savemessage
							test = raw_input("Continue? ")
						if test == 'y':
							nummodified += 1
							page.save(savemessage)
							continue
				
				# Now check to see if the local one is a redirect to the wikidata one
				if 'Category:'+id_val != sitelink:
					sitelink_redirect = ''
					for option in catredirect_templates:
						if "{{" + option in category_text:
							try:
								sitelink_redirect = (category_text.split("{{" + option + "|"))[1].split("}}")[0]
							except:
								try:
									sitelink_redirect = (category_text.split("{{" + option + " |"))[1].split("}}")[0]
								except:
									print 'Wikitext parsing issue!'
							sitelink_redirect = sitelink_redirect.replace(u":Category:","").strip()
							sitelink_redirect = sitelink_redirect.replace(u"Category:","").strip()
							print 'Redirect target:' + sitelink_redirect
					if sitelink_redirect != '':
						if sitelink == 'Category:'+sitelink_redirect:
							print 'We have a redirect to the Wikidata entry, so use the wikidata entry'
							target_text = target_text.replace(commonscat_string2a + commonscat_string2, commonscat_string2a+"|"+sitelink.replace('Category:',''))
							page.text = target_text
							test = 'y'
							savemessage = 'Updating the Commons category from "Category:'+id_val+'" to "' + sitelink + '" to avoid a category redirect'
							if debug == 1:
								print target_text
								print id_val
								print savemessage
								test = raw_input("Continue? ")
							if test == 'y':
								nummodified += 1
								page.save(savemessage)
								continue

				# What if it is pointing at a disambig page?
				# Disabled for now
				# if '{{Disambig' in target_text or '{{disambig' in target_text:
				# 	if sitelink in target_text:
				# 		print 'We have a disambig category, so use the wikidata entry'
				# 		target_text = target_text.replace(commonscat_string2, '')
				# 		page.text = target_text
				# 		test = 'y'
				# 		savemessage = "Removing locally defined Commons category ("+id_val+") as it points to a disambiguation page - use the one from Wikidata instead"
				# 		if debug == 1:
				# 			print target_text
				# 			print "Removing locally-defined commons link from " + page.title()
				# 			print savemessage
				# 			test = raw_input("Continue? ")
				# 		if test == 'y':
				# 			nummodified += 1
				# 			page.save()
				# 			continue

				# ... That's all for now

print 'Done! Edited ' + str(nummodified) + ' entries'
		
# EOF