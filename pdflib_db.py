import sqlite3
import os

pdf_main = os.getenv('HOME')+'/.pdflib'
pdf_repo = pdf_main+'/docs'
db_path = pdf_main+'/pdflib.db'

class Paper:
	def __init__(self, author=None, title=None, year=None, filename = None):
		self.__author = author
		self.__title = title
		self.__year = year
		self.__file = filename
	
	def GetTitle(self):
		return self.__title
	def GetYear(self):
		return self.__year
	def GetAuthor(self):
		return self.__author
	def GetFile(self):
		return self.__file

	def SetFileName(self, fn):
		self.__file = fn

	def SetAuthors(self, authors):
		self.__author = authors

	def Valid(self):
		if self.__author == None:
			return False
		if self.__title == None:
			return False
		if self.__year == None:
			return False
		return True 

def init_repo():
	if os.path.exists(pdf_repo):
		return
	if not os.path.exists(pdf_main):
		os.mkdir(pdf_main)
	os.mkdir(pdf_repo)

def CreateDB(cursor):
	q = 'create table docs (id integer primary key not null, title text, authors text, year integer, file text)'
	cursor.execute(q)

def load_docs_from_db():
	make_db = False
	if not os.path.exists(db_path):
		make_db = True
		init_repo()

	db = sqlite3.connect(db_path)
	c = db.cursor()
	if make_db:
		CreateDB(c)
		db.commit()
		return None

	q = 'select title, authors, year, file from docs'
	c.execute(q)

	# get all the results
	recs = c.fetchall()
	if len(recs) == 0:
		return None
	
	c.close()
	db.close()

	return [Paper(title = r[0], author = r[1], year = r[2], filename = r[3]) for r in recs]

def add_doc_to_db(paper):
	if paper == None or not paper.Valid():
		return

	make_db = False
	if not os.path.exists(db_path):
		make_db = True
		init_repo()
	
	db = sqlite3.connect(db_path)
	c = db.cursor()
	if make_db:
		CreateDB(c)
		db.commit()

	q = 'insert into docs (title, authors, year, file) values(?, ?, ?, ?)'
	authors = paper.GetAuthor()
	title = paper.GetTitle()
	year = paper.GetYear()
	filename = os.path.basename(paper.GetFile())

	if isinstance(authors, list):
		db_authors = ', '.join(authors)
	else:
		db_authors = authors
	if isinstance(authors, list):
		#file_authors = '_'.join([x.replace(' ', '') for x in authors])
		file_authors = '_'.join(authors)
	else:
		file_authors = authors
	#else:
	#	file_authors = authors.replace(' ', '')
	
	#name = paper.GetTitle().replace(' ', '') + '_' + file_authors + '.pdf'
	# Use an MD5 hash of name+authors
	while 1:
		name=hashlib.md5(paper.GetTitle()+'_' +file_authors).hexdigest()+'.pdf'

		# check for existence
		if not os.path.exists(pdf_repo+'/'+name):
			break
		else:
			file_authors += '_'

	c.execute(q, (title, db_authors, year, name))
	db.commit()
	c.close()
	db.close()

	paper.SetAuthors(db_authors)

	# move the documents to the repository
	# construct the name
	shutil.move(paper.GetFile(), pdf_repo + '/' + name)
	paper.SetFileName(name)

