import sqlite3
import os

pdf_main = os.getenv('HOME')+'/.pdflib'
pdf_repo = pdf_main+'/docs'
db_path = pdf_main+'/pdflib.db'

class Paper:
	def __init__(self, author = None, title = None, year = None,
				filename = None,
				venue = None):
		self.__author = author
		self.__title = title
		self.__year = year
		self.__file = filename
		self.__venue = venue
	
	def get_title(self):
		return self.__title

	def get_year(self):
		return self.__year

	def get_author(self):
		return self.__author

	def get_file(self):
		return self.__file

	def get_venue(self):
		return self.__venue

	def set_title(self, title):
		self.title = title

	def set_file(self, fn):
		self.__file = fn

	def set_author(self, author):
		self.__author = author
	
	def set_venue(self, venue):
		self.__venue = venue
	
	def set_year(self, year):
		self.__year = year

	def is_valid(self):
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

def create_db(cursor):
	q = 'create table docs (id integer primary key not null, title text, authors text, year integer, file text, venue text)'
	cursor.execute(q)

def load_docs_from_db():
	make_db = False
	if not os.path.exists(db_path):
		make_db = True
		init_repo()

	db = sqlite3.connect(db_path)
	c = db.cursor()
	if make_db:
		create_db(c)
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
	if paper == None or not paper.is_valid():
		return

	make_db = False
	if not os.path.exists(db_path):
		make_db = True
		init_repo()
	
	db = sqlite3.connect(db_path)
	c = db.cursor()
	if make_db:
		create_db(c)
		db.commit()

	q = 'insert into docs (title, authors, year, file) values(?, ?, ?, ?)'
	authors = paper.get_author()
	title = paper.get_title()
	year = paper.get_year()
	filename = os.path.basename(paper.get_file())

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
	
	#name = paper.get_title().replace(' ', '') + '_' + file_authors + '.pdf'
	# Use an MD5 hash of name+authors
	while 1:
		name=hashlib.md5(paper.get_title()+'_' +file_authors).hexdigest()+'.pdf'

		# check for existence
		if not os.path.exists(pdf_repo+'/'+name):
			break
		else:
			file_authors += '_'

	c.execute(q, (title, db_authors, year, name))
	db.commit()
	c.close()
	db.close()

	paper.set_author(db_authors)

	# move the documents to the repository
	# construct the name
	shutil.move(paper.get_file(), pdf_repo + '/' + name)
	paper.set_file(name)

