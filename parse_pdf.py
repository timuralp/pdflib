#!/usr/bin/python

import pdfminer.pdfparser
import pdfminer.pdfinterp
import pdfminer.pdfdevice
import pdfminer.converter
import pdfminer.layout

def get_text_objs(pdf_handle):
	# Create a PDF parser object associated with the file object.
	parser = pdfminer.pdfparser.PDFParser(pdf_handle)
	
	# Create a PDF document object that stores the document structure.
	doc = pdfminer.pdfparser.PDFDocument()
	
	# Connect the parser and document objects.
	parser.set_document(doc)
	doc.set_parser(parser)
	
	# Supply the password for initialization.
	# (If no password is set, give an empty string.)
	doc.initialize()
	
	# Check if the document allows text extraction. If not, abort.
	if not doc.is_extractable:
		raise pdfminer.PDFTextExtractionNotAllowed
	
	# Create a PDF resource manager object that stores shared resources.
	rsrcmgr = pdfminer.pdfinterp.PDFResourceManager()
	
	# Create a PDF device object.
	laparams = pdfminer.layout.LAParams()
	device = pdfminer.converter.PDFPageAggregator(rsrcmgr, laparams = laparams)
	
	# Create a PDF interpreter object.
	interpreter = pdfminer.pdfinterp.PDFPageInterpreter(rsrcmgr, device)
	
	# Process each page contained in the document.
	first_page = doc.get_pages().next()
	interpreter.process_page(first_page)
	layout = device.get_result()
	
	text_objs = []
	for lt in layout:
		if isinstance(lt, pdfminer.layout.LTTextBox):
			text_objs.append(lt)
		elif isinstance(lt,	pdfminer.layout.LTTextLine):
			text_objs.append(lt)
	return text_objs

def get_title_authors(lt_text_list):
	# find the title
	title = None
	authors = None
	for lt in lt_text_list:
		if lt.is_empty():
			continue
		text = lt.get_text().strip()
		if len(text) < 5:
			continue
		if text.lower().startswith('abstract'):
			break
		if title == None:
			title = text.replace('\n', ' ')
			continue
		# now look for authors
		if text.find('\n') != -1:
			# could be many authors (with institutions)
			name = text.split('\n')[0]
			if not authors:
				authors = []
			authors.append(name)
		elif text.find(',') != -1:
			# single author field, it appears
			authors = text.strip().split(',')
	return (title, authors)

def main():
	# Open a PDF file.
	fp = open(sys.argv[1], 'rb')
	
	lt_list = get_text_objs(fp)
	title, authors = get_title_authors(lt_list)

	print title
	print authors
	fp.close()

if __name__ == '__main__':
	import sys
	main()
