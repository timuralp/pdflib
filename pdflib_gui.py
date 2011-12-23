#!/usr/bin/python

import wx
import os
import pyPdf
import shutil
import hashlib
import subprocess

from pdflib_db import Paper
from pdflib_db import load_docs_from_db
from pdflib_db import add_doc_to_db

icon_path = "tango-icon-theme/32x32/"

PAPER_ADD = 0
PAPER_DEL = 1
PAPER_UPDATE = 2

def ParsePDF(path):
	return None

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
	def __init__(self, parent, id, title):
		wx.Dialog.__init__(self, parent, id, title)

		vbox = wx.BoxSizer(wx.VERTICAL)

		input_boxes = [u"Title:", u"Authors:", u"Year:"]
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

class PDFLibFrame(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title)

		# add the necessary lists, menus, buttons
		self.__grid = wx.GridBagSizer(5, 5)
		self.__toolbar = wx.ToolBar(self, -1, style = wx.TB_HORIZONTAL)
		add_img = wx.Image(icon_path+"actions/list-add.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		bib_img = wx.Image(icon_path+"actions/document-properties.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		self.__toolbar.AddSimpleTool(wx.ID_ADD, add_img, 'Add document', '')
		self.__toolbar.AddSimpleTool(wx.ID_FILE1, bib_img, 'Make a bib', '')
		self.__toolbar.Realize()

		self.__doc_list = wx.ListBox(self, -1, style = wx.LB_SINGLE | wx.LB_SORT)
		
		self.__doc_properties = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)
		self.__doc_properties.SetEditable(False)
		
		self.__grid.Add(self.__toolbar, (0, 0), (1, 30), wx.EXPAND)
		self.__grid.Add(self.__doc_list, (1, 10), (6, 20), wx.EXPAND|wx.RIGHT, border=10)
		self.__grid.Add(self.__doc_properties, (7, 10), (5, 20), wx.EXPAND|wx.RIGHT|wx.BOTTOM, border=10)

		self.__grid.AddGrowableCol(10)
		self.__grid.AddGrowableRow(1)

		self.SetSizer(self.__grid)
		self.__grid.Fit(self)
		self.Centre()
		self.Show(True)
		self.InitializeDocList()

		self.__doc_list.Bind(wx.EVT_LISTBOX, self.OnDocListBox)
		self.__doc_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnListDblClick)
		self.Bind(wx.EVT_TOOL, self.OnAddDocument, id = wx.ID_ADD)
		self.Bind(wx.EVT_TOOL, self.OnMakeBib, id = wx.ID_FILE1)

	def InitializeDocList(self):
		self.__docs = load_docs_from_db()
		if self.__docs == None:
			return

		for doc in self.__docs:
			# set the list entries
			self.__doc_list.Append(doc.GetTitle(), clientData = doc)

	def UpdateDocList(self, paper, action = PAPER_ADD):
		self.__doc_list.Append(paper.GetTitle(), clientData = paper)

	def OnDocListBox(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if clicked == None:
			return

		# set the properties in the text box
		self.__doc_properties.Clear()
		self.__doc_properties.WriteText("Title: %s\n" % clicked.GetTitle())
		self.__doc_properties.WriteText("Authors: %s\n" % clicked.GetAuthor())
		self.__doc_properties.WriteText("Year: %d" % clicked.GetYear())

	def OnListDblClick(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if clicked == None:
			return
		name = u'acroread ' + pdf_repo + u'/' + clicked.GetFile()
		subprocess.Popen(name.encode('ascii', 'replace').split(' '))

	def OnAddDocument(self, event):
		# prompt for the document to add
		dialog = wx.FileDialog(None, message = 'Select a file...', style = wx.OPEN, wildcard = '*.pdf')

		if dialog.ShowModal() == wx.ID_OK:
			file_path = dialog.GetPath()

		paper = ParsePDF(file_path)
		dialog.Destroy()

		if paper == None:
			dialog = DocumentPromptDialog(self, -1, "PDF Information Prompt")
			result = dialog.ShowModal()
			if result == wx.ID_OK:
				info = dialog.GetData()
				if info != None:
					paper = Paper(title=info['title'], author=info['authors'],\
									year=info['year'], filename=file_path)
			else:
				print "not ok??", result
			dialog.Destroy()
		if paper == None:
			return
		
		# add the paper to the DB and the list
		add_doc_to_db(paper)
		self.UpdateDocList(paper)

	def OnMakeBib(self, event):
		clicked = self.__doc_list.GetClientData(self.__doc_list.GetSelection())
		if not clicked:
			return
		name = clicked.GetTitle()
		year = str(clicked.GetYear())
		authors = clicked.GetAuthor()

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

app = wx.App()
PDFLibFrame(None, -1, "PDFLib")
app.MainLoop()
