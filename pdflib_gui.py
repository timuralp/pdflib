#!/usr/bin/python

import wx
import os
import pyPdf
import shutil
import hashlib
import subprocess

from pdflib_db import Paper, load_docs_from_db, add_doc_to_db

icon_path = "tango-icon-theme/32x32/"

PAPER_ADD = 0
PAPER_DEL = 1
PAPER_UPDATE = 2

ADD_ID 	= 1
BIB_ID 	= 2
EDIT_ID = 3

def ParsePDF(path):
	return Paper()

	# in the future, figure out how to extract the title, authors, etc
	try:
		pdf = pyPdf.PdfFileReader(open(path, 'rb'))
	except Exception, e:
		print e
		print 'Exception: no file'
		return None

	if pdf == None:
		print 'None in open: no file'
		return None
	
	try:
		title = pdf.getDocumentInfo().title
	except:
		pass

	txt = pdf.getPage(0).extractText()
	txt = " ".join(txt.replace(u"\xa0", " ").strip().split())
	txt = txt.encode("ascii", "ignore")

class DocumentPromptDialog(wx.Dialog):
	def __init__(self, parent, id, title, paper = None):
		wx.Dialog.__init__(self, parent, id, title)

		vbox = wx.BoxSizer(wx.VERTICAL)

		input_boxes = [u"Title:", u"Authors:", u"Year:", u"Venue:"]
		bttn_sizer = self.CreateButtonSizer(wx.CANCEL|wx.OK)
		self.ctrl = {}

		for i in input_boxes:
			hbox = wx.BoxSizer(wx.HORIZONTAL)
			ctrl = wx.TextCtrl(self, -1)
			label = wx.StaticText(self, -1, label = i)
			hbox.Add(label, 1)
			hbox.Add(ctrl, 2)
			vbox.Add(hbox, 2, wx.EXPAND|wx.ALL, 5)
			self.ctrl[i] = ctrl

		vbox.AddSizer(bttn_sizer, proportion = 1, flag = wx.ALIGN_BOTTOM|wx.ALL, border = 5)

		self.SetSizer(vbox)
		self.__results = None

		self.Centre()
		self.Show(True)

	def GetData(self):
		self.__results = {}
		self.__results['title'] = ' '.join(self.ctrl[u'Title:'].GetValue().split())
		self.__results['authors'] =	' '.join(self.ctrl[u'Authors:'].GetValue().split()).split(',')
		self.__results['year'] = int(self.ctrl[u'Year:'].GetValue())
		return self.__results

def make_image(path):
	return wx.Image(icon_path+path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()

class PDFLibFrame(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title)

		# add the necessary lists, menus, buttons
		self.__grid = wx.GridBagSizer(5, 5)
		self.__toolbar = wx.ToolBar(self, -1, style = wx.TB_HORIZONTAL)
		add_img = make_image("actions/list-add.png")
		bib_img = make_image("actions/document-properties.png")
		edit_img = make_image("actions/edit-find-replace.png")
		self.__toolbar.AddLabelTool(ADD_ID, '', add_img,
									shortHelp = 'Add document')
		self.__toolbar.AddLabelTool(BIB_ID, '', bib_img,
									shortHelp = 'Make a bib')
		self.__toolbar.AddLabelTool(EDIT_ID, '', edit_img,
									shortHelp = 'Edit entry')
		self.__toolbar.Realize()

		self.__doc_list = wx.ListBox(self, -1, style = wx.LB_SINGLE | wx.LB_SORT)

		self.__doc_properties = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)
		self.__doc_properties.SetEditable(False)
	
		self.__title_txt = wx.StaticText(self, -1, label = 'Title:')
		self.__author_txt = wx.StaticText(self, -1, label = 'Author:')
		self.__venue_txt = wx.StaticText(self, -1, label = 'Venue:')
		self.__year_txt = wx.StaticText(self, -1, label = 'Year:')
		self.__find_title = wx.TextCtrl(self, -1)
		self.__find_author = wx.TextCtrl(self, -1)
		self.__find_venue = wx.TextCtrl(self, -1)
		self.__find_year = wx.TextCtrl(self, -1)
		self.__find_bttn = wx.Button(self, wx.ID_FIND)

		self.__grid.Add(self.__toolbar, (0, 0), wx.GBSpan(1, 40), wx.EXPAND)
		self.__grid.Add(self.__title_txt, (1, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__find_title, (2, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__author_txt, (3, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__find_author, (4, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__venue_txt, (5, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__find_venue, (6, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__year_txt, (7, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__find_year, (8, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__find_bttn, (9, 0), flag = wx.LEFT, border = 10)
		self.__grid.Add(self.__doc_list, (1, 1), wx.GBSpan(10, 40), wx.EXPAND|wx.RIGHT, border=10)
		self.__grid.Add(self.__doc_properties, (11, 1), (10, 40), wx.EXPAND|wx.RIGHT|wx.BOTTOM, border=10)

		#self.__grid.AddGrowableCol(10)
		#self.__grid.AddGrowableRow(1)

		self.SetSizer(self.__grid)
		self.__grid.Fit(self)
		self.Centre()
		self.Show(True)
		self.InitializeDocList()

		self.__doc_list.Bind(wx.EVT_LISTBOX, self.OnDocListBox)
		self.__doc_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnListDblClick)
		self.Bind(wx.EVT_TOOL, self.OnAddDocument, id = ADD_ID)
		self.Bind(wx.EVT_TOOL, self.OnMakeBib, id = BIB_ID)
		self.Bind(wx.EVT_SIZE, self.OnSize)

	def InitializeDocList(self):
		self.__docs = load_docs_from_db()
		if self.__docs == None:
			return

		for doc in self.__docs:
			# set the list entries
			self.__doc_list.Append(doc.get_title(), clientData = doc)

	def UpdateDocList(self, paper, action = PAPER_ADD):
		self.__doc_list.Append(paper.get_title(), clientData = paper)

	def OnDocListBox(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if clicked == None:
			return

		# set the properties in the text box
		self.__doc_properties.Clear()
		self.__doc_properties.WriteText("Title: %s\n" % clicked.get_title())
		self.__doc_properties.WriteText("Authors: %s\n" % clicked.get_author())
		self.__doc_properties.WriteText("Year: %d" % clicked.get_year())

	def OnListDblClick(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if clicked == None:
			return
		name = u'acroread ' + pdf_repo + u'/' + clicked.GetFile()
		subprocess.Popen(name.encode('ascii', 'replace').split(' '))

	def OnAddDocument(self, event):
		# prompt for the document to add
		dialog = wx.FileDialog(None, message = 'Select a file...', style = wx.OPEN, wildcard = '*.pdf')

		file_path = None
		paper = None

		if dialog.ShowModal() == wx.ID_OK:
			file_path = dialog.GetPath()

		if file_path and len(file_path) > 0:
			paper = ParsePDF(file_path)
		dialog.Destroy()

		if not paper:
			return

		dialog = DocumentPromptDialog(self, -1, "PDF Information Prompt", paper)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			info = dialog.GetData()
			if info != None:
				paper = Paper(title=info['title'], author=info['authors'],\
								year=info['year'], filename=file_path)
		else:
			print "not ok??", result
			paper = None
		dialog.Destroy()
		if not paper:
			return
		
		# add the paper to the DB and the list
		add_doc_to_db(paper)
		self.UpdateDocList(paper)

	def OnMakeBib(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if not clicked:
			return
		name = clicked.get_title()
		year = str(clicked.get_year())
		authors = clicked.get_author()

		ref_name = authors.split(',')[0].split(' ')[1]+year
		author_list = []
		for a in authors.split(','):
			a = a.strip()
			author_names = a.split(' ')
			first = author_names[0]
			last = author_names[-1]
			if not first.endswith('.'):
				author_list.append(last + ', ' + first[0] + '.')
			else:
				author_list.append(last + ', ' + first)
		authors_line = ' and '.join(author_list)

		msg = '@inproceedings{%s,\n' % ref_name
		msg += '\ttitle = {{%s}},\n' % name
		msg += '\tauthor = {%s},\n' % authors_line
		msg += '\tyear = {%s},\n' % year
		msg += '}'

		wx.MessageBox(msg, 'bibtex entry for %s' % ref_name, wx.OK)

	def OnSize(self, event):
		x, y = event.GetSize()
		#doc_list_size = 
		#self.__doc_list.SetMinSize(event.GetSize())
		#self.__grid.SetMinSize(event.GetSize())
		self.__grid.Fit(self)
		self.Layout()
		self.Refresh()

if __name__ == '__main__':
	app = wx.App()
	PDFLibFrame(None, -1, "PDFLib")
	app.MainLoop()
